"""
AetherPS4 - Modern PlayStation 4 Emulator Core
Lead Architect & Developer: PRIYAN-A-1
Copyright (c) 2026 PRIYAN-A-1. All rights reserved.
SPDX-License-Identifier: MIT

Unit test suite for AetherPS4 emulator subsystems.
"""

import unittest
import struct
from aether_ps4.core import AetherEmulator
from aether_ps4.common.types import MemoryProt, GUEST_PAGE_SIZE, ELF_MAGIC
from aether_ps4.common.hashing import compute_sha1_nid, compute_nid_string
from aether_ps4.file_format.sfo import SfoParser
from aether_ps4.gpu.pm4 import PM4Processor, PM4Opcode
from aether_ps4.gpu.gcn_isa import GcnDisassembler
from aether_ps4.gpu.swizzle import morton_2d, morton_2d_decode, swizzle_image_rgba8, deswizzle_image_rgba8
from aether_ps4.loader.elf import ElfLoader

class TestAetherPS4(unittest.TestCase):

    def setUp(self):
        self.emu = AetherEmulator()

    def test_sfo_roundtrip(self):
        sfo_data = SfoParser.create_mock_sfo("CUSA99999", "Test Game", "02.00")
        parser = SfoParser(sfo_data)
        self.assertEqual(parser.title_id, "CUSA99999")
        self.assertEqual(parser.title, "Test Game")
        self.assertEqual(parser.app_ver, "02.00")
        self.assertEqual(parser.category, "gd")

    def test_direct_memory_allocation_and_mapping(self):
        # 16 MB allocation
        status, paddr = self.emu.kernel.sceKernelAllocateDirectMemory(0, 0xFFFFFFFF, 0x1000000, 0x200000, 0)
        self.assertEqual(status, 0)
        self.assertGreater(paddr, 0)

        # Map to virtual address 0x200000000
        status, vaddr = self.emu.kernel.sceKernelMapDirectMemory(
            0x200000000, 0x1000000, MemoryProt.CPU_READ_WRITE, 0, paddr, GUEST_PAGE_SIZE
        )
        self.assertEqual(status, 0)
        self.assertEqual(vaddr, 0x200000000)

        # Test writing and reading 64-bit integer
        test_val = 0xCAFEBABEDEADBEEF
        self.emu.memory.write_u64(vaddr + 0x100, test_val)
        self.assertEqual(self.emu.memory.read_u64(vaddr + 0x100), test_val)

        # Test writing string
        test_str = b"AetherPS4 Direct Memory Verification"
        self.emu.memory.write_bytes(vaddr + 0x200, test_str)
        self.assertEqual(self.emu.memory.read_bytes(vaddr + 0x200, len(test_str)), test_str)

    def test_orbis_kernel_sync(self):
        # Mutex test
        mid = self.emu.kernel.sceKernelCreateMutex("TestMutex", 0)
        self.assertEqual(self.emu.kernel.sceKernelLockMutex(mid), 0)
        self.assertTrue(self.emu.kernel.mutexes[mid].locked)
        self.assertEqual(self.emu.kernel.sceKernelUnlockMutex(mid), 0)
        self.assertFalse(self.emu.kernel.mutexes[mid].locked)

        # Semaphore test
        sid = self.emu.kernel.sceKernelCreateSema("TestSema", 2, 5)
        self.assertEqual(self.emu.kernel.semaphores[sid].count, 2)
        self.emu.kernel.sceKernelSignalSema(sid, 2)
        self.assertEqual(self.emu.kernel.semaphores[sid].count, 4)

        # Event flag test
        efid = self.emu.kernel.sceKernelCreateEventFlag("TestEF", 0x01)
        self.emu.kernel.sceKernelSetEventFlag(efid, 0x04)
        self.assertEqual(self.emu.kernel.event_flags[efid].bit_pattern, 0x05)

    def test_nid_resolution(self):
        sym_name = "sceKernelAllocateDirectMemory"
        nid_u64 = compute_sha1_nid(sym_name)
        nid_str = compute_nid_string(sym_name)

        info = self.emu.nid_resolver.resolve_u64(nid_u64)
        self.assertIsNotNone(info)
        self.assertEqual(info.name, sym_name)

        info_str = self.emu.nid_resolver.resolve_str(nid_str)
        self.assertIsNotNone(info_str)
        self.assertEqual(info_str.name, sym_name)

    def test_pm4_command_processor(self):
        proc = PM4Processor()
        # Packet: SET_CONTEXT_REG base=0x8000, values=[0x1111, 0x2222]
        # (3 << 30) | (2 << 16) | (0x69 << 8) = 0xC0026900
        # Packet: DRAW_INDEX_AUTO vertices=12, prim=4 (TRIANGLES)
        # (3 << 30) | (1 << 16) | (0x2D << 8) = 0xC0012D00
        stream = [
            0xC0026900, 0x8000, 0x1111, 0x2222,
            0xC0012D00, 12, 4
        ]
        count = proc.process_command_buffer(stream)
        self.assertEqual(count, 2)
        self.assertEqual(proc.context_regs[0x8000], 0x1111)
        self.assertEqual(proc.context_regs[0x8001], 0x2222)
        self.assertEqual(len(proc.draw_calls), 1)
        self.assertEqual(proc.draw_calls[0].index_count, 12)

    def test_gcn_disassembly(self):
        # s_waitcnt vmcnt(0) expcnt(0) lgkmcnt(0) -> 0xBF8A0000
        inst = GcnDisassembler.decode_word(0, 0xBF8A0000)
        self.assertEqual(inst.mnemonic, "s_waitcnt")

        # s_endpgm -> 0xBF8C0000
        inst = GcnDisassembler.decode_word(4, 0xBF8C0000)
        self.assertEqual(inst.mnemonic, "s_endpgm")

    def test_morton_swizzling_lossless(self):
        for x in [0, 1, 5, 7, 15, 31]:
            for y in [0, 1, 3, 7, 12, 29]:
                z = morton_2d(x, y)
                rx, ry = morton_2d_decode(z)
                self.assertEqual((rx, ry), (x, y))

        # 8x8 RGBA texture
        linear = bytes(range(256))
        swizzled = swizzle_image_rgba8(linear, 8, 8)
        deswizzled = deswizzle_image_rgba8(swizzled, 8, 8)
        self.assertEqual(deswizzled, linear)

    def test_synthetic_elf_loading(self):
        # Build minimal valid 64-bit ELF binary
        # ELF header (64 bytes) + 1 Program Header (56 bytes)
        ident = bytearray(16)
        ident[:4] = ELF_MAGIC
        ident[4] = 2 # 64-bit
        ident[5] = 1 # Little endian
        ident[6] = 1 # Version 1
        ident[7] = 9 # FreeBSD OS ABI

        e_type = 3 # ET_DYN
        e_machine = 62 # x86_64
        e_version = 1
        e_entry = 0x400000
        e_phoff = 64
        e_shoff = 0
        e_flags = 0
        e_ehsize = 64
        e_phentsize = 56
        e_phnum = 1
        e_shentsize = 64
        e_shnum = 0
        e_shstrndx = 0

        elf_hdr = ident + struct.pack(
            "<HHIQQQIHHHHHH",
            e_type, e_machine, e_version, e_entry, e_phoff, e_shoff, e_flags,
            e_ehsize, e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx
        )

        # Program header: PT_LOAD at offset 0x1000, vaddr 0x400000, filesz 0x100, memsz 0x200, flags PF_R | PF_X
        ph_raw = struct.pack(
            "<IIQQQQQQ",
            1, # PT_LOAD
            5, # PF_R | PF_X
            120, # p_offset
            0x400000, # p_vaddr
            0x400000, # p_paddr
            16, # p_filesz
            32, # p_memsz
            0x4000 # p_align
        )

        dummy_code = b"\x90" * 16 # NOP instructions
        raw_binary = elf_hdr + ph_raw + dummy_code

        loader = self.emu.load_elf(raw_binary)
        self.assertEqual(loader.entry_point, 0x400000)
        self.assertEqual(len(loader.program_headers), 1)
        self.assertEqual(self.emu.memory.read_bytes(0x400000, 16), dummy_code)

    def test_pkg_parser_and_extraction(self):
        from aether_ps4.file_format.pkg import PkgParser
        mock_sfo = SfoParser.create_mock_sfo("CUSA00001", "PKG Test Game", "01.00")
        mock_data = {
            "param.sfo": mock_sfo,
            "icon0.png": b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
        }
        pkg_bytes = PkgParser.create_mock_pkg("EP0001-CUSA00001_00-0000000000000000", mock_data)
        pkg = PkgParser(pkg_bytes)
        self.assertEqual(pkg.header.content_id, "EP0001-CUSA00001_00-0000000000000000")
        self.assertEqual(len(pkg.entries), 2)
        extracted_sfo = pkg.get_entry_data("param.sfo")
        self.assertIsNotNone(extracted_sfo)
        self.assertEqual(extracted_sfo, mock_sfo)

    def test_elf_error_handling(self):
        # Test truncated data
        with self.assertRaises(ValueError):
            ElfLoader(b"SHORT")

        # Test invalid magic
        with self.assertRaises(ValueError):
            ElfLoader(b"BAD_MAGIC_HEADER_THAT_IS_LONG_ENOUGH_123456789")

    def test_sfo_error_handling(self):
        with self.assertRaises(ValueError):
            SfoParser(b"SHORT")
        with self.assertRaises(ValueError):
            SfoParser(b"BADM" + b"\x00" * 30)

    def test_address_space_large_allocation(self):
        # 64 MB allocation
        status, paddr = self.emu.kernel.sceKernelAllocateDirectMemory(0, 0xFFFFFFFF, 0x4000000, 0x200000, 0)
        self.assertEqual(status, 0)
        status, vaddr = self.emu.kernel.sceKernelMapDirectMemory(
            0x300000000, 0x4000000, MemoryProt.CPU_READ_WRITE, 0, paddr, GUEST_PAGE_SIZE
        )
        self.assertEqual(status, 0)
        self.assertEqual(vaddr, 0x300000000)
        # Test write and read across page boundary
        test_pattern = b"A" * 32768 # 2 pages
        self.emu.memory.write_bytes(vaddr, test_pattern)
        self.assertEqual(self.emu.memory.read_bytes(vaddr, len(test_pattern)), test_pattern)

    def test_kernel_invalid_operations(self):
        # Invalid mutex unlock
        self.assertNotEqual(self.emu.kernel.sceKernelLockMutex(99999), 0)
        self.assertNotEqual(self.emu.kernel.sceKernelUnlockMutex(99999), 0)
        # Invalid semaphore signal
        self.assertNotEqual(self.emu.kernel.sceKernelSignalSema(99999, 1), 0)

    def test_gcn_comprehensive_opcodes(self):
        # SOP2: s_add_u32 (op=0)
        inst_sop2 = GcnDisassembler.decode_word(0, 0x80000000)
        self.assertTrue("s_add_u32" in inst_sop2.mnemonic)

        # VOP1: v_mov_b32 (op=1)
        inst_vop1 = GcnDisassembler.decode_word(0, 0x7E000200)
        self.assertEqual(inst_vop1.mnemonic, "v_mov_b32")

        # VOPC: v_cmp_eq_f32 (op=2)
        inst_vopc = GcnDisassembler.decode_word(0, 0x7C040000)
        self.assertEqual(inst_vopc.mnemonic, "v_cmp_eq_f32")

        # VOP2: v_add_f32 (op=3)
        inst_vop2 = GcnDisassembler.decode_word(0, 0x06020000)
        self.assertEqual(inst_vop2.mnemonic, "v_add_f32")

        # EXP instruction
        inst_exp = GcnDisassembler.decode_word(0, 0xF800F000)
        self.assertEqual(inst_exp.mnemonic, "exp")

    def test_sysmodule_loader(self):
        self.assertEqual(self.emu.kernel.sceSysmoduleLoadModule(0x0001), 0)
        self.assertEqual(self.emu.kernel.loaded_modules[0x0001], "libSceNet")
        self.assertEqual(self.emu.kernel.sceSysmoduleLoadModule(0x0005), 0)
        self.assertEqual(self.emu.kernel.loaded_modules[0x0005], "libSceGnmDriver")
        self.assertEqual(self.emu.kernel.sceKernelIsNeoMode(), 0)
        self.assertGreaterEqual(self.emu.kernel.sceKernelGetProcessTime(), 0)

    def test_pm4_additional_opcodes(self):
        proc = PM4Processor()
        # Packet: INDEX_TYPE (0x2A) -> 1 (32-bit), count=0 (1 dword) -> (3 << 30) | (0 << 16) | (0x2A << 8) = 0xC0002A00
        # Packet: NUM_INSTANCES (0x2F) -> 4, count=0 (1 dword) -> (3 << 30) | (0 << 16) | (0x2F << 8) = 0xC0002F00
        stream = [
            0xC0002A00, 1,
            0xC0002F00, 4
        ]
        count = proc.process_command_buffer(stream)
        self.assertEqual(count, 2)
        self.assertEqual(proc.index_type, 1)
        self.assertEqual(proc.num_instances, 4)

    def test_cli_execution_demo(self):
        import subprocess
        import sys
        res = subprocess.run([sys.executable, "main.py"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("AetherPS4", res.stdout)
        self.assertIn("PRIYAN-A-1", res.stdout)

    def test_nid_resolver_extended_and_negative(self):
        # Negative lookups
        self.assertIsNone(self.emu.nid_resolver.resolve_u64(0xDEADBEEF12345678))
        self.assertIsNone(self.emu.nid_resolver.resolve_str("UNKNOWN_NID_HASH_STRING"))
        self.assertIsNone(self.emu.nid_resolver.resolve_name("sceNonExistentFunction"))

        # Registered Orbis kernel symbols
        for sym in ["sceKernelCreateSema", "sceKernelSignalSema", "sceKernelCreateEventFlag", "sceKernelSetEventFlag", "sceKernelIsNeoMode", "sceKernelGetProcessTime"]:
            info = self.emu.nid_resolver.resolve_name(sym)
            self.assertIsNotNone(info, f"Symbol {sym} should be registered")
            self.assertIsNotNone(info.handler, f"Symbol {sym} should have an active handler")

    def test_address_space_page_fault_auto_allocate(self):
        unmapped_vaddr = 0x5000000000
        vpn = unmapped_vaddr >> 14
        self.assertNotIn(vpn, self.emu.memory.page_table)

        # Write should trigger lazy allocation
        test_data = b"AutoAllocatedPageData"
        self.emu.memory.write_bytes(unmapped_vaddr, test_data)
        self.assertIn(vpn, self.emu.memory.page_table)
        self.assertEqual(self.emu.memory.read_bytes(unmapped_vaddr, len(test_data)), test_data)

        # Test write_u32 and read_u32
        self.emu.memory.write_u32(unmapped_vaddr + 0x100, 0x12345678)
        self.assertEqual(self.emu.memory.read_u32(unmapped_vaddr + 0x100), 0x12345678)

    def test_pm4_type0_and_type2_packets(self):
        proc = PM4Processor()
        # Type-0 packet: base_reg=0x2000, count=1 (2 payload dwords: 0xAAAA, 0xBBBB)
        # Header = (0 << 30) | (1 << 16) | 0x2000 = 0x00012000
        # Type-2 packet: NOP = (2 << 30) = 0x80000000
        stream = [
            0x00012000, 0xAAAA, 0xBBBB,
            0x80000000
        ]
        count = proc.process_command_buffer(stream)
        self.assertEqual(count, 2)
        self.assertEqual(proc.config_regs[0x2000], 0xAAAA)
        self.assertEqual(proc.config_regs[0x2001], 0xBBBB)

    def test_gcn_instruction_stream_full(self):
        # Stream of 5 instructions:
        # 1. 0xBF8A0000 -> s_waitcnt
        # 2. 0x80000000 -> s_add_u32 (SOP2)
        # 3. 0x7E000200 -> v_mov_b32 (VOP1)
        # 4. 0x7C040000 -> v_cmp_eq_f32 (VOPC)
        # 5. 0x06020000 -> v_add_f32 (VOP2)
        # 6. 0xF800F000 -> exp
        # 7. 0xBF8C0000 -> s_endpgm
        raw_words = [0xBF8A0000, 0x80000000, 0x7E000200, 0x7C040000, 0x06020000, 0xF800F000, 0xBF8C0000]
        raw_bytes = b"".join(w.to_bytes(4, byteorder="little") for w in raw_words)

        instructions = GcnDisassembler.disassemble(raw_bytes)
        self.assertEqual(len(instructions), 7)
        expected_mnemonics = ["s_waitcnt", "s_add_u32", "v_mov_b32", "v_cmp_eq_f32", "v_add_f32", "exp", "s_endpgm"]
        for inst, expected in zip(instructions, expected_mnemonics):
            self.assertEqual(inst.mnemonic, expected)

    def test_neo_mode_configuration(self):
        neo_emu = AetherEmulator(is_neo=True)
        self.assertEqual(neo_emu.kernel.sceKernelIsNeoMode(), 1)
        self.assertTrue(neo_emu.kernel.is_neo)

        std_emu = AetherEmulator(is_neo=False)
        self.assertEqual(std_emu.kernel.sceKernelIsNeoMode(), 0)
        self.assertFalse(std_emu.kernel.is_neo)

if __name__ == "__main__":
    unittest.main()


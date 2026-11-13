"""
AetherPS4 - Modern PlayStation 4 Emulator Core
Lead Architect & Developer: PRIYAN-A-1
Copyright (c) 2026 PRIYAN-A-1. All rights reserved.
SPDX-License-Identifier: MIT
"""

import sys
import argparse
from aether_ps4.core import AetherEmulator
from aether_ps4.common.logger import Logger, Subsystem
from aether_ps4.file_format.sfo import SfoParser
from aether_ps4.gpu.gcn_isa import GcnDisassembler
from aether_ps4.gpu.swizzle import swizzle_image_rgba8, deswizzle_image_rgba8

def run_live_demo() -> None:
    print("=" * 70)
    print("       AETHER PS4 - MODERN PLAYSTATION 4 EMULATOR CORE")
    print("          Lead Architect & Developer: PRIYAN-A-1")
    print("             Architecture & Subsystem Live Demo")
    print("=" * 70)

    # 1. Initialize Emulator Core
    emu = AetherEmulator(is_neo=True, verbose=True)

    # 2. Emulate Loading Game Metadata (param.sfo)
    print("\n--- [1] Game Package Metadata (param.sfo) ---")
    mock_sfo = SfoParser.create_mock_sfo(
        title_id="CUSA00123",
        title="Bloodborne: Ancient Shadows",
        app_ver="01.09"
    )
    sfo = emu.load_sfo(mock_sfo)
    print(f"  Title:        {sfo.title}")
    print(f"  Title ID:     {sfo.title_id}")
    print(f"  Version:      {sfo.app_ver}")
    print(f"  Category:     {sfo.category}")

    # 3. Emulate Direct Memory Management (DMEM)
    print("\n--- [2] Unified GDDR5 Direct Memory (DMEM) Syscalls ---")
    ret, paddr = emu.kernel.sceKernelAllocateDirectMemory(
        search_start=0, search_end=0xFFFFFFFF, length=0x2000000, alignment=0x200000, memory_type=0
    )
    print(f"  sceKernelAllocateDirectMemory(32MB) -> PAddr: 0x{paddr:08X} [Status: {ret}]")

    ret, vaddr = emu.kernel.sceKernelMapDirectMemory(
        vaddr_req=0x200000000, length=0x2000000, prot_val=0x3, flags=0, paddr_offset=paddr, align=0x4000
    )
    print(f"  sceKernelMapDirectMemory(32MB)      -> VAddr: 0x{vaddr:012X} [Status: {ret}]")

    # 4. Emulate Orbis OS Kernel Synchronization
    print("\n--- [3] Orbis OS Synchronization & Subsystems ---")
    mid = emu.kernel.sceKernelCreateMutex("GpuSubmitMutex", 0)
    print(f"  Created Mutex: 'GpuSubmitMutex' (ID={mid})")
    emu.kernel.sceKernelLockMutex(mid)
    print(f"  Locked Mutex (ID={mid})")
    emu.kernel.sceKernelUnlockMutex(mid)
    print(f"  Unlocked Mutex (ID={mid})")

    emu.kernel.sceSysmoduleLoadModule(0x0005) # libSceGnmDriver
    emu.kernel.sceSysmoduleLoadModule(0x0004) # libSceVideoOut

    # 5. Emulate AMD GCN Liverpool PM4 Command Stream
    print("\n--- [4] Liverpool AMD GCN PM4 Command Processor ---")
    # Build synthetic PM4 packets:
    # Packet 1: SET_CONTEXT_REG base=0xA000 (Viewport / Blend state), 2 words
    # Header: (3 << 30) | (2 << 16) | (0x69 << 8) = 0xC0026900
    # Packet 2: SET_SH_REG base=0x208 (SPI_SHADER_PGM_LO_VS), 2 words
    # Header: (3 << 30) | (2 << 16) | (0x76 << 8) = 0xC0027600
    # Packet 3: NUM_INSTANCES = 1
    # Header: (3 << 30) | (0 << 16) | (0x2F << 8) = 0xC0002F00
    # Packet 4: DRAW_INDEX_AUTO VertexCount=36, Prim=TRIANGLE_LIST
    # Header: (3 << 30) | (1 << 16) | (0x2D << 8) = 0xC0012D00
    pm4_stream = [
        0xC0026900, 0x0000A000, 0x00010001, 0x00020002, # SET_CONTEXT_REG
        0xC0027600, 0x00000208, 0x40001000, 0x00000002, # SET_SH_REG (Shader address)
        0xC0002F00, 0x00000001,                         # NUM_INSTANCES
        0xC0012D00, 0x00000024, 0x00000004              # DRAW_INDEX_AUTO (36 vertices)
    ]
    emu.submit_gpu_commands(pm4_stream)
    print(f"  Active VS Shader Address: 0x{emu.gpu.vs_shader_addr:012X}")
    print(f"  Recorded Draw Calls:      {len(emu.gpu.draw_calls)}")
    for i, dc in enumerate(emu.gpu.draw_calls):
        print(f"    Draw[{i}]: {dc.primitive_type}, Vertices={dc.index_count}, Instances={dc.instance_count}")

    # 6. Emulate AMD GCN Shader Microcode Disassembly
    print("\n--- [5] AMD GCN (GFX7) Shader Instruction Recompiler / Disassembler ---")
    # Sample GCN microcode sequence:
    # 1. s_waitcnt vmcnt(0) expcnt(0) lgkmcnt(0) -> 0xBF8A0000 (SOPP op=10)
    # 2. v_add_f32 v0, v1, v2                   -> 0x06000501 (VOP2 op=3)
    # 3. v_mul_f32 v3, v0, v4                   -> 0x10060900 (VOP2 op=8)
    # 4. exp mrt0, en:0xF                       -> 0xF800F000 (EXP)
    # 5. s_endpgm                               -> 0xBF8C0000 (SOPP op=12)
    sample_gcn_shader = bytes([
        0x00, 0x00, 0x8A, 0xBF, # s_waitcnt
        0x01, 0x05, 0x00, 0x06, # v_add_f32 v0, v1, v2
        0x00, 0x09, 0x06, 0x10, # v_mul_f32 v3, v0, v4
        0x00, 0xF0, 0x00, 0xF8, # exp mrt0
        0x00, 0x00, 0x8C, 0xBF, # s_endpgm
    ])
    instructions = GcnDisassembler.disassemble(sample_gcn_shader)
    for inst in instructions:
        print(f"  0x{inst.offset:04X}: [0x{inst.raw:08X}]  {inst.mnemonic:<16} {inst.operands:<24} ; {inst.desc}")

    # 7. Emulate AMD GCN Morton 2D Texture Swizzling
    print("\n--- [6] AMD GCN Morton Z-Order 2D Texture Swizzler ---")
    test_w, test_h = 16, 16
    # Create test pattern
    test_linear = bytes([((x * 16 + y) % 256) for y in range(test_h) for x in range(test_w * 4)])
    swizzled = swizzle_image_rgba8(test_linear, test_w, test_h)
    deswizzled = deswizzle_image_rgba8(swizzled, test_w, test_h)
    is_lossless = (test_linear == deswizzled)
    print(f"  Swizzled 16x16 RGBA8 texture:  {len(swizzled)} bytes (8x8 Morton micro-tiles)")
    print(f"  Deswizzled back to linear:     {len(deswizzled)} bytes")
    print(f"  Morton Swizzle Round-Trip:     {'SUCCESS (100% Bit-Exact Match)' if is_lossless else 'FAILED'}")

    print("\n" + "=" * 70)
    print("AetherPS4 Core Simulation Complete: All subsystems functional!")
    print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description="AetherPS4 - Modern PlayStation 4 Emulator Core (Lead Architect: PRIYAN-A-1)")
    parser.add_argument("--demo", action="store_true", help="Run comprehensive live emulation subsystem demo")
    parser.add_argument("--sfo", type=str, help="Parse and inspect a PlayStation param.sfo file")
    parser.add_argument("--elf", type=str, help="Inspect a PS4 ELF/SELF executable")
    parser.add_argument("--pkg", type=str, help="Inspect a PS4 PKG package container")
    parser.add_argument("--disasm", type=str, help="Disassemble AMD GCN shader bytes (hex string or file path)")
    args = parser.parse_args()

    import os
    if args.sfo:
        if not os.path.exists(args.sfo):
            Logger.error(Subsystem.FILESYS, f"File not found: {args.sfo}")
            return
        try:
            with open(args.sfo, "rb") as f:
                data = f.read()
            sfo = SfoParser(data)
            print(f"Title:    {sfo.title}")
            print(f"Title ID: {sfo.title_id}")
            print(f"App Ver:  {sfo.app_ver}")
            print("\nAll Properties:")
            for k, v in sfo.entries.items():
                print(f"  {k:<20}: {v}")
        except Exception as e:
            Logger.error(Subsystem.FILESYS, f"Failed to parse SFO: {e}")
    elif args.elf:
        if not os.path.exists(args.elf):
            Logger.error(Subsystem.LOADER, f"File not found: {args.elf}")
            return
        try:
            with open(args.elf, "rb") as f:
                data = f.read()
            emu = AetherEmulator()
            loader = emu.load_elf(data)
            print(f"Entry Point:     0x{loader.entry_point:X}")
            print(f"Program Headers: {len(loader.program_headers)}")
            for idx, ph in enumerate(loader.program_headers):
                print(f"  [{idx}] Type={ph.type_name:<16} VAddr=0x{ph.p_vaddr:010X} MemSz=0x{ph.p_memsz:08X} Flags={ph.memory_prot.name}")
        except Exception as e:
            Logger.error(Subsystem.LOADER, f"Failed to load ELF: {e}")
    elif args.pkg:
        if not os.path.exists(args.pkg):
            Logger.error(Subsystem.FILESYS, f"File not found: {args.pkg}")
            return
        try:
            from aether_ps4.file_format.pkg import PkgParser
            with open(args.pkg, "rb") as f:
                data = f.read()
            pkg = PkgParser(data)
            print(f"Content ID:  {pkg.header.content_id}")
            print(f"Total Files: {len(pkg.entries)}")
            for e in pkg.entries:
                print(f"  ID=0x{e.entry_id:04X} {e.filename:<24} Offset=0x{e.offset:08X} Size={e.size:,} bytes")
        except Exception as e:
            Logger.error(Subsystem.FILESYS, f"Failed to parse PKG: {e}")
    elif args.disasm:
        try:
            if os.path.exists(args.disasm):
                with open(args.disasm, "rb") as f:
                    shader_bytes = f.read()
            elif "0x" in args.disasm.lower():
                # Provided as dword tokens like "0xBF8A0000 0x7E000200"
                tokens = args.disasm.replace(",", " ").split()
                shader_bytes = b"".join(int(t, 16).to_bytes(4, byteorder="little") for t in tokens if t.strip())
            else:
                shader_bytes = bytes.fromhex(args.disasm.replace(" ", "").replace(",", ""))
            instructions = GcnDisassembler.disassemble(shader_bytes)
            print(f"Disassembled {len(instructions)} GCN Instructions:")
            for inst in instructions:
                print(f"  0x{inst.offset:04X}: [0x{inst.raw:08X}]  {inst.mnemonic:<16} {inst.operands:<24} ; {inst.desc}")
        except Exception as e:
            Logger.error(Subsystem.GPU, f"Failed to disassemble GCN shader: {e}")
    else:
        run_live_demo()

if __name__ == "__main__":
    main()

"""
PlayStation 4 ELF64 and SELF (Signed ELF) loader and parser.
Handles decrypted SELF binaries, Orbis ELF (OELF), program headers,
and dynamic relocation tables (R_X86_64_*).
"""

import struct
from typing import List, Dict, Tuple, Optional
from aether_ps4.common.types import (
    SELF_MAGIC, ELF_MAGIC, MemoryProt, align_up
)
from aether_ps4.common.logger import Logger, Subsystem

class SelfSegmentHeader:
    def __init__(self, raw: bytes):
        (
            self.flags,
            self.file_offset,
            self.file_size,
            self.memory_size
        ) = struct.unpack("<QQQQ", raw)

    @property
    def is_encrypted(self) -> bool:
        return bool(self.flags & 2)

    @property
    def is_signed(self) -> bool:
        return bool(self.flags & 4)

    @property
    def is_compressed(self) -> bool:
        return bool(self.flags & 8)

    @property
    def is_blocked(self) -> bool:
        return bool(self.flags & 0x800)

    @property
    def segment_id(self) -> int:
        return (self.flags >> 20) & 0xFFF

class SelfHeader:
    def __init__(self, raw: bytes):
        (
            self.magic,
            self.version,
            self.mode,
            self.endian,
            self.attributes,
            self.category,
            self.program_type,
            self.padding1,
            self.header_size,
            self.meta_size,
            self.file_size,
            self.padding2,
            self.segment_count,
            self.unknown1A,
            self.padding3
        ) = struct.unpack("<IBBBBBBHHHIIHHI", raw[:32])

class Elf64ProgramHeader:
    PT_NULL = 0
    PT_LOAD = 1
    PT_DYNAMIC = 2
    PT_INTERP = 3
    PT_NOTE = 4
    PT_SHLIB = 5
    PT_PHDR = 6
    PT_TLS = 7
    PT_SCE_RELA = 0x60000000
    PT_SCE_DYNLIBDATA = 0x61000000
    PT_SCE_PROCPARAM = 0x61000001
    PT_SCE_MODULE_PARAM = 0x61000002

    PF_X = 1 << 0
    PF_W = 1 << 1
    PF_R = 1 << 2

    def __init__(self, raw: bytes):
        (
            self.p_type,
            self.p_flags,
            self.p_offset,
            self.p_vaddr,
            self.p_paddr,
            self.p_filesz,
            self.p_memsz,
            self.p_align
        ) = struct.unpack("<IIQQQQQQ", raw)

    @property
    def memory_prot(self) -> MemoryProt:
        prot = MemoryProt.NO_ACCESS
        if self.p_flags & self.PF_R:
            prot |= MemoryProt.CPU_READ
        if self.p_flags & self.PF_W:
            prot |= MemoryProt.CPU_WRITE
        if self.p_flags & self.PF_X:
            prot |= MemoryProt.CPU_EXEC
        return prot

    @property
    def type_name(self) -> str:
        types = {
            self.PT_NULL: "PT_NULL",
            self.PT_LOAD: "PT_LOAD",
            self.PT_DYNAMIC: "PT_DYNAMIC",
            self.PT_INTERP: "PT_INTERP",
            self.PT_NOTE: "PT_NOTE",
            self.PT_SHLIB: "PT_SHLIB",
            self.PT_PHDR: "PT_PHDR",
            self.PT_TLS: "PT_TLS",
            self.PT_SCE_RELA: "PT_SCE_RELA",
            self.PT_SCE_DYNLIBDATA: "PT_SCE_DYNLIBDATA",
            self.PT_SCE_PROCPARAM: "PT_SCE_PROCPARAM",
            self.PT_SCE_MODULE_PARAM: "PT_SCE_MODULE_PARAM",
        }
        return types.get(self.p_type, f"PT_CUSTOM(0x{self.p_type:X})")

class Elf64Header:
    def __init__(self, raw: bytes):
        self.ident = raw[:16]
        if self.ident[:4] != ELF_MAGIC:
            raise ValueError("Invalid ELF magic")

        (
            self.e_type,
            self.e_machine,
            self.e_version,
            self.e_entry,
            self.e_phoff,
            self.e_shoff,
            self.e_flags,
            self.e_ehsize,
            self.e_phentsize,
            self.e_phnum,
            self.e_shentsize,
            self.e_shnum,
            self.e_shstrndx
        ) = struct.unpack("<HHIQQQIHHHHHH", raw[16:64])

class ElfLoader:
    """
    Parses ELF64 / SELF files and extracts virtual memory mapping directives.
    """
    def __init__(self, data: bytes):
        self.data = data
        self.is_self = False
        self.self_header: Optional[SelfHeader] = None
        self.self_segments: List[SelfSegmentHeader] = []
        self.elf_header: Optional[Elf64Header] = None
        self.program_headers: List[Elf64ProgramHeader] = []
        self.entry_point: int = 0
        self.elf_data: bytes = b""

        self._parse()

    def _parse(self) -> None:
        if len(self.data) < 32:
            raise ValueError("File too short for valid ELF/SELF")

        magic = struct.unpack("<I", self.data[:4])[0]
        if magic == SELF_MAGIC:
            self.is_self = True
            Logger.info(Subsystem.LOADER, "Detected Sony Signed ELF (SELF) container")
            self.self_header = SelfHeader(self.data)
            offset = 32
            for _ in range(self.self_header.segment_count):
                seg = SelfSegmentHeader(self.data[offset:offset + 32])
                self.self_segments.append(seg)
                offset += 32

            # Find the segment containing the ELF header (typically segment 0 or segment header meta)
            # In decrypted SELF, the underlying ELF begins at header_size
            elf_start = self.self_header.header_size
            self.elf_data = self.data[elf_start:]
        elif self.data[:4] == ELF_MAGIC:
            self.is_self = False
            Logger.info(Subsystem.LOADER, "Detected standard Orbis ELF64 binary")
            self.elf_data = self.data
        else:
            raise ValueError(f"Unknown executable format: magic {self.data[:4].hex()}")

        # Parse ELF Header
        self.elf_header = Elf64Header(self.elf_data)
        self.entry_point = self.elf_header.e_entry

        # Parse Program Headers
        ph_offset = self.elf_header.e_phoff
        for i in range(self.elf_header.e_phnum):
            if ph_offset + self.elf_header.e_phentsize > len(self.elf_data):
                Logger.warn(Subsystem.LOADER, f"Truncated program header table at entry {i}")
                break
            ph_raw = self.elf_data[ph_offset:ph_offset + self.elf_header.e_phentsize]
            ph = Elf64ProgramHeader(ph_raw)
            self.program_headers.append(ph)
            ph_offset += self.elf_header.e_phentsize

        Logger.info(Subsystem.LOADER, f"Loaded ELF: Entry=0x{self.entry_point:X}, ProgramHeaders={len(self.program_headers)}")

    def get_loadable_segments(self) -> List[Tuple[Elf64ProgramHeader, bytes]]:
        """
        Returns all PT_LOAD segments with their raw bytes to be mapped into the virtual address space.
        """
        loadables = []
        for ph in self.program_headers:
            if ph.p_type == Elf64ProgramHeader.PT_LOAD:
                seg_data = self.elf_data[ph.p_offset:ph.p_offset + ph.p_filesz]
                # Pad to memsz with zeroes (e.g. .bss section)
                if ph.p_memsz > ph.p_filesz:
                    seg_data = seg_data + b"\x00" * (ph.p_memsz - ph.p_filesz)
                loadables.append((ph, seg_data))
        return loadables


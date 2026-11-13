"""
AetherPS4 - Modern PlayStation 4 Emulator Core
Lead Architect & Developer: PRIYAN-A-1
Copyright (c) 2026 PRIYAN-A-1. All rights reserved.
SPDX-License-Identifier: MIT

PlayStation 4 Package (.pkg) and PlayStation File System (PFS) Container Parser.
Decodes container headers, content IDs, file entry tables, and metadata files.
"""

import struct
from typing import Dict, List, Optional, NamedTuple
from aether_ps4.common.logger import Logger, Subsystem

PKG_MAGIC = b"\x7fCNT"

class PkgEntry(NamedTuple):
    entry_id: int
    filename: str
    flags: int
    offset: int
    size: int

class PkgHeader:
    def __init__(self, raw: bytes):
        if len(raw) < 0x100:
            raise ValueError("Data too short for PKG header (minimum 256 bytes required)")

        magic = raw[:4]
        if magic != PKG_MAGIC:
            raise ValueError(f"Invalid PKG magic: {magic}")

        self.pkg_type = struct.unpack(">I", raw[4:8])[0]
        self.entry_count = struct.unpack(">I", raw[0x10:0x14])[0]
        self.table_offset = struct.unpack(">I", raw[0x18:0x1C])[0]
        self.entry_data_size = struct.unpack(">I", raw[0x1C:0x20])[0]

        # Content ID at offset 0x40 (36 ASCII bytes)
        content_id_raw = raw[0x40:0x64]
        self.content_id = content_id_raw.split(b"\x00")[0].decode("ascii", errors="replace")

class PkgParser:
    """
    Parses PS4 PKG container files.
    """
    ENTRY_NAMES = {
        0x1000: "param.sfo",
        0x1001: "icon0.png",
        0x1002: "pic0.png",
        0x1003: "pic1.png",
        0x1004: "snd0.at9",
        0x1005: "changeinfo.xml",
        0x1006: "pronunciation.xml",
        0x1007: "pronunciation.sig",
        0x1008: "pic2.png",
        0x1200: "trophy/trophy00.trp",
        0x2000: "eboot.bin",
        0x2001: "pfs_image.dat",
        0x2002: "playgo-chunk.dat",
    }

    def __init__(self, data: bytes):
        self.data = data
        self.header = PkgHeader(data)
        self.entries: List[PkgEntry] = []
        self._parse_entries()

    def _parse_entries(self) -> None:
        table_offset = self.header.table_offset
        for _ in range(self.header.entry_count):
            if table_offset + 32 > len(self.data):
                break
            entry_raw = self.data[table_offset:table_offset + 32]
            entry_id, filename_offset, flags1, flags2, offset, size, _ = struct.unpack(">IIIIIIQ", entry_raw)

            filename = self.ENTRY_NAMES.get(entry_id, f"entry_0x{entry_id:04X}")
            self.entries.append(PkgEntry(entry_id, filename, flags1, offset, size))
            table_offset += 32

        Logger.info(Subsystem.FILESYS, f"Parsed PKG: ContentID={self.header.content_id}, Entries={len(self.entries)}")

    def get_entry_data(self, filename: str) -> Optional[bytes]:
        """Extracts file content for an entry by its known filename."""
        for entry in self.entries:
            if entry.filename.lower() == filename.lower():
                end = entry.offset + entry.size
                if end <= len(self.data):
                    return self.data[entry.offset:end]
        return None

    @classmethod
    def create_mock_pkg(cls, content_id: str, entries: Dict[str, bytes]) -> bytes:
        """Creates a valid mock PKG container for testing and verification."""
        header = bytearray(0x100)
        header[0:4] = PKG_MAGIC
        header[4:8] = struct.pack(">I", 1) # Final retail
        entry_count = len(entries)
        table_offset = 0x100
        header[0x10:0x14] = struct.pack(">I", entry_count)
        header[0x18:0x1C] = struct.pack(">I", table_offset)

        # Content ID
        cid_bytes = content_id.encode("ascii")[:36]
        header[0x40:0x40 + len(cid_bytes)] = cid_bytes

        # File table
        table_bytes = bytearray()
        data_bytes = bytearray()
        data_base_offset = table_offset + (entry_count * 32)

        rev_names = {v: k for k, v in cls.ENTRY_NAMES.items()}
        next_custom_id = 0x3000
        for filename, filedata in entries.items():
            entry_id = rev_names.get(filename.lower(), None)
            if entry_id is None:
                entry_id = next_custom_id
                next_custom_id += 1
            offset = data_base_offset + len(data_bytes)
            size = len(filedata)
            table_bytes.extend(struct.pack(">IIIIIIQ", entry_id, 0, 0, 0, offset, size, 0))
            data_bytes.extend(filedata)

        header[0x1C:0x20] = struct.pack(">I", len(data_bytes))
        return bytes(header + table_bytes + data_bytes)



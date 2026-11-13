"""
Sony PlayStation System File Object (param.sfo) parser and generator.
Every PS4 game package contains a param.sfo holding critical metadata:
Title ID, Content ID, Application Version, Category, and Display Title.
"""

import struct
from typing import Dict, Any, Union
from aether_ps4.common.logger import Logger, Subsystem

PSF_MAGIC = b"\x00PSF"

class SfoParser:
    """
    Parses binary param.sfo files into Python dictionaries and serializes dictionaries back to SFO.
    """
    def __init__(self, data: bytes):
        self.data = data
        self.entries: Dict[str, Union[str, int, bytes]] = {}
        self._parse()

    def _parse(self) -> None:
        if len(self.data) < 20:
            raise ValueError("SFO file too small to contain valid header")

        magic, version, key_table_offset, data_table_offset, entry_count = struct.unpack("<4sIIII", self.data[:20])
        if magic != PSF_MAGIC:
            raise ValueError(f"Invalid SFO magic: {magic}")

        entry_offset = 20
        for _ in range(entry_count):
            if entry_offset + 16 > len(self.data):
                break
            key_off, data_fmt, data_len, max_len, data_off = struct.unpack("<HHIII", self.data[entry_offset:entry_offset + 16])
            entry_offset += 16

            # Read key name from key table
            abs_key_off = key_table_offset + key_off
            key_end = self.data.find(b"\x00", abs_key_off)
            key_str = self.data[abs_key_off:key_end].decode("utf-8", errors="replace")

            # Read data from data table
            abs_data_off = data_table_offset + data_off
            raw_val = self.data[abs_data_off:abs_data_off + data_len]

            if data_fmt in (0x0004, 0x0204): # UTF-8 String
                # Strip null terminators
                val = raw_val.rstrip(b"\x00").decode("utf-8", errors="replace")
            elif data_fmt == 0x0404: # Unsigned 32-bit Integer
                val = struct.unpack("<I", raw_val[:4])[0]
            else:
                val = raw_val

            self.entries[key_str] = val

        Logger.debug(Subsystem.FILESYS, f"Parsed param.sfo with {len(self.entries)} properties")

    @property
    def title_id(self) -> str:
        return str(self.entries.get("TITLE_ID", "UNKNOWN"))

    @property
    def title(self) -> str:
        return str(self.entries.get("TITLE", "Unknown Game"))

    @property
    def app_ver(self) -> str:
        return str(self.entries.get("APP_VER", "1.00"))

    @property
    def category(self) -> str:
        return str(self.entries.get("CATEGORY", "gd"))

    @classmethod
    def create_mock_sfo(cls, title_id: str, title: str, app_ver: str = "01.00") -> bytes:
        """
        Creates a valid binary param.sfo file with provided parameters.
        """
        entries_data = [
            ("APP_VER", 0x0204, (app_ver + "\x00").encode("utf-8")),
            ("CATEGORY", 0x0204, b"gd\x00\x00"),
            ("TITLE", 0x0204, (title + "\x00").encode("utf-8")),
            ("TITLE_ID", 0x0204, (title_id + "\x00").encode("utf-8")),
        ]
        # Sort keys lexicographically as required by Sony spec
        entries_data.sort(key=lambda x: x[0])

        entry_count = len(entries_data)
        header_size = 20 + (entry_count * 16)

        # Build key table
        key_table = bytearray()
        key_offsets = []
        for k, _, _ in entries_data:
            key_offsets.append(len(key_table))
            key_table.extend(k.encode("utf-8") + b"\x00")

        # Key table alignment
        key_table_pad = (4 - (len(key_table) % 4)) % 4
        key_table.extend(b"\x00" * key_table_pad)

        key_table_offset = header_size
        data_table_offset = key_table_offset + len(key_table)

        # Build data table
        data_table = bytearray()
        data_offsets = []
        for _, _, v in entries_data:
            # Align data table entries to 4 bytes
            pad = (4 - (len(data_table) % 4)) % 4
            data_table.extend(b"\x00" * pad)
            data_offsets.append(len(data_table))
            data_table.extend(v)

        # Assemble header
        buf = bytearray()
        buf.extend(struct.pack("<4sIIII", PSF_MAGIC, 0x00000101, key_table_offset, data_table_offset, entry_count))

        for idx, (k, fmt, v) in enumerate(entries_data):
            k_off = key_offsets[idx]
            d_off = data_offsets[idx]
            d_len = len(v)
            buf.extend(struct.pack("<HHIII", k_off, fmt, d_len, d_len, d_off))

        buf.extend(key_table)
        buf.extend(data_table)
        return bytes(buf)


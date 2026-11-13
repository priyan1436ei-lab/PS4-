"""
AetherPS4 - Modern PlayStation 4 Emulator Core
Lead Architect & Developer: PRIYAN-A-1
Copyright (c) 2026 PRIYAN-A-1. All rights reserved.
SPDX-License-Identifier: MIT

Common architectural constants and types.
"""

from enum import IntEnum, IntFlag
from typing import NamedTuple

# Guest architectural constants
GUEST_PAGE_BITS = 14          # PS4 Orbis OS uses 16 KB virtual pages
GUEST_PAGE_SIZE = 1 << GUEST_PAGE_BITS # 16,384 bytes
ADDRESS_SPACE_BITS = 40       # 1 Terabyte virtual user address space
MAX_VIRTUAL_ADDRESS = (1 << ADDRESS_SPACE_BITS) - 1
DEFAULT_MAPPING_BASE = 0x200000000 # 8 GB base offset for user mappings

# SELF (Signed ELF) signature: 0x1D3D154F
SELF_MAGIC = 0x1D3D154F
ELF_MAGIC = b"\x7fELF"

class MemoryProt(IntFlag):
    NO_ACCESS = 0
    CPU_READ = 1 << 0
    CPU_WRITE = 1 << 1
    CPU_READ_WRITE = CPU_READ | CPU_WRITE
    CPU_EXEC = 1 << 2
    CPU_ALL = CPU_READ | CPU_WRITE | CPU_EXEC
    GPU_READ = 1 << 4
    GPU_WRITE = 1 << 5
    GPU_READ_WRITE = GPU_READ | GPU_WRITE
    ALL = CPU_ALL | GPU_READ_WRITE

class PhysicalMemoryType(IntEnum):
    FREE = 0
    ALLOCATED = 1
    MAPPED = 2
    POOLED = 3
    COMMITTED = 4
    FLEXIBLE = 5

class OrbisErrorCode(IntEnum):
    SCE_OK = 0
    SCE_KERNEL_ERROR_EINVAL = 0x80020016
    SCE_KERNEL_ERROR_ENOMEM = 0x8002000C
    SCE_KERNEL_ERROR_EBUSY = 0x80020010
    SCE_KERNEL_ERROR_EAGAIN = 0x80020023
    SCE_KERNEL_ERROR_ENOENT = 0x80020002
    SCE_KERNEL_ERROR_EEXIST = 0x80020011
    SCE_KERNEL_ERROR_ETIMEDOUT = 0x8002003C

def align_up(value: int, alignment: int) -> int:
    """Align value up to the next multiple of alignment."""
    return (value + alignment - 1) & ~(alignment - 1)

def align_down(value: int, alignment: int) -> int:
    """Align value down to the previous multiple of alignment."""
    return value & ~(alignment - 1)


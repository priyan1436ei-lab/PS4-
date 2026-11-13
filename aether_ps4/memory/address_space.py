"""
PS4 Unified Virtual & Physical Memory (DMEM) Subsystem.
Implements 40-bit Address Space, 16KB Guest Page Tables,
Physical Memory Allocator (GDDR5 Direct Memory), and Memory Protection.
"""

from typing import Dict, Optional, Tuple, List
from aether_ps4.common.types import (
    GUEST_PAGE_BITS, GUEST_PAGE_SIZE, ADDRESS_SPACE_BITS,
    DEFAULT_MAPPING_BASE, MemoryProt, align_up, align_down
)
from aether_ps4.common.logger import Logger, Subsystem

class PhysicalBlock:
    def __init__(self, paddr: int, size: int, mem_type: int):
        self.paddr = paddr
        self.size = size
        self.mem_type = mem_type
        self.allocated = True

class PageEntry:
    def __init__(self, phys_offset: int, prot: MemoryProt):
        self.phys_offset = phys_offset
        self.prot = prot

class AddressSpace:
    """
    Manages the 40-bit user virtual address space, backed by an 8 GB unified physical GDDR5 heap.
    """
    TOTAL_PHYSICAL_RAM = 8 * 1024 * 1024 * 1024 # 8 GB unified GDDR5

    def __init__(self):
        # 8 GB backing storage
        self.physical_ram = bytearray()
        # Allocate on demand or track memory chunks
        self._ram_chunks: Dict[int, bytearray] = {} # chunk_idx (1MB) -> bytearray(1MB)
        self.next_phys_alloc = 0x1000000 # 16 MB reserved for kernel
        self.phys_blocks: Dict[int, PhysicalBlock] = {}

        # Page table: vpn (Virtual Page Number) -> PageEntry
        self.page_table: Dict[int, PageEntry] = {}
        self.next_mmap_vaddr = DEFAULT_MAPPING_BASE

        Logger.info(Subsystem.MEMORY, "Initialized 40-bit Virtual Address Space with 16KB pages")

    def _get_ram_slice(self, phys_addr: int, size: int) -> memoryview:
        chunk_size = 1024 * 1024 # 1MB chunks
        chunk_idx = phys_addr // chunk_size
        offset_in_chunk = phys_addr % chunk_size

        if chunk_idx not in self._ram_chunks:
            self._ram_chunks[chunk_idx] = bytearray(chunk_size)

        return memoryview(self._ram_chunks[chunk_idx])[offset_in_chunk:offset_in_chunk + size]

    def allocate_direct_memory(self, length: int, alignment: int, memory_type: int) -> int:
        """
        Emulates sceKernelAllocateDirectMemory: allocates contiguous physical memory.
        """
        aligned_len = align_up(length, alignment if alignment > 0 else GUEST_PAGE_SIZE)
        paddr = align_up(self.next_phys_alloc, alignment if alignment > 0 else GUEST_PAGE_SIZE)
        
        if paddr + aligned_len > self.TOTAL_PHYSICAL_RAM:
            raise MemoryError("Out of physical GDDR5 direct memory")

        self.next_phys_alloc = paddr + aligned_len
        block = PhysicalBlock(paddr, aligned_len, memory_type)
        self.phys_blocks[paddr] = block

        Logger.debug(Subsystem.MEMORY, f"Allocated physical DMEM: Base=0x{paddr:X}, Size=0x{aligned_len:X}")
        return paddr

    def map_direct_memory(self, vaddr_request: int, length: int, prot: MemoryProt, phys_offset: int, alignment: int = GUEST_PAGE_SIZE) -> int:
        """
        Emulates sceKernelMapDirectMemory: maps physical memory into user virtual address space.
        """
        aligned_len = align_up(length, GUEST_PAGE_SIZE)
        if vaddr_request == 0:
            vaddr = align_up(self.next_mmap_vaddr, alignment)
            self.next_mmap_vaddr = vaddr + aligned_len
        else:
            vaddr = align_down(vaddr_request, GUEST_PAGE_SIZE)

        start_vpn = vaddr >> GUEST_PAGE_BITS
        num_pages = aligned_len >> GUEST_PAGE_BITS

        for i in range(num_pages):
            vpn = start_vpn + i
            cur_phys = phys_offset + (i << GUEST_PAGE_BITS)
            self.page_table[vpn] = PageEntry(cur_phys, prot)

        Logger.debug(Subsystem.MEMORY, f"Mapped DMEM: VAddr=0x{vaddr:X} -> PAddr=0x{phys_offset:X}, Size=0x{aligned_len:X}, Prot={prot.name}")
        return vaddr

    def allocate_virtual_memory(self, vaddr_request: int, length: int, prot: MemoryProt, alignment: int = GUEST_PAGE_SIZE) -> int:
        """
        Allocates anonymous virtual memory (like mmap/VirtualAlloc).
        """
        paddr = self.allocate_direct_memory(length, alignment, 0)
        return self.map_direct_memory(vaddr_request, length, prot, paddr, alignment)

    def write_bytes(self, vaddr: int, data: bytes) -> None:
        """
        Writes data into the virtual address space, translating virtual pages to physical memory.
        """
        size = len(data)
        written = 0
        while written < size:
            cur_vaddr = vaddr + written
            vpn = cur_vaddr >> GUEST_PAGE_BITS
            page_offset = cur_vaddr & (GUEST_PAGE_SIZE - 1)
            bytes_in_page = min(size - written, GUEST_PAGE_SIZE - page_offset)

            if vpn not in self.page_table:
                # Page fault / lazy allocate
                self.allocate_virtual_memory(cur_vaddr, GUEST_PAGE_SIZE, MemoryProt.ALL)

            entry = self.page_table[vpn]
            phys_addr = entry.phys_offset + page_offset

            chunk_size = 1024 * 1024
            chunk_idx = phys_addr // chunk_size
            offset = phys_addr % chunk_size

            if chunk_idx not in self._ram_chunks:
                self._ram_chunks[chunk_idx] = bytearray(chunk_size)

            self._ram_chunks[chunk_idx][offset:offset + bytes_in_page] = data[written:written + bytes_in_page]
            written += bytes_in_page

    def read_bytes(self, vaddr: int, size: int) -> bytes:
        """
        Reads data from virtual address space.
        """
        result = bytearray(size)
        read = 0
        while read < size:
            cur_vaddr = vaddr + read
            vpn = cur_vaddr >> GUEST_PAGE_BITS
            page_offset = cur_vaddr & (GUEST_PAGE_SIZE - 1)
            bytes_in_page = min(size - read, GUEST_PAGE_SIZE - page_offset)

            if vpn not in self.page_table:
                # Return zeroes for unmapped memory
                read += bytes_in_page
                continue

            entry = self.page_table[vpn]
            phys_addr = entry.phys_offset + page_offset

            chunk_size = 1024 * 1024
            chunk_idx = phys_addr // chunk_size
            offset = phys_addr % chunk_size

            if chunk_idx in self._ram_chunks:
                result[read:read + bytes_in_page] = self._ram_chunks[chunk_idx][offset:offset + bytes_in_page]

            read += bytes_in_page

        return bytes(result)

    def write_u32(self, vaddr: int, val: int) -> None:
        self.write_bytes(vaddr, val.to_bytes(4, byteorder="little"))

    def read_u32(self, vaddr: int) -> int:
        return int.from_bytes(self.read_bytes(vaddr, 4), byteorder="little")

    def write_u64(self, vaddr: int, val: int) -> None:
        self.write_bytes(vaddr, val.to_bytes(8, byteorder="little"))

    def read_u64(self, vaddr: int) -> int:
        return int.from_bytes(self.read_bytes(vaddr, 8), byteorder="little")


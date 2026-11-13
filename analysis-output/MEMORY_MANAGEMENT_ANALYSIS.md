# Virtual & Physical Memory Management

Source references:
- `src/core/address_space.h:L20-L80`
- `src/core/address_space.cpp:L30-L150`
- `src/core/memory.h:L30-L110`
- `src/core/memory.cpp:L50-L280`

## Address Space Characteristics
- **Virtual Address Space**: 40-bit address space (1 Terabyte capacity).
- **Page Size**: 16 KB (`GUEST_PAGE_BITS = 14`, `GUEST_PAGE_SIZE = 16384`).
- **Base Offset**: User mappings begin at `0x200000000` (8 GB).

## Direct Memory (DMEM) vs Flexible Memory
1. **Direct Memory (`sceKernelAllocateDirectMemory`)**:
   - Allocates contiguous physical memory from the 8 GB GDDR5 unified pool.
   - Games map physical allocations to virtual addresses using `sceKernelMapDirectMemory`.
   - Multiple virtual addresses can reference the exact same physical block (aliasing for GPU buffers, display surfaces, and compute queues).
2. **Flexible Memory (`sceKernelAllocateFlexibleMemory`)**:
   - Paged anonymous virtual memory for general CPU heap and stack usage.

## Host Implementation
- On Windows: Uses `VirtualAlloc2` / `MapViewOfFile3` with placeholder mappings.
- On Linux/macOS: Uses `mmap` with `MAP_SHARED` and anonymous file descriptors (`memfd_create`).

// SPDX-License-Identifier: MIT
// AetherPS4 - Modern PlayStation 4 Emulator Core
#pragma once

#include <cstdint>
#include <unordered_map>
#include <vector>
#include <memory>

namespace Aether::Memory {

constexpr uint64_t GUEST_PAGE_BITS = 14;
constexpr uint64_t GUEST_PAGE_SIZE = 1ULL << GUEST_PAGE_BITS; // 16 KB
constexpr uint64_t ADDRESS_SPACE_BITS = 40;                   // 1 TB
constexpr uint64_t DEFAULT_MAP_BASE = 0x200000000ULL;        // 8 GB

enum class MemoryProt : uint32_t {
    None = 0,
    CpuRead = 1 << 0,
    CpuWrite = 1 << 1,
    CpuExec = 1 << 2,
    CpuReadWrite = CpuRead | CpuWrite,
    GpuRead = 1 << 4,
    GpuWrite = 1 << 5,
    All = CpuRead | CpuWrite | CpuExec | GpuRead | GpuWrite
};

struct PageEntry {
    uint64_t phys_offset;
    MemoryProt prot;
};

class AddressSpace {
public:
    explicit AddressSpace();
    ~AddressSpace() = default;

    uint64_t AllocateDirectMemory(uint64_t length, uint64_t alignment, uint32_t memory_type);
    uint64_t MapDirectMemory(uint64_t vaddr_req, uint64_t length, MemoryProt prot, uint64_t phys_offset, uint64_t alignment);

    void WriteBytes(uint64_t vaddr, const uint8_t* data, size_t size);
    void ReadBytes(uint64_t vaddr, uint8_t* out_data, size_t size);

private:
    uint64_t m_next_phys_alloc{0x1000000};
    uint64_t m_next_mmap_vaddr{DEFAULT_MAP_BASE};
    std::unordered_map<uint64_t, PageEntry> m_page_table;
    std::unordered_map<uint64_t, std::vector<uint8_t>> m_ram_chunks; // 1 MB chunks
};

} // namespace Aether::Memory


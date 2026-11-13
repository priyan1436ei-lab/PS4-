// SPDX-License-Identifier: MIT
// AetherPS4 - Modern PlayStation 4 Emulator Core
#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <span>

namespace Aether::Loader {

#pragma pack(push, 1)
struct SelfHeader {
    static constexpr uint32_t SIGNATURE = 0x1D3D154F; // \x4F\x15\x3D\x1D

    uint32_t magic;
    uint8_t version;
    uint8_t mode;
    uint8_t endian; // 1 = Little Endian
    uint8_t attributes;
    uint8_t category;
    uint8_t program_type;
    uint16_t padding1;
    uint16_t header_size;
    uint16_t meta_size;
    uint32_t file_size;
    uint32_t padding2;
    uint16_t segment_count;
    uint16_t unknown1A; // 0x22
    uint32_t padding3;
};

struct SelfSegmentHeader {
    uint64_t flags;
    uint64_t file_offset;
    uint64_t file_size;
    uint64_t memory_size;

    [[nodiscard]] bool IsEncrypted() const noexcept { return (flags & 2) != 0; }
    [[nodiscard]] bool IsSigned() const noexcept { return (flags & 4) != 0; }
    [[nodiscard]] bool IsCompressed() const noexcept { return (flags & 8) != 0; }
    [[nodiscard]] bool IsBlocked() const noexcept { return (flags & 0x800) != 0; }
    [[nodiscard]] uint32_t GetId() const noexcept { return (flags >> 20) & 0xFFF; }
};

struct Elf64Header {
    uint8_t e_ident[16];
    uint16_t e_type;
    uint16_t e_machine;
    uint32_t e_version;
    uint64_t e_entry;
    uint64_t e_phoff;
    uint64_t e_shoff;
    uint32_t e_flags;
    uint16_t e_ehsize;
    uint16_t e_phentsize;
    uint16_t e_phnum;
    uint16_t e_shentsize;
    uint16_t e_shnum;
    uint16_t e_shstrndx;
};

struct Elf64Phdr {
    uint32_t p_type;
    uint32_t p_flags;
    uint64_t p_offset;
    uint64_t p_vaddr;
    uint64_t p_paddr;
    uint64_t p_filesz;
    uint64_t p_memsz;
    uint64_t p_align;
};
#pragma pack(pop)

class ElfBinary {
public:
    explicit ElfBinary(std::span<const uint8_t> data);
    [[nodiscard]] uint64_t GetEntryPoint() const noexcept { return m_entry; }
    [[nodiscard]] const std::vector<Elf64Phdr>& GetProgramHeaders() const noexcept { return m_phdrs; }

private:
    uint64_t m_entry{0};
    std::vector<Elf64Phdr> m_phdrs;
};

} // namespace Aether::Loader


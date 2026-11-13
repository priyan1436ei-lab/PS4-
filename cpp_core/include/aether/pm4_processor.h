// SPDX-License-Identifier: MIT
// AetherPS4 - Modern PlayStation 4 Emulator Core
#pragma once

#include <cstdint>
#include <vector>
#include <span>
#include <unordered_map>

namespace Aether::Gpu {

enum class PM4Type : uint32_t {
    Type0 = 0,
    Type1 = 1,
    Type2 = 2,
    Type3 = 3
};

enum class PM4Opcode : uint32_t {
    Nop = 0x10,
    IndexType = 0x2A,
    DrawIndex2 = 0x27,
    DrawIndexAuto = 0x2D,
    NumInstances = 0x2F,
    IndirectBuffer = 0x3F,
    SetContextReg = 0x69,
    SetShReg = 0x76,
};

struct DrawRecord {
    uint32_t vertex_count;
    uint32_t instance_count;
    bool is_indexed;
};

class PM4Processor {
public:
    explicit PM4Processor() = default;
    size_t ProcessCommandBuffer(std::span<const uint32_t> dwords);

    [[nodiscard]] const std::vector<DrawRecord>& GetDrawCalls() const noexcept { return m_draws; }
    [[nodiscard]] uint64_t GetVsShaderAddress() const noexcept { return m_vs_addr; }

private:
    std::unordered_map<uint32_t, uint32_t> m_context_regs;
    std::unordered_map<uint32_t, uint32_t> m_sh_regs;
    std::vector<DrawRecord> m_draws;
    uint32_t m_instances{1};
    uint64_t m_vs_addr{0};
};

} // namespace Aether::Gpu


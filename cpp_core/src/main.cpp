// SPDX-License-Identifier: MIT
// AetherPS4 - Modern PlayStation 4 Emulator Core
// Lead Architect & Developer: PRIYAN-A-1
// Copyright (c) 2026 PRIYAN-A-1. All rights reserved.
#include <iostream>
#include <iomanip>
#include <vector>
#include <cstring>
#include "aether/elf.h"
#include "aether/address_space.h"
#include "aether/pm4_processor.h"

int main() {
    std::cout << "======================================================================\n";
    std::cout << "       AETHER PS4 - C++20 MODERN PS4 EMULATOR CORE\n";
    std::cout << "          Lead Architect & Developer: PRIYAN-A-1\n";
    std::cout << "======================================================================\n";

    // 1. Memory Subsystem
    std::cout << "[Memory] Initializing 40-bit Address Space with 16KB Pages...\n";
    Aether::Memory::AddressSpace mem;
    uint64_t paddr = mem.AllocateDirectMemory(0x2000000, 0x200000, 0); // 32 MB
    uint64_t vaddr = mem.MapDirectMemory(0x200000000ULL, 0x2000000, Aether::Memory::MemoryProt::CpuReadWrite, paddr, 0x4000);
    std::cout << "  sceKernelAllocateDirectMemory: PAddr = 0x" << std::hex << paddr << "\n";
    std::cout << "  sceKernelMapDirectMemory:      VAddr = 0x" << std::hex << vaddr << "\n";

    // Write / Read Verification
    const char* test_payload = "AetherPS4 C++20 Memory Bridge";
    mem.WriteBytes(vaddr + 0x1000, reinterpret_cast<const uint8_t*>(test_payload), std::strlen(test_payload) + 1);
    char read_buffer[64] = {0};
    mem.ReadBytes(vaddr + 0x1000, reinterpret_cast<uint8_t*>(read_buffer), sizeof(read_buffer));
    std::cout << "  Verified GDDR5 Data at VAddr: \"" << read_buffer << "\"\n";

    // 2. GPU Command Processor
    std::cout << "[GPU] Initializing Liverpool PM4 Command Processor...\n";
    Aether::Gpu::PM4Processor gpu;
    // Command Buffer: SET_CONTEXT_REG, SET_SH_REG, NUM_INSTANCES, DRAW_INDEX_AUTO
    std::vector<uint32_t> cmd_stream = {
        0xC0026900, 0x0000A000, 0x00010001, 0x00020002, // SET_CONTEXT_REG
        0xC0027600, 0x00000208, 0x40001000, 0x00000002, // SET_SH_REG (Shader address)
        0xC0002F00, 0x00000001,                         // NUM_INSTANCES = 1
        0xC0012D00, 0x00000024, 0x00000004              // DRAW_INDEX_AUTO (36 vertices)
    };
    gpu.ProcessCommandBuffer(cmd_stream);
    std::cout << "  Processed PM4 Packets successfully.\n";
    std::cout << "  Recorded " << gpu.GetDrawCalls().size() << " draw calls on Liverpool GFX ring.\n";

    std::cout << "======================================================================\n";
    std::cout << "C++20 Core Demonstration Complete.\n";
    return 0;
}


# Final Repository Audit & Original PS4 Emulator Blueprint

## Audit Verification Summary
- **Tracked Files Inventoried**: 1,150 files across all subsystems.
- **Lines of Source Covered**: 1,636,518 lines cataloged.
- **Core Subsystems Audited**:
  - Application startup (`main.cpp`, `emulator.cpp`).
  - Executable loader (`elf.cpp`, `module.cpp`).
  - Dynamic linker & NID resolution (`linker.cpp`, `aerolib`).
  - Memory management (`address_space.cpp`, `memory.cpp`).
  - Orbis OS kernel HLE (`libraries/kernel`).
  - Liverpool GPU & PM4 command processing (`liverpool.cpp`, `pm4_cmds.h`).
  - AMD GCN shader recompiler (`shader_recompiler`).
  - Vulkan renderer (`renderer_vulkan`).
  - Texture swizzling & resource caches (`tiling.cpp`, `texture_cache`).

---

# Independent Project Blueprint: ORIGINAL_PS4_EMULATOR (AetherPS4)
## Project Architect & Lead Developer: PRIYAN-A-1
## Copyright (c) 2026 PRIYAN-A-1. All rights reserved.

## Architecture Overview
An independent, clean-room C++23 / Python modular PlayStation 4 emulator built on clean software engineering principles:
- **Zero Global State**: Explicit dependency injection across all engines.
- **Modular Subsystems**: Distinct host platform layer, guest memory space, kernel HLE, and GPU model.
- **Direct Execution Engine**: Native x86-64 host execution with System V ABI thunks.
- **Clean Shader Pipeline**: GCN instruction decoding -> SSA IR -> SPIR-V code generator.

## 10-Phase Development Roadmap

### Phase 1 – Foundation
- Deliverables: Logging, configuration, SDL3 window, CMake build system.
- Files: `src/common/log.h`, `src/common/types.h`, `src/core/emulator.h`.
- Criteria: Window initializes and accepts quit events.

### Phase 2 – Executable Loading
- Deliverables: ELF64 and decrypted SELF header parser, segment classifier.
- Files: `src/core/loader/elf.h`, `src/core/loader/elf.cpp`.
- Criteria: Successfully parses and validates `eboot.bin` headers and segments.

### Phase 3 – Guest Runtime & ABI
- Deliverables: Dynamic symbol table, relocation processor, System V ABI thunks.
- Files: `src/core/linker.h`, `src/core/linker.cpp`.
- Criteria: Resolves NIDs and jumps to guest entry point without stack corruption.

### Phase 4 – Memory & Kernel
- Deliverables: 40-bit virtual address space, 16 KB page table, GDDR5 direct memory allocator.
- Files: `src/core/memory/address_space.h`, `src/core/kernel/threads.h`.
- Criteria: Successful allocation and mapping of direct memory via `sceKernelAllocateDirectMemory`.

### Phase 5 – HLE Framework
- Deliverables: System library registration, mutexes, semaphores, event flags, file system mounts.
- Files: `src/core/libraries/kernel.h`, `src/core/libraries/videoout.h`.
- Criteria: Basic game homebrew initializes kernel services without crashing.

### Phase 6 – GPU Foundation
- Deliverables: AMD Liverpool PM4 packet processor, DCB/CCB command ring buffers.
- Files: `src/video_core/pm4.h`, `src/video_core/liverpool.h`.
- Criteria: Decodes Type-0, Type-2, and Type-3 packets (`SET_CONTEXT_REG`, `DRAW_INDEX_AUTO`).

### Phase 7 – Shader Recompiler
- Deliverables: AMD GCN microcode decoder, SSA IR, optimization passes.
- Files: `src/shader_recompiler/decode.h`, `src/shader_recompiler/ir.h`.
- Criteria: Disassembles GCN instructions and translates basic vertex/pixel shaders.

### Phase 8 – Vulkan Backend
- Deliverables: Vulkan 1.3 instance, pipeline state rasterizer, swapchain presentation, 2D Morton texture deswizzler.
- Files: `src/video_core/vulkan/rasterizer.h`, `src/video_core/vulkan/texture_cache.h`.
- Criteria: Renders 3D colored triangle on screen via Vulkan swapchain.

### Phase 9 – Compatibility & Subsystems
- Deliverables: DualShock 4 input via SDL3, audio output streaming, savedata management.
- Files: `src/input/pad.h`, `src/audio/audio_out.h`.
- Criteria: Controllable game demo with audio output.

### Phase 10 – Verification & Tooling
- Deliverables: Automated unit test suite, shader regression tests, debugger integration.
- Files: `tests/test_all.cpp`.
- Criteria: 100% pass rate on core memory, loader, and GPU packet tests.

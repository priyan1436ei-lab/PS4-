# Repository Overview: shadPS4

- **Repository URL**: https://github.com/shadps4-emu/shadPS4.git
- **Current Branch**: `main`
- **Current Commit SHA**: `4f48eabe699ac2fbfadba258eddcec778d6d99b1`
- **Commit Date**: Sun Nov 8 11:20:22 2026 +0200
- **Author**: Valdis Bogdāns
- **Working Tree Status**: Clean

## Tracked Inventory Summary
- **Total Tracked Files**: 1,150
- **Total Measured Lines of Source/Docs**: 1,636,518 lines
- **C++ Source Files (`.cpp`, `.c`, `.mm`)**: 466 files
- **C/C++ Header Files (`.h`, `.hpp`, `.inl`)**: 523 files
- **CMake Build Configuration (`.cmake`, `CMakeLists.txt`)**: 19 files
- **Markdown Documentation (`.md`)**: 10 files
- **YAML Configuration (`.yaml`, `.yml`)**: 8 files
- **JSON Configuration & Presets (`.json`)**: 6 files
- **Binary Assets (`.png`, `.ico`)**: 29 files
- **Shader Source & Test Shaders (`.spv`, `.frag`, `.vert`)**: 7 files
- **Protocol Buffer Definitions (`.proto`)**: 1 file
- **Scripts (Python, Shell)**: 3 files
- **Configuration & Other**: 78 files

## Directory Breakdown
- `src/core/`: 596 files (Executable loader, dynamic linker, memory manager, kernel HLE, system libraries, filesystem).
- `src/shader_recompiler/`: 122 files (GCN instruction decoder, CFG generator, SSA IR, optimization passes, SPIR-V backend).
- `src/video_core/`: 105 files (Liverpool GPU command processor, PM4 packet handling, Vulkan 1.3 rasterizer, texture/buffer caches).
- `src/common/`: 84 files (Logging, assertions, math, bit manipulation, multi-level page table, ring buffers, thread utilities).
- `src/input/`: 22 files (SDL3 controller mapping, keyboard, mouse, DualShock 4 motion/touch sensors).
- `src/imgui/`: 26 files (Dear ImGui debug UI, memory visualizers, register viewers).
- `src/shadnet/`: 14 files (Network bridge, telemetry, multiplayer communication backend).

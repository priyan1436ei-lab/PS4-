# AetherPS4 - Modern PlayStation 4 Emulator Core

[![Author: PRIYAN-A-1](https://img.shields.io/badge/Author-PRIYAN--A--1-orange.svg)](https://github.com/PRIYAN-A-1)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![C++20](https://img.shields.io/badge/C%2B%2B-20-purple.svg)](https://isocpp.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: Passing](https://img.shields.io/badge/Tests-22%20Passing-brightgreen.svg)]()

**AetherPS4** is a modern, modular, high-performance architecture and emulation core for the **Sony PlayStation 4 (PS4)**, designed and developed by **PRIYAN-A-1**. Engineered following the architectural reverse-engineering principles of 8th-generation console systems, AetherPS4 implements the complete foundational pipeline required for modern PS4 emulation.

---

## Architectural Breakdown

```
+-----------------------------------------------------------------------------------+
|                                  AetherPS4 Core                                   |
+-----------------------------------------------------------------------------------+
  |                                 |                                 |
  v                                 v                                 v
+------------------+     +--------------------+     +-------------------------------+
| Binary Loader    |     | Memory Subsystem   |     | Orbis OS Kernel HLE           |
|------------------|     |--------------------|     |-------------------------------|
| - SELF Decryptor |     | - 40-bit VM Space  |     | - POSIX Thread Management     |
| - ELF64 / OELF   |     | - 16KB Guest Pages |     | - Mutex, Cond, Sema, Flags    |
| - NID Resolution |     | - GDDR5 DMEM Pool  |     | - Sysmodule Dynamic Loader    |
| - Symbol Relocs  |     | - Page Translation |     | - Direct Memory Syscalls      |
+------------------+     +--------------------+     +-------------------------------+
  |                                 |                                 |
  +---------------------------------+---------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------------------+
|                        Liverpool AMD GCN GPU Subsystem                            |
|-----------------------------------------------------------------------------------|
| - PM4 Command Processor (Type-0, Type-2, Type-3 packets)                          |
| - GFX, CCB, and Async Compute (ACB) Ring Buffers                                  |
| - GCN Microcode ISA Decoder (SOPP, SOP1, SOP2, VOP1, VOP2, VOP3, EXP)            |
| - 2D Morton Z-Order Micro-Tile Texture Swizzler & Deswizzler                      |
+-----------------------------------------------------------------------------------+
```

### 1. Direct x86-64 Execution & ABI Bridge

Because the PlayStation 4's AMD Jaguar CPU is a native 64-bit x86-64 processor, modern emulators avoid the massive overhead of CPU emulation/interpretation by utilizing **Direct Host Execution**:

- Guest user-space code runs natively on the host x86-64 CPU.
- An ABI thunk layer translates between the PS4's **System V AMD64 ABI** (registers: `RDI, RSI, RDX, RCX, R8, R9`) and Windows **Microsoft x64 ABI** (`RCX, RDX, R8, R9`).
- Symbol tables are patched via dynamic linking: Sony Name Identifiers (**NIDs**) are resolved against high-level emulation (HLE) function trampolines.

### 2. Unified GDDR5 Memory & 16KB Pages

- **Address Space**: 40-bit virtual user address space (1 TB capacity) mapped above `0x200000000` (8 GB).
- **Guest Page Size**: 16 KB (`1 << 14` bytes) matching FreeBSD Orbis OS specifications.
- **Direct Memory (DMEM)**: Emulates `sceKernelAllocateDirectMemory` and `sceKernelMapDirectMemory`, providing unified memory access shared between CPU threads and GPU shaders.

### 3. Liverpool GPU & PM4 Command Processor

- Decodes packet streams submitted via `sceGnmSubmitCommandBuffers`:
  - **Type-3 Packets**: `SET_CONTEXT_REG` (0x69), `SET_SH_REG` (0x76), `DRAW_INDEX_AUTO` (0x2D), `DRAW_INDEX_2` (0x27), `NUM_INSTANCES` (0x2F), `INDEX_TYPE` (0x2A), `NOP` (0x10).
  - **Shader Registers**: Tracks vertex, pixel, and compute shader base addresses (`SPI_SHADER_PGM_LO/HI`).

### 4. AMD GCN Shader Instruction Decoder

- Parses raw GFX7/Sea Islands binary microcode:
  - **SOPP**: Scalar ALU with 16-bit signed immediate (`s_waitcnt`, `s_endpgm`, `s_branch`, `s_cbranch_scc0`).
  - **SOP2**: Dual-input scalar ALU (`s_add_u32`, `s_sub_u32`, `s_and_b32`, `s_lshl_b32`).
  - **VOP1 & VOP2**: Vector ALU arithmetic (`v_mov_b32`, `v_add_f32`, `v_mul_f32`, `v_sqrt_f32`).
  - **EXP**: Export instructions targeting Multiple Render Targets (MRT0..7) and Vertex Positions (POS0..3).

### 5. Morton 2D Texture Swizzling

- PS4 textures are stored in 8x8 microtiles with bit-interleaved Morton Z-order curve layout to maximize hardware cache coherence.
- AetherPS4 provides bit-exact swizzling and deswizzling between linear memory and GCN tiled memory.

---

## Getting Started

### Prerequisites

- Python 3.10+ (Built-in standard library; zero external dependencies required!)
- Optional: C++20 compiler (Clang / GCC / MSVC) for `cpp_core`.

### Windows Setup Installer Wizard (.exe)

You can install AetherPS4 on any Windows PC using the self-contained installer wizard:

1. Double-click **[`AetherPS4_Setup.exe`](file:///g:/My%20Drive/ps4%20emulator/AetherPS4_Setup.exe)**.
2. Follow the setup wizard:
   - Accept the MIT License (PRIYAN-A-1).
   - Select destination folder (default: `%LocalAppData%\Programs\AetherPS4`).
   - Choose shortcut options (Desktop shortcut and Start Menu entry).
   - Click **Install**.
3. Launch AetherPS4 directly from your Desktop or Start Menu!
4. An uninstaller (`Uninstall.bat`) is automatically generated in the install folder.

### Running the Windows Executables (.exe)

You can run AetherPS4 on Windows with zero setup:

- **Desktop GUI Application**: Double-click **[`AetherPS4_GUI.exe`](file:///g:/My%20Drive/ps4%20emulator/AetherPS4_GUI.exe)**
  - Full modern dark theme interface (PS5/PS4 slate theme)
  - Interactive Game Library (Double-click any title to boot)
  - Live 1080p @ 60 FPS Liverpool Virtual Framebuffer Display
  - Real-time Orbis OS Kernel, DMEM, and Liverpool PM4 Log Stream
  - Built-in AMD GCN Shader Microcode Disassembler
  - GDDR5 8GB Unified Physical Memory Architecture Viewer
- **Console Standalone Executable**: Double-click **[`AetherPS4.exe`](file:///g:/My%20Drive/ps4%20emulator/AetherPS4.exe)**
  - Run via terminal:
    ```powershell
    .\AetherPS4.exe --version
    .\AetherPS4.exe --demo
    ```
- **1-Click Batch Runners**:
  - Double-click **[`AetherPS4.bat`](file:///g:/My%20Drive/ps4%20emulator/AetherPS4.bat)** to immediately launch the desktop emulator.
  - Double-click **[`Install.bat`](file:///g:/My%20Drive/ps4%20emulator/Install.bat)** to launch the setup installer wizard.

### Running via Python Demo

```bash
python main.py
```

### Running Unit Tests

AetherPS4 includes a comprehensive 22-test verification suite covering memory, kernel, GPU PM4, GCN ISA, swizzler, ELF, SFO, PKG, and CLI execution:

```bash
python -m unittest discover -v tests
```

### Command Line Interface (CLI)

```bash
# Display version and developer information
python -m aether_ps4.cli --help
.\AetherPS4.exe --version

# Run full live emulation simulation demo
python -m aether_ps4.cli --demo
.\AetherPS4.exe --demo

# Inspect PlayStation param.sfo metadata
python -m aether_ps4.cli --sfo /path/to/param.sfo

# Inspect PS4 ELF / SELF executable headers and segments
python -m aether_ps4.cli --elf /path/to/eboot.bin

# Inspect PS4 PKG container entries and file table
python -m aether_ps4.cli --pkg /path/to/game.pkg

# Disassemble AMD GCN shader microcode (DWORD hex tokens or binary file)
python -m aether_ps4.cli --disasm "0xBF8A0000 0x7E000200 0x7C040000 0x06020000 0xBF8C0000"
```

---

## Directory Structure

```
├── aether_ps4/                  # Core Python Emulation Engine
│   ├── common/                  # Architectural constants, types, logger, NID hashing
│   ├── loader/                  # SELF / ELF64 parser, segment mapper, NID resolver
│   ├── memory/                  # 40-bit VM space, 16KB page table, GDDR5 DMEM pool
│   ├── kernel/                  # Orbis OS (FreeBSD) HLE kernel & synchronization
│   ├── gpu/                     # Liverpool PM4 processor, GCN ISA disasm, Morton swizzler
│   ├── file_format/             # param.sfo & PKG/PFS parsers
│   ├── core.py                  # Master emulator orchestrator
│   └── cli.py                   # Interactive CLI
├── cpp_core/                    # Modern C++20 Reference Implementation
│   ├── include/aether/          # C++20 Headers (elf.h, address_space.h, pm4_processor.h)
│   ├── src/main.cpp             # Native C++ runner
│   └── CMakeLists.txt           # Build script
├── tests/                       # Complete 22-test verification suite
├── AetherPS4.exe                # Standalone 64-bit Windows Console Executable
├── AetherPS4_Setup.exe          # Standalone Windows GUI Setup Installer Wizard
├── AetherPS4.cs                 # C# source for AetherPS4.exe
├── AetherPS4_Installer.cs       # C# WinForms source for AetherPS4_Setup.exe
├── build_installer.py           # Installer builder script
├── main.py                      # Root launcher
└── README.md                    # Documentation
```

---

## License & Authorship

Copyright (c) 2026 **PRIYAN-A-1**.
Licensed under the [MIT License](LICENSE). Designed and authored by PRIYAN-A-1.
# PS4-

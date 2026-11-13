# Complete Overall System Architecture

The execution architecture of shadPS4 divides the responsibilities of emulating the PlayStation 4 into two interdependent pipelines: the **CPU/OS Execution Path** and the **GPU/Graphics Execution Path**.

```
+---------------------------------------------------------------------------------------------+
|                                    PlayStation 4 Title                                      |
|                            (eboot.bin / SELF / OELF / param.sfo)                            |
+---------------------------------------------------------------------------------------------+
               |                                                           |
               v                                                           v
+-------------------------------+                         +-----------------------------------+
|      CPU & OS Subsystem       |                         |          GPU Subsystem            |
|-------------------------------|                         |-----------------------------------|
| - Executable Loader (ELF/SELF)|                         | - AMD Liverpool GPU Model         |
| - Dynamic Linker & NID Resolver|                        | - PM4 Packet Processor            |
| - Direct x86-64 Host Execution|                         |   (Type-0, Type-2, Type-3)        |
| - System V <-> Win64 ABI Bridge|                        | - DCB, CCB & 56 Async Compute Rings|
| - Orbis OS Kernel HLE         |                         | - GCN Microcode Decoder           |
|   (Threads, Mutex, Semaphores)|                         | - SSA IR & Control Flow Graph     |
| - 40-bit Virtual Address Space|                         | - SPIR-V Shader Generator         |
| - 16 KB Guest Page Table      |                         | - Vulkan 1.3 Pipeline Rasterizer  |
| - GDDR5 DMEM Allocator        |                         | - 2D Morton Texture Deswizzler    |
+-------------------------------+                         +-----------------------------------+
               |                                                           |
               +-----------------------------+-----------------------------+
                                             |
                                             v
+---------------------------------------------------------------------------------------------+
|                                  Host System Platform                                       |
|                     (SDL3 Window / Vulkan 1.3 / OpenAL / Audio / Input)                     |
+---------------------------------------------------------------------------------------------+
```

## Key Interactions
1. **CPU & Kernel**: `RunMainEntry()` in `src/core/linker.cpp:L41-L60` aligns the stack and jumps directly to guest code. When guest code calls imported library functions, it hits linker trampolines that invoke C++ HLE implementations.
2. **Memory Sharing**: Both CPU threads and the Liverpool GPU model share a unified 8 GB GDDR5 backing pool managed by `AddressSpace` (`src/core/address_space.cpp`).
3. **GPU Command Submission**: The guest calls `sceGnmSubmitCommandBuffers()` (`src/core/libraries/gnmdriver/gnmdriver.cpp`), which enqueues command buffers into the Liverpool GPU thread.
4. **GPU Execution**: `Liverpool::Process()` (`src/video_core/amdgpu/liverpool.cpp:L71`) consumes PM4 packets, configures Vulkan pipeline states, translates GCN shaders to SPIR-V, and triggers Vulkan draws.

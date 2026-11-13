# Data Flow Architecture

```
[Disk: eboot.bin / PKG]
         |
         v
[ELF / SELF Loader]  ======(Virtual Memory Mappings)======>  [40-bit Address Space]
         |                                                            ^
         v                                                            |
[Dynamic Linker] ----(Patches NID PLT Entries)----+                   |
                                                  |                   |
                                                  v                   v
                                     [Guest x86-64 CPU Execution] ----+
                                                  | (Draw Calls / Buffers)
                                                  v
                                     [libSceGnmDriver HLE API]
                                                  | (Command Buffers)
                                                  v
                                     [Liverpool PM4 Command Ring]
                                                  | (GCN Bytecode)
                                                  v
                                     [Shader Recompiler (SPIR-V)]
                                                  | (VkPipeline)
                                                  v
                                     [Vulkan 1.3 Rasterizer]
                                                  |
                                                  v
                                     [Host Screen / Presentation]
```

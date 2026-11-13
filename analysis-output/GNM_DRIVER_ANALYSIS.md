# GNM & GNMX Graphics Driver Interface

Source reference: `src/core/libraries/gnmdriver/gnmdriver.cpp:L30-L240`

## Driver Role
`libSceGnmDriver` is the low-level graphics driver interface used by PS4 titles:
1. `sceGnmSubmitCommandBuffers()`: Enqueues DCB, CCB, and compute command lists into Liverpool GPU queues.
2. `sceGnmSubmitAndFlipCommandBuffers()`: Submits rendering commands and registers a display flip event with `libSceVideoOut`.
3. `sceGnmFlushGarlic()`: Flushes GPU L2 caches for write-combined host-visible memory.
4. `sceGnmDingDong()`: GPU doorbell mechanism to kick compute queues.

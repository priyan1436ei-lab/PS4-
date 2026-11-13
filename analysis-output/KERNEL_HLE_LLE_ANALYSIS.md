# Orbis OS Kernel HLE Analysis

Source references:
- `src/core/libraries/kernel/threads.cpp`
- `src/core/libraries/kernel/memory.cpp`
- `src/core/libraries/kernel/synch.cpp`

## Kernel Primitives Emulated
1. **Threads (`scePthread*`, `sceKernelCreateThread`)**:
   - Mapped to host `std::jthread` / POSIX pthreads.
   - Custom stack allocation with guard pages.
2. **Mutexes (`sceKernelCreateMutex`, `sceKernelLockMutex`)**:
   - Recursive and adaptive mutex modes.
3. **Condition Variables (`sceKernelCreateCond`)**:
   - Paired with mutexes for thread signaling.
4. **Semaphores (`sceKernelCreateSema`)**:
   - Counting semaphores with resource limits.
5. **Event Flags (`sceKernelCreateEventFlag`)**:
   - Bitwise pattern matching (`AND`, `OR`, clear-on-read).
6. **Event Queues (`sceKernelCreateEqueue`)**:
   - FreeBSD `kqueue`-derived multi-event notification system.

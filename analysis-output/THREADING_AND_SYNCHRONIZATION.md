# Concurrency, Threading & Synchronization

## Thread Architecture
1. **Main UI Thread**: Runs the SDL3 event loop, window management, and Dear ImGui overlays.
2. **Guest Game Threads**: Dedicated `std::jthread` instances executing native x86-64 guest code.
3. **Liverpool GPU Thread**: `Liverpool::Process()` runs continuously processing PM4 submissions.
4. **Audio Streamer Thread**: Pushes audio frames to the audio output device.

## Synchronization Primitives
- Mutexes, semaphores, and condition variables are abstracted to prevent race conditions.
- Coroutines (`co_yield` / fibers) synchronize the constant engine (CCB) and compute rings (ACB) with the graphics ring (DCB).

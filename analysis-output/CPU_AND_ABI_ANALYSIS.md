# CPU Architecture & ABI Compatibility

## Direct Host Execution
The PS4 CPU is an 8-core AMD Jaguar based on x86-64. Because the target architecture matches modern desktop x86-64 PCs, shadPS4 executes guest CPU instructions **natively on the host CPU** without instruction translation overhead.

## Calling Convention Bridging
- **PS4 Guest ABI**: System V AMD64 ABI.
  - Parameter registers: `RDI`, `RSI`, `RDX`, `RCX`, `R8`, `R9`.
  - Floating point: `XMM0` - `XMM7`.
  - Callee-saved: `RBX`, `RSP`, `RBP`, `R12`, `R13`, `R14`, `R15`.
- **Windows Host ABI**: Microsoft x64 ABI.
  - Parameter registers: `RCX`, `RDX`, `R8`, `R9`.
  - Mandatory 32-byte shadow space on stack.
  - Callee-saved: `RBX`, `RBP`, `RDI`, `RSI`, `RSP`, `R12` - `R15`.
- **Bridging Mechanism**:
  - Functions dispatched to HLE use `PS4_SYSV_ABI` (`__attribute__((sysv_abi))`) on Clang/GCC.
  - Stack alignment of 16 bytes is maintained strictly across calls.
  - Thread Local Storage registers (`FS_BASE` / `GS_BASE`) are managed via host OS primitives (`_writefsbase_u64` / `arch_prctl`).

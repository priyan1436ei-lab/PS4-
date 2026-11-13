# Dynamic Linker & Symbol Resolution

Source references:
- `src/core/linker.h:L20-L90`
- `src/core/linker.cpp:L40-L310`

## Relocation Types Supported
The dynamic linker evaluates relocations defined in `PT_SCE_DYNLIBDATA` or `PT_DYNAMIC`:
- `R_X86_64_RELATIVE` (8): `*ref = base + addend`
- `R_X86_64_GLOB_DAT` (6): Binds global symbol address.
- `R_X86_64_JUMP_SLOT` (7): Procedure Linkage Table (PLT) stub resolution.
- `R_X86_64_64` (1): Direct 64-bit address assignment.
- `R_X86_64_DTPMOD64` (16): Dynamic TLS module index.

## Symbol Resolution (`Linker::Resolve`)
1. Receives library name, module name, and 64-bit NID hash.
2. Searches HLE database (`src/core/aerolib/`).
3. If found in HLE, returns function pointer to C++ trampoline.
4. If found in an LLE module, returns guest code address.
5. If unresolved, logs a warning and installs a fallback stub to prevent instant crash.

## Guest Entry Point (`RunMainEntry`)
In `src/core/linker.cpp:L41-L60`:
```cpp
static PS4_SYSV_ABI void* RunMainEntry [[noreturn]](EntryParams* params) {
    asm volatile(
        "andq $-16, %%rsp\n"
        "subq $8, %%rsp\n"
        "pushq 8(%1)\n"
        "pushq 0(%1)\n"
        "movq %1, %%rdi\n"
        "movq %2, %%rsi\n"
        "jmp *%0\n"
        :
        : "r"(params->entry_addr), "r"(params), "r"(ProgramExitFunc)
        : "rax", "rsi", "rdi"
    );
}
```

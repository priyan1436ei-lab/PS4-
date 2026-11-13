# SELF / ELF Executable Loader Analysis

Source references:
- `src/core/loader/elf.h:L14-L80`
- `src/core/loader/elf.cpp:L50-L320`
- `src/core/module.cpp:L80-L220`

## Container Formats
1. **SELF (Signed ELF)**:
   - Header signature: `0x1D3D154F` (`O=` in little endian).
   - Contains segment headers specifying encryption, compression, and blocked memory flags:
     - `IsEncrypted()`: `flags & 2`
     - `IsSigned()`: `flags & 4`
     - `IsCompressed()`: `flags & 8`
     - `IsBlocked()`: `flags & 0x800`
2. **ELF64 (Orbis ELF)**:
   - Standard 64-bit ELF header with `EI_OSABI = 9` (FreeBSD) and `e_machine = 62` (EM_X86_64).

## Memory Layout and Base Addresses
In `src/core/module.cpp`, modules are assigned strict guest virtual memory regions:
- **Main Executable (`eboot.bin`)**: Base address `0x400000`.
- **Game PRX Modules**: Base address `0x80000000`.
- **System Modules (`libkernel`, etc.)**: Base address `0x800000000`.

## Segment Loading Process
1. Validate SELF / ELF magic numbers.
2. Iterate `Elf64_Phdr` program headers:
   - `PT_LOAD`: Mapped with `PROT_READ`, `PROT_WRITE`, or `PROT_EXEC` matching `p_flags`.
   - `PT_SCE_DYNLIBDATA`: Imports, exports, and NID symbol metadata.
   - `PT_SCE_PROCPARAM` & `PT_SCE_MODULE_PARAM`: System SDK versions and heap limits.
   - `PT_TLS`: Thread Local Storage template.

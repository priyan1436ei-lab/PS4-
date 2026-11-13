# Application Startup & Game Boot Sequence

## Entry Point: `src/main.cpp`
Source reference: `src/main.cpp:L50-L160`
1. **Platform Configuration**: Sets console encoding, DPI awareness, and initializes the crash handler.
2. **Argument Parsing**: Uses CLI11 to parse arguments:
   - `--game <path|id>`: Specifies path to game folder or Game ID (e.g., `CUSA00123`).
   - `--patch <path>`: Specifies game patches.
   - `--fullscreen`, `--big-picture`, `--show-fps`.
   - `--mount`: Defines custom guest mount mappings.
   - Arguments following `--` are forwarded to the guest program's `argv`.
3. **Settings & Logging**: Initializes `Config` and `Common::Log` (`src/common/logging/log.cpp`).

## Lifecycle Controller: `src/emulator.cpp`
Source reference: `src/emulator.cpp:L80-L240`
The core sequence executed inside `Emulator::Run()`:
1. **Game Path Resolution**: Resolves target directory and locates `eboot.bin`.
2. **Virtual Filesystem Mounting**:
   - Maps `<game_dir>` to `/app0`.
   - Maps host root to `/hostapp`.
   - Maps savedata directory to `/savedata`.
3. **Metadata Extraction**: Reads `/app0/sce_sys/param.sfo` to retrieve `TITLE_ID`, `APP_VER`, `CONTENT_ID`.
4. **HLE Library Initialization**: Invokes `Libraries::InitHLELibs()` (`src/core/libraries/libs.cpp`) to register all known system functions.
5. **Memory System Allocation**: Initializes `Core::Memory` and `Core::AddressSpace`.
6. **Executable Loading**: Calls `Core::Loader::Elf` to parse `eboot.bin` and map segments.
7. **Execution Handoff**: Calls `Linker::Execute()`, which jumps into `RunMainEntry()`.

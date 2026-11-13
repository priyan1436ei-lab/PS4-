# Build System & Technology Stack

## Build Requirements
- **C++ Standard**: C++23 (`-std=c++23`)
- **Compiler**: Clang 18+ (CI uses Clang 23)
- **Generator**: Ninja
- **Build System**: CMake 3.25+

## Validated Platform Build Instructions
### Windows 11 (MSVC / Clang)
```bash
git clone --recursive https://github.com/shadps4-emu/shadPS4.git
cd shadPS4
cmake --preset x64-Clang-Release
cmake --build Build/x64-Clang-Release --parallel
```

### Linux (Ubuntu 24.04 / Arch)
```bash
git clone --recursive https://github.com/shadps4-emu/shadPS4.git
cd shadPS4
cmake -S . -B build -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++
cmake --build build --parallel
```

### macOS (Apple Silicon, macOS 14+)
```bash
git clone --recursive https://github.com/shadps4-emu/shadPS4.git
cd shadPS4
cmake -S . -B build
cmake --build build --parallel
```

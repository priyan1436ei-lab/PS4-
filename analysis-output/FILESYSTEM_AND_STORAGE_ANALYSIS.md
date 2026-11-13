# Filesystem & Storage Subsystems

Source reference: `src/core/file_sys/`

## Mount Hierarchy
- `/app0`: Read-only game installation directory containing `eboot.bin` and assets.
- `/hostapp`: Direct link to host workspace.
- `/savedata`: Per-user read-write savedata directory.
- `/system`: System fonts and configuration.
- `/dev`: Virtual device nodes (`devfs`).

## Container Formats
- **PFS (PlayStation File System)**: Inode-based encrypted container used on commercial discs and PKG packages.
- **param.sfo**: Binary metadata dictionary holding Title ID, Category, Version.

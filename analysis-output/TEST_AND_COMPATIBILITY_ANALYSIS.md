# Testing Infrastructure & Compatibility Matrix

## Test Suite
- Located in `tests/`:
  - Unit tests for ELF parser, memory alignment, and address space mapping.
  - Shader recompiler unit tests verifying GCN -> SPIR-V instruction transformations.
  - Crypto and hashing unit tests (NID hashing, Murmur, SHA-1).

## Compatibility Database
- Maintained externally at `shadps4-game-compatibility`.
- Notable running titles:
  - *Bloodborne* (Bootable, ingame 30-60 FPS)
  - *Dark Souls Remastered* (Playable)
  - *Red Dead Redemption* (Playable)

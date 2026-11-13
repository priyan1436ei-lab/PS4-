# AMD Liverpool GPU Subsystem

Source references:
- `src/video_core/amdgpu/liverpool.h:L30-L120`
- `src/video_core/amdgpu/liverpool.cpp:L70-L550`
- `src/video_core/amdgpu/pm4_opcodes.h:L10-L75`

## Command Processing Architecture
- Dedicated GPU worker thread: `process_thread = std::jthread(&Liverpool::Process, this)`.
- Multi-ring support:
  - **DCB (Direct Command Buffer)**: Graphics rendering commands.
  - **CCB (Constant Engine Command Buffer)**: Register and constant buffer updates.
  - **ACB (Async Compute Buffers)**: Up to 56 independent compute rings.

## PM4 Packet Types
- **Type-0**: Configuration register writes (`0x0000 - 0xFFFF`).
- **Type-2**: NOP padding packets.
- **Type-3**: Command execution packets:
  - `0x69 SET_CONTEXT_REG`: Configures rasterizer state, blend state, and viewport.
  - `0x76 SET_SH_REG`: Configures shader base addresses (`SPI_SHADER_PGM_LO/HI`) and user data.
  - `0x2D DRAW_INDEX_AUTO`: Auto non-indexed draw.
  - `0x27 DRAW_INDEX_2`: Indexed draw.
  - `0x2F NUM_INSTANCES`: Instanced rendering counts.
  - `0x3F INDIRECT_BUFFER`: Calls secondary command buffer.

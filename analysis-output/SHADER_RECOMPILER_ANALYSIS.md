# AMD GCN Shader Recompiler Pipeline

Source references:
- `src/shader_recompiler/frontend/decode.cpp`
- `src/shader_recompiler/frontend/control_flow_graph.cpp`
- `src/shader_recompiler/recompiler.cpp`

## Recompilation Stages
1. **Binary Acquisition**: Read GCN microcode from guest memory referenced by `SPI_SHADER_PGM_LO/HI`.
2. **Instruction Decoding**: Decode 32-bit and 64-bit GCN instruction words:
   - **SOPP**: Control flow (`s_branch`, `s_cbranch_scc0`, `s_waitcnt`, `s_endpgm`).
   - **SOP2**: Scalar ALU arithmetic (`s_add_u32`, `s_and_b32`).
   - **VOP1 & VOP2**: Vector ALU arithmetic (`v_mov_b32`, `v_add_f32`, `v_mul_f32`).
   - **VOP3**: 3-operand vector ALU (`v_mad_f32`, `v_fma_f32`).
   - **EXP**: Export output to Multiple Render Targets (`MRT0..7`) or Vertex Positions (`POS0..3`).
3. **Control Flow Graph (CFG)**: Build basic blocks and identify loops and merge blocks.
4. **Intermediate Representation (IR)**: Transform instructions into SSA (Static Single Assignment) form.
5. **Optimization Passes**:
   - Constant propagation.
   - Dead code elimination.
   - Workgroup barrier consolidation.

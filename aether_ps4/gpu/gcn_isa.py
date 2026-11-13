"""
AMD GCN (Graphics Core Next - GFX7 / Sea Islands / Liverpool) Instruction Decoder.
Decodes binary microcode instructions (SOPP, SOP1, SOP2, VOP1, VOP2, VOP3, EXP)
and disassembles them to AMD ISA assembly and shader intermediate representation.
"""

from typing import List, Optional, Tuple, NamedTuple
from aether_ps4.common.logger import Logger, Subsystem

class GcnInstruction(NamedTuple):
    offset: int
    raw: int
    mnemonic: str
    operands: str
    desc: str

class GcnDisassembler:
    """
    Decodes GCN GFX7 microcode instructions into human-readable assembly.
    """
    @staticmethod
    def decode_word(offset: int, dword: int) -> GcnInstruction:
        # Check SOPP (Scalar ALU with 16-bit immediate)
        # Format: 101111111 [31:23] | OP [22:16] | SIMM16 [15:0]
        if (dword >> 23) == 0b101111111:
            op = (dword >> 16) & 0x7F
            simm16 = dword & 0xFFFF
            if simm16 & 0x8000:
                simm16 -= 0x10000 # Sign extend

            sopp_ops = {
                0: ("s_nop", f"0x{simm16 & 0xFFFF:X}", "No Operation"),
                1: ("s_setkill", f"{simm16}", "Set kill state"),
                2: ("s_branch", f".+4{simm16*4:+d}", "Unconditional relative branch"),
                4: ("s_cbranch_scc0", f".+4{simm16*4:+d}", "Branch if SCC == 0"),
                5: ("s_cbranch_scc1", f".+4{simm16*4:+d}", "Branch if SCC == 1"),
                6: ("s_cbranch_vccz", f".+4{simm16*4:+d}", "Branch if VCC == 0"),
                7: ("s_cbranch_vccnz", f".+4{simm16*4:+d}", "Branch if VCC != 0"),
                10: ("s_waitcnt", f"vmcnt({simm16 & 0xF}) expcnt({(simm16 >> 4) & 0x7}) lgkmcnt({(simm16 >> 8) & 0x1F})", "Wait on memory counters"),
                12: ("s_endpgm", "", "End of shader program"),
            }
            if op in sopp_ops:
                mne, ops, desc = sopp_ops[op]
                return GcnInstruction(offset, dword, mne, ops, desc)
            return GcnInstruction(offset, dword, f"s_sopp_unk_{op}", f"{simm16}", "Unknown SOPP")

        # Check SOP2 (Scalar ALU: 2 inputs, 1 output)
        # Format: 10 [31:30] | OP [29:23] | SDEST [22:16] | SSRC1 [15:8] | SSRC0 [7:0]
        if (dword >> 30) == 0b10:
            op = (dword >> 23) & 0x7F
            sdest = (dword >> 16) & 0x7F
            ssrc1 = (dword >> 8) & 0xFF
            ssrc0 = dword & 0xFF

            sop2_ops = {
                0: ("s_add_u32", "Add unsigned 32-bit integers"),
                1: ("s_sub_u32", "Subtract unsigned 32-bit integers"),
                2: ("s_add_i32", "Add signed 32-bit integers"),
                3: ("s_sub_i32", "Subtract signed 32-bit integers"),
                4: ("s_addc_u32", "Add unsigned with carry"),
                12: ("s_and_b32", "Bitwise AND 32-bit"),
                13: ("s_or_b32", "Bitwise OR 32-bit"),
                14: ("s_xor_b32", "Bitwise XOR 32-bit"),
                28: ("s_lshl_b32", "Logical shift left 32-bit"),
                29: ("s_lshr_b32", "Logical shift right 32-bit"),
            }
            if op in sop2_ops:
                mne, desc = sop2_ops[op]
                return GcnInstruction(offset, dword, mne, f"s{sdest}, s{ssrc0}, s{ssrc1}", desc)
            return GcnInstruction(offset, dword, f"s_sop2_{op}", f"s{sdest}, s{ssrc0}, s{ssrc1}", "SOP2 Operation")

        # Check VOP1 (Vector ALU: 1 input, 1 output) - Checked before VOP2 due to prefix hierarchy
        # Format: 0111111 [31:25] | VDEST [24:17] | OP [16:9] | SRC0 [8:0]
        if (dword >> 25) == 0b0111111:
            vdest = (dword >> 17) & 0xFF
            op = (dword >> 9) & 0xFF
            src0 = dword & 0x1FF

            vop1_ops = {
                1: ("v_mov_b32", "Move vector 32-bit register"),
                33: ("v_rcp_f32", "Reciprocal float (1.0 / x)"),
                35: ("v_rsq_f32", "Reciprocal square root (1.0 / sqrt(x))"),
                36: ("v_sqrt_f32", "Square root float"),
                41: ("v_trunc_f32", "Truncate float to int"),
                42: ("v_floor_f32", "Floor float"),
            }
            if op in vop1_ops:
                mne, desc = vop1_ops[op]
                return GcnInstruction(offset, dword, mne, f"v{vdest}, v{src0}", desc)
            return GcnInstruction(offset, dword, f"v_vop1_{op}", f"v{vdest}, v{src0}", "VOP1 Operation")

        # Check VOPC (Vector Compare: writes condition to VCC)
        # Format: 0111110 [31:25] | OP [24:17] | SRC0 [16:9] | VSRC1 [8:0]
        if (dword >> 25) == 0b0111110:
            op = (dword >> 17) & 0xFF
            src0 = (dword >> 9) & 0xFF
            vsrc1 = dword & 0x1FF
            vopc_ops = {
                0x00: ("v_cmp_f_f32", "Vector compare float false"),
                0x01: ("v_cmp_lt_f32", "Vector compare float less than"),
                0x02: ("v_cmp_eq_f32", "Vector compare float equal"),
                0x03: ("v_cmp_le_f32", "Vector compare float less than or equal"),
                0x04: ("v_cmp_gt_f32", "Vector compare float greater than"),
                0x05: ("v_cmp_lg_f32", "Vector compare float not equal"),
                0x06: ("v_cmp_ge_f32", "Vector compare float greater than or equal"),
                0x80: ("v_cmp_f_i32", "Vector compare int false"),
                0x81: ("v_cmp_lt_i32", "Vector compare int less than"),
                0x82: ("v_cmp_eq_i32", "Vector compare int equal"),
                0xC1: ("v_cmp_lt_u32", "Vector compare unsigned less than"),
                0xC2: ("v_cmp_eq_u32", "Vector compare unsigned equal"),
            }
            if op in vopc_ops:
                mne, desc = vopc_ops[op]
                return GcnInstruction(offset, dword, mne, f"vcc, v{src0}, v{vsrc1}", desc)
            return GcnInstruction(offset, dword, f"v_vopc_{op}", f"vcc, v{src0}, v{vsrc1}", "VOPC Comparison")

        # Check VOP2 (Vector ALU: 2 inputs, 1 output)
        # Format: 0 [31] | OP [30:25] | VDEST [24:17] | SRC0 [16:9] | VSRC1 [8:0]
        if (dword >> 31) == 0:
            op = (dword >> 25) & 0x3F
            vdest = (dword >> 17) & 0xFF
            src0 = (dword >> 9) & 0xFF
            vsrc1 = dword & 0x1FF

            vop2_ops = {
                1: ("v_cndmask_b32", "Vector conditional mask"),
                3: ("v_add_f32", "Vector float add"),
                4: ("v_sub_f32", "Vector float subtract"),
                5: ("v_subrev_f32", "Vector float subtract reverse"),
                8: ("v_mul_f32", "Vector float multiply"),
                15: ("v_min_f32", "Vector float minimum"),
                16: ("v_max_f32", "Vector float maximum"),
                25: ("v_add_i32", "Vector integer add"),
                26: ("v_sub_i32", "Vector integer subtract"),
                37: ("v_lshlrev_b32", "Vector shift left reverse"),
            }
            if op in vop2_ops:
                mne, desc = vop2_ops[op]
                return GcnInstruction(offset, dword, mne, f"v{vdest}, v{src0}, v{vsrc1}", desc)
            return GcnInstruction(offset, dword, f"v_vop2_{op}", f"v{vdest}, v{src0}, v{vsrc1}", "VOP2 Operation")

        # Check EXP (Export instruction for Render Targets and Vertex Pos)
        # Format: 111110 [31:26]
        if (dword >> 26) == 0b111110:
            en = (dword >> 12) & 0xF
            target = (dword >> 4) & 0x3F
            target_str = f"mrt{target}" if target < 8 else f"pos{target - 12}" if 12 <= target <= 15 else f"target_{target}"
            return GcnInstruction(offset, dword, "exp", f"{target_str}, en:0x{en:X}", "Export vector to MRT/Position output")

        return GcnInstruction(offset, dword, "raw_dword", f"0x{dword:08X}", "Unparsed GCN dword")

    @classmethod
    def disassemble(cls, binary: bytes) -> List[GcnInstruction]:
        """
        Disassembles a raw GCN shader bytecode stream.
        """
        instructions = []
        for i in range(0, len(binary), 4):
            if i + 4 <= len(binary):
                dword = int.from_bytes(binary[i:i + 4], byteorder="little")
                inst = cls.decode_word(i, dword)
                instructions.append(inst)
                if inst.mnemonic == "s_endpgm":
                    break
        return instructions


"""
AMD GCN / Liverpool PM4 Command Processor for PlayStation 4.
Parses Type-0, Type-2, and Type-3 packets submitted via sceGnmSubmitCommandBuffers.
Tracks context registers, shader user data, and draw call states.
"""

from enum import IntEnum
from typing import List, Dict, Optional, Tuple
from aether_ps4.common.logger import Logger, Subsystem

class PM4Type(IntEnum):
    TYPE_0 = 0
    TYPE_1 = 1
    TYPE_2 = 2
    TYPE_3 = 3

class PM4Opcode(IntEnum):
    NOP = 0x10
    SET_BASE = 0x11
    CLEAR_STATE = 0x12
    INDEX_BUFFER_SIZE = 0x13
    DISPATCH_DIRECT = 0x15
    DISPATCH_INDIRECT = 0x16
    SET_PREDICATION = 0x20
    INDEX_BASE = 0x26
    DRAW_INDEX_2 = 0x27
    CONTEXT_CONTROL = 0x28
    INDEX_TYPE = 0x2A
    DRAW_INDEX_AUTO = 0x2D
    NUM_INSTANCES = 0x2F
    DRAW_INDEX_MULTI_AUTO = 0x30
    INDIRECT_BUFFER = 0x3F
    EVENT_WRITE = 0x46
    RELEASE_MEM = 0x49
    DMA_DATA = 0x50
    ACQUIRE_MEM = 0x58
    SET_CONFIG_REG = 0x68
    SET_CONTEXT_REG = 0x69
    SET_SH_REG = 0x76
    SET_UCONFIG_REG = 0x79

class DrawCallRecord:
    def __init__(self, index_count: int, instance_count: int, is_indexed: bool, primitive_type: str):
        self.index_count = index_count
        self.instance_count = instance_count
        self.is_indexed = is_indexed
        self.primitive_type = primitive_type

class PM4Processor:
    """
    Simulates the Liverpool GPU command processor frontend.
    """
    def __init__(self):
        # Register banks
        self.context_regs: Dict[int, int] = {}
        self.sh_regs: Dict[int, int] = {}
        self.config_regs: Dict[int, int] = {}

        # Pipeline state
        self.num_instances: int = 1
        self.index_type: int = 0 # 0=16-bit, 1=32-bit
        self.index_base: int = 0
        self.vs_shader_addr: int = 0
        self.ps_shader_addr: int = 0
        self.draw_calls: List[DrawCallRecord] = []

        Logger.info(Subsystem.GPU, "Liverpool PM4 Command Processor Initialized")

    def process_command_buffer(self, dwords: List[int]) -> int:
        """
        Processes a raw stream of 32-bit DWORDs from a PS4 command buffer.
        Returns the number of processed packets.
        """
        idx = 0
        packet_count = 0

        while idx < len(dwords):
            header = dwords[idx]
            pkt_type = (header >> 30) & 0x3

            if pkt_type == PM4Type.TYPE_3:
                count = (header >> 16) & 0x3FFF
                opcode_val = (header >> 8) & 0xFF
                payload_len = count + 1 # Payload DWORDs
                payload = dwords[idx + 1:idx + 1 + payload_len]

                try:
                    opcode = PM4Opcode(opcode_val)
                    self._handle_type3(opcode, payload)
                except ValueError:
                    Logger.warn(Subsystem.GPU, f"Unknown PM4 Type-3 opcode: 0x{opcode_val:02X} (Payload len: {payload_len})")

                idx += 1 + payload_len
                packet_count += 1

            elif pkt_type == PM4Type.TYPE_0:
                count = (header >> 16) & 0x3FFF
                base_reg = header & 0xFFFF
                payload_len = count + 1
                payload = dwords[idx + 1:idx + 1 + payload_len]
                for offset, val in enumerate(payload):
                    self.config_regs[base_reg + offset] = val
                idx += 1 + payload_len
                packet_count += 1

            elif pkt_type == PM4Type.TYPE_2:
                # Type-2 is NOP padding
                idx += 1
                packet_count += 1
            else:
                Logger.warn(Subsystem.GPU, f"Unrecognized PM4 packet type {pkt_type} at offset {idx}")
                idx += 1

        return packet_count

    def _handle_type3(self, opcode: PM4Opcode, payload: List[int]) -> None:
        if opcode == PM4Opcode.NOP:
            pass # NOP packet

        elif opcode == PM4Opcode.SET_CONTEXT_REG:
            if not payload:
                return
            base_reg = payload[0] & 0xFFFF
            values = payload[1:]
            for offset, val in enumerate(values):
                reg = base_reg + offset
                self.context_regs[reg] = val
            Logger.debug(Subsystem.GPU, f"SET_CONTEXT_REG base=0x{base_reg:X}, count={len(values)}")

        elif opcode == PM4Opcode.SET_SH_REG:
            if not payload:
                return
            base_reg = payload[0] & 0xFFFF
            values = payload[1:]
            for offset, val in enumerate(values):
                reg = base_reg + offset
                self.sh_regs[reg] = val
                # Track shader program base addresses (SPI_SHADER_PGM_LO/HI)
                if reg == 0x208: # SPI_SHADER_PGM_LO_VS
                    self.vs_shader_addr = (self.vs_shader_addr & ~0xFFFFFFFF) | val
                elif reg == 0x209: # SPI_SHADER_PGM_HI_VS
                    self.vs_shader_addr = (self.vs_shader_addr & 0xFFFFFFFF) | (val << 32)
                elif reg == 0x20C: # SPI_SHADER_PGM_LO_PS
                    self.ps_shader_addr = (self.ps_shader_addr & ~0xFFFFFFFF) | val
                elif reg == 0x20D: # SPI_SHADER_PGM_HI_PS
                    self.ps_shader_addr = (self.ps_shader_addr & 0xFFFFFFFF) | (val << 32)
            Logger.debug(Subsystem.GPU, f"SET_SH_REG base=0x{base_reg:X}, count={len(values)}")

        elif opcode == PM4Opcode.INDEX_TYPE:
            self.index_type = payload[0] & 0x1
            Logger.debug(Subsystem.GPU, f"INDEX_TYPE set to {'32-bit' if self.index_type else '16-bit'}")

        elif opcode == PM4Opcode.INDEX_BASE:
            lo = payload[0]
            hi = payload[1] if len(payload) > 1 else 0
            self.index_base = lo | (hi << 32)
            Logger.debug(Subsystem.GPU, f"INDEX_BASE set to 0x{self.index_base:016X}")

        elif opcode == PM4Opcode.NUM_INSTANCES:
            self.num_instances = payload[0]
            Logger.debug(Subsystem.GPU, f"NUM_INSTANCES set to {self.num_instances}")

        elif opcode == PM4Opcode.DRAW_INDEX_AUTO:
            index_count = payload[0]
            draw_type = payload[1] if len(payload) > 1 else 0
            prim = "TRIANGLE_LIST" if (draw_type & 0x3F) == 4 else "RECT_LIST"
            record = DrawCallRecord(index_count, self.num_instances, is_indexed=False, primitive_type=prim)
            self.draw_calls.append(record)
            Logger.info(Subsystem.GPU, f"DRAW_INDEX_AUTO: VertexCount={index_count}, Instances={self.num_instances}, Prim={prim}")

        elif opcode == PM4Opcode.DRAW_INDEX_2:
            max_size = payload[0]
            index_base = payload[1] | (payload[2] << 32) if len(payload) > 2 else self.index_base
            index_count = payload[3] if len(payload) > 3 else max_size
            record = DrawCallRecord(index_count, self.num_instances, is_indexed=True, primitive_type="TRIANGLES")
            self.draw_calls.append(record)
            Logger.info(Subsystem.GPU, f"DRAW_INDEX_2: IndexCount={index_count}, Base=0x{index_base:X}, Instances={self.num_instances}")


"""
AetherPS4 - Modern PlayStation 4 Emulator Core
Lead Architect & Developer: PRIYAN-A-1
Copyright (c) 2026 PRIYAN-A-1. All rights reserved.
SPDX-License-Identifier: MIT

Core Emulator Orchestrator for AetherPS4.
"""

from typing import Optional, List, Dict
from aether_ps4.common.logger import Logger, Subsystem
from aether_ps4.common.types import MemoryProt
from aether_ps4.memory.address_space import AddressSpace
from aether_ps4.kernel.orbis import OrbisKernel
from aether_ps4.loader.elf import ElfLoader
from aether_ps4.loader.nid_resolver import NidResolver
from aether_ps4.gpu.pm4 import PM4Processor
from aether_ps4.file_format.sfo import SfoParser

class AetherEmulator:
    """
    Main PS4 Emulator Instance.
    """
    def __init__(self, is_neo: bool = False, verbose: bool = False):
        Logger.VERBOSE = verbose
        Logger.info(Subsystem.EMU, "Initializing AetherPS4 Modern Emulator Core...")

        self.memory = AddressSpace()
        self.kernel = OrbisKernel(self.memory, is_neo=is_neo)
        self.nid_resolver = NidResolver()
        self.gpu = PM4Processor()

        self.current_loader: Optional[ElfLoader] = None
        self.current_sfo: Optional[SfoParser] = None

        self._bind_kernel_handlers()
        Logger.success(Subsystem.EMU, "AetherPS4 Core Subsystems Initialized Successfully")

    def _bind_kernel_handlers(self) -> None:
        """
        Connects Orbis OS kernel HLE syscall implementations to the NID resolver.
        """
        self.nid_resolver.register(
            "sceKernelAllocateDirectMemory", "libkernel.sprx", "libkernel",
            self.kernel.sceKernelAllocateDirectMemory
        )
        self.nid_resolver.register(
            "sceKernelMapDirectMemory", "libkernel.sprx", "libkernel",
            self.kernel.sceKernelMapDirectMemory
        )
        self.nid_resolver.register(
            "sceKernelCreateMutex", "libkernel.sprx", "libkernel",
            self.kernel.sceKernelCreateMutex
        )
        self.nid_resolver.register(
            "sceKernelLockMutex", "libkernel.sprx", "libkernel",
            self.kernel.sceKernelLockMutex
        )
        self.nid_resolver.register(
            "sceKernelUnlockMutex", "libkernel.sprx", "libkernel",
            self.kernel.sceKernelUnlockMutex
        )
        self.nid_resolver.register(
            "sceSysmoduleLoadModule", "libSceSysmodule.sprx", "libSceSysmodule",
            self.kernel.sceSysmoduleLoadModule
        )
        self.nid_resolver.register(
            "sceKernelCreateSema", "libkernel.sprx", "libkernel",
            self.kernel.sceKernelCreateSema
        )
        self.nid_resolver.register(
            "sceKernelSignalSema", "libkernel.sprx", "libkernel",
            self.kernel.sceKernelSignalSema
        )
        self.nid_resolver.register(
            "sceKernelCreateEventFlag", "libkernel.sprx", "libkernel",
            self.kernel.sceKernelCreateEventFlag
        )
        self.nid_resolver.register(
            "sceKernelSetEventFlag", "libkernel.sprx", "libkernel",
            self.kernel.sceKernelSetEventFlag
        )
        self.nid_resolver.register(
            "sceKernelIsNeoMode", "libkernel.sprx", "libkernel",
            self.kernel.sceKernelIsNeoMode
        )
        self.nid_resolver.register(
            "sceKernelGetProcessTime", "libkernel.sprx", "libkernel",
            self.kernel.sceKernelGetProcessTime
        )

    def load_elf(self, elf_bytes: bytes) -> ElfLoader:
        """
        Loads and maps an ELF64 / SELF executable into virtual memory.
        """
        loader = ElfLoader(elf_bytes)
        self.current_loader = loader

        # Map PT_LOAD segments into virtual address space
        for ph, data in loader.get_loadable_segments():
            Logger.info(
                Subsystem.LOADER,
                f"Mapping PT_LOAD: VAddr=0x{ph.p_vaddr:012X}, Size=0x{ph.p_memsz:X}, Prot={ph.memory_prot.name}"
            )
            # Allocate and map memory for the segment
            self.memory.allocate_virtual_memory(
                ph.p_vaddr, ph.p_memsz, ph.memory_prot, alignment=ph.p_align
            )
            self.memory.write_bytes(ph.p_vaddr, data)

        Logger.success(Subsystem.LOADER, f"Mapped executable with entry point at 0x{loader.entry_point:012X}")
        return loader

    def load_sfo(self, sfo_bytes: bytes) -> SfoParser:
        """
        Loads and parses game param.sfo metadata.
        """
        sfo = SfoParser(sfo_bytes)
        self.current_sfo = sfo
        Logger.info(Subsystem.FILESYS, f"Active Title: '{sfo.title}' [{sfo.title_id}] (v{sfo.app_ver})")
        return sfo

    def submit_gpu_commands(self, dwords: List[int]) -> int:
        """
        Dispatches GPU command buffer to Liverpool PM4 processor.
        """
        Logger.info(Subsystem.GPU, f"Submitting command buffer ({len(dwords)} DWORDs)...")
        count = self.gpu.process_command_buffer(dwords)
        Logger.success(Subsystem.GPU, f"Processed {count} PM4 packets; {len(self.gpu.draw_calls)} draw calls generated")
        return count


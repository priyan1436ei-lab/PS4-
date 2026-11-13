"""
FreeBSD 9 / Orbis OS High-Level Emulation (HLE) Kernel Subsystem.
Implements synchronization primitives, thread tracking,
direct memory syscalls, and system module dispatching.
"""

import time
from typing import Dict, Optional, List, Any, Tuple
from aether_ps4.common.types import OrbisErrorCode, MemoryProt, GUEST_PAGE_SIZE
from aether_ps4.common.logger import Logger, Subsystem
from aether_ps4.memory.address_space import AddressSpace

class OrbisMutex:
    def __init__(self, mid: int, name: str, attr: int):
        self.mid = mid
        self.name = name
        self.attr = attr
        self.locked = False
        self.owner_thread_id = 0

class OrbisSemaphore:
    def __init__(self, sid: int, name: str, init_count: int, max_count: int):
        self.sid = sid
        self.name = name
        self.count = init_count
        self.max_count = max_count

class OrbisEventFlag:
    def __init__(self, efid: int, name: str, init_val: int):
        self.efid = efid
        self.name = name
        self.bit_pattern = init_val

class OrbisThread:
    def __init__(self, tid: int, name: str, entry: int, arg: int, stack_base: int, stack_size: int):
        self.tid = tid
        self.name = name
        self.entry = entry
        self.arg = arg
        self.stack_base = stack_base
        self.stack_size = stack_size
        self.state = "READY"

class OrbisKernel:
    """
    Central Orbis OS HLE environment managing process state, threads, and kernel objects.
    """
    def __init__(self, memory: AddressSpace, is_neo: bool = False):
        self.memory = memory
        self.is_neo = is_neo # PS4 Pro Neo mode
        self.threads: Dict[int, OrbisThread] = {}
        self.mutexes: Dict[int, OrbisMutex] = {}
        self.semaphores: Dict[int, OrbisSemaphore] = {}
        self.event_flags: Dict[int, OrbisEventFlag] = {}
        self.loaded_modules: Dict[int, str] = {} # ModuleId -> Name

        self._next_tid = 1
        self._next_mid = 1
        self._next_sid = 1
        self._next_efid = 1
        self.start_time = time.time()

        Logger.info(Subsystem.KERNEL, f"Orbis OS Kernel Initialized (Hardware Mode: {'PS4 Pro Neo' if is_neo else 'Standard PS4'})")

    # --- Direct Memory Management ---
    def sceKernelAllocateDirectMemory(self, search_start: int, search_end: int, length: int, alignment: int, memory_type: int) -> Tuple[int, int]:
        try:
            paddr = self.memory.allocate_direct_memory(length, alignment, memory_type)
            Logger.info(Subsystem.KERNEL, f"sceKernelAllocateDirectMemory(len=0x{length:X}, align=0x{alignment:X}) -> PAddr=0x{paddr:X}")
            return OrbisErrorCode.SCE_OK, paddr
        except MemoryError:
            return OrbisErrorCode.SCE_KERNEL_ERROR_ENOMEM, 0

    def sceKernelMapDirectMemory(self, vaddr_req: int, length: int, prot_val: int, flags: int, paddr_offset: int, align: int) -> Tuple[int, int]:
        prot = MemoryProt(prot_val)
        vaddr = self.memory.map_direct_memory(vaddr_req, length, prot, paddr_offset, align)
        Logger.info(Subsystem.KERNEL, f"sceKernelMapDirectMemory(req=0x{vaddr_req:X}, len=0x{length:X}, prot={prot.name}) -> VAddr=0x{vaddr:X}")
        return OrbisErrorCode.SCE_OK, vaddr

    # --- Mutex Primitives ---
    def sceKernelCreateMutex(self, name: str, attr: int) -> int:
        mid = self._next_mid
        self._next_mid += 1
        self.mutexes[mid] = OrbisMutex(mid, name, attr)
        Logger.debug(Subsystem.KERNEL, f"sceKernelCreateMutex('{name}') -> ID={mid}")
        return mid

    def sceKernelLockMutex(self, mid: int) -> int:
        if mid not in self.mutexes:
            return OrbisErrorCode.SCE_KERNEL_ERROR_EINVAL
        self.mutexes[mid].locked = True
        return OrbisErrorCode.SCE_OK

    def sceKernelUnlockMutex(self, mid: int) -> int:
        if mid not in self.mutexes:
            return OrbisErrorCode.SCE_KERNEL_ERROR_EINVAL
        self.mutexes[mid].locked = False
        return OrbisErrorCode.SCE_OK

    # --- Semaphore Primitives ---
    def sceKernelCreateSema(self, name: str, init_val: int, max_val: int) -> int:
        sid = self._next_sid
        self._next_sid += 1
        self.semaphores[sid] = OrbisSemaphore(sid, name, init_val, max_val)
        Logger.debug(Subsystem.KERNEL, f"sceKernelCreateSema('{name}', init={init_val}, max={max_val}) -> ID={sid}")
        return sid

    def sceKernelSignalSema(self, sid: int, count: int) -> int:
        if sid not in self.semaphores:
            return OrbisErrorCode.SCE_KERNEL_ERROR_EINVAL
        sema = self.semaphores[sid]
        sema.count = min(sema.max_count, sema.count + count)
        return OrbisErrorCode.SCE_OK

    # --- Event Flags ---
    def sceKernelCreateEventFlag(self, name: str, init_val: int) -> int:
        efid = self._next_efid
        self._next_efid += 1
        self.event_flags[efid] = OrbisEventFlag(efid, name, init_val)
        Logger.debug(Subsystem.KERNEL, f"sceKernelCreateEventFlag('{name}', init=0x{init_val:X}) -> ID={efid}")
        return efid

    def sceKernelSetEventFlag(self, efid: int, bits: int) -> int:
        if efid not in self.event_flags:
            return OrbisErrorCode.SCE_KERNEL_ERROR_EINVAL
        self.event_flags[efid].bit_pattern |= bits
        return OrbisErrorCode.SCE_OK

    # --- System Info ---
    def sceKernelIsNeoMode(self) -> int:
        return 1 if self.is_neo else 0

    def sceKernelGetProcessTime(self) -> int:
        """Returns process execution time in microseconds."""
        return int((time.time() - self.start_time) * 1_000_000)

    # --- Module Loader ---
    def sceSysmoduleLoadModule(self, module_id: int) -> int:
        MODULE_NAMES = {
            0x0001: "libSceNet",
            0x0002: "libSceAudioOut",
            0x0003: "libScePad",
            0x0004: "libSceVideoOut",
            0x0005: "libSceGnmDriver",
            0x0006: "libSceSaveData",
            0x0007: "libSceSysmodule",
            0x0017: "libSceNpCommon",
        }
        mod_name = MODULE_NAMES.get(module_id, f"UnknownModule_0x{module_id:04X}")
        self.loaded_modules[module_id] = mod_name
        Logger.info(Subsystem.KERNEL, f"sceSysmoduleLoadModule(0x{module_id:04X}: {mod_name}) -> OK")
        return OrbisErrorCode.SCE_OK

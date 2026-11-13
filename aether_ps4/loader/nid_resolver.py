"""
Sony Name Identifier (NID) database and resolver.
Resolves obfuscated 64-bit and base64 NIDs to human-readable API signatures
and binds them to emulator High-Level Emulation (HLE) functions.
"""

from typing import Dict, Optional, Callable, Any
from aether_ps4.common.hashing import compute_sha1_nid, compute_nid_string
from aether_ps4.common.logger import Logger, Subsystem

class SymbolInfo:
    def __init__(self, name: str, module: str, library: str, handler: Optional[Callable[..., Any]] = None):
        self.name = name
        self.module = module
        self.library = library
        self.handler = handler
        self.nid_u64 = compute_sha1_nid(name)
        self.nid_str = compute_nid_string(name)

    def __repr__(self) -> str:
        return f"<SymbolInfo {self.module}::{self.name} (NID: 0x{self.nid_u64:016X})>"

class NidResolver:
    """
    Central symbol and NID registry for the emulator dynamic linker.
    """
    def __init__(self):
        self._by_u64: Dict[int, SymbolInfo] = {}
        self._by_str: Dict[str, SymbolInfo] = {}
        self._by_name: Dict[str, SymbolInfo] = {}
        self._register_known_symbols()

    def register(self, name: str, module: str, library: str, handler: Optional[Callable[..., Any]] = None) -> SymbolInfo:
        sym = SymbolInfo(name, module, library, handler)
        self._by_u64[sym.nid_u64] = sym
        self._by_str[sym.nid_str] = sym
        self._by_name[name] = sym
        return sym

    def resolve_u64(self, nid: int) -> Optional[SymbolInfo]:
        return self._by_u64.get(nid)

    def resolve_str(self, nid_str: str) -> Optional[SymbolInfo]:
        return self._by_str.get(nid_str)

    def resolve_name(self, name: str) -> Optional[SymbolInfo]:
        return self._by_name.get(name)

    def _register_known_symbols(self) -> None:
        # libkernel symbols
        kernel_syms = [
            "sceKernelAllocateDirectMemory",
            "sceKernelMapDirectMemory",
            "sceKernelReleaseDirectMemory",
            "sceKernelCreateEqueue",
            "sceKernelDeleteEqueue",
            "sceKernelAddUserEvent",
            "sceKernelWaitEqueue",
            "sceKernelCreateMutex",
            "sceKernelDestroyMutex",
            "sceKernelLockMutex",
            "sceKernelUnlockMutex",
            "sceKernelTryLockMutex",
            "sceKernelCreateCond",
            "sceKernelDestroyCond",
            "sceKernelSignalCond",
            "sceKernelWaitCond",
            "sceKernelCreateSema",
            "sceKernelDestroySema",
            "sceKernelSignalSema",
            "sceKernelWaitSema",
            "sceKernelCreateEventFlag",
            "sceKernelDestroyEventFlag",
            "sceKernelSetEventFlag",
            "sceKernelWaitEventFlag",
            "sceKernelCreateThread",
            "sceKernelStartThread",
            "sceKernelExitThread",
            "sceKernelWaitThreadEnd",
            "scePthreadCreate",
            "scePthreadJoin",
            "scePthreadExit",
            "sceKernelGettimeofday",
            "sceKernelGetProcessTime",
            "sceKernelUsleep",
            "sceKernelNanosleep",
            "sceKernelIsNeoMode",
            "sceKernelIccSetBuzzer",
            "sceKernelGetDirectMemorySize",
        ]
        for name in kernel_syms:
            self.register(name, "libkernel.sprx", "libkernel")

        # libSceGnmDriver (Graphics Driver)
        gnm_syms = [
            "sceGnmSubmitCommandBuffers",
            "sceGnmSubmitAndFlipCommandBuffers",
            "sceGnmDrawIndexAuto",
            "sceGnmDrawIndex",
            "sceGnmDispatchDirect",
            "sceGnmSetCsShader",
            "sceGnmSetPsShader",
            "sceGnmSetVsShader",
            "sceGnmInsertPushMarker",
            "sceGnmInsertPopMarker",
            "sceGnmFlushGarlic",
            "sceGnmDingDong",
        ]
        for name in gnm_syms:
            self.register(name, "libSceGnmDriver.sprx", "libSceGnmDriver")

        # libSceVideoOut (Display Output)
        video_syms = [
            "sceVideoOutOpen",
            "sceVideoOutClose",
            "sceVideoOutRegisterBuffers",
            "sceVideoOutSubmitFlip",
            "sceVideoOutGetResolutionStatus",
            "sceVideoOutAddFlipEvent",
        ]
        for name in video_syms:
            self.register(name, "libSceVideoOut.sprx", "libSceVideoOut")

        # libScePad (DualShock 4 Controller)
        pad_syms = [
            "scePadOpen",
            "scePadClose",
            "scePadReadState",
            "scePadSetLightBar",
            "scePadSetVibration",
            "scePadResetOrientation",
        ]
        for name in pad_syms:
            self.register(name, "libScePad.sprx", "libScePad")

        # libSceAudioOut (Audio System)
        audio_syms = [
            "sceAudioOutOpen",
            "sceAudioOutClose",
            "sceAudioOutOutput",
            "sceAudioOutSetVolume",
        ]
        for name in audio_syms:
            self.register(name, "libSceAudioOut.sprx", "libSceAudioOut")

        # libSceSysmodule (Module Loader)
        sysmod_syms = [
            "sceSysmoduleLoadModule",
            "sceSysmoduleUnloadModule",
            "sceSysmoduleIsLoaded",
        ]
        for name in sysmod_syms:
            self.register(name, "libSceSysmodule.sprx", "libSceSysmodule")

        Logger.debug(Subsystem.LOADER, f"Initialized NID database with {len(self._by_u64)} known API entries")


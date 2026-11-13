"""
Colored and structured logging for AetherPS4 emulator subsystems.
"""

import sys
import time

class Subsystem:
    LOADER = "Loader"
    MEMORY = "Memory"
    KERNEL = "Kernel"
    GPU = "GPU"
    AUDIO = "Audio"
    INPUT = "Input"
    FILESYS = "FileSys"
    LINKER = "Linker"
    EMU = "AetherPS4"

class Logger:
    ENABLED = True
    VERBOSE = False

    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    @classmethod
    def _timestamp(cls) -> str:
        return time.strftime("%H:%M:%S")

    @classmethod
    def info(cls, subsystem: str, message: str) -> None:
        if not cls.ENABLED:
            return
        print(f"[{cls._timestamp()}] {cls.CYAN}[{subsystem}]{cls.RESET} {message}")

    @classmethod
    def debug(cls, subsystem: str, message: str) -> None:
        if not cls.ENABLED or not cls.VERBOSE:
            return
        print(f"[{cls._timestamp()}] {cls.MAGENTA}[{subsystem}:DEBUG]{cls.RESET} {message}")

    @classmethod
    def warn(cls, subsystem: str, message: str) -> None:
        if not cls.ENABLED:
            return
        print(f"[{cls._timestamp()}] {cls.YELLOW}[{subsystem}:WARN]{cls.RESET} {message}")

    @classmethod
    def error(cls, subsystem: str, message: str) -> None:
        print(f"[{cls._timestamp()}] {cls.RED}[{subsystem}:ERROR]{cls.RESET} {cls.BOLD}{message}{cls.RESET}", file=sys.stderr)

    @classmethod
    def success(cls, subsystem: str, message: str) -> None:
        if not cls.ENABLED:
            return
        print(f"[{cls._timestamp()}] {cls.GREEN}[{subsystem}:OK]{cls.RESET} {message}")


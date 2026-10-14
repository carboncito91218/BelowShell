"""Utilidades de sistema compartidas por el núcleo."""
from __future__ import annotations

import subprocess
import sys

IS_WINDOWS = sys.platform.startswith("win")
NO_WINDOW = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0  # evita parpadeos de consola

if IS_WINDOWS:
    import ctypes

    CONSOLE_ENCODING = f"cp{ctypes.windll.kernel32.GetOEMCP()}"  # codificación de ping.exe
else:
    CONSOLE_ENCODING = "utf-8"


def run(cmd: list[str], timeout: float = 3) -> str:
    """Ejecuta un comando y devuelve su salida; cadena vacía si falla."""
    try:
        return subprocess.run(
            cmd, capture_output=True, encoding=CONSOLE_ENCODING, errors="replace",
            timeout=timeout, creationflags=NO_WINDOW,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return ""

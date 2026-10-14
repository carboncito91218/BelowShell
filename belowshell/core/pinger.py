"""Ping con el comando del sistema, mostrando la salida en el formato del wireframe."""
from __future__ import annotations

import re
import subprocess
import threading
from typing import Callable

from belowshell.config import PING_COUNT, PING_TIMEOUT_S

from .system import CONSOLE_ENCODING, IS_WINDOWS, NO_WINDOW

Emit = Callable[[str, str], None]  # (tipo de salida, texto)

_HOST = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_NIX = re.compile(r"^(\d+) bytes from (.+?): icmp_seq=(\d+) ttl=(\d+) time=([\d.]+) ms", re.I)
_WIN = re.compile(r"bytes\s*=\s*(\d+)\s+\w+\s*([=<])\s*(\d+)\s*ms\s+TTL\s*=\s*(\d+)", re.I)  # sirve en cualquier idioma
_IPV4 = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}")


def _command(host: str) -> list[str]:
    if IS_WINDOWS:
        return ["ping", "-n", str(PING_COUNT), "-w", str(PING_TIMEOUT_S * 1000), host]
    return ["ping", "-c", str(PING_COUNT), "-W", str(PING_TIMEOUT_S), host]


def _parse_reply(line: str, seq: int) -> tuple[str, float] | None:
    """Si la línea es una respuesta, devuelve (línea normalizada, tiempo en ms)."""
    if m := _NIX.match(line):
        size, origin, seq, ttl, rtt = m.groups()
        return f"{size} bytes from {origin}: icmp_seq={seq} ttl={ttl} time={rtt} ms", float(rtt)
    if m := _WIN.search(line):
        size, sign, rtt, ttl = m.groups()
        origin = ip[0] if (ip := _IPV4.search(line)) else "?"
        return f"{size} bytes from {origin}: icmp_seq={seq} ttl={ttl} time{sign}{rtt} ms", float(rtt)
    return None


def _watch(proc: subprocess.Popen, cancel: threading.Event, finished: threading.Event) -> None:
    """Mata el ping apenas el usuario cancela (Ctrl+C)."""
    while not finished.is_set():
        if cancel.wait(0.1):
            try:
                proc.kill()
            except OSError:
                pass
            return


def run_ping(host: str, emit: Emit, cancel: threading.Event) -> None:
    if not _HOST.match(host):
        emit("err", f"Host no válido: {host}")
        return
    try:
        proc = subprocess.Popen(
            _command(host), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            encoding=CONSOLE_ENCODING, errors="replace", creationflags=NO_WINDOW,
        )
    except OSError:
        emit("err", "No se encontró el comando ping en este equipo.")
        return

    finished = threading.Event()
    threading.Thread(target=_watch, args=(proc, cancel, finished), daemon=True).start()
    rtts: list[float] = []
    failures, header_seen, raw = 0, False, []
    try:
        for raw_line in proc.stdout:
            line = raw_line.strip()
            if not line:
                if header_seen:
                    break  # lo que sigue es el resumen del sistema: se genera uno propio
                continue
            raw.append(line)
            if not header_seen:  # primera línea = cabecera ("Pinging...", "PING ...")
                header_seen = True
                continue
            if reply := _parse_reply(line, len(rtts) + failures + 1):
                rtts.append(reply[1])
                emit("out", reply[0])
            else:
                failures += 1
                emit("err", line)
    finally:
        finished.set()
        if proc.poll() is None:
            proc.kill()
        proc.wait()
        proc.stdout.close()

    if cancel.is_set():
        emit("dim", "^C")
    elif not rtts and not failures:  # p. ej. host inexistente: se muestra el mensaje del sistema
        for line in raw:
            emit("err", line)
    else:
        sent = len(rtts) + failures
        emit("dim", f"\n--- {host} ping statistics ---")
        emit("dim", f"{sent} packets transmitted, {len(rtts)} received, {round(100 * failures / sent)}% packet loss")
        if rtts:
            emit("dim", f"rtt min/avg/max = {min(rtts):.4g}/{sum(rtts) / len(rtts):.4g}/{max(rtts):.4g} ms")

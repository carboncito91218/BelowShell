"""Mensajería entre equipos: cada BelowShell escucha por TCP y envía directo a la IP destino."""
from __future__ import annotations

import json
import socket
import socketserver
import sys
import threading
from dataclasses import dataclass
from typing import Callable

from belowshell.config import MSG_MAX_CHARS, MSG_PORT, MSG_TIMEOUT_S

_MAX_BYTES = MSG_MAX_CHARS * 4 + 512  # UTF-8 usa hasta 4 bytes por carácter


@dataclass(frozen=True)
class IncomingMessage:
    sender_ip: str
    sender_host: str
    text: str


@dataclass(frozen=True)
class SendResult:
    ok: bool
    detail: str


class _Handler(socketserver.StreamRequestHandler):
    timeout = 3

    def handle(self) -> None:
        try:
            payload = json.loads(self.rfile.readline(_MAX_BYTES + 1).decode("utf-8"))
            message = IncomingMessage(
                self.client_address[0], str(payload["host"])[:64], str(payload["text"])[:MSG_MAX_CHARS]
            )
        except (OSError, ValueError, KeyError, TypeError):
            self._reply(b"ERR\n")
            return
        self.server.on_message(message)
        self._reply(b"OK\n")

    def _reply(self, data: bytes) -> None:
        try:
            self.wfile.write(data)
        except OSError:
            pass


class _Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    # En Windows SO_REUSEADDR permite que dos programas compartan el puerto: se desactiva.
    allow_reuse_address = not sys.platform.startswith("win")


class MessageServer:
    """Escucha mensajes en segundo plano y los entrega a `on_message` (desde otro hilo)."""

    def __init__(self, on_message: Callable[[IncomingMessage], None], port: int = MSG_PORT):
        self._on_message, self._port = on_message, port
        self._server: _Server | None = None

    def start(self) -> str | None:
        """Abre el puerto. Devuelve un texto de error si no se pudo, None si todo salió bien."""
        try:
            self._server = _Server(("0.0.0.0", self._port), _Handler)
        except OSError as exc:
            return f"No se pudo abrir el puerto {self._port} ({exc.strerror or exc}). No podrás recibir mensajes."
        self._server.on_message = self._on_message
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        return None

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server.server_close()


def send_message(ip: str, text: str, sender_host: str, port: int = MSG_PORT) -> SendResult:
    data = json.dumps({"host": sender_host, "text": text}).encode("utf-8") + b"\n"
    try:
        with socket.create_connection((ip, port), timeout=MSG_TIMEOUT_S) as sock:
            sock.sendall(data)
            ack = sock.recv(16)
    except ConnectionRefusedError:
        return SendResult(False, f"{ip} está encendido pero BelowShell no está abierto allí.")
    except (socket.timeout, TimeoutError):
        return SendResult(False, f"Sin respuesta de {ip}: equipo apagado, IP incorrecta o puerto bloqueado.")
    except OSError as exc:
        return SendResult(False, f"No se pudo enviar el mensaje: {exc.strerror or exc}")
    if ack.startswith(b"OK"):
        return SendResult(True, f"Mensaje enviado correctamente a {ip}.")
    return SendResult(False, f"{ip} rechazó el mensaje.")

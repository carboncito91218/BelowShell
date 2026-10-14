"""Infraestructura de comandos: registro, contexto y decorador para añadir comandos nuevos."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable

Emit = Callable[[str, str], None]  # (tipo, texto); tipos: out, err, ok, dim


@dataclass(frozen=True)
class CommandContext:
    emit: Emit                # envía salida a la pantalla (seguro entre hilos)
    cancel: threading.Event   # se activa cuando el usuario presiona Ctrl+C
    registry: "Registry"


@dataclass(frozen=True)
class Command:
    name: str
    usage: str
    description: str
    handler: Callable[[str, CommandContext], None]


class Registry:
    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}

    def register(self, name: str, usage: str, description: str):
        def decorator(handler):
            self._commands[name] = Command(name, usage, description, handler)
            return handler
        return decorator

    def get(self, name: str) -> Command | None:
        return self._commands.get(name.lower())

    def all(self) -> list[Command]:
        return sorted(self._commands.values(), key=lambda c: c.name)


registry = Registry()

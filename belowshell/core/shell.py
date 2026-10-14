"""Intérprete: separa comando y argumentos, lo ejecuta en un hilo y permite cancelarlo."""
from __future__ import annotations

import threading
from typing import Callable

from .commands import CommandContext, Registry, registry as default_registry

Emit = Callable[[str, str], None]


class Shell:
    def __init__(self, registry: Registry = default_registry) -> None:
        self._registry = registry
        self._cancel = threading.Event()

    def execute(self, line: str, emit: Emit, on_done: Callable[[], None]) -> None:
        """Corre `line` en segundo plano; `emit` y `on_done` se llaman desde ese hilo."""
        self._cancel = threading.Event()
        ctx = CommandContext(emit, self._cancel, self._registry)
        threading.Thread(target=self._run, args=(line, ctx, on_done), daemon=True).start()

    def interrupt(self) -> None:
        self._cancel.set()

    def _run(self, line: str, ctx: CommandContext, on_done: Callable[[], None]) -> None:
        name, _, args = line.strip().partition(" ")
        command = self._registry.get(name)
        try:
            if command is None:
                ctx.emit("err", f"'{name}' no se reconoce como un comando. Escribe help para ver la lista.")
            else:
                command.handler(args.strip(), ctx)
        except Exception as exc:  # un comando con error nunca debe tumbar la shell
            ctx.emit("err", f"Error inesperado en '{name}': {exc}")
        finally:
            on_done()

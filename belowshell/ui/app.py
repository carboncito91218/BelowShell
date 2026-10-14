"""Ventana principal de BelowShell: une la terminal, la shell y el servidor de mensajes."""
from __future__ import annotations

import queue

import customtkinter as ctk

from belowshell.config import APP_NAME, VERSION
from belowshell.core.messaging import IncomingMessage, MessageServer
from belowshell.core.network import get_network_info
from belowshell.core.shell import Shell

from . import theme
from .popup import MessagePopup
from .terminal import Terminal

POLL_MS = 30


class BelowShellApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__(fg_color=theme.BG_WINDOW)
        self.title(f"{APP_NAME} {VERSION}")
        self.geometry("920x580")
        self.minsize(560, 360)

        self._events: queue.SimpleQueue = queue.SimpleQueue()  # los hilos dejan eventos; solo la UI los dibuja
        self._shell = Shell()
        self._popups: list[MessagePopup] = []
        self._server = MessageServer(lambda message: self._events.put(("msg", message)))

        info = get_network_info()
        self._build_header()
        self._terminal = Terminal(self, f"{info.hostname} : ", self._submit, self._shell.interrupt)
        self._terminal.grid(row=1, column=0, sticky="nsew", padx=16, pady=(6, 16))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._terminal.print(f"IPv4: {info.ip}   Escribe help para ver los comandos." if info.connected
                             else "Sin conexión de red: el equipo no tiene IP. Escribe help para ver los comandos.", "dim")
        if error := self._server.start():
            self._terminal.print(error, "err")
        self._terminal.show_prompt()

        self.protocol("WM_DELETE_WINDOW", self._close)
        self.after(POLL_MS, self._poll)

    def _build_header(self) -> None:
        bar = ctk.CTkFrame(self, fg_color=theme.BAR, corner_radius=10, height=36)
        bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 0))
        ctk.CTkLabel(bar, text=APP_NAME, text_color=theme.BAR_TEXT,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=14, pady=6)
        ctk.CTkLabel(bar, text=f"Version {VERSION}", text_color=theme.BAR_TEXT,
                     font=ctk.CTkFont(size=13)).pack(side="right", padx=14)

    # ---------- Comandos ----------
    def _submit(self, line: str) -> None:
        if not line:
            self._terminal.show_prompt()
            return
        self._shell.execute(
            line,
            emit=lambda kind, text: self._events.put(("out", kind, text)),
            on_done=lambda: self._events.put(("done",)),
        )

    # ---------- Eventos desde otros hilos ----------
    def _poll(self) -> None:
        while True:
            try:
                event = self._events.get_nowait()
            except queue.Empty:
                break
            if event[0] == "out":
                self._terminal.print(event[2], event[1])
            elif event[0] == "done":
                self._terminal.show_prompt()
            elif event[0] == "msg":
                self._show_message(event[1])
        self.after(POLL_MS, self._poll)

    def _show_message(self, message: IncomingMessage) -> None:
        self._popups = [p for p in self._popups if p.winfo_exists()]
        self._popups.append(MessagePopup(self, message, offset=len(self._popups)))

    def _close(self) -> None:
        self._shell.interrupt()
        self._server.stop()
        self.destroy()

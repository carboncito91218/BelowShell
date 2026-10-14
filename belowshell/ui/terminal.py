"""Terminal: un único cuadro de texto con salida de solo lectura y una línea de entrada al final."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

import customtkinter as ctk

from . import theme

# Teclas de desplazamiento que se permiten aunque haya un comando ejecutándose
_MOVE_KEYS = {"Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next"}


class Terminal(ctk.CTkTextbox):
    def __init__(self, master, prompt: str, on_submit: Callable[[str], None], on_interrupt: Callable[[], None]):
        super().__init__(
            master, font=theme.mono_font(), fg_color=theme.BG_TERMINAL, text_color=theme.TEXT,
            corner_radius=10, wrap="word", border_spacing=14,
        )
        self._prompt, self._on_submit, self._on_interrupt = prompt, on_submit, on_interrupt
        self._history: list[str] = []
        self._hist_pos, self._draft = 0, ""
        self._locked = True  # bloqueado mientras corre un comando

        text = self._text = self._textbox
        text.configure(insertbackground=theme.TEXT, insertwidth=2, spacing1=2, spacing3=2,
                       selectbackground=theme.SELECTION, inactiveselectbackground=theme.SELECTION)
        for kind, color in theme.KIND_COLORS.items():
            text.tag_configure(kind, foreground=color)
        text.mark_set("input", "1.0")
        text.mark_gravity("input", "left")

        text.bind("<Key>", self._on_key)
        text.bind("<Return>", self._on_return)
        text.bind("<KP_Enter>", self._on_return)
        for letter in "cC":
            text.bind(f"<Control-{letter}>", self._on_ctrl_c)
        for letter in "vV":
            text.bind(f"<Control-{letter}>", self._on_paste)
        for letter in "aA":
            text.bind(f"<Control-{letter}>", self._select_all)
        text.bind("<<Paste>>", self._on_paste)  # Shift+Insert y menú contextual
        for event in ("<<Cut>>", "<Button-2>"):  # cortar y pegar con clic central editarían la salida
            text.bind(event, lambda e: "break")

    # ---------- API pública ----------
    def print(self, text: str, kind: str = "out") -> None:
        self._text.insert("end-1c", text + "\n", kind)
        self._text.see("end")

    def show_prompt(self) -> None:
        """Dibuja el prompt y deja la línea lista para escribir."""
        t = self._text
        t.insert("end-1c", self._prompt, "prompt")
        t.mark_set("input", "end-1c")
        t.mark_set("insert", "end-1c")
        t.see("end")
        self._locked = False
        t.focus_set()

    # ---------- Teclado ----------
    def _on_key(self, e: tk.Event):
        key, t = e.keysym, self._text
        if self._locked:
            return None if key in _MOVE_KEYS else "break"
        if key in ("Up", "Down"):
            return self._browse_history(-1 if key == "Up" else 1)
        if key == "Home":
            t.mark_set("insert", "input")
            return "break"
        if key == "Left":
            return "break" if t.compare("insert", "==", "input") else None
        if key in ("BackSpace", "Delete"):
            self._prepare_edit()
            if key == "BackSpace" and not t.tag_ranges("sel") and t.compare("insert", "<=", "input"):
                return "break"
            return None
        if e.char and ord(e.char) >= 32 and e.char != "\x7f":  # carácter imprimible (incluye AltGr y acentos)
            self._prepare_edit()
            return None
        return "break" if e.char else None  # bloquea atajos tipo Ctrl+K o Tab que editarían el texto

    def _prepare_edit(self) -> None:
        """Garantiza que la edición ocurra solo dentro de la línea de entrada."""
        t = self._text
        if t.tag_ranges("sel") and t.compare("sel.first", "<", "input"):
            t.tag_remove("sel", "1.0", "end")
        if t.compare("insert", "<", "input"):
            t.mark_set("insert", "end-1c")

    def _on_return(self, _e):
        if self._locked:
            return "break"
        line = self._text.get("input", "end-1c").strip()
        self._text.insert("end-1c", "\n")
        self._locked = True
        if line and (not self._history or self._history[-1] != line):
            self._history.append(line)
        self._hist_pos = len(self._history)
        self._on_submit(line)
        return "break"

    def _browse_history(self, step: int):
        if self._history:
            if self._hist_pos == len(self._history):
                self._draft = self._text.get("input", "end-1c")
            self._hist_pos = min(max(self._hist_pos + step, 0), len(self._history))
            at_end = self._hist_pos == len(self._history)
            self._set_input(self._draft if at_end else self._history[self._hist_pos])
        return "break"

    def _set_input(self, value: str) -> None:
        self._text.delete("input", "end-1c")
        self._text.insert("end-1c", value)
        self._text.mark_set("insert", "end-1c")
        self._text.see("end")

    # ---------- Portapapeles y Ctrl+C ----------
    def _on_ctrl_c(self, _e):
        t = self._text
        if t.tag_ranges("sel"):  # con texto seleccionado: copiar
            self.clipboard_clear()
            self.clipboard_append(t.get("sel.first", "sel.last"))
            t.tag_remove("sel", "1.0", "end")
        elif self._locked:  # sin selección y con un comando en curso: matarlo
            self._on_interrupt()
        else:  # sin selección en el prompt: cancela la línea, como el CMD
            self.print("^C", "dim")
            self.show_prompt()
        return "break"

    def _on_paste(self, _e):
        if not self._locked:
            try:
                data = self.clipboard_get().replace("\r", "").replace("\n", " ")
            except tk.TclError:  # portapapeles vacío o sin texto
                return "break"
            self._prepare_edit()
            if self._text.tag_ranges("sel"):
                self._text.delete("sel.first", "sel.last")
            self._text.insert("insert", data)
            self._text.see("insert")
        return "break"

    def _select_all(self, _e):
        self._text.tag_add("sel", "1.0", "end-1c")
        return "break"

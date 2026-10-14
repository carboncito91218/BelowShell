"""Paleta y tipografía. Parten de los wireframes: terminal negra, barra gris y popup azul marino."""
from __future__ import annotations

import tkinter.font as tkfont

import customtkinter as ctk

# Ventana principal
BG_WINDOW = "#1E1E1E"
BG_TERMINAL = "#050505"
BAR = "#D9D9D9"
BAR_TEXT = "#16161A"
BAR_ACCENT = "#1F2A87"

# Texto de la terminal por tipo de salida
TEXT = "#E8E8EC"
KIND_COLORS = {
    "out": TEXT,
    "err": "#FF6B6B",
    "ok": "#7EE787",
    "dim": "#8E8E99",
    "prompt": "#7CC4FF",
}
SELECTION = "#2D4F7C"

# Popup de mensaje recibido
POPUP_BAR = "#1F2A87"
POPUP_BODY = "#D9D9D9"
POPUP_TEXT = "#16161A"
POPUP_MUTED = "#55555F"
POPUP_BORDER = "#141B5C"
CLOSE_HOVER = "#E5484D"

_MONO = ("Cascadia Mono", "Cascadia Code", "Consolas", "DejaVu Sans Mono", "Menlo", "Courier New")


def mono_font(size: int = 15) -> ctk.CTkFont:
    """Primera fuente monoespaciada disponible en el equipo (requiere ventana ya creada)."""
    installed = set(tkfont.families())
    return ctk.CTkFont(family=next((f for f in _MONO if f in installed), "Courier"), size=size)

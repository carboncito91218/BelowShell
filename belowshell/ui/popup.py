"""Ventana flotante para un mensaje recibido. Se adapta al tamaño del mensaje."""
from __future__ import annotations

import customtkinter as ctk

from belowshell.core.messaging import IncomingMessage

from . import theme

PAD = 18
CASCADE_PX = 30
MAX_SCREEN_H = 0.7  # alto máximo como fracción de la pantalla; después aparece scroll


class MessagePopup(ctk.CTkToplevel):
    def __init__(self, master, message: IncomingMessage, offset: int = 0):
        super().__init__(master, fg_color=theme.POPUP_BORDER)
        self.withdraw()
        self.overrideredirect(True)           # barra de título propia, con el diseño de BelowShell
        self.attributes("-topmost", True)     # visible sobre otras ventanas, sin robar el foco ni hacer ruido
        self._drag = (0, 0)

        card = ctk.CTkFrame(self, fg_color=theme.POPUP_BODY, corner_radius=0)
        card.pack(padx=1, pady=1, fill="both", expand=True)
        self._build_bar(card)
        self._body = ctk.CTkFrame(card, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=PAD, pady=(14, PAD))
        self._build_body(message)

        self.update_idletasks()
        self._place(offset)
        self.deiconify()

    # ---------- Construcción ----------
    def _build_bar(self, parent) -> None:
        bar = ctk.CTkFrame(parent, fg_color=theme.POPUP_BAR, corner_radius=0, height=36)
        bar.pack(fill="x")
        title = ctk.CTkLabel(bar, text="BelowShell", text_color="#C9CEF5", font=ctk.CTkFont(size=12))
        title.pack(side="left", padx=PAD - 4)
        for text, command, hover in (("✕", self.destroy, theme.CLOSE_HOVER), ("–", self._toggle, "#33409E")):
            ctk.CTkButton(bar, text=text, width=40, height=36, corner_radius=0, fg_color="transparent",
                          hover_color=hover, text_color="white", command=command).pack(side="right")
        for widget in (bar, title):  # arrastrar la ventana desde la barra
            widget.bind("<ButtonPress-1>", lambda e: setattr(self, "_drag", (e.x_root - self.winfo_x(), e.y_root - self.winfo_y())))
            widget.bind("<B1-Motion>", lambda e: self.wm_geometry(f"+{e.x_root - self._drag[0]}+{e.y_root - self._drag[1]}"))

    def _build_body(self, message: IncomingMessage) -> None:
        sender = f"Mensaje de {message.sender_ip}"
        ctk.CTkLabel(self._body, text=sender, text_color=theme.POPUP_TEXT, anchor="w",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(fill="x")
        if message.sender_host:
            ctk.CTkLabel(self._body, text=message.sender_host, text_color=theme.POPUP_MUTED, anchor="w",
                         font=ctk.CTkFont(size=12)).pack(fill="x")

        scale = self._get_window_scaling()
        screen_w, screen_h = self.winfo_screenwidth() / scale, self.winfo_screenheight() / scale
        length = len(message.text)
        width = min(340 if length <= 60 else 440 if length <= 200 else 560, int(screen_w * 0.6))
        font = ctk.CTkFont(size=15)

        label = ctk.CTkLabel(self._body, text=message.text, text_color=theme.POPUP_TEXT, font=font,
                             justify="left", anchor="w", width=width, wraplength=width)
        label.pack(fill="x", pady=(10, 0))
        self.update_idletasks()

        max_h = screen_h * MAX_SCREEN_H - 130  # descuenta barra, remitente y márgenes
        if label.winfo_reqheight() / scale > max_h:  # no cabe: se cambia por un cuadro con scroll
            label.destroy()
            box = ctk.CTkTextbox(self._body, width=width, height=int(max_h), wrap="word", font=font,
                                 fg_color="transparent", text_color=theme.POPUP_TEXT)
            box.insert("1.0", message.text)
            box.configure(state="disabled")
            box.pack(fill="both", expand=True, pady=(10, 0))

    # ---------- Comportamiento ----------
    def _toggle(self) -> None:
        """Minimiza el popup a solo su barra (y lo restaura)."""
        if self._body.winfo_manager():
            self._body.pack_forget()
        else:
            self._body.pack(fill="both", expand=True, padx=PAD, pady=(14, PAD))

    def _place(self, offset: int) -> None:
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        shift = (offset % 8) * CASCADE_PX
        x = (self.winfo_screenwidth() - w) // 2 + shift
        y = (self.winfo_screenheight() - h) // 2 + shift
        self.wm_geometry(f"+{x}+{y}")  # solo posición: el tamaño lo define el contenido

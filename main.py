"""Punto de entrada de BelowShell: python main.py"""
import customtkinter as ctk

from belowshell.ui.app import BelowShellApp


def main() -> None:
    ctk.set_appearance_mode("dark")
    BelowShellApp().mainloop()


if __name__ == "__main__":
    main()

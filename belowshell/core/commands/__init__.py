"""Cada archivo cmd_*.py de esta carpeta se registra solo: para un comando nuevo basta crear uno."""
import importlib
import pkgutil

from .base import CommandContext, Registry, registry

for _module in pkgutil.iter_modules(__path__):
    if _module.name.startswith("cmd_"):
        importlib.import_module(f"{__name__}.{_module.name}")

__all__ = ["CommandContext", "Registry", "registry"]

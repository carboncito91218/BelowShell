"""Información de red del equipo local: IP entregada por el DHCP, máscara, gateway y MAC."""
from __future__ import annotations

import re
import socket
from dataclasses import dataclass

from .system import IS_WINDOWS, run

try:
    import psutil
except ImportError:  # sin psutil la shell funciona, solo con menos datos
    psutil = None

_WIN_ROUTE = re.compile(r"^\s*0\.0\.0\.0\s+0\.0\.0\.0\s+(\S+)\s+(\S+)\s+(\d+)", re.M)
_NIX_ROUTE = re.compile(r"default via (\S+)")


@dataclass(frozen=True)
class NetworkInfo:
    hostname: str
    ip: str
    netmask: str | None
    gateway: str | None
    mac: str | None
    interface: str | None

    @property
    def connected(self) -> bool:
        return not self.ip.startswith("127.")


def _primary_ip() -> str:
    """IP de la interfaz con salida a la red (la que asignó el DHCP).

    connect() sobre UDP no envía paquetes: solo consulta la tabla de rutas.
    """
    for target in (("8.8.8.8", 80), ("10.255.255.255", 1)):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(target)
                return sock.getsockname()[0]
        except OSError:
            continue
    return "127.0.0.1"


def _interface_details(ip: str) -> tuple[str | None, str | None, str | None]:
    """(nombre de interfaz, máscara, MAC) de la interfaz que tiene esa IP."""
    if psutil is None:
        return None, None, None
    try:
        for name, addrs in psutil.net_if_addrs().items():
            v4 = next((a for a in addrs if a.family == socket.AF_INET and a.address == ip), None)
            if v4:
                mac = next((a.address for a in addrs if a.family == psutil.AF_LINK), None)
                return name, v4.netmask, mac
    except Exception:  # psutil puede fallar según permisos del equipo
        pass
    return None, None, None


def _default_gateway(ip: str) -> str | None:
    if IS_WINDOWS:  # "route print" tiene columnas numéricas: no depende del idioma
        routes = [(int(m[3]), m[1]) for m in _WIN_ROUTE.finditer(run(["route", "print", "-4", "0.0.0.0"])) if m[2] == ip]
        return min(routes)[1] if routes else None
    match = _NIX_ROUTE.search(run(["ip", "route", "show", "default"]))
    return match[1] if match else None


def get_network_info() -> NetworkInfo:
    ip = _primary_ip()
    interface, netmask, mac = _interface_details(ip)
    return NetworkInfo(socket.gethostname(), ip, netmask, _default_gateway(ip), mac, interface)

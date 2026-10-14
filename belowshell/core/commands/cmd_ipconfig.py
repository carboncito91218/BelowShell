from belowshell.core.network import get_network_info

from .base import CommandContext, registry


@registry.register("ipconfig", "ipconfig", "Muestra tu IP, máscara y puerta de enlace")
def ipconfig(args: str, ctx: CommandContext) -> None:
    info = get_network_info()
    rows = [
        ("Host", info.hostname), ("Adaptador", info.interface), ("IPv4", info.ip),
        ("Máscara de subred", info.netmask), ("Puerta de enlace", info.gateway), ("MAC", info.mac),
    ]
    for label, value in rows:
        ctx.emit("out", f"  {label:<19}: {value or 'No disponible'}")
    if not info.connected:
        ctx.emit("err", "Sin conexión: el equipo no recibió una IP del DHCP.")

from belowshell.core.pinger import run_ping

from .base import CommandContext, registry


@registry.register("ping", "ping <host>", "Envía 4 paquetes ICMP a un equipo")
def ping(args: str, ctx: CommandContext) -> None:
    if not args:
        ctx.emit("err", "Uso: ping <ip o nombre>")
        return
    run_ping(args.split()[0], ctx.emit, ctx.cancel)

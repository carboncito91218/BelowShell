import ipaddress
import socket

from belowshell.config import MSG_MAX_CHARS
from belowshell.core.messaging import send_message

from .base import CommandContext, registry

USAGE = 'Uso: msg <ip> "mensaje"'


@registry.register("msg", 'msg <ip> "mensaje"', "Envía un mensaje a otro equipo")
def msg(args: str, ctx: CommandContext) -> None:
    ip, _, text = args.partition(" ")
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] == '"':  # las comillas son opcionales
        text = text[1:-1]
    try:
        ipaddress.IPv4Address(ip)
    except ValueError:
        ctx.emit("err", USAGE)
        return
    if not text:
        ctx.emit("err", USAGE)
    elif len(text) > MSG_MAX_CHARS:
        ctx.emit("err", f"El mensaje supera los {MSG_MAX_CHARS} caracteres.")
    else:
        result = send_message(ip, text, socket.gethostname())
        ctx.emit("ok" if result.ok else "err", result.detail)

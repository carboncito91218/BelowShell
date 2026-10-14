from .base import CommandContext, registry


@registry.register("help", "help", "Muestra esta ayuda")
def help_command(args: str, ctx: CommandContext) -> None:
    ctx.emit("dim", "Comandos disponibles:")
    for cmd in ctx.registry.all():
        ctx.emit("out", f"  {cmd.usage:<22}{cmd.description}")
    ctx.emit("dim", "\nCtrl+C copia (o cancela el comando en curso), Ctrl+V pega, flechas arriba/abajo recorren el historial.")

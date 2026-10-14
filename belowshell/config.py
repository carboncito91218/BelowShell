"""Constantes globales de BelowShell."""

APP_NAME = "BelowShell"
VERSION = "1.0"

MSG_PORT = 50505          # puerto TCP donde cada equipo escucha mensajes
MSG_MAX_CHARS = 4000      # largo máximo de un mensaje
MSG_TIMEOUT_S = 2.0       # espera máxima al enviar (RNF-2: responder en 1-2 s)

PING_COUNT = 4            # paquetes por ping, como en Windows
PING_TIMEOUT_S = 2        # espera por paquete

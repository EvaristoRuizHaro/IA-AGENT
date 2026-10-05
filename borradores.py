# Guarda los borradores pendientes en pendientes.json para poder publicarlos cuando quieras.
import json
import os

from telegram_bot import enviar_mensaje

ARCHIVO = "pendientes.json"
MAX_PENDIENTES = 10  # si se acumulan más, se olvidan los más antiguos


def cargar_estado():
    if os.path.exists(ARCHIVO):
        with open(ARCHIVO, encoding="utf-8") as f:
            return json.load(f)
    return {"offset": 0, "borradores": {}}


def guardar_estado(estado):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)


def crear_borrador(estado, post, clave, formato, descartados=None, intento=1, especial=False):
    """Envía el borrador a Telegram con botones y lo guarda como pendiente."""
    etiqueta = "📌 Post especial" if especial else f"📝 Borrador ({formato})"
    message_id = enviar_mensaje(
        f"{etiqueta}:\n\n{post}\n\n⏳ Puedes publicarlo cuando quieras.",
        con_botones=True,
    )
    estado["borradores"][str(message_id)] = {
        "post": post,
        "clave": clave,
        "formato": formato,
        "descartados": descartados or [],
        "intento": intento,
        "especial": especial,
    }
    # Limitamos la cantidad de borradores guardados
    ids = sorted(estado["borradores"], key=int)
    for viejo in ids[:-MAX_PENDIENTES]:
        del estado["borradores"][viejo]
    return message_id

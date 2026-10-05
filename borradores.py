# Guarda los borradores pendientes en pendientes.json para poder publicarlos cuando quieras.
import json
import os

from imagenes import imagen_del_post
from telegram_bot import enviar_mensaje, enviar_foto
from linkedin import preparar_menciones

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


def crear_borrador(estado, post, clave, formato, descartados=None, intento=1, especial=False,
                   imagen=None):
    """Envía el borrador a Telegram (imagen + texto con botones) y lo guarda como pendiente."""
    ruta = imagen_del_post(post, "especial" if especial else formato, imagen)
    id_foto = enviar_foto(ruta, "🖼️ Imagen del post (en LinkedIn saldrán juntos en una sola publicación)") if ruta else None
    etiqueta = "📌 Post especial" if especial else f"📝 Borrador ({formato})"
    message_id = enviar_mensaje(
        f"{etiqueta}:\n\n{preparar_menciones(post)[0]}\n\n⏳ Decide cuando quieras: este borrador no caduca.",
        con_botones=True,
        responder_a=id_foto,
    )
    estado["borradores"][str(message_id)] = {
        "post": post,
        "clave": clave,
        "formato": formato,
        "descartados": descartados or [],
        "intento": intento,
        "especial": especial,
        "imagen": imagen,  # solo en posts especiales; las demás se generan al publicar
    }
    # Limitamos la cantidad de borradores guardados
    ids = sorted(estado["borradores"], key=int)
    for viejo in ids[:-MAX_PENDIENTES]:
        del estado["borradores"][viejo]
    return message_id

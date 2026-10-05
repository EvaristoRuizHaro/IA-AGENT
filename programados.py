# Lee los posts especiales de posts_programados.json.
# Cada fecha puede tener solo el texto, o {"texto": ..., "imagen": "imagenes/archivo.png"}.
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo


def post_programado(fecha=None):
    """Devuelve (texto, imagen) del post especial de esa fecha (hoy por defecto), o (None, None)."""
    if not os.path.exists("posts_programados.json"):
        return None, None
    with open("posts_programados.json", encoding="utf-8") as f:
        programados = json.load(f)
    fecha = fecha or datetime.now(ZoneInfo("Europe/Madrid")).date().isoformat()
    post = programados.get(fecha)
    if isinstance(post, dict):
        return post.get("texto"), post.get("imagen")
    return post, None

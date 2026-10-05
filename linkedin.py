import os
import re
from datetime import date

import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
AUTOR = os.getenv("LINKEDIN_PERSON_URN")
CADUCA = os.getenv("LINKEDIN_TOKEN_CADUCA")


def dias_hasta_caducar():
    """Cuántos días le quedan al permiso de LinkedIn."""
    if not CADUCA:
        return -1
    return (date.fromisoformat(CADUCA) - date.today()).days


# Menciones: en el texto se escriben como @[Nombre](urn:li:organization:12345)
MENCION = re.compile(r"@\[([^\]]+)\]\((urn:li:organization:\d+)\)")


def preparar_menciones(texto):
    """Quita la marca de las menciones y devuelve (texto limpio, etiquetas para LinkedIn).
    Si la URN aún no tiene número, se queda solo el nombre, sin etiqueta."""
    etiquetas = []
    limpio = ""
    pos = 0
    for m in MENCION.finditer(texto):
        limpio += texto[pos:m.start()]
        # LinkedIn cuenta posiciones en unidades UTF-16 (los emojis cuentan doble)
        inicio = len(limpio.encode("utf-16-le")) // 2
        limpio += m.group(1)
        etiquetas.append({
            "start": inicio,
            "length": len(m.group(1).encode("utf-16-le")) // 2,
            "value": {"com.linkedin.common.CompanyAttributedEntity": {"company": m.group(2)}},
        })
        pos = m.end()
    limpio += texto[pos:]
    # Menciones sin número todavía: dejamos solo el nombre
    limpio = re.sub(r"@\[([^\]]+)\]\([^)]*\)", r"\1", limpio)
    return limpio, etiquetas


def subir_imagen(ruta):
    """Sube una imagen a LinkedIn y devuelve su identificador (asset), o None si falla."""
    cabeceras = {"Authorization": f"Bearer {TOKEN}", "X-Restli-Protocol-Version": "2.0.0"}
    # 1) Pedimos a LinkedIn una dirección donde subirla
    r = requests.post(
        "https://api.linkedin.com/v2/assets?action=registerUpload",
        headers=cabeceras,
        json={"registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": AUTOR,
            "serviceRelationships": [{"relationshipType": "OWNER",
                                      "identifier": "urn:li:userGeneratedContent"}],
        }},
    )
    if r.status_code not in (200, 201):
        print("No se pudo preparar la subida de la imagen:", r.status_code, r.text[:300])
        return None
    valor = r.json()["value"]
    url = valor["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    # 2) Subimos los bytes de la imagen a esa dirección
    with open(ruta, "rb") as f:
        r = requests.put(url, data=f.read(), headers={"Authorization": f"Bearer {TOKEN}"})
    if r.status_code not in (200, 201):
        print("No se pudo subir la imagen:", r.status_code, r.text[:300])
        return None
    return valor["asset"]


def publicar_post(texto, imagen=None):
    """Publica el texto en tu perfil, con imagen si se indica. Devuelve (True/False, mensaje)."""
    texto, etiquetas = preparar_menciones(texto)
    asset = subir_imagen(imagen) if imagen else None
    # Buscamos el enlace de la noticia dentro del post para que salga con vista previa
    enlace = re.search(r"https?://\S+", texto)

    contenido = {
        "shareCommentary": {"text": texto, "attributes": etiquetas},
        "shareMediaCategory": "NONE",
    }
    if asset:
        # Con imagen, el enlace queda en el texto (LinkedIn no permite imagen + vista previa)
        contenido["shareMediaCategory"] = "IMAGE"
        contenido["media"] = [{"status": "READY", "media": asset}]
    elif enlace:
        contenido["shareMediaCategory"] = "ARTICLE"
        contenido["media"] = [{"status": "READY", "originalUrl": enlace.group(0)}]

    cuerpo = {
        "author": AUTOR,
        "lifecycleState": "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": contenido},
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    r = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "X-Restli-Protocol-Version": "2.0.0",
        },
        json=cuerpo,
    )
    if r.status_code == 201:
        urn = r.headers.get("x-restli-id") or r.json().get("id", "")
        url = f"https://www.linkedin.com/feed/update/{urn}/" if urn else ""
        return True, url
    return False, f"Error {r.status_code}: {r.text[:300]}"


if __name__ == "__main__":
    print(f"Al permiso de LinkedIn le quedan {dias_hasta_caducar()} días.")
    respuesta = input("¿Publicar un post de prueba en tu perfil? (s/n): ")
    if respuesta.lower() == "s":
        print(publicar_post("Probando mi agente de noticias de IA hecho en Python 🤖"))

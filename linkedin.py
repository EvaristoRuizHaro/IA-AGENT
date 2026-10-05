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


def publicar_post(texto):
    """Publica el texto en tu perfil. Devuelve (True/False, mensaje)."""
    # Buscamos el enlace de la noticia dentro del post para que salga con vista previa
    enlace = re.search(r"https?://\S+", texto)

    contenido = {
        "shareCommentary": {"text": texto},
        "shareMediaCategory": "NONE",
    }
    if enlace:
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
        return True, "Publicado en LinkedIn"
    return False, f"Error {r.status_code}: {r.text[:300]}"


if __name__ == "__main__":
    print(f"Al permiso de LinkedIn le quedan {dias_hasta_caducar()} días.")
    respuesta = input("¿Publicar un post de prueba en tu perfil? (s/n): ")
    if respuesta.lower() == "s":
        print(publicar_post("Probando mi agente de noticias de IA hecho en Python 🤖"))

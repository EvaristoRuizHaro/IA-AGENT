# El agente completo: redacta, te pregunta por Telegram y actúa según tu respuesta.
from redactor import redactar_post
from telegram_bot import enviar_mensaje, limpiar_pendientes, esperar_boton
from linkedin import publicar_post, dias_hasta_caducar
from recolector import guardar_en_historial
import re
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo


def post_programado_de_hoy():
    """Si hay un post especial para hoy en posts_programados.json, lo devuelve."""
    if not os.path.exists("posts_programados.json"):
        return None
    with open("posts_programados.json", encoding="utf-8") as f:
        programados = json.load(f)
    hoy = datetime.now(ZoneInfo("Europe/Madrid")).date().isoformat()
    return programados.get(hoy)


def ejecutar_agente(max_intentos=3):
    limpiar_pendientes()

    # Aviso si el permiso de LinkedIn está a punto de caducar
    dias = dias_hasta_caducar()
    if dias < 0:
        enviar_mensaje("⚠️ El permiso de LinkedIn ha caducado. Ejecuta autorizar_linkedin.py")
    elif dias <= 7:
        enviar_mensaje(f"⏰ El permiso de LinkedIn caduca en {dias} días. "
                       "Ejecuta autorizar_linkedin.py cuando puedas.")

    # ¿Hay un post especial programado para hoy?
    especial = post_programado_de_hoy()
    if especial:
        enviar_mensaje(f"📌 Hoy toca post especial:\n\n{especial}\n\n"
                       "(🔄 Otro = publicar una noticia normal en su lugar)", con_botones=True)
        decision = esperar_boton()
        print(f"Post especial - has elegido: {decision}")
        if decision == "publicar":
            ok, mensaje = publicar_post(especial)
            enviar_mensaje("✅ ¡Post especial publicado!" if ok else
                           f"⚠️ No se pudo publicar ({mensaje}). Cópialo y pégalo a mano.")
            print(mensaje)
            return
        elif decision != "regenerar":
            enviar_mensaje("❌ Descartado. Hoy no se publica nada.")
            return
        # si pulsas 🔄, sigue con una noticia normal

    descartados = []  # lo que has rechazado hoy (para no volver a proponerlo)

    for intento in range(1, max_intentos + 1):
        print(f"Redactando borrador {intento}...")
        post, clave = redactar_post(descartados)
        if post.startswith("No se pudo generar"):
            enviar_mensaje(f"⚠️ {post} Hoy no se publica nada.")
            return

        enviar_mensaje(f"📝 Borrador {intento} de {max_intentos}:\n\n{post}", con_botones=True)
        print("Borrador enviado a Telegram. Esperando tu respuesta...")

        decision = esperar_boton()
        print(f"Has elegido: {decision}")

        if decision == "publicar":
            ok, mensaje = publicar_post(post)
            if ok:
                if clave:
                    guardar_en_historial(clave)
                enviar_mensaje("✅ ¡Publicado en LinkedIn!")
            else:
                enviar_mensaje(f"⚠️ No se pudo publicar ({mensaje}).\n"
                               "Cópialo y pégalo a mano en LinkedIn.")
            print(mensaje)
            return
        elif decision == "regenerar":
            # Para noticias pasamos el borrador entero; para trucos/herramientas, su clave
            descartados.append(post if clave is None or clave.startswith("http") else clave)
            enviar_mensaje("🔄 Vale, preparo otro...")
            continue
        else:  # descartar o sin respuesta
            enviar_mensaje("❌ Descartado. Hoy no se publica nada.")
            return

    enviar_mensaje("Se acabaron los intentos por hoy. ¡Hasta la próxima!")


if __name__ == "__main__":
    ejecutar_agente()

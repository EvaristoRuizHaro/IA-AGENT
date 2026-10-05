# Procesa los botones pulsados en Telegram.
# - Si viene ACCION y MESSAGE_ID (lanzado al instante por el webhook de Cloudflare), procesa esa pulsación.
# - Si no (ejecución programada), lee las pulsaciones pendientes con getUpdates.
import os

from borradores import cargar_estado, guardar_estado, crear_borrador
from linkedin import publicar_post
from recolector import guardar_en_historial
from redactor import redactar_post
from telegram_bot import leer_pulsaciones, responder_pulsacion, editar_mensaje, enviar_mensaje

MAX_INTENTOS = 5  # cuántas veces se puede pedir "Otro" para un mismo borrador


def procesar(estado, accion, message_id, callback_id=None):
    mid = str(message_id)
    borrador = estado["borradores"].pop(mid, None)
    if borrador is None:
        responder_pulsacion(callback_id, "Este borrador ya no está disponible")
        enviar_mensaje("🤷 Ese borrador ya no está disponible (ya se publicó, descartó o sustituyó).")
        return
    responder_pulsacion(callback_id, "Recibido 👍")
    post = borrador["post"]

    if accion == "publicar":
        editar_mensaje(mid, f"⏳ Publicando en LinkedIn...\n\n{post}")
        ok, resultado = publicar_post(post)
        if ok:
            if borrador["clave"]:
                guardar_en_historial(borrador["clave"])
            editar_mensaje(mid, f"✅ PUBLICADO EN LINKEDIN\n\n{post}")
            enviar_mensaje("🎉 ¡Publicado!" + (f"\nMíralo aquí: {resultado}" if resultado else ""))
        else:
            editar_mensaje(mid, f"⚠️ No se pudo publicar\n\n{post}")
            enviar_mensaje(f"⚠️ LinkedIn ha dado un error: {resultado}\n"
                           "Te lo reenvío para que lo intentes otra vez cuando quieras.")
            crear_borrador(estado, post, borrador["clave"], borrador["formato"],
                           borrador["descartados"], borrador["intento"], borrador["especial"])
        print(resultado)

    elif accion == "regenerar":
        editar_mensaje(mid, f"🔄 Sustituido por otro borrador\n\n{post}")
        if borrador["intento"] >= MAX_INTENTOS:
            enviar_mensaje("🛑 Has llegado al máximo de borradores alternativos. Mañana habrá uno nuevo.")
            return
        enviar_mensaje("✍️ Escribiendo otro borrador...")
        clave = borrador["clave"]
        descartados = borrador["descartados"]
        if not borrador["especial"]:
            # Noticias: pasamos el post entero; trucos/herramientas: su clave
            descartados = descartados + [post if clave is None or clave.startswith("http") else clave]
        nuevo, nueva_clave = redactar_post(descartados, borrador["formato"])
        if nuevo.startswith("No se pudo generar"):
            enviar_mensaje(f"⚠️ {nuevo}")
            return
        crear_borrador(estado, nuevo, nueva_clave, borrador["formato"],
                       descartados, borrador["intento"] + 1)

    else:  # descartar
        editar_mensaje(mid, f"❌ Descartado\n\n{post}")
        enviar_mensaje("👌 Descartado. Mañana te preparo otro.")


def main():
    estado = cargar_estado()
    accion, message_id = os.getenv("ACCION"), os.getenv("MESSAGE_ID")

    if accion and message_id:  # lanzado al instante desde Cloudflare
        procesar(estado, accion, message_id)
        guardar_estado(estado)
        print(f"Procesado: {accion} sobre el mensaje {message_id}")
        return

    pulsaciones = leer_pulsaciones(estado.get("offset", 0))
    for p in pulsaciones:
        estado["offset"] = p["update_id"] + 1
        if p["accion"] in ("publicar", "regenerar", "descartar") and p["message_id"]:
            procesar(estado, p["accion"], p["message_id"], p["callback_id"])
        guardar_estado(estado)
    print(f"{len(pulsaciones)} pulsaciones procesadas.")


if __name__ == "__main__":
    main()

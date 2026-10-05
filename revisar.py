# Se ejecuta cada pocos minutos: mira si has pulsado algún botón en Telegram y actúa.
from borradores import cargar_estado, guardar_estado, crear_borrador
from linkedin import publicar_post
from recolector import guardar_en_historial
from redactor import redactar_post
from telegram_bot import leer_pulsaciones, responder_pulsacion, editar_mensaje, enviar_mensaje

MAX_INTENTOS = 5  # cuántas veces se puede pedir "Otro" para un mismo día


def procesar(estado, p):
    mid = str(p["message_id"])
    borrador = estado["borradores"].pop(mid, None)
    if borrador is None:
        responder_pulsacion(p["callback_id"], "Este borrador ya no está disponible")
        return

    post = borrador["post"]
    accion = p["accion"]
    responder_pulsacion(p["callback_id"], "Recibido 👍")

    if accion == "publicar":
        ok, mensaje = publicar_post(post)
        if ok:
            if borrador["clave"]:
                guardar_en_historial(borrador["clave"])
            editar_mensaje(mid, f"✅ PUBLICADO EN LINKEDIN\n\n{post}")
        else:
            estado["borradores"][mid] = borrador  # lo dejamos pendiente para reintentar
            enviar_mensaje(f"⚠️ No se pudo publicar ({mensaje}). El borrador sigue pendiente.")
        print(mensaje)

    elif accion == "regenerar":
        editar_mensaje(mid, f"🔄 Sustituido por otro borrador\n\n{post}")
        if borrador["intento"] >= MAX_INTENTOS:
            enviar_mensaje("Se acabaron los intentos para este borrador. Mañana habrá uno nuevo.")
            return
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


def main():
    estado = cargar_estado()
    pulsaciones = leer_pulsaciones(estado.get("offset", 0))
    for p in pulsaciones:
        estado["offset"] = p["update_id"] + 1
        if p["accion"] and p["message_id"]:
            procesar(estado, p)
        guardar_estado(estado)  # guardamos tras cada acción por si algo falla después
    print(f"{len(pulsaciones)} pulsaciones procesadas.")


if __name__ == "__main__":
    main()

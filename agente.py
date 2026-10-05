# El agente completo: redacta, te pregunta por Telegram y actúa según tu respuesta.
from redactor import redactar_post
from telegram_bot import enviar_mensaje, limpiar_pendientes, esperar_boton
from linkedin import publicar_post, dias_hasta_caducar


def ejecutar_agente(max_intentos=3):
    limpiar_pendientes()

    # Aviso si el permiso de LinkedIn está a punto de caducar
    dias = dias_hasta_caducar()
    if dias < 0:
        enviar_mensaje("⚠️ El permiso de LinkedIn ha caducado. Ejecuta autorizar_linkedin.py")
    elif dias <= 7:
        enviar_mensaje(f"⏰ El permiso de LinkedIn caduca en {dias} días. "
                       "Ejecuta autorizar_linkedin.py cuando puedas.")

    descartados = []  # borradores que has rechazado

    for intento in range(1, max_intentos + 1):
        print(f"Redactando borrador {intento}...")
        post = redactar_post(descartados)

        enviar_mensaje(f"📝 Borrador {intento} de {max_intentos}:\n\n{post}", con_botones=True)
        print("Borrador enviado a Telegram. Esperando tu respuesta...")

        decision = esperar_boton()
        print(f"Has elegido: {decision}")

        if decision == "publicar":
            ok, mensaje = publicar_post(post)
            if ok:
                enviar_mensaje("✅ ¡Publicado en LinkedIn!")
            else:
                enviar_mensaje(f"⚠️ No se pudo publicar ({mensaje}).\n"
                               "Cópialo y pégalo a mano en LinkedIn.")
            print(mensaje)
            return
        elif decision == "regenerar":
            descartados.append(post)
            enviar_mensaje("🔄 Vale, busco otra noticia...")
            continue
        else:  # descartar o sin respuesta
            enviar_mensaje("❌ Descartado. Hoy no se publica nada.")
            return

    enviar_mensaje("Se acabaron los intentos por hoy. ¡Hasta la próxima!")


if __name__ == "__main__":
    ejecutar_agente()

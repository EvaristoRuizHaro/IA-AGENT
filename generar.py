# Se ejecuta cada mañana: prepara el borrador del día y lo manda a Telegram.
# No espera respuesta: los botones los procesa revisar.py (cuando quieras pulsarlos).
from borradores import cargar_estado, guardar_estado, crear_borrador
from linkedin import dias_hasta_caducar
from programados import post_programado
from redactor import redactar_post, formato_de_hoy
from telegram_bot import enviar_mensaje


def main():
    # Aviso si el permiso de LinkedIn está a punto de caducar
    dias = dias_hasta_caducar()
    if dias < 0:
        enviar_mensaje("⚠️ El permiso de LinkedIn ha caducado. Ejecuta autorizar_linkedin.py")
    elif dias <= 7:
        enviar_mensaje(f"⏰ El permiso de LinkedIn caduca en {dias} días. "
                       "Ejecuta autorizar_linkedin.py cuando puedas.")

    estado = cargar_estado()
    formato = formato_de_hoy()

    especial, imagen = post_programado()
    if especial:
        crear_borrador(estado, especial, None, formato, especial=True, imagen=imagen)
    else:
        post, clave = redactar_post(formato=formato)
        if post.startswith("No se pudo generar"):
            enviar_mensaje(f"⚠️ {post} Hoy no hay borrador.")
            return
        crear_borrador(estado, post, clave, formato)

    guardar_estado(estado)
    print("Borrador enviado a Telegram.")


if __name__ == "__main__":
    main()

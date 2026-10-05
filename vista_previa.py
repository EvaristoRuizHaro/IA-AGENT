# Manda a Telegram una vista previa de un post programado, SIN botones y sin guardarlo como
# pendiente: no publica nada ni cuenta para el día programado.
# Uso: python vista_previa.py 2026-10-06
import sys

from imagenes import imagen_del_post
from linkedin import preparar_menciones
from programados import post_programado
from telegram_bot import enviar_mensaje, enviar_foto

fecha = sys.argv[1]
post, imagen = post_programado(fecha)

if not post:
    print(f"No hay ningún post programado para {fecha}.")
    sys.exit(1)

ruta = imagen_del_post(post, "especial", imagen)
id_foto = enviar_foto(ruta, "🖼️ Imagen del post (en LinkedIn saldrán juntos en una sola publicación)") if ruta else None
texto, etiquetas = preparar_menciones(post)
nota = f"\n\n🏷️ Al publicar se etiquetará: {', '.join(texto[e['start']:e['start'] + e['length']] for e in etiquetas)}" if etiquetas else ""
enviar_mensaje(f"👀 VISTA PREVIA del post del {fecha} (no se publica):\n\n{texto}{nota}",
               responder_a=id_foto)
print("Vista previa enviada.")

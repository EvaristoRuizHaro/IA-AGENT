# Manda a Telegram una vista previa de un post programado, SIN botones y sin guardarlo como
# pendiente: no publica nada ni cuenta para el día programado.
# Uso: python vista_previa.py 2026-10-06
import json
import sys

from linkedin import preparar_menciones
from telegram_bot import enviar_mensaje

fecha = sys.argv[1]
with open("posts_programados.json", encoding="utf-8") as f:
    post = json.load(f).get(fecha)

if not post:
    print(f"No hay ningún post programado para {fecha}.")
    sys.exit(1)

texto, etiquetas = preparar_menciones(post)
nota = f"\n\n🏷️ Al publicar se etiquetará: {', '.join(texto[e['start']:e['start'] + e['length']] for e in etiquetas)}" if etiquetas else ""
enviar_mensaje(f"👀 VISTA PREVIA del post del {fecha} (no se publica):\n\n{texto}{nota}")
print("Vista previa enviada.")

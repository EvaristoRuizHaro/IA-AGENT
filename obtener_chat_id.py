# Script de un solo uso: averigua tu "chat id" de Telegram.
# Antes de ejecutarlo, mándale cualquier mensaje a tu bot desde el móvil.
import os
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

datos = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates").json()

if not datos.get("ok"):
    print("Error: revisa que el TELEGRAM_TOKEN del .env esté bien copiado.")
elif not datos["result"]:
    print("No hay mensajes. Mándale un 'hola' a tu bot en Telegram y vuelve a ejecutar esto.")
else:
    chat = datos["result"][-1]["message"]["chat"]
    print(f"Tu chat id es: {chat['id']}  (de {chat.get('first_name', '')})")
    print("Cópialo en el .env, en TELEGRAM_CHAT_ID")

# Muestra el estado de la conexión Telegram -> Cloudflare (y el último error, si lo hay)
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()
info = requests.get(f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/getWebhookInfo").json()["result"]
print("URL:", info.get("url"))
print("Pulsaciones pendientes de entregar:", info.get("pending_update_count"))
if info.get("last_error_date"):
    print("Último error:", datetime.fromtimestamp(info["last_error_date"]), "->", info.get("last_error_message"))
else:
    print("Sin errores ✅")

# Conecta tu bot de Telegram con el Worker de Cloudflare (o lo desconecta).
# Uso:  python activar_webhook.py            -> activa
#       python activar_webhook.py quitar     -> vuelve al modo sin webhook
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()
API = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}"

if len(sys.argv) > 1 and sys.argv[1] == "quitar":
    print(requests.post(f"{API}/deleteWebhook").json())
else:
    r = requests.post(f"{API}/setWebhook", json={
        "url": os.getenv("WEBHOOK_URL"),
        "secret_token": os.getenv("WEBHOOK_SECRET"),
        "allowed_updates": ["callback_query"],
    }).json()
    print("✅ Webhook activado" if r.get("ok") else f"❌ Error: {r}")

print(requests.get(f"{API}/getWebhookInfo").json()["result"])

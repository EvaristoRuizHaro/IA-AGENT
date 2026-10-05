import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API = f"https://api.telegram.org/bot{TOKEN}"


def enviar_mensaje(texto, con_botones=False):
    """Manda un mensaje a tu Telegram. Si con_botones=True, añade los 3 botones."""
    datos = {"chat_id": CHAT_ID, "text": texto}
    if con_botones:
        datos["reply_markup"] = {
            "inline_keyboard": [[
                {"text": "✅ Publicar", "callback_data": "publicar"},
                {"text": "🔄 Otro", "callback_data": "regenerar"},
                {"text": "❌ Descartar", "callback_data": "descartar"},
            ]]
        }
    requests.post(f"{API}/sendMessage", json=datos)


def limpiar_pendientes():
    """Marca como leídas las pulsaciones antiguas, para no confundirlas con las nuevas."""
    updates = requests.get(f"{API}/getUpdates").json().get("result", [])
    if updates:
        requests.get(f"{API}/getUpdates", params={"offset": updates[-1]["update_id"] + 1})


def esperar_boton(minutos_max=60):
    """Espera a que pulses un botón y devuelve cuál: 'publicar', 'regenerar' o 'descartar'."""
    offset = None
    limite = time.time() + minutos_max * 60
    while time.time() < limite:
        # timeout=30: Telegram espera hasta 30 s a que pase algo antes de responder
        params = {"timeout": 30, "allowed_updates": '["callback_query"]'}
        if offset:
            params["offset"] = offset
        updates = requests.get(f"{API}/getUpdates", params=params, timeout=40).json().get("result", [])
        for u in updates:
            offset = u["update_id"] + 1
            if "callback_query" in u:
                # Avisamos a Telegram de que hemos recibido la pulsación (quita el "relojito")
                requests.post(f"{API}/answerCallbackQuery",
                              json={"callback_query_id": u["callback_query"]["id"]})
                return u["callback_query"]["data"]
    return "sin_respuesta"


if __name__ == "__main__":
    enviar_mensaje("👋 ¡Hola! Tu bot de LinkedIn está funcionando.")
    print("Mensaje enviado. Mira tu Telegram.")

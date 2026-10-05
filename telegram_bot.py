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
    r = requests.post(f"{API}/sendMessage", json=datos).json()
    return r.get("result", {}).get("message_id")  # identificador del mensaje enviado


def enviar_foto(ruta, pie=""):
    """Manda una imagen a tu Telegram (con un pie de foto corto opcional)."""
    with open(ruta, "rb") as f:
        r = requests.post(f"{API}/sendPhoto", data={"chat_id": CHAT_ID, "caption": pie[:1000]},
                          files={"photo": f}).json()
    return r.get("result", {}).get("message_id")


def editar_mensaje(message_id, texto):
    """Cambia el texto de un mensaje ya enviado y le quita los botones."""
    requests.post(f"{API}/editMessageText",
                  json={"chat_id": CHAT_ID, "message_id": message_id, "text": texto[:4000]})


def leer_pulsaciones(offset=0):
    """Devuelve los botones pulsados desde la última vez, sin esperar (para GitHub Actions)."""
    params = {"timeout": 0, "allowed_updates": '["callback_query"]'}
    if offset:
        params["offset"] = offset
    respuesta = requests.get(f"{API}/getUpdates", params=params, timeout=30).json()
    if not respuesta.get("ok"):
        # Si hay webhook activo (Cloudflare), Telegram no deja leer así: no pasa nada
        print("getUpdates no disponible:", respuesta.get("description"))
        return []
    updates = respuesta.get("result", [])
    pulsaciones = []
    for u in updates:
        cq = u.get("callback_query")
        pulsaciones.append({
            "update_id": u["update_id"],
            "callback_id": cq["id"] if cq else None,
            "accion": cq["data"] if cq else None,
            "message_id": cq["message"]["message_id"] if cq and "message" in cq else None,
        })
    return pulsaciones


def responder_pulsacion(callback_id, texto=""):
    """Confirma a Telegram que hemos recibido la pulsación."""
    if callback_id:
        requests.post(f"{API}/answerCallbackQuery",
                      json={"callback_query_id": callback_id, "text": texto})


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

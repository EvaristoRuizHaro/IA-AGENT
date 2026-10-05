# Ejecútalo la primera vez y cada ~60 días, cuando caduque el permiso.
# Abre LinkedIn en el navegador, le das a "Permitir" y guarda la llave (token) en el .env
import os
import secrets
import webbrowser
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlencode, urlparse, parse_qs

import requests
from dotenv import load_dotenv, set_key

load_dotenv()
CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"
ESTADO = secrets.token_urlsafe(16)  # código aleatorio de seguridad
codigo_recibido = {}


class RecogerCodigo(BaseHTTPRequestHandler):
    """Mini servidor web que recibe la respuesta de LinkedIn tras pulsar 'Permitir'."""
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        codigo_recibido.update({k: v[0] for k, v in params.items()})
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("<h2>Listo, ya puedes cerrar esta pestaña y volver a VS Code.</h2>".encode())

    def log_message(self, *args):
        pass  # que no llene la terminal de mensajes


# 1. Abrimos la página de permiso de LinkedIn
url = "https://www.linkedin.com/oauth/v2/authorization?" + urlencode({
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "state": ESTADO,
    "scope": "openid profile w_member_social",
})
print("Abriendo LinkedIn en el navegador... dale a 'Permitir'.")
webbrowser.open(url)

# 2. Esperamos a que LinkedIn nos devuelva el código
HTTPServer(("localhost", 8000), RecogerCodigo).handle_request()

if "error" in codigo_recibido:
    print("LinkedIn ha devuelto un error:", codigo_recibido.get("error_description"))
    raise SystemExit
if codigo_recibido.get("state") != ESTADO:
    print("Error de seguridad: la respuesta no coincide. Vuelve a intentarlo.")
    raise SystemExit

# 3. Cambiamos el código por el token de acceso
r = requests.post("https://www.linkedin.com/oauth/v2/accessToken", data={
    "grant_type": "authorization_code",
    "code": codigo_recibido["code"],
    "redirect_uri": REDIRECT_URI,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
}).json()

if "access_token" not in r:
    print("No se pudo obtener el token:", r)
    raise SystemExit

token = r["access_token"]
caduca = date.today() + timedelta(seconds=r.get("expires_in", 60 * 86400))

# 4. Preguntamos a LinkedIn quién eres (tu identificador de persona)
yo = requests.get("https://api.linkedin.com/v2/userinfo",
                  headers={"Authorization": f"Bearer {token}"}).json()

# 5. Guardamos todo en el .env
set_key(".env", "LINKEDIN_ACCESS_TOKEN", token)
set_key(".env", "LINKEDIN_PERSON_URN", f"urn:li:person:{yo['sub']}")
set_key(".env", "LINKEDIN_TOKEN_CADUCA", caduca.isoformat())

print(f"✅ ¡Autorizado como {yo.get('name', '')}! El permiso caduca el {caduca:%d/%m/%Y}.")

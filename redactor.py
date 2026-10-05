import json
import os
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google import genai
from google.genai import types

from recolector import recoger_noticias, cargar_historial, cargar_config

load_dotenv()
cliente = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
# Modelos gratuitos de Google, en orden de preferencia (si uno está saturado, se prueba el siguiente)
MODELOS = ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.5-flash"]

# Todo lo personal (nombre, tema, fuentes, formatos por día) está en config.json
CONFIG = cargar_config()

REGLAS = """Reglas:
- Escribe en español, tono cercano y profesional, nada de frases de vendehúmos ni exceso de emojis.
- No inventes cifras, fechas, precios ni datos que no te haya dado.
- Máximo 1.300 caracteres.
- Termina con 3-5 hashtags.
- Devuelve únicamente lo que se te pide, sin explicaciones."""

REGLA_TEMA = """La PRIMERA línea de tu respuesta debe ser "TEMA: <nombre corto del tema>",
y a continuación, en una línea nueva, el post."""


def rellenar(texto):
    """Sustituye {nombre}, {perfil} y {publico} por los datos de config.json."""
    for campo in ("nombre", "perfil", "publico"):
        texto = texto.replace("{" + campo + "}", CONFIG[campo])
    return texto


def instrucciones(formato, extra=""):
    perfil = (f"Eres el redactor de LinkedIn de {CONFIG['nombre']}, {CONFIG['perfil']}. "
              "Sus posts deben ayudarle a mostrar interés y conocimiento ante recruiters.")
    return f"{perfil}\n\n{rellenar(CONFIG['formatos'][formato]['instrucciones'])}\n{extra}\n{REGLAS}"


def formato_de_hoy():
    hoy = datetime.now(ZoneInfo("Europe/Madrid")).weekday()
    return CONFIG["dias"].get(str(hoy), "noticia")


def llamar_gemini(instrucciones_sistema, texto):
    """Envía el texto a Gemini, con modelos de reserva y reintentos si están saturados."""
    config = types.GenerateContentConfig(
        system_instruction=instrucciones_sistema,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    for ronda in range(3):
        for modelo in MODELOS:
            try:
                respuesta = cliente.models.generate_content(model=modelo, contents=texto, config=config)
                print(f"(Generado con {modelo})")
                return respuesta.text.strip()
            except Exception as error:
                print(f"  {modelo} no disponible: {str(error)[:80]}...")
        espera = 20 * (ronda + 1)
        print(f"  Todos ocupados. Reintento en {espera} segundos...")
        time.sleep(espera)
    raise RuntimeError("Gemini no está disponible ahora mismo.")


# --- Tres tipos de post ------------------------------------------------------

def tipo_noticia(formato, descartados):
    """Elige una noticia de las fuentes RSS y escribe sobre ella."""
    noticias = recoger_noticias()
    if not noticias:
        raise RuntimeError("no se ha podido leer ninguna noticia de las fuentes (revisa config.json)")
    texto = ""
    for i, n in enumerate(noticias, start=1):
        texto += f"{i}. [{n['fuente']}] {n['titulo']}\n   Resumen: {n['resumen']}\n   Enlace: {n['enlace']}\n\n"
    if descartados:
        texto += "NO elijas la noticia de estos borradores ya rechazados:\n" + "\n---\n".join(descartados)

    post = llamar_gemini(instrucciones(formato), texto)
    enlace = re.search(r"https?://\S+", post)
    return post, (enlace.group(0) if enlace else None)


def tipo_tema_libre(formato, descartados):
    """La IA elige un tema (truco, concepto...) sin repetir los ya publicados."""
    prefijo = f"{formato}: "
    usados = [h[len(prefijo):] for h in cargar_historial() if h.startswith(prefijo)]
    rechazados = [d[len(prefijo):] for d in descartados]
    texto = "Escribe el post de esta semana."
    if usados or rechazados:
        texto += "\nNO repitas ninguno de estos temas: " + "; ".join(usados + rechazados)

    respuesta = llamar_gemini(instrucciones(formato, REGLA_TEMA), texto)
    tema = "sin tema"
    if respuesta.upper().startswith("TEMA:"):
        primera, _, resto = respuesta.partition("\n")
        tema, respuesta = primera[5:].strip(), resto.strip()
    return respuesta, prefijo + tema


def tipo_lista(formato, descartados):
    """Recorre una lista fija (herramientas, recursos...) sin repetir."""
    prefijo = f"{formato}: "
    with open(CONFIG["formatos"][formato]["archivo"], encoding="utf-8") as f:
        elementos = json.load(f)
    usados = {h[len(prefijo):] for h in cargar_historial() if h.startswith(prefijo)}
    rechazados = {d[len(prefijo):] for d in descartados}

    pendientes = [e for e in elementos if e["nombre"] not in usados | rechazados]
    if not pendientes:  # si ya salieron todos, volvemos a empezar
        pendientes = [e for e in elementos if e["nombre"] not in rechazados] or elementos
    e = pendientes[0]

    texto = f"Nombre: {e['nombre']}\nDescripción: {e['descripcion']}\nEnlace: {e['url']}"
    return llamar_gemini(instrucciones(formato), texto), prefijo + e["nombre"]


TIPOS = {"noticia": tipo_noticia, "tema_libre": tipo_tema_libre, "lista": tipo_lista}


def redactar_post(descartados=None, formato=None):
    """Devuelve (post, clave). 'clave' identifica el contenido para no repetirlo."""
    descartados = descartados or []
    formato = formato or formato_de_hoy()
    tipo = CONFIG["formatos"][formato]["tipo"]
    print(f"Formato de hoy: {formato} ({tipo})")
    try:
        return TIPOS[tipo](formato, descartados)
    except RuntimeError as error:
        return f"No se pudo generar el post: {error}", None


if __name__ == "__main__":
    # Para probar un formato concreto: python redactor.py truco
    import sys
    formato = sys.argv[1] if len(sys.argv) > 1 else None
    post, clave = redactar_post(formato=formato)
    print(f"\n{post}\n\n[clave para el historial: {clave}]")

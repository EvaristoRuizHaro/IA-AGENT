import json
import os
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google import genai
from google.genai import types

from recolector import recoger_noticias, cargar_historial

# Carga la clave de la API desde el archivo .env
load_dotenv()
cliente = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
# Modelos gratuitos de Google, en orden de preferencia.
# Si el primero está saturado, se prueba el siguiente.
MODELOS = ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.5-flash"]

# ---------------------------------------------------------------------------
# QUÉ TIPO DE POST TOCA CADA DÍA (0 = lunes ... 6 = domingo). Cámbialo a tu gusto.
#   "destacada"   -> la noticia más importante de la semana
#   "noticia"     -> noticia del día + opinión
#   "truco"       -> truco de Python / datos con un trozo de código
#   "herramienta" -> herramienta recomendada (de herramientas.json)
# ---------------------------------------------------------------------------
FORMATOS = {
    0: "destacada",
    1: "noticia",
    2: "truco",
    3: "noticia",
    4: "herramienta",
    5: "noticia",
    6: "noticia",
}

PERFIL = """Eres el redactor de LinkedIn de Evaristo, estudiante de una especialización
en Inteligencia Artificial y Big Data en España. Sus posts deben ayudarle a mostrar
interés y conocimiento ante recruiters."""

REGLAS = """Reglas:
- Escribe en español, tono cercano y profesional, nada de frases de vendehúmos ni exceso de emojis.
- No inventes cifras, fechas, precios ni datos que no te haya dado.
- Máximo 1.300 caracteres.
- Termina con 3-5 hashtags.
- Devuelve únicamente lo que se te pide, sin explicaciones."""

INSTRUCCIONES = {
    "noticia": f"""{PERFIL}

De la lista de noticias, elige LA MÁS interesante para un perfil junior de
IA / Big Data / programación y escribe un post sobre ella:
- Primera línea: un gancho corto que dé ganas de seguir leyendo.
- 2-3 líneas resumiendo la noticia (usa SOLO el título y el resumen).
- 2-3 líneas con la opinión de Evaristo: qué significa para alguien que empieza en IA.
- Una pregunta final para invitar a comentar.
- El enlace a la noticia.
{REGLAS}""",

    "destacada": f"""{PERFIL}

Es lunes: toca "la noticia de la semana". De la lista, elige la noticia con MÁS
IMPACTO para el sector de la IA y el desarrollo, y escribe un post:
- Primera línea: empieza con "📌 La noticia de la semana:" seguido de un gancho.
- 3-4 líneas explicando qué ha pasado y por qué es importante (usa SOLO el título y el resumen).
- 2 líneas con la opinión de Evaristo y cómo puede afectar a quienes empiezan.
- Una pregunta final para invitar a comentar.
- El enlace a la noticia.
{REGLAS}""",

    "truco": f"""{PERFIL}

Es miércoles: toca "truco de la semana". Escribe un post con un truco práctico y
útil de Python, pandas, SQL o análisis de datos, pensado para estudiantes y juniors:
- Primera línea: empieza con "💡 Truco de Python:" (o de SQL/pandas) seguido de un gancho.
- 1-2 líneas explicando qué problema resuelve.
- Un ejemplo de código CORTO (máximo 6 líneas), correcto y que funcione. Sin bloques
  markdown (```), solo las líneas de código, porque LinkedIn no los muestra.
- 1-2 líneas explicando el resultado.
- Una pregunta final ("¿Lo conocíais?", "¿Qué truco añadiríais?"...).
La PRIMERA línea de tu respuesta debe ser "TEMA: <nombre corto del truco>", y a
continuación, en una línea nueva, el post.
{REGLAS}""",

    "herramienta": f"""{PERFIL}

Es viernes: toca "herramienta de la semana". Escribe un post recomendando la
herramienta que te paso:
- Primera línea: empieza con "🛠️ Herramienta de la semana:" y su nombre.
- 2-3 líneas sobre qué es y para qué sirve (basado en la descripción que te doy).
- 2 líneas con un caso de uso concreto para un estudiante de IA o datos.
- Una pregunta final para invitar a comentar.
- El enlace a la herramienta.
No inventes funcionalidades, versiones ni precios que no aparezcan en la descripción.
{REGLAS}""",
}


def formato_de_hoy():
    hoy = datetime.now(ZoneInfo("Europe/Madrid")).weekday()
    return FORMATOS.get(hoy, "noticia")


def llamar_gemini(instrucciones, texto):
    """Envía el texto a Gemini, con modelos de reserva y reintentos si están saturados."""
    config = types.GenerateContentConfig(
        system_instruction=instrucciones,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    for ronda in range(3):
        for modelo in MODELOS:
            try:
                respuesta = cliente.models.generate_content(
                    model=modelo, contents=texto, config=config
                )
                print(f"(Generado con {modelo})")
                return respuesta.text.strip()
            except Exception as error:
                print(f"  {modelo} no disponible: {str(error)[:80]}...")
        espera = 20 * (ronda + 1)
        print(f"  Todos ocupados. Reintento en {espera} segundos...")
        time.sleep(espera)
    raise RuntimeError("Gemini no está disponible ahora mismo.")


def post_noticia(formato, descartados):
    noticias = recoger_noticias()
    texto = ""
    for i, n in enumerate(noticias, start=1):
        texto += f"{i}. [{n['fuente']}] {n['titulo']}\n"
        texto += f"   Resumen: {n['resumen']}\n"
        texto += f"   Enlace: {n['enlace']}\n\n"
    if descartados:
        texto += "NO elijas la noticia de estos borradores ya rechazados:\n"
        texto += "\n---\n".join(descartados)

    post = llamar_gemini(INSTRUCCIONES[formato], texto)
    enlace = re.search(r"https?://\S+", post)
    clave = enlace.group(0) if enlace else None  # lo que se guarda en el historial
    return post, clave


def post_truco(descartados):
    usados = [h[len("truco: "):] for h in cargar_historial() if h.startswith("truco: ")]
    texto = "Escribe el truco de esta semana."
    if usados or descartados:
        texto += "\nNO repitas ninguno de estos temas: " + "; ".join(usados + descartados)

    respuesta = llamar_gemini(INSTRUCCIONES["truco"], texto)
    # Separamos la línea "TEMA: ..." del post
    tema = "sin tema"
    if respuesta.upper().startswith("TEMA:"):
        primera, _, resto = respuesta.partition("\n")
        tema, respuesta = primera[5:].strip(), resto.strip()
    return respuesta, f"truco: {tema}"


def post_herramienta(descartados):
    with open("herramientas.json", encoding="utf-8") as f:
        herramientas = json.load(f)
    usadas = {h[len("herramienta: "):] for h in cargar_historial() if h.startswith("herramienta: ")}
    rechazadas = {d[len("herramienta: "):] for d in descartados}

    pendientes = [h for h in herramientas if h["nombre"] not in usadas | rechazadas]
    if not pendientes:  # si ya se han recomendado todas, volvemos a empezar
        pendientes = [h for h in herramientas if h["nombre"] not in rechazadas] or herramientas
    h = pendientes[0]

    texto = f"Herramienta: {h['nombre']}\nDescripción: {h['descripcion']}\nEnlace: {h['url']}"
    return llamar_gemini(INSTRUCCIONES["herramienta"], texto), f"herramienta: {h['nombre']}"


def redactar_post(descartados=None, formato=None):
    """Devuelve (post, clave). 'clave' identifica el contenido para no repetirlo."""
    descartados = descartados or []
    formato = formato or formato_de_hoy()
    print(f"Formato de hoy: {formato}")
    try:
        if formato == "truco":
            return post_truco(descartados)
        if formato == "herramienta":
            return post_herramienta(descartados)
        return post_noticia(formato, descartados)
    except RuntimeError as error:
        return f"No se pudo generar el post: {error}", None


if __name__ == "__main__":
    # Para probar un formato concreto: python redactor.py truco
    import sys
    formato = sys.argv[1] if len(sys.argv) > 1 else None
    post, clave = redactar_post(formato=formato)
    print(f"\n{post}\n\n[clave para el historial: {clave}]")

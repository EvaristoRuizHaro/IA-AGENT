import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from recolector import recoger_noticias

# Carga la clave de la API desde el archivo .env
load_dotenv()
cliente = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
# Modelos gratuitos de Google, en orden de preferencia.
# Si el primero está saturado, se prueba el siguiente.
MODELOS = ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.5-flash"]

# Instrucciones fijas: quién eres y cómo quieres que suenen tus posts
INSTRUCCIONES = """Eres el redactor de LinkedIn de Evaristo, estudiante de una
especialización en Inteligencia Artificial y Big Data en España.

Tu tarea:
1. De la lista de noticias que te paso, elige LA MÁS interesante para un perfil
   junior de IA / Big Data / programación que quiere llamar la atención de recruiters.
2. Escribe un post de LinkedIn en español sobre ella.

Formato del post:
- Primera línea: un gancho corto que dé ganas de seguir leyendo.
- 2-3 líneas resumiendo la noticia.
- 2-3 líneas con la opinión de Evaristo: qué significa para alguien que está
  empezando en IA o por qué le parece relevante.
- Una pregunta final para invitar a comentar.
- El enlace a la noticia.
- 3-5 hashtags.

Reglas:
- Usa SOLO la información del título y resumen. No inventes cifras ni datos.
- Tono cercano y profesional, nada de frases de vendehúmos ni exceso de emojis.
- Máximo 1.300 caracteres.
- Devuelve únicamente el texto del post, sin explicaciones."""


def redactar_post(descartados=None):
    noticias = recoger_noticias()

    # Convertimos la lista de noticias en texto para mandársela a la IA
    texto_noticias = ""
    for i, n in enumerate(noticias, start=1):
        texto_noticias += f"{i}. [{n['fuente']}] {n['titulo']}\n"
        texto_noticias += f"   Resumen: {n['resumen']}\n"
        texto_noticias += f"   Enlace: {n['enlace']}\n\n"

    # Si ya rechazaste algún borrador, le pedimos que elija otra noticia
    if descartados:
        texto_noticias += "NO elijas la noticia de estos borradores ya rechazados:\n"
        texto_noticias += "\n---\n".join(descartados)

    config = types.GenerateContentConfig(
        system_instruction=INSTRUCCIONES,
        # Desactiva una función que no usamos (y quita el aviso amarillo)
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    # Hasta 3 rondas probando todos los modelos, esperando entre rondas
    for ronda in range(3):
        for modelo in MODELOS:
            try:
                respuesta = cliente.models.generate_content(
                    model=modelo, contents=texto_noticias, config=config
                )
                print(f"(Post generado con {modelo})\n")
                return respuesta.text
            except Exception as error:
                print(f"  {modelo} no disponible: {str(error)[:80]}...")
        espera = 20 * (ronda + 1)
        print(f"  Todos ocupados. Reintento en {espera} segundos...\n")
        time.sleep(espera)

    return "No se pudo generar el post. Prueba otra vez más tarde."


if __name__ == "__main__":
    print("Leyendo noticias y redactando post...\n")
    print(redactar_post())

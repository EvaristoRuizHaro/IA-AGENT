# Genera la imagen que acompaña a cada post (una "tarjeta" de 1080x1080 con el titular).
# Se crea a partir del propio texto del post, así que siempre sale igual: no hace falta guardarla.
import os
import re
import tempfile
import textwrap
import unicodedata
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont

from linkedin import preparar_menciones
from recolector import cargar_config

CONFIG = cargar_config()
CARPETA_FUENTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuentes")
LADO = 1080
MARGEN = 84

# Colores (fondo claro, tinta oscura y un color de acento por formato)
FONDO, TINTA, TINTA_2, SUAVE, LINEA = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
FORMATOS = {
    "noticia":     ("NOTICIA",                  "#2a78d6"),
    "destacada":   ("LA NOTICIA DE LA SEMANA",  "#4a3aa7"),
    "truco":       ("TRUCO DE LA SEMANA",       "#1baf7a"),
    "herramienta": ("HERRAMIENTA DE LA SEMANA", "#eb6834"),
    "especial":    ("PROYECTO",                 "#e34948"),
}
# Prefijos que pone Gemini en la primera línea y que en la imagen ya van en la etiqueta
PREFIJOS = r"^(la noticia (económica )?de la semana|truco de (python|sql|pandas)[^:]*|" \
           r"herramienta de la semana|concepto de la semana|recurso de la semana)\s*:\s*"


def fuente(nombre, tam):
    return ImageFont.truetype(os.path.join(CARPETA_FUENTES, nombre), tam)


def sin_emojis(texto):
    """Quita emojis y símbolos que la fuente no sabe dibujar."""
    limpio = "".join(c for c in texto
                     if unicodedata.category(c) not in ("So", "Sk", "Cs", "Co")
                     and not 0xFE00 <= ord(c) <= 0xFE0F and ord(c) != 0x200D)
    return re.sub(r"\s+", " ", limpio).strip()


def lineas_de_codigo(post):
    """Saca las líneas de código del post (solo en los trucos)."""
    patron = re.compile(r"^\s*(import |from |print\(|def |for |if |while |return |with |class |"
                        r"select |where |group by |order by |>>> |#|[\w\.\[\]'\"]+\s*[+\-*/]?=[^=])",
                        re.IGNORECASE)
    return [l.rstrip() for l in post.splitlines() if patron.match(l)][:6]


def ajustar(dibujo, texto, nombre_fuente, tam_max, tam_min, ancho, max_lineas):
    """Busca el tamaño de letra más grande con el que el texto cabe en max_lineas."""
    for tam in range(tam_max, tam_min - 1, -4):
        f = fuente(nombre_fuente, tam)
        caracteres = max(10, int(ancho / (tam * 0.55)))
        lineas = textwrap.wrap(texto, caracteres)
        if len(lineas) <= max_lineas and all(dibujo.textlength(l, font=f) <= ancho for l in lineas):
            return f, lineas
    f = fuente(nombre_fuente, tam_min)
    lineas = textwrap.wrap(texto, max(10, int(ancho / (tam_min * 0.55))))[:max_lineas]
    lineas[-1] = lineas[-1].rstrip(".,;:") + "…"
    return f, lineas


def generar_tarjeta(post, formato, ruta):
    post = preparar_menciones(post)[0]  # "@[Nombre](urn...)" → "Nombre"
    etiqueta, acento = FORMATOS.get(formato, FORMATOS["noticia"])
    img = Image.new("RGB", (LADO, LADO), FONDO)
    d = ImageDraw.Draw(img)
    ancho = LADO - 2 * MARGEN

    # Barra de color arriba y etiqueta del formato
    d.rectangle([0, 0, LADO, 14], fill=acento)
    d.rounded_rectangle([MARGEN, 96, MARGEN + 18, 114], radius=4, fill=acento)
    d.text((MARGEN + 34, 105), etiqueta, font=fuente("DejaVuSans-Bold.ttf", 26), fill=TINTA_2, anchor="lm")

    # Titular: la primera línea del post, sin emojis ni prefijo
    lineas_post = [l for l in post.splitlines() if l.strip() and not l.strip().startswith("TEMA:")]
    titular = re.sub(PREFIJOS, "", sin_emojis(lineas_post[0] if lineas_post else ""), flags=re.IGNORECASE)
    titular = titular[:1].upper() + titular[1:]
    codigo = lineas_de_codigo(post) if formato == "truco" else []

    f_tit, lineas = ajustar(d, titular, "DejaVuSans-Bold.ttf", 76, 44, ancho, 4 if codigo else 6)
    alto_linea = int(f_tit.size * 1.22)
    f_cod = fuente("DejaVuSansMono.ttf", 30)
    if codigo:
        while f_cod.size > 18 and max(d.textlength(l, font=f_cod) for l in codigo) > ancho - 64:
            f_cod = fuente("DejaVuSansMono.ttf", f_cod.size - 2)
    alto_caja = int(f_cod.size * 1.5) * len(codigo) + 56 if codigo else 0
    # Centramos el bloque (titular + código o dominio) entre la etiqueta y el pie
    alto_bloque = alto_linea * len(lineas) + (40 + alto_caja if codigo else 70)
    y = max(180, (170 + LADO - 150 - alto_bloque) // 2)
    for l in lineas:
        d.text((MARGEN, y), l, font=f_tit, fill=TINTA)
        y += alto_linea

    if codigo:
        # Caja de código con fuente monoespaciada
        y += 40
        d.rounded_rectangle([MARGEN, y, LADO - MARGEN, y + alto_caja], radius=16, fill="#1a1a19")
        yy = y + 28
        for l in codigo:
            texto = l if d.textlength(l, font=f_cod) <= ancho - 64 else l[:int((ancho - 64) / (f_cod.size * 0.6)) - 1] + "…"
            d.text((MARGEN + 32, yy), texto, font=f_cod, fill="#e8e6dc")
            yy += int(f_cod.size * 1.5)
    else:
        # Debajo del titular, de dónde viene (en las noticias y herramientas con enlace)
        enlace = re.search(r"https?://\S+", post)
        if enlace:
            dominio = urlparse(enlace.group(0)).netloc.removeprefix("www.")
            d.text((MARGEN, y + 30), dominio, font=fuente("DejaVuSans.ttf", 30), fill=SUAVE)

    # Pie: nombre del autor
    d.line([MARGEN, LADO - 130, LADO - MARGEN, LADO - 130], fill=LINEA, width=2)
    d.text((MARGEN, LADO - 82), CONFIG.get("firma", CONFIG["nombre"]),
           font=fuente("DejaVuSans-Bold.ttf", 28), fill=TINTA_2, anchor="lm")
    d.text((LADO - MARGEN, LADO - 82), CONFIG.get("subtitulo_imagen", ""),
           font=fuente("DejaVuSans.ttf", 24), fill=SUAVE, anchor="rm")
    img.save(ruta)
    return ruta


def imagen_del_post(post, formato, imagen=None):
    """Devuelve la ruta de la imagen del post: la indicada (posts especiales) o una tarjeta generada.
    Devuelve None si las imágenes están desactivadas en config.json o algo falla."""
    if not CONFIG.get("imagenes", True):
        return None
    if imagen:
        return imagen if os.path.exists(imagen) else None
    try:
        ruta = os.path.join(tempfile.gettempdir(), f"tarjeta_{abs(hash(post))}.png")
        return generar_tarjeta(post, formato, ruta)
    except Exception as e:  # una imagen nunca debe impedir que salga el post
        print("No se pudo generar la imagen:", e)
        return None


if __name__ == "__main__":
    # Prueba: python imagenes.py  → crea ejemplos en la carpeta actual
    ejemplos = {
        "noticia": "🚀 OpenAI presenta un modelo que razona sobre vídeos largos\n\nTexto...\nhttps://www.theverge.com/ai/123",
        "destacada": "📌 La noticia de la semana: la UE aprueba las normas de transparencia para modelos de IA generativa\n\nhttps://huggingface.co/blog/x",
        "truco": "💡 Truco de pandas: cuenta valores en una línea\n\nResuelve...\n\nimport pandas as pd\ndf = pd.DataFrame({'equipo': ['A', 'B', 'A']})\nprint(df['equipo'].value_counts())\n\n¿Lo conocíais?",
        "herramienta": "🛠️ Herramienta de la semana: DuckDB\n\nTexto...\nhttps://duckdb.org",
    }
    for formato, post in ejemplos.items():
        print(generar_tarjeta(post, formato, f"ejemplo_{formato}.png"))

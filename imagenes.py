# Genera la imagen que acompaña a cada post: una obra abstracta de 1080x1080 (manchas de color
# difuminadas, ondas y grano) con el titular encima. Cada post tiene su propia composición, que
# sale del propio texto: siempre es la misma para el mismo post, así que no hace falta guardarla.
import hashlib
import math
import os
import re
import tempfile
import textwrap
import unicodedata

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from linkedin import preparar_menciones
from recolector import cargar_config

CONFIG = cargar_config()
CARPETA_FUENTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuentes")
LADO = 1080
MARGEN = 84
BLANCO = (255, 255, 255)

# Por formato: etiqueta y paleta (fondo oscuro, fondo claro y tres colores para las manchas)
FORMATOS = {
    "noticia":     ("NOTICIA",                  ["#0b1d3a", "#123d73", "#2a78d6", "#22c3e6", "#7b5cff"]),
    "destacada":   ("LA NOTICIA DE LA SEMANA",  ["#170f3d", "#3a1f7a", "#7b5cff", "#e05fb0", "#4a90ff"]),
    "truco":       ("TRUCO DE LA SEMANA",       ["#06231f", "#0b4a42", "#1baf7a", "#5ee0b5", "#2a9fd6"]),
    "herramienta": ("HERRAMIENTA DE LA SEMANA", ["#2a0f0a", "#6b2412", "#eb6834", "#ffb347", "#e0457b"]),
    "especial":    ("PROYECTO",                 ["#2a0a14", "#6e1530", "#e34948", "#ff9e5e", "#9b5cff"]),
}
# Prefijos que pone Gemini en la primera línea y que en la imagen ya van en la etiqueta
PREFIJOS = r"^(la noticia (económica )?de la semana|truco de (python|sql|pandas)[^:]*|" \
           r"herramienta de la semana|concepto de la semana|recurso de la semana)\s*:\s*"


def fuente(nombre, tam):
    return ImageFont.truetype(os.path.join(CARPETA_FUENTES, nombre), tam)


def rgb(hex_):
    return tuple(int(hex_[i:i + 2], 16) for i in (1, 3, 5))


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


def fondo_artistico(paleta, semilla):
    """Pinta el fondo: degradado, manchas de color difuminadas, ondas finas y grano."""
    azar = np.random.default_rng(semilla)
    oscuro, medio, *vivos = [np.array(rgb(c), dtype=float) for c in paleta]

    # 1) Degradado diagonal en un ángulo distinto para cada post
    ang = azar.uniform(0, 2 * math.pi)
    yy, xx = np.mgrid[0:LADO, 0:LADO] / LADO
    t = np.clip(((xx - 0.5) * math.cos(ang) + (yy - 0.5) * math.sin(ang)) + 0.5, 0, 1)[..., None]
    lienzo = Image.fromarray((oscuro * (1 - t) + medio * t).astype(np.uint8))

    # 2) Manchas grandes de color, muy difuminadas (efecto "aurora")
    capa = Image.new("RGB", (LADO, LADO), (0, 0, 0))
    d = ImageDraw.Draw(capa)
    for i in range(5):
        color = tuple(int(c) for c in vivos[i % len(vivos)])
        r = azar.uniform(220, 420)
        cx, cy = azar.uniform(0.1, 1.0) * LADO, azar.uniform(-0.1, 0.75) * LADO
        d.ellipse([cx - r, cy - r * azar.uniform(0.6, 1), cx + r, cy + r], fill=color)
    capa = capa.filter(ImageFilter.GaussianBlur(150))
    lienzo = Image.blend(lienzo, Image.composite(capa, lienzo, capa.convert("L")), 0.85)

    # 3) Ondas finas semitransparentes, como un flujo de datos
    ondas = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
    d = ImageDraw.Draw(ondas)
    base, amp, frec = azar.uniform(0.25, 0.55) * LADO, azar.uniform(40, 110), azar.uniform(1.2, 2.6)
    fase, giro = azar.uniform(0, 2 * math.pi), azar.uniform(-0.25, 0.25)
    for k in range(26):
        puntos = [(x, base + k * 9 + giro * x
                   + amp * math.sin(frec * 2 * math.pi * x / LADO + fase + k * 0.12)
                   + 0.35 * amp * math.sin(3.1 * 2 * math.pi * x / LADO + k * 0.3))
                  for x in range(-20, LADO + 21, 12)]
        d.line(puntos, fill=(255, 255, 255, 18 + int(30 * math.sin(math.pi * k / 25))), width=2)
    lienzo = Image.alpha_composite(lienzo.convert("RGBA"), ondas)

    # 4) Oscurecemos la parte de abajo para que el texto se lea bien
    sombra = np.zeros((LADO, LADO, 4), dtype=np.uint8)
    sombra[..., 3] = (np.clip((yy - 0.35) / 0.65, 0, 1) ** 1.4 * 190).astype(np.uint8)
    lienzo = Image.alpha_composite(lienzo, Image.fromarray(sombra, "RGBA"))

    # 5) Grano de película para un acabado menos "digital"
    grano = azar.normal(0, 7, (LADO, LADO, 1))
    arr = np.clip(np.array(lienzo.convert("RGB"), dtype=float) + grano, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def generar_tarjeta(post, formato, ruta):
    post = preparar_menciones(post)[0]  # "@[Nombre](urn...)" → "Nombre"
    etiqueta, paleta = FORMATOS.get(formato, FORMATOS["noticia"])
    semilla = int(hashlib.md5(post.encode("utf-8")).hexdigest()[:8], 16)
    img = fondo_artistico(paleta, semilla).convert("RGBA")
    capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    ancho = LADO - 2 * MARGEN

    # Etiqueta del formato en una "píldora" translúcida
    f_et = fuente("DejaVuSans-Bold.ttf", 24)
    w = d.textlength(etiqueta, font=f_et)
    d.rounded_rectangle([MARGEN, 84, MARGEN + w + 44, 132], radius=24,
                        fill=(255, 255, 255, 40), outline=(255, 255, 255, 90), width=2)
    d.text((MARGEN + 22, 108), etiqueta, font=f_et, fill=BLANCO, anchor="lm")

    # Titular: la primera línea del post, sin emojis ni prefijo
    lineas_post = [l for l in post.splitlines() if l.strip() and not l.strip().startswith("TEMA:")]
    titular = re.sub(PREFIJOS, "", sin_emojis(lineas_post[0] if lineas_post else ""), flags=re.IGNORECASE)
    titular = titular[:1].upper() + titular[1:]
    codigo = lineas_de_codigo(post) if formato == "truco" else []

    f_tit, lineas = ajustar(d, titular, "DejaVuSans-Bold.ttf", 78, 44, ancho, 4 if codigo else 6)
    alto_linea = int(f_tit.size * 1.18)
    f_cod = fuente("DejaVuSansMono.ttf", 30)
    if codigo:
        while f_cod.size > 18 and max(d.textlength(l, font=f_cod) for l in codigo) > ancho - 64:
            f_cod = fuente("DejaVuSansMono.ttf", f_cod.size - 2)
    alto_caja = int(f_cod.size * 1.5) * len(codigo) + 56 if codigo else 0

    # El texto va abajo, apoyado sobre el pie (como la portada de una revista)
    pie_y = LADO - 96
    y = pie_y - 70 - (alto_caja + 44 if codigo else 0) - alto_linea * len(lineas)
    for l in lineas:
        d.text((MARGEN + 3, y + 4), l, font=f_tit, fill=(0, 0, 0, 90))  # sombra suave
        d.text((MARGEN, y), l, font=f_tit, fill=BLANCO)
        y += alto_linea

    if codigo:
        # Caja de código translúcida ("cristal")
        y += 44
        d.rounded_rectangle([MARGEN, y, LADO - MARGEN, y + alto_caja], radius=18,
                            fill=(10, 12, 16, 170), outline=(255, 255, 255, 50), width=2)
        yy = y + 28
        for l in codigo:
            limite = int((ancho - 64) / (f_cod.size * 0.6)) - 1
            texto = l if d.textlength(l, font=f_cod) <= ancho - 64 else l[:limite] + "…"
            d.text((MARGEN + 32, yy), texto, font=f_cod, fill=(232, 230, 220, 255))
            yy += int(f_cod.size * 1.5)

    # Pie: firma y subtítulo
    d.line([MARGEN, pie_y - 34, MARGEN + 64, pie_y - 34], fill=(255, 255, 255, 200), width=4)
    d.text((MARGEN, pie_y), CONFIG.get("firma", CONFIG["nombre"]),
           font=fuente("DejaVuSans-Bold.ttf", 26), fill=(255, 255, 255, 235), anchor="lm")
    d.text((LADO - MARGEN, pie_y), CONFIG.get("subtitulo_imagen", ""),
           font=fuente("DejaVuSans.ttf", 24), fill=(255, 255, 255, 170), anchor="rm")

    Image.alpha_composite(img, capa).convert("RGB").save(ruta)
    return ruta


def imagen_del_post(post, formato, imagen=None):
    """Devuelve la ruta de la imagen del post: la indicada (posts especiales) o una generada.
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
        "herramienta": "🛠️ Herramienta de la semana: DuckDB, SQL analítico rapidísimo sin servidor\n\nTexto...\nhttps://duckdb.org",
    }
    for formato, post in ejemplos.items():
        print(generar_tarjeta(post, formato, f"ejemplo_{formato}.png"))

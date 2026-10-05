import json
import os
import feedparser

HISTORIAL = "historial.json"  # enlaces de noticias ya publicadas


def cargar_historial():
    if os.path.exists(HISTORIAL):
        with open(HISTORIAL, encoding="utf-8") as f:
            return json.load(f)
    return []


def guardar_en_historial(enlace):
    historial = cargar_historial()
    historial.append(enlace)
    with open(HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(historial[-200:], f, indent=2)  # guardamos solo los 200 últimos

# Webs de las que vamos a sacar noticias
FUENTES = {
    "Hugging Face": "https://huggingface.co/blog/feed.xml",
    "The Verge (IA)": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "Hacker News": "https://hnrss.org/frontpage",
}

def recoger_noticias():
    noticias = []
    ya_publicadas = set(cargar_historial())
    for nombre, url in FUENTES.items():
        feed = feedparser.parse(url)
        for entrada in feed.entries[:5]:  # las 5 más recientes de cada web
            if entrada.get("link", "") in ya_publicadas:
                continue  # esta ya la publicamos otro día
            noticias.append({
                "fuente": nombre,
                "titulo": entrada.get("title", ""),
                "enlace": entrada.get("link", ""),
                "resumen": entrada.get("summary", "")[:500],  # primeros 500 caracteres
            })
    return noticias

if __name__ == "__main__":
    for n in recoger_noticias():
        print(f"[{n['fuente']}] {n['titulo']}")
        print(f"   {n['enlace']}\n")

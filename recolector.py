import feedparser

# Webs de las que vamos a sacar noticias
FUENTES = {
    "Hugging Face": "https://huggingface.co/blog/feed.xml",
    "The Verge (IA)": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "Hacker News": "https://hnrss.org/frontpage",
}

def recoger_noticias():
    noticias = []
    for nombre, url in FUENTES.items():
        feed = feedparser.parse(url)
        for entrada in feed.entries[:5]:  # las 5 más recientes de cada web
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

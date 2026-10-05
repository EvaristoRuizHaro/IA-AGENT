import json
import os
import feedparser

HISTORIAL = "historial.json"  # lo que ya se ha publicado (enlaces, temas, herramientas...)


def cargar_config():
    """Lee config.json: el nombre, el tema y las fuentes de cada persona."""
    with open("config.json", encoding="utf-8") as f:
        return json.load(f)


def cargar_historial():
    if os.path.exists(HISTORIAL):
        with open(HISTORIAL, encoding="utf-8") as f:
            return json.load(f)
    return []


def guardar_en_historial(clave):
    historial = cargar_historial()
    historial.append(clave)
    with open(HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(historial[-200:], f, indent=2, ensure_ascii=False)  # solo los 200 últimos


def recoger_noticias():
    noticias = []
    ya_publicadas = set(cargar_historial())
    for nombre, url in cargar_config()["fuentes"].items():
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
    # Útil para comprobar qué fuentes funcionan
    for nombre, url in cargar_config()["fuentes"].items():
        n = len(feedparser.parse(url).entries)
        print(f"{'✅' if n else '❌'} {nombre}: {n} noticias")
    print()
    for n in recoger_noticias():
        print(f"[{n['fuente']}] {n['titulo']}")
        print(f"   {n['enlace']}\n")

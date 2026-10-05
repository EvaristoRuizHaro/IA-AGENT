# 🤖 Agente de noticias de IA para LinkedIn

Agente en Python que, cada día a las 12:00, busca las noticias más recientes sobre
Inteligencia Artificial y programación, elige la más relevante con un LLM, redacta un
post y lo publica en LinkedIn **tras mi aprobación por Telegram**.

## Cómo funciona

```
GitHub Actions (diario 12:00) → Recolector RSS → Gemini elige y redacta → Telegram (✅ 🔄 ❌) → LinkedIn API
```

1. **Recolector** (`recolector.py`): lee feeds RSS de Hugging Face, The Verge y Hacker News.
2. **Redactor** (`redactor.py`): Google Gemini selecciona la noticia más interesante y escribe el post
   siguiendo un *system prompt* con tono y estructura definidos. Incluye reintentos y modelos de reserva
   ante errores 503.
3. **Aprobación humana** (`telegram_bot.py`): el borrador llega a Telegram con botones para publicar,
   pedir otra noticia o descartar (*human-in-the-loop*).
4. **Publicación** (`linkedin.py`): API oficial de LinkedIn (`ugcPosts`) con autenticación OAuth 2.0
   (`autorizar_linkedin.py`).
5. **Orquestación** (`agente.py`) y **ejecución programada** con GitHub Actions
   (`.github/workflows/agente.yml`).

## Tecnologías

Python · Google Gemini API · Telegram Bot API · LinkedIn API · OAuth 2.0 · GitHub Actions · RSS

## Uso en local

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python autorizar_linkedin.py # una vez cada ~60 días
python agente.py
```

Las claves se guardan en un archivo `.env` (no incluido en el repositorio).

---
Proyecto de Evaristo Ruiz Haro · Especialización en IA y Big Data

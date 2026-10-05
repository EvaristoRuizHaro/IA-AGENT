# 🤖 Agente de contenido para LinkedIn con IA

Agente en Python que **cada día a las 12:00** prepara un post de LinkedIn sobre una temática
configurable (IA, economía o la que quieras), te lo envía a **Telegram para que lo apruebes** y,
si das el visto bueno, lo publica en tu perfil.

Empezó como mi agente personal de noticias de IA y lo convertí en una **plantilla reutilizable**:
el mismo código funciona para cualquier persona y tema cambiando solo un archivo de configuración.

## ✨ Qué hace

- 📰 Lee noticias recientes de varias fuentes RSS.
- 🧠 Usa un LLM (Google Gemini) para elegir el contenido más relevante y redactar el post.
- 📅 Cambia de formato según el día de la semana (noticia destacada, concepto o truco, herramienta...).
- 📱 Envía el borrador a Telegram con botones **✅ Publicar · 🔄 Otro · ❌ Descartar**.
- 🔗 Publica en LinkedIn mediante su API oficial (OAuth 2.0).
- 🗂️ Lleva un historial para no repetir noticias, temas ni herramientas.
- ☁️ Se ejecuta solo en la nube con GitHub Actions, sin depender de ningún ordenador.

## ⚙️ Cómo funciona

```
GitHub Actions (12:00) → config.json → Formato del día → Gemini redacta → Telegram (✅ 🔄 ❌) → LinkedIn
                                            ↑                                                  ↓
                                 Fuentes RSS / listas                                historial.json
```

| Módulo | Función |
|---|---|
| `agente.py` | Orquesta todo el flujo: post especial del día, borradores, aprobación y publicación |
| `redactor.py` | Genera el post con Gemini según el formato del día. Tres tipos: `noticia`, `tema_libre` y `lista` |
| `recolector.py` | Lee las fuentes RSS de `config.json` y gestiona el historial |
| `telegram_bot.py` | Envía borradores con botones y espera la respuesta (*long polling*) |
| `linkedin.py` | Publica en LinkedIn (`ugcPosts`) con vista previa del enlace |
| `autorizar_linkedin.py` | Flujo OAuth 2.0: abre LinkedIn, recoge el token y lo guarda en `.env` |
| `configurar.py` | Asistente para crear `config.json` a partir de un tema de `presets/` |

## 🎨 Temas disponibles

Cada tema define el perfil del autor, las fuentes de noticias y qué se publica cada día.

| Día | `ia` | `economia` |
|---|---|---|
| Lunes | 📌 Noticia de la semana | 📌 Noticia económica de la semana |
| Miércoles | 💡 Truco de Python / datos con código | 📚 Concepto económico explicado |
| Viernes | 🛠️ Herramienta de la semana | 🧰 Recurso de la semana (INE, FRED, Power BI...) |
| Resto | Noticia del día + opinión | Noticia económica + análisis |
| **Fuentes** | Hugging Face, The Verge, Hacker News | Expansión, Cinco Días, El Economista, BBC Business |

Para crear un tema nuevo basta con copiar un archivo de `presets/` y cambiar las fuentes y las
instrucciones.

## 🧩 Decisiones técnicas

- **Human-in-the-loop**: nada se publica sin aprobación. Un LLM puede equivocarse o inventar datos,
  y los posts salen con el nombre de una persona real.
- **Prompts anti-alucinación**: el modelo solo puede usar el título y resumen de la noticia, o la
  descripción verificada de cada herramienta/recurso. Nada de cifras inventadas.
- **Resiliencia**: si un modelo de Gemini está saturado (error 503), se prueba con modelos de
  reserva y se reintenta con espera progresiva.
- **Configuración separada del código**: todo lo personal vive en `config.json`, lo que permite
  reutilizar el agente para cualquier persona y temática.
- **Horario de verano/invierno**: GitHub Actions usa UTC, así que el workflow programa dos horas y
  descarta la que no corresponde según la hora de España.
- **Coste cero**: plan gratuito de Gemini, Telegram, la API de LinkedIn y GitHub Actions.

## 🚀 Instalación

Guía paso a paso (también para personas sin experiencia en programación):
**[GUIA_INSTALACION.md](GUIA_INSTALACION.md)**

Resumen:

```bash
py -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python configurar.py           # elegir tema, nombre y perfil
python autorizar_linkedin.py   # permiso de LinkedIn (cada ~60 días)
python agente.py               # ejecución manual
```

Para probar un formato concreto sin publicar nada: `python redactor.py <formato>`
(por ejemplo `python redactor.py truco`).

Las claves se guardan en `.env` en local y como *Secrets* en GitHub; nunca se suben al repositorio.

## 📁 Estructura

```
├── agente.py, redactor.py, recolector.py, telegram_bot.py, linkedin.py
├── autorizar_linkedin.py, obtener_chat_id.py, configurar.py
├── config.json              # configuración de la persona (tema, fuentes, formatos)
├── presets/                 # temas listos: ia.json, economia.json
├── herramientas.json        # herramientas para el tema "ia"
├── recursos_economia.json   # recursos para el tema "economia"
├── posts_programados.json   # posts especiales para fechas concretas
├── historial.json           # lo ya publicado (lo actualiza el propio workflow)
└── .github/workflows/agente.yml
```

## 🛠️ Tecnologías

Python · Google Gemini API · Telegram Bot API · LinkedIn API · OAuth 2.0 · GitHub Actions · RSS

---
Proyecto de **Evaristo Ruiz Haro** · Especialización en Inteligencia Artificial y Big Data

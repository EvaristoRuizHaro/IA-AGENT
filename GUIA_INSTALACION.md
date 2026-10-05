# Guía de instalación para una persona nueva

Tiempo aproximado: 45-60 minutos. Cada persona tiene **su propia copia** del agente, con sus
propias claves, y publica en **su propio perfil** de LinkedIn.

## 1. Cuentas necesarias (todas gratis)
- **GitHub**: github.com
- **Google** (para la clave de Gemini)
- **Telegram** en el móvil
- **LinkedIn**

## 2. Copiar el proyecto
1. Con la cuenta de GitHub de la persona, abrir el repositorio original y pulsar
   **Use this template → Create a new repository** (público o privado).
2. Instalar **GitHub Desktop**, iniciar sesión y clonar el repositorio nuevo
   (*File → Clone repository*).
3. Instalar **Python** (python.org, marcando *"Add python.exe to PATH"*) y **VS Code**.

## 3. Preparar Python
En la terminal de VS Code, dentro de la carpeta del proyecto:
```
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
Si sale el error de "scripts deshabilitados": `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## 4. Elegir el tema
```
python configurar.py
```
Elegir el tema (por ejemplo `economia`), el nombre y una frase de perfil.
Responder **s** a "¿Es una instalación nueva?".

## 5. Claves (archivo `.env`)
Crear un archivo llamado `.env` en la carpeta con este contenido:
```
GEMINI_API_KEY=
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
```
- **Gemini**: aistudio.google.com → *Get API key* → *Create API key*.
- **Telegram**: hablar con @BotFather → `/newbot` → copiar el token. Abrir el bot, pulsar
  *Iniciar*, escribirle "hola" y ejecutar `python obtener_chat_id.py` para sacar el chat id.
- **LinkedIn**: ver paso 6.

Comprobar: `python telegram_bot.py` (llega un mensaje al móvil) y `python redactor.py`
(imprime un post). `python recolector.py` muestra qué fuentes de noticias funcionan.

## 6. LinkedIn
Dos opciones:
- **A (independiente, recomendada)**: la persona crea su propia app en linkedin.com/developers
  (necesita una página de empresa cualquiera), activa *Share on LinkedIn* y *Sign In with
  LinkedIn using OpenID Connect*, añade la redirect URL `http://localhost:8000/callback` y copia
  Client ID y Client Secret al `.env`.
- **B (rápida)**: usar el Client ID y Client Secret de una app que ya exista (la de quien le
  ayuda a instalarlo). Cada persona autoriza con su propia cuenta, así que publica en su perfil,
  pero para renovar el permiso cada 60 días necesitará ese Client Secret.

Después: `python autorizar_linkedin.py` → iniciar sesión **con la cuenta de LinkedIn de la
persona** → *Permitir*. (Si se hace en el ordenador de otro, usar una ventana de incógnito.)

## 7. Subir a GitHub y programar
1. GitHub Desktop: *Commit to main* → *Push origin*. Comprobar que `.env` **no** aparece.
2. En github.com → *Settings → Secrets and variables → Actions*, crear estos 6 secretos copiando
   los valores del `.env`: `GEMINI_API_KEY`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`,
   `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN`, `LINKEDIN_TOKEN_CADUCA`.
3. Pestaña *Actions* → si lo pide, activar los workflows → *Agente LinkedIn* → *Run workflow*.

Listo: cada día a las 12:00 llegará un borrador a Telegram con los botones ✅ 🔄 ❌.

## Cada 60 días
Cuando el bot avise: `python autorizar_linkedin.py` y actualizar en GitHub los secretos
`LINKEDIN_ACCESS_TOKEN` y `LINKEDIN_TOKEN_CADUCA`.

## Personalizar
- **Horario**: `.github/workflows/agente.yml` (líneas `cron`, en hora UTC).
- **Qué se publica cada día, fuentes, tono**: `config.json`.
- **Lista de herramientas/recursos**: `herramientas.json` o `recursos_economia.json`.

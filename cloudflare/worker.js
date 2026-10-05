// Webhook de Telegram en Cloudflare Workers (gratis).
// Recibe las pulsaciones de botones AL INSTANTE, da feedback inmediato en Telegram
// y lanza el workflow "Revisar botones" de GitHub con la acción pulsada.
//
// Variables que hay que configurar en Cloudflare (Settings → Variables and Secrets):
//   TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, GITHUB_TOKEN, GITHUB_REPO (ej. "Usuario/IA-AGENT"),
//   WEBHOOK_SECRET (una contraseña inventada, la misma que en el .env)

const TEXTOS = {
  publicar: "⏳ Publicando en LinkedIn...",
  regenerar: "⏳ Preparando otro borrador...",
  descartar: "⏳ Descartando...",
};

export default {
  async fetch(request, env) {
    if (request.method !== "POST") return new Response("El webhook está funcionando ✅");

    // Solo aceptamos mensajes de Telegram (llevan nuestra contraseña secreta)
    if (request.headers.get("X-Telegram-Bot-Api-Secret-Token") !== env.WEBHOOK_SECRET) {
      return new Response("forbidden", { status: 403 });
    }

    const update = await request.json();
    const cq = update.callback_query;
    if (!cq || !cq.message) return new Response("ok");
    if (String(cq.message.chat.id) !== String(env.TELEGRAM_CHAT_ID)) return new Response("ok");

    const telegram = (metodo, datos) =>
      fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/${metodo}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datos),
      });

    // Botón de estado ("⏳ ..."): ya está en marcha, no hacemos nada más
    if (!TEXTOS[cq.data]) {
      await telegram("answerCallbackQuery", { callback_query_id: cq.id, text: "⏳ Ya estoy en ello..." });
      return new Response("ok");
    }

    // 1. Feedback inmediato: aviso emergente + cambiar los botones por el estado
    await telegram("answerCallbackQuery", { callback_query_id: cq.id, text: TEXTOS[cq.data] });
    await telegram("editMessageReplyMarkup", {
      chat_id: cq.message.chat.id,
      message_id: cq.message.message_id,
      reply_markup: { inline_keyboard: [[{ text: TEXTOS[cq.data], callback_data: "en_marcha" }]] },
    });

    // 2. Lanzar el workflow de GitHub con la acción
    const r = await fetch(
      `https://api.github.com/repos/${env.GITHUB_REPO}/actions/workflows/revisar.yml/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GITHUB_TOKEN}`,
          Accept: "application/vnd.github+json",
          "User-Agent": "agente-linkedin",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ref: "main",
          inputs: { accion: cq.data, message_id: String(cq.message.message_id) },
        }),
      }
    );

    if (!r.ok) {
      await telegram("sendMessage", {
        chat_id: cq.message.chat.id,
        text: `⚠️ No he podido avisar a GitHub (error ${r.status}). Revisa el GITHUB_TOKEN en Cloudflare.`,
      });
    }
    return new Response("ok");
  },
};

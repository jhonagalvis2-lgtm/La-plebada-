import os
import logging
import csv
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import anthropic

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """Eres el asistente de La Plebada, comunidad educativa de trading colombiana creada por Alexander Guzmán. Responde en español colombiano. Educa sobre trading, forex y criptomonedas. SIEMPRE aclara que tu contenido es educativo, no asesoría financiera."""

logging.basicConfig(level=logging.INFO)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
historial = {}

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 Qué es Trading", callback_data="trading"), InlineKeyboardButton("📊 Análisis", callback_data="analisis")],
        [InlineKeyboardButton("💰 Riesgo", callback_data="riesgo"), InlineKeyboardButton("🧠 Psicología", callback_data="psicologia")],
        [InlineKeyboardButton("💬 Hablar con IA", callback_data="ia"), InlineKeyboardButton("ℹ️ Nosotros", callback_data="about")],
    ])

def volver():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data="menu")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👋 Bienvenido a *La Plebada*, {update.effective_user.first_name}! 🇨🇴\n\nComunidad educativa de trading.\n\n⚠️ _Contenido educativo, no asesoría financiera._",
        parse_mode="Markdown", reply_markup=menu()
    )

async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    textos = {
        "menu": "👇 Menú Principal:",
        "trading": "📈 *Trading*\n\nComprar y vender activos para ganar con cambios de precio.\n\nTipos:\n• Swing Trading\n• Day Trading\n• Scalping\n\n⚠️ _Siempre implica riesgo._",
        "analisis": "📊 *Análisis Técnico*\n\nEstudio de gráficos para anticipar precios.\n\n• Velas japonesas\n• Soporte y Resistencia\n• RSI, MACD, Medias Móviles\n\n💡 Practica en TradingView.com",
        "riesgo": "💰 *Gestión de Riesgo*\n\n• Arriesga máximo 1-2% por operación\n• Usa siempre Stop Loss\n• Risk/Reward mínimo 1:2\n\n🇨🇴 Con $1.000.000 COP arriesga máx $20.000 por trade.",
        "psicologia": "🧠 *Psicología*\n\nErrores comunes:\n• FOMO\n• Revenge trading\n• Sobreconfianza\n\nHábitos ganadores:\n✅ Diario de operaciones\n✅ Respetar el plan",
        "about": "ℹ️ *La Plebada*\n\n👤 Creador: Alexander Guzmán 🇨🇴\nTrader colombiano que democratiza la educación financiera.\n\n⚠️ _No gestionamos dinero de terceros._",
        "ia": "💬 Escríbeme cualquier pregunta sobre trading y te respondo con IA 🤖",
    }
    t = textos.get(q.data, "...")
    k = menu() if q.data == "menu" else volver()
    await q.edit_message_text(t, parse_mode="Markdown", reply_markup=k)

async def mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    texto = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    if uid not in historial:
        historial[uid] = []
    historial[uid].append({"role": "user", "content": texto})
    try:
        r = client.messages.create(model="claude-opus-4-5", max_tokens=512, system=SYSTEM_PROMPT, messages=historial[uid][-10:])
        respuesta = r.content[0].text
        historial[uid].append({"role": "assistant", "content": respuesta})
        await update.message.reply_text(respuesta + "\n\n⚠️ _Educativo, no asesoría financiera._", parse_mode="Markdown", reply_markup=volver())
    except Exception as e:
        await update.message.reply_text("😅 Error técnico, intenta de nuevo.")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    historial.pop(update.effective_user.id, None)
    await update.message.reply_text("🗑️ Chat reiniciado!", reply_markup=menu())

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CallbackQueryHandler(botones))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje))
    app.run_polling()

if __name__ == "__main__":
    main()


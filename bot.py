import os
import logging
import csv
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes,
)
import anthropic

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """Eres el asistente de IA de La Plebada, comunidad educativa de trading colombiana.
Creado por Alexander Guzmán, trader colombiano.
Responde en español colombiano, de forma amigable y cercana.
Educa sobre trading, forex, criptomonedas y mercados financieros.
SIEMPRE aclara que tu contenido es educativo, no asesoría financiera.
NUNCA prometas ganancias garantizadas."""

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
conversation_history = {}
registered_users = {}

def registrar_usuario(user):
    if user.id in registered_users:
        return
    data = {
        "id": user.id,
        "username": user.username or "N/A",
        "nombre": user.first_name or "N/A",
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    registered_users[user.id] = data
    archivo = "usuarios.csv"
    existe = os.path.exists(archivo)
    with open(archivo, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        if not existe:
            writer.writeheader()
        writer.writerow(data)

def menu_principal():
    keyboard = [
        [InlineKeyboardButton("📈 Qué es el Trading", callback_data="trading"),
         InlineKeyboardButton("📊 Análisis Técnico", callback_data="analisis")],
        [InlineKeyboardButton("💰 Gestión de Riesgo", callback_data="riesgo"),
         InlineKeyboardButton("🧠 Psicología", callback_data="psicologia")],
        [InlineKeyboardButton("💬 Hablar con IA", callback_data="ia"),
         InlineKeyboardButton("ℹ️ Sobre nosotros", callback_data="about")],
        [InlineKeyboardButton("⚠️ Aviso Legal", callback_data="disclaimer")],
    ]
    return InlineKeyboardMarkup(keyboard)

def menu_volver():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú principal", callback_data="menu")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    registrar_usuario(update.effective_user)
    await update.message.reply_text(
        f"👋 Bienvenido/a a *La Plebada*, {update.effective_user.first_name}!\n\n"
        "Somos una comunidad educativa de trading colombiana 🇨🇴🚀\n\n"
        "📌 Aquí puedes:\n"
        "• Aprender sobre trading y forex\n"
        "• Consultar con nuestra IA\n"
        "• Recibir educación financiera gratis\n\n"
        "⚠️ _Todo el contenido es educativo. No somos asesores financieros._",
        parse_mode="Markdown", reply_markup=menu_principal()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    respuestas = {
        "menu": "👇 *Menú Principal - La Plebada*\n\nElige un tema:",
        "trading": "📈 *¿Qué es el Trading?*\n\nEs comprar y vender activos financieros para ganar con los cambios de precio.\n\n*Tipos:*\n• Swing Trading - días a semanas\n• Day Trading - mismo día\n• Scalping - minutos\n\n⚠️ _Todo trading implica riesgo._",
        "analisis": "📊 *Análisis Técnico*\n\nEstudio de gráficos para anticipar movimientos.\n\n*Conceptos:*\n• Velas japonesas\n• Soporte y Resistencia\n• Tendencias\n• Indicadores: RSI, MACD, Medias Móviles\n\n💡 Practica gratis en TradingView.com",
        "riesgo": "💰 *Gestión de Riesgo*\n\nLa regla más importante del trading.\n\n*Reglas básicas:*\n• Arriesga máximo el 1-2% por operación\n• Usa siempre Stop Loss\n• Busca Risk/Reward mínimo 1:2\n• Nunca operes con dinero que no puedas perder\n\n🇨🇴 Si tienes $1.000.000 COP, arriesga máximo $20.000 por trade.",
        "psicologia": "🧠 *Psicología del Trading*\n\nEl mayor enemigo eres tú mismo.\n\n*Errores comunes:*\n• FOMO - entrar por miedo a perderse el movimiento\n• Revenge trading - operar furioso tras perder\n• Sobreconfianza tras ganar\n\n*Hábitos ganadores:*\n✅ Diario de operaciones\n✅ Respetar el plan\n✅ Aceptar las pérdidas",
        "about": "ℹ️ *Sobre La Plebada*\n\nComunidad educativa de trading colombiana 🇨🇴\n\n👤 *Creador:* Alexander Guzmán\nTrader colombiano apasionado por enseñar finanzas a la gente.\n\n🎯 *Misión:* Que todo colombiano tenga acceso a educación financiera de calidad.\n\n⚠️ _No gestionamos dinero de terceros ni somos asesores financieros._",
        "disclaimer": "⚠️ *Aviso Legal*\n\nTodo el contenido de La Plebada es *educativo e informativo*.\n\n• NO somos asesores financieros\n• NO garantizamos ganancias\n• El trading implica riesgo de pérdida\n• Consulta un profesional antes de invertir\n\n_Al usar este bot aceptas que el contenido es solo educativo._",
        "ia": "💬 *Chat con IA*\n\nEscríbeme cualquier pregunta sobre trading 🤖\n\nEjemplos:\n• ¿Qué es el RSI?\n• ¿Cómo pongo un Stop Loss?\n• Explícame las velas japonesas",
    }
    texto = respuestas.get(query.data, "Opción no encontrada")
    teclado = menu_principal() if query.data == "menu" else menu_volver()
    await query.edit_message_text(texto, parse_mode="Markdown", reply_markup=teclado)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    registrar_usuario(update.effective_user)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    user_id = update.effective_user.id
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    conversation_history[user_id].append({"role": "user", "content": update.message.text})
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=conversation_history[user_id][-20:],
        )
        reply = response.content[0].text
        conversation_history[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(
            reply + "\n\n⚠️ _Contenido educativo, no asesoría financiera._",
            parse_mode="Markdown",
            reply_markup=menu_volver()
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("😅 Tuve un problema, intenta de nuevo.")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conversation_history.pop(update.effective_user.id, None)
    await update.message.reply_text("🗑️ Chat reiniciado!", reply_markup=menu_principal())

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🚀 La Plebada Bot iniciado!")
    app.run_polling()

if __name__ == "__main__":
    main()

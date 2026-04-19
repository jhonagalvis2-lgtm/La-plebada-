import os
import logging
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
NEQUI_NUMERO = os.environ.get("NEQUI_NUMERO", "")
PRECIO = "$25.000 COP"

SYSTEM_PROMPT = """Eres el asistente de La Plebada, comunidad educativa de trading colombiana creada por Alexander Guzmán. Responde en español colombiano amigable. Educa sobre trading, forex y criptomonedas. SIEMPRE aclara que tu contenido es educativo, no asesoría financiera. NUNCA prometas ganancias."""

logging.basicConfig(level=logging.INFO)
historial = {}
usuarios_premium = {}

def es_premium(uid):
    if uid not in usuarios_premium:
        return False
    return datetime.now() < usuarios_premium[uid]

def preguntar_gemini(uid, texto):
    if uid not in historial:
        historial[uid] = []
    historial[uid].append({"role": "user", "parts": [{"text": texto}]})
    mensajes = historial[uid][-10:]
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json={
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": mensajes
        }
    )
    respuesta = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    historial[uid].append({"role": "model", "parts": [{"text": respuesta}]})
    return respuesta

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 Qué es Trading", callback_data="trading"),
         InlineKeyboardButton("📊 Análisis", callback_data="analisis")],
        [InlineKeyboardButton("💰 Riesgo", callback_data="riesgo"),
         InlineKeyboardButton("🧠 Psicología", callback_data="psicologia")],
        [InlineKeyboardButton("💬 Hablar con IA", callback_data="ia"),
         InlineKeyboardButton("ℹ️ Nosotros", callback_data="about")],
        [InlineKeyboardButton("⭐ Suscripción Premium", callback_data="premium")],
    ])

def volver():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data="menu")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    nombre = update.effective_user.first_name
    badge = "⭐ PREMIUM" if es_premium(uid) else "🆓 Gratis"
    await update.message.reply_text(
        f"👋 Bienvenido a *La Plebada*, {nombre}! 🇨🇴\n"
        f"Estado: {badge}\n\n"
        "Comunidad educativa de trading.\n\n"
        "⚠️ _Contenido educativo, no asesoría financiera._",
        parse_mode="Markdown", reply_markup=menu()
    )

async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "premium":
        if es_premium(uid):
            await q.edit_message_text(
                "⭐ *Ya eres Premium!*\n\nTienes acceso a todo el contenido exclusivo.\n\n"
                "Funcionalidades:\n"
                "• 📊 Análisis diarios\n"
                "• 🎯 Señales educativas\n"
                "• 🤖 IA sin límites\n"
                "• 💬 Grupo VIP",
                parse_mode="Markdown", reply_markup=volver()
            )
        else:
            await q.edit_message_text(
                f"⭐ *Suscripción Premium - La Plebada*\n\n"
                f"💰 Precio: *{PRECIO}/mes*\n\n"
                "✅ Qué incluye:\n"
                "• 📊 Análisis diarios EUR/USD, BTC, ETH\n"
                "• 🎯 Señales educativas con entrada y SL\n"
                "• 🤖 IA sin límites\n"
                "• 📚 Lecciones exclusivas\n"
                "• 💬 Acceso a grupo VIP\n\n"
                "📱 *Cómo pagar:*\n"
                f"1️⃣ Abre Nequi y envía *{PRECIO}* al número:\n"
                f"📲 *{NEQUI_NUMERO}*\n"
                f"2️⃣ Toca el botón de abajo para notificar tu pago\n"
                f"3️⃣ En menos de 1 hora te activamos ✅\n\n"
                f"🆔 Tu ID: `{uid}` _(envíalo con el comprobante)_",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Ya pagué, notificar", callback_data="notificar_pago")],
                    [InlineKeyboardButton("🔙 Menú", callback_data="menu")]
                ])
            )
        return

    if q.data == "notificar_pago":
        nombre = q.from_user.first_name
        username = q.from_user.username or "sin usuario"
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💰 *Nuevo pago reportado!*\n\n"
                 f"👤 Nombre: {nombre}\n"
                 f"📱 Username: @{username}\n"
                 f"🆔 ID: `{uid}`\n\n"
                 f"Para activar:\n`/activar {uid}`",
            parse_mode="Markdown"
        )
        await q.edit_message_text(
            "✅ *Pago notificado!*\n\n"
            "El admin revisará tu pago y te activará en menos de 1 hora.\n\n"
            "Recuerda enviar tu comprobante de Nequi al admin 📸",
            parse_mode="Markdown", reply_markup=volver()
        )
        return

    textos = {
        "menu": "👇 *Menú Principal La Plebada:*",
        "trading": "📈 *Trading*\n\nComprar y vender activos para ganar con cambios de precio.\n\nTipos:\n• Swing Trading\n• Day Trading\n• Scalping\n\n⚠️ _Siempre implica riesgo._",
        "analisis": "📊 *Análisis Técnico*\n\nEstudio de gráficos para anticipar precios.\n\n• Velas japonesas\n• Soporte y Resistencia\n• RSI, MACD, Medias Móviles\n\n💡 Practica gratis en TradingView.com",
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
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        respuesta = preguntar_gemini(uid, update.message.text)
        await update.message.reply_text(
            respuesta + "\n\n⚠️ _Educativo, no asesoría financiera._",
            parse_mode="Markdown", reply_markup=volver()
        )
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("😅 Error técnico, intenta de nuevo.")

async def activar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No tienes permiso.")
        return
    if not context.args:
        await update.message.reply_text("Uso: /activar ID_USUARIO")
        return
    uid = int(context.args[0])
    usuarios_premium[uid] = datetime.now() + timedelta(days=30)
    await update.message.reply_text(f"✅ Usuario {uid} activado por 30 días!")
    try:
        await context.bot.send_message(
            chat_id=uid,
            text="🎉 *Tu acceso Premium fue activado!*\n\n"
                 "Ya tienes acceso a todo el contenido exclusivo de La Plebada.\n\n"
                 "Escribe /start para ver tu nuevo menú ⭐",
            parse_mode="Markdown"
        )
    except:
        pass

async def desactivar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Uso: /desactivar ID_USUARIO")
        return
    uid = int(context.args[0])
    usuarios_premium.pop(uid, None)
    await update.message.reply_text(f"✅ Usuario {uid} desactivado.")

async def usuarios_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not usuarios_premium:
        await update.message.reply_text("No hay usuarios premium activos.")
        return
    lista = "⭐ *Usuarios Premium activos:*\n\n"
    for uid, fecha in usuarios_premium.items():
        lista += f"• ID: `{uid}` — vence: {fecha.strftime('%d/%m/%Y')}\n"
    await update.message.reply_text(lista, parse_mode="Markdown")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    historial.pop(update.effective_user.id, None)
    await update.message.reply_text("🗑️ Chat reiniciado!", reply_markup=menu())

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("activar", activar))
    app.add_handler(CommandHandler("desactivar", desactivar))
    app.add_handler(CommandHandler("usuarios", usuarios_cmd))
    app.add_handler(CallbackQueryHandler(botones))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje))
    app.run_polling()

if __name__ == "__main__":
    main()import os
import logging
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
NEQUI_NUMERO = os.environ.get("NEQUI_NUMERO", "")
PRECIO = "$25.000 COP"

SYSTEM_PROMPT = """Eres el asistente de La Plebada, comunidad educativa de trading colombiana creada por Alexander Guzmán. Responde en español colombiano amigable. Educa sobre trading, forex y criptomonedas. SIEMPRE aclara que tu contenido es educativo, no asesoría financiera. NUNCA prometas ganancias."""

logging.basicConfig(level=logging.INFO)
historial = {}
usuarios_premium = {}

def es_premium(uid):
    if uid not in usuarios_premium:
        return False
    return datetime.now() < usuarios_premium[uid]

def preguntar_gemini(uid, texto):
    if uid not in historial:
        historial[uid] = []
    historial[uid].append({"role": "user", "parts": [{"text": texto}]})
    mensajes = historial[uid][-10:]
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json={
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": mensajes
        }
    )
    respuesta = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    historial[uid].append({"role": "model", "parts": [{"text": respuesta}]})
    return respuesta

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 Qué es Trading", callback_data="trading"),
         InlineKeyboardButton("📊 Análisis", callback_data="analisis")],
        [InlineKeyboardButton("💰 Riesgo", callback_data="riesgo"),
         InlineKeyboardButton("🧠 Psicología", callback_data="psicologia")],
        [InlineKeyboardButton("💬 Hablar con IA", callback_data="ia"),
         InlineKeyboardButton("ℹ️ Nosotros", callback_data="about")],
        [InlineKeyboardButton("⭐ Suscripción Premium", callback_data="premium")],
    ])

def volver():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data="menu")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    nombre = update.effective_user.first_name
    badge = "⭐ PREMIUM" if es_premium(uid) else "🆓 Gratis"
    await update.message.reply_text(
        f"👋 Bienvenido a *La Plebada*, {nombre}! 🇨🇴\n"
        f"Estado: {badge}\n\n"
        "Comunidad educativa de trading.\n\n"
        "⚠️ _Contenido educativo, no asesoría financiera._",
        parse_mode="Markdown", reply_markup=menu()
    )

async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "premium":
        if es_premium(uid):
            await q.edit_message_text(
                "⭐ *Ya eres Premium!*\n\nTienes acceso a todo el contenido exclusivo.\n\n"
                "Funcionalidades:\n"
                "• 📊 Análisis diarios\n"
                "• 🎯 Señales educativas\n"
                "• 🤖 IA sin límites\n"
                "• 💬 Grupo VIP",
                parse_mode="Markdown", reply_markup=volver()
            )
        else:
            await q.edit_message_text(
                f"⭐ *Suscripción Premium - La Plebada*\n\n"
                f"💰 Precio: *{PRECIO}/mes*\n\n"
                "✅ Qué incluye:\n"
                "• 📊 Análisis diarios EUR/USD, BTC, ETH\n"
                "• 🎯 Señales educativas con entrada y SL\n"
                "• 🤖 IA sin límites\n"
                "• 📚 Lecciones exclusivas\n"
                "• 💬 Acceso a grupo VIP\n\n"
                "📱 *Cómo pagar:*\n"
                f"1️⃣ Abre Nequi y envía *{PRECIO}* al número:\n"
                f"📲 *{NEQUI_NUMERO}*\n"
                f"2️⃣ Toca el botón de abajo para notificar tu pago\n"
                f"3️⃣ En menos de 1 hora te activamos ✅\n\n"
                f"🆔 Tu ID: `{uid}` _(envíalo con el comprobante)_",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Ya pagué, notificar", callback_data="notificar_pago")],
                    [InlineKeyboardButton("🔙 Menú", callback_data="menu")]
                ])
            )
        return

    if q.data == "notificar_pago":
        nombre = q.from_user.first_name
        username = q.from_user.username or "sin usuario"
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💰 *Nuevo pago reportado!*\n\n"
                 f"👤 Nombre: {nombre}\n"
                 f"📱 Username: @{username}\n"
                 f"🆔 ID: `{uid}`\n\n"
                 f"Para activar:\n`/activar {uid}`",
            parse_mode="Markdown"
        )
        await q.edit_message_text(
            "✅ *Pago notificado!*\n\n"
            "El admin revisará tu pago y te activará en menos de 1 hora.\n\n"
            "Recuerda enviar tu comprobante de Nequi al admin 📸",
            parse_mode="Markdown", reply_markup=volver()
        )
        return

    textos = {
        "menu": "👇 *Menú Principal La Plebada:*",
        "trading": "📈 *Trading*\n\nComprar y vender activos para ganar con cambios de precio.\n\nTipos:\n• Swing Trading\n• Day Trading\n• Scalping\n\n⚠️ _Siempre implica riesgo._",
        "analisis": "📊 *Análisis Técnico*\n\nEstudio de gráficos para anticipar precios.\n\n• Velas japonesas\n• Soporte y Resistencia\n• RSI, MACD, Medias Móviles\n\n💡 Practica gratis en TradingView.com",
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
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        respuesta = preguntar_gemini(uid, update.message.text)
        await update.message.reply_text(
            respuesta + "\n\n⚠️ _Educativo, no asesoría financiera._",
            parse_mode="Markdown", reply_markup=volver()
        )
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("😅 Error técnico, intenta de nuevo.")

async def activar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No tienes permiso.")
        return
    if not context.args:
        await update.message.reply_text("Uso: /activar ID_USUARIO")
        return
    uid = int(context.args[0])
    usuarios_premium[uid] = datetime.now() + timedelta(days=30)
    await update.message.reply_text(f"✅ Usuario {uid} activado por 30 días!")
    try:
        await context.bot.send_message(
            chat_id=uid,
            text="🎉 *Tu acceso Premium fue activado!*\n\n"
                 "Ya tienes acceso a todo el contenido exclusivo de La Plebada.\n\n"
                 "Escribe /start para ver tu nuevo menú ⭐",
            parse_mode="Markdown"
        )
    except:
        pass

async def desactivar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Uso: /desactivar ID_USUARIO")
        return
    uid = int(context.args[0])
    usuarios_premium.pop(uid, None)
    await update.message.reply_text(f"✅ Usuario {uid} desactivado.")

async def usuarios_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not usuarios_premium:
        await update.message.reply_text("No hay usuarios premium activos.")
        return
    lista = "⭐ *Usuarios Premium activos:*\n\n"
    for uid, fecha in usuarios_premium.items():
        lista += f"• ID: `{uid}` — vence: {fecha.strftime('%d/%m/%Y')}\n"
    await update.message.reply_text(lista, parse_mode="Markdown")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    historial.pop(update.effective_user.id, None)
    await update.message.reply_text("🗑️ Chat reiniciado!", reply_markup=menu())

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("activar", activar))
    app.add_handler(CommandHandler("desactivar", desactivar))
    app.add_handler(CommandHandler("usuarios", usuarios_cmd))
    app.add_handler(CallbackQueryHandler(botones))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje))
    app.run_polling()

if __name__ == "__main__":
    main()

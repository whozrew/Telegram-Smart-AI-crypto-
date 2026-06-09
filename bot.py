import logging
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import asyncio

from config import TELEGRAM_BOT_TOKEN, HALAL_COINS
import database as db
from scanner import market_cache, cached_rankings, run_market_scanner_loop, analyze_single_coin
from charts import generate_professional_chart
from ai_helper import get_education_menu_text, search_knowledge_base, KNOWLEDGE_BASE

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Asosiy klaviatura menyusi (Uzbek tilida)
MAIN_MENU = [
    ["📊 Signal", "📈 Coin Tahlili"],
    ["⭐ Watchlist", "🚨 Kuchli Signallar"],
    ["📚 AI Yordamchi", "📊 Bozor Holati"],
    ["🏆 Eng Kuchli Imkoniyatlar", "📈 Reyting"],
    ["⚙️ Sozlamalar", "ℹ️ Yordam"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username)
    
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    welcome_text = (
        f"Assalomu alaykum, {user.first_name}!\n\n"
        f"🏁 **HALOL CRYPTO AI BOT V3.5** platformasiga xush kelibsiz.\n"
        f"Bu bot faqat **HALOL SPOT SAVDO** va ta'limga asoslangan bo'lib, fyuchers, kaldıraç va short signallardan mutlaqo xolidir."
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    # Kutish rejimlarini tekshirish (Masalan, qidiruv yoki coin tahlili uchun)
    user_state = context.user_data.get('state')

    if user_state == 'waiting_for_analysis_coin':
        context.user_data['state'] = None
        coin = text.upper().strip()
        if not coin.endswith("USDT"):
            coin += "USDT"
            
        if coin not in HALAL_COINS:
            await update.message.reply_text("❌ Bu coin taqiqlangan yoki halol ro'yxatda mavjud emas.")
            return
            
        await update.message.reply_text("🔄 Tahlil qilinmoqda, iltimos kuting...")
        res = await analyze_single_coin(coin)
        if not res or coin not in market_cache:
            await update.message.reply_text("❌ Ma'lumot olishda xatolik yuz berdi.")
            return

        # Matnli hisobot tayyorlash
        data = market_cache[coin]["signal_data"]
        report = (
            f"🪙 **Koin:** {coin}\n"
            f"📊 **Signal:** {data['signal']}\n"
            f"🎯 **Entry Quality Score:** {data['entry_quality']}/100\n"
            f"💵 **Joriy narx:** ${data['price']}\n\n"
            f"✅ **Kirish zonasi:** ${data['price']}\n"
            f"🛡️ **Stop Loss:** ${data['stop_loss']}\n"
            f"🎯 **TP1 (Konservativ):** ${data['tp1']}\n"
            f"🎯 **TP2 (Mo'tadil):** ${data['tp2']}\n"
            f"🎯 **TP3 (Agressiv):** ${data['tp3']}\n"
            f"⚖️ **Risk/Reward:** {data['risk_reward']}\n\n"
            f"📝 {data['rationale']}"
        )
        
        # Grafik yaratish va jo'natish
        df = market_cache[coin]["df_1h"]
        chart_buf = generate_professional_chart(df, coin, data)
        
        # Watchlistga qo'shish tugmasi
        keyboard = [[InlineKeyboardButton("⭐ Watchlistga qo'shish", callback_data=f"add_wl_{coin}")]]
        markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_photo(photo=chart_buf, caption=report, reply_markup=markup, parse_mode="Markdown")
        return

    if user_state == 'waiting_for_ai_search':
        context.user_data['state'] = None
        answer = search_knowledge_base(text)
        await update.message.reply_text(answer, parse_mode="Markdown")
        return

    # Asosiy menyu navigatsiyasi
    if text == "📊 Signal":
        context.user_data['state'] = 'waiting_for_analysis_coin'
        await update.message.reply_text("🔍 Tahlil qilish uchun halol coin nomini yozing (Masalan: BTC, ETH, SOL):")
        
    elif text == "📈 Coin Tahlili":
        context.user_data['state'] = 'waiting_for_analysis_coin'
        await update.message.reply_text("🔍 Tahlil va professional grafik olish uchun coin nomini kiriting:")
        
    elif text == "⭐ Watchlist":
        wl = db.get_watchlist(user_id)
        if not wl:
            await update.message.reply_text("Kuzatuv ro'yxatingiz bo'sh. Coin tahlili sahifasidan koinlarni qo'shishingiz mumkin.")
            return
        
        msg = "⭐ **Sizning kuzatuv ro'yxatingiz (Har 10 daqiqada yangilanadi):**\n\n"
        for coin in wl:
            if coin in market_cache:
                s_data = market_cache[coin]["signal_data"]
                msg += f"• **{coin}**: {s_data['signal']} | Narx: ${s_data['price']}\n"
            else:
                msg += f"• **{coin}**: Yuklanmoqda...\n"
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    elif text == "🚨 Kuchli Signallar":
        strong_signals = [c for c, v in market_cache.items() if v["signal_data"]["score"] >= 80]
        if not strong_signals:
            await update.message.reply_text("🔄 Hozirgi lahzada bozorda xarid uchun o'ta kuchli signal mavjud emas. Kutish tavsiya etiladi.")
            return
        msg = "🚨 **BOZORDAGI ENGL KUCHLI XARID SIGNALLARI:**\n\n"
        for coin in strong_signals:
            s_data = market_cache[coin]["signal_data"]
            msg += f"🔥 **{coin}** - Score: {s_data['score']}/100 | Kirish: ${s_data['price']}\n"
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    elif text == "📚 AI Yordamchi":
        keyboard = [
            [InlineKeyboardButton("🕌 Halol Kripto Asoslari", callback_data="edu_halal"), InlineKeyboardButton("📉 Fyuchers Xavfi", callback_data="edu_futures")],
            [InlineKeyboardButton("📈 SMC va Trendlar", callback_data="edu_smc"), InlineKeyboardButton("🔍 Savol Berish", callback_data="edu_search")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(get_education_menu_text(), reply_markup=markup, parse_mode="Markdown")
        
    elif text == "📊 Bozor Holati":
        # Global bozor holati indeksatsiyasi (Halol coinlar o'rtacha ko'rsatkichi)
        if not market_cache:
            await update.message.reply_text("Ma'lumotlar yuklanmoqda, birozdan so'ng qayta urinib ko'ring.")
            return
        avg_score = int(sum([v["signal_data"]["score"] for v in market_cache.values()]) / len(market_cache))
        
        status = "Stabil" if 40 <= avg_score <= 60 else "Bullish ✅" if avg_score > 60 else "Bearish ⚠️"
        msg = (
            f"📊 **Global Bozor Holati Indeksi:** {avg_score}/100\n\n"
            f"• **Trend:** {status}\n"
            f"• **Momentum:** {'Kuchli ✅' if avg_score > 55 else 'Oʻrta 🟡'}\n"
            f"• **Hajm harakati:** Faol\n"
            f"• **Volatillik:** Barqaror\n\n"
            f"_Ushbu ko'rsatkich barcha halol spot juftliklarning umumiy quvvati asosida hisoblangan._"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    elif text == "🏆 Eng Kuchli Imkoniyatlar":
        top = cached_rankings.get('top_opportunities', [])
        if not top:
            await update.message.reply_text("Ma'lumotlar tayyorlanmoqda, biroz kuting...")
            return
        msg = "🏆 **Eng Kuchli Spot Imkoniyatlar (Top 10):**\n\n"
        for idx, item in enumerate(top, 1):
            msg += f"{idx}. **{item['coin']}** | Ball: {item['score']} | Signal: {item['signal']}\n"
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    elif text == "📈 Reyting":
        top_trend = cached_rankings.get('top_opportunities', [])[:5]
        top_quality = cached_rankings.get('highest_volume', [])[:5]
        
        msg = "📈 **Bozor Reytingi Etalonlari**\n\n"
        msg += "🏆 **Top Trenddagi Aktivlar:**\n"
        for i, item in enumerate(top_trend, 1):
            msg += f"{i}. {item['coin']} ({item['score']} ball)\n"
            
        msg += "\n🎯 **Eng Sifatli Kirish Nuqtasiga Ega Koinlar:**\n"
        for i, item in enumerate(top_quality, 1):
            msg += f"{i}. {item['coin']} (Sifat: {item['entry_quality']}/100)\n"
            
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    elif text == "⚙️ Sozlamalar":
        await update.message.reply_text("⚙️ **Sozlamalar paneli:**\n\nTil: O'zbekcha 🇺🇿\nBozor ma'lumotlari: Binance Spot\nTizim versiyasi: v3.5 Stable")
        
    elif text == "ℹ️ Yordam":
        help_text = (
            "ℹ️ **Botdan foydalanish qo'llanmasi:**\n\n"
            "1. Bot mutlaqo halol spot savdo qoidalariga asoslangan.\n"
            "2. Kaldıraç, Fyuchers va Short bitimlari Islom dinida harom bo'lganligi sababli dasturga qo'shilmagan.\n"
            "3. Signallar SMC (Smart Money Concepts) va 12 ta texnik indikator asosida hisoblanadi."
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

async def handle_callback_queries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id

    if data.startswith("add_wl_"):
        coin = data.replace("add_wl_", "")
        success = db.add_to_watchlist(user_id, coin)
        if success:
            await query.edit_message_reply_markup(reply_markup=None)
            await context.bot.send_message(chat_id=user_id, text=f"✅ {coin} muvaffaqiyatli kuzatuv ro'yxatiga (Watchlist) qo'shildi.")
        else:
            await context.bot.send_message(chat_id=user_id, text=f"ℹ️ {coin} allaqachon watchlistga qo'shilgan.")
            
    elif data == "edu_halal":
        await query.message.reply_text(KNOWLEDGE_BASE["spot"], parse_mode="Markdown")
    elif data == "edu_futures":
        await query.message.reply_text(KNOWLEDGE_BASE["futures"], parse_mode="Markdown")
    elif data == "edu_smc":
        smc_combined = f"{KNOWLEDGE_BASE['order block']}\n\n{KNOWLEDGE_BASE['fvg']}\n\n{KNOWLEDGE_BASE['bos']}\n\n{KNOWLEDGE_BASE['choch']}"
        await query.message.reply_text(smc_combined, parse_mode="Markdown")
    elif data == "edu_search":
        context.user_data['state'] = 'waiting_for_ai_search'
        await query.message.reply_text("🔍 Bilimlar bazasidan qidirish uchun kalit so'zni yozing (Masalan: rsi, fvg, bos, risk):")

def main():
    # DB yaratish
    db.init_db()
    
    # Bot dasturini qurish
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Skaner va fon vazifalarini asinxron ishga tushirish zanjiri
    loop = asyncio.get_event_loop()
    loop.create_task(run_market_scanner_loop(app.bot))

    # Handlerlarni ro'yxatdan o'tkazish
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback_queries))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    
    logger.info("Bot muvaffaqiyatli ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()

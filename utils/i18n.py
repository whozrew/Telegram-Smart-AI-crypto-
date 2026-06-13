"""
Internationalization system.
Supports Uzbek (uz), Russian (ru), English (en).
"""
from __future__ import annotations

from typing import Optional

# ─────────────────────────────────────────────
# All translations
# ─────────────────────────────────────────────

TRANSLATIONS: dict[str, dict[str, str]] = {
    # ── Start / Welcome ─────────────────────────────────────────────
    "welcome": {
        "uz": "👋 <b>Bozor Narxlari</b> botiga xush kelibsiz!\n\n"
              "Men sizga O'zbekiston va xalqaro do'konlarda mahsulot narxlarini solishtiraman.\n\n"
              "Qidiruv uchun mahsulot nomini yuboring, URL manzilini yuboring yoki screenshot tashlang.",
        "ru": "👋 Добро пожаловать в <b>Bozor Narxlari</b>!\n\n"
              "Я помогу вам сравнить цены на товары в магазинах Узбекистана и по всему миру.\n\n"
              "Отправьте название товара, ссылку или скриншот для поиска.",
        "en": "👋 Welcome to <b>Bozor Narxlari</b>!\n\n"
              "I help you compare product prices across Uzbekistan and global marketplaces.\n\n"
              "Send a product name, URL, or screenshot to start searching.",
    },
    "language_select": {
        "uz": "🌐 Tilni tanlang:",
        "ru": "🌐 Выберите язык:",
        "en": "🌐 Select language:",
    },
    "language_changed": {
        "uz": "✅ Til o'zgartirildi: O'zbekcha",
        "ru": "✅ Язык изменён: Русский",
        "en": "✅ Language changed: English",
    },
    # ── Search ───────────────────────────────────────────────────────
    "search_prompt": {
        "uz": "🔍 Mahsulot nomini, URL manzilini yuboring yoki screenshot tashlang:",
        "ru": "🔍 Отправьте название товара, ссылку или скриншот:",
        "en": "🔍 Send a product name, URL, or screenshot:",
    },
    "searching": {
        "uz": "🔍 Qidirilmoqda... Iltimos kuting.",
        "ru": "🔍 Поиск... Пожалуйста, подождите.",
        "en": "🔍 Searching... Please wait.",
    },
    "search_no_results": {
        "uz": "😕 <b>{query}</b> bo'yicha natija topilmadi.\n\nBoshqa so'z bilan urinib ko'ring.",
        "ru": "😕 По запросу <b>{query}</b> ничего не найдено.\n\nПопробуйте другой запрос.",
        "en": "😕 No results found for <b>{query}</b>.\n\nTry a different search term.",
    },
    "search_results_header": {
        "uz": "🛍 <b>{query}</b> bo'yicha {count} ta natija topildi:",
        "ru": "🛍 По запросу <b>{query}</b> найдено {count} результатов:",
        "en": "🛍 Found {count} results for <b>{query}</b>:",
    },
    "exact_matches": {
        "uz": "✅ <b>Aniq moslamalar:</b>",
        "ru": "✅ <b>Точные совпадения:</b>",
        "en": "✅ <b>Exact matches:</b>",
    },
    "similar_products": {
        "uz": "🔄 <b>O'xshash mahsulotlar:</b>",
        "ru": "🔄 <b>Похожие товары:</b>",
        "en": "🔄 <b>Similar products:</b>",
    },
    # ── Product Card ─────────────────────────────────────────────────
    "product_card": {
        "uz": "🏷 <b>{title}</b>\n\n"
              "💰 <b>Narx:</b> {price}\n"
              "📦 <b>Mavjudlik:</b> {availability}\n"
              "⭐ <b>Reyting:</b> {rating}\n"
              "🏪 <b>Do'kon:</b> {store}\n"
              "🕒 <b>Yangilangan:</b> {updated}",
        "ru": "🏷 <b>{title}</b>\n\n"
              "💰 <b>Цена:</b> {price}\n"
              "📦 <b>Наличие:</b> {availability}\n"
              "⭐ <b>Рейтинг:</b> {rating}\n"
              "🏪 <b>Магазин:</b> {store}\n"
              "🕒 <b>Обновлено:</b> {updated}",
        "en": "🏷 <b>{title}</b>\n\n"
              "💰 <b>Price:</b> {price}\n"
              "📦 <b>Availability:</b> {availability}\n"
              "⭐ <b>Rating:</b> {rating}\n"
              "🏪 <b>Store:</b> {store}\n"
              "🕒 <b>Updated:</b> {updated}",
    },
    "in_stock": {
        "uz": "✅ Mavjud",
        "ru": "✅ В наличии",
        "en": "✅ In Stock",
    },
    "out_of_stock": {
        "uz": "❌ Mavjud emas",
        "ru": "❌ Нет в наличии",
        "en": "❌ Out of Stock",
    },
    "no_price": {
        "uz": "Narx yo'q",
        "ru": "Цена не указана",
        "en": "No price",
    },
    "no_rating": {
        "uz": "Reyting yo'q",
        "ru": "Нет рейтинга",
        "en": "No rating",
    },
    "result_counter": {
        "uz": "{current}/{total}",
        "ru": "{current}/{total}",
        "en": "{current}/{total}",
    },
    # ── Buttons ──────────────────────────────────────────────────────
    "btn_ai_advice": {
        "uz": "🧠 AI Maslahat",
        "ru": "🧠 AI Совет",
        "en": "🧠 AI Advice",
    },
    "btn_compare": {
        "uz": "📊 Solishtirish",
        "ru": "📊 Сравнить",
        "en": "📊 Compare",
    },
    "btn_save": {
        "uz": "⭐ Saqlash",
        "ru": "⭐ Сохранить",
        "en": "⭐ Save",
    },
    "btn_saved": {
        "uz": "⭐ Saqlangan",
        "ru": "⭐ Сохранено",
        "en": "⭐ Saved",
    },
    "btn_track": {
        "uz": "🔔 Narxni kuzatish",
        "ru": "🔔 Отслеживать цену",
        "en": "🔔 Track Price",
    },
    "btn_open": {
        "uz": "🛒 Ochish",
        "ru": "🛒 Открыть",
        "en": "🛒 Open",
    },
    "btn_prev": {
        "uz": "⬅ Oldingi",
        "ru": "⬅ Назад",
        "en": "⬅ Previous",
    },
    "btn_next": {
        "uz": "Keyingi ➡",
        "ru": "Следующий ➡",
        "en": "Next ➡",
    },
    "btn_back": {
        "uz": "🔙 Orqaga",
        "ru": "🔙 Назад",
        "en": "🔙 Back",
    },
    "btn_search": {
        "uz": "🔍 Qidirish",
        "ru": "🔍 Поиск",
        "en": "🔍 Search",
    },
    "btn_favorites": {
        "uz": "⭐ Saqlangan",
        "ru": "⭐ Избранное",
        "en": "⭐ Favorites",
    },
    "btn_watchlist": {
        "uz": "👁 Kuzatuv",
        "ru": "👁 Список наблюдения",
        "en": "👁 Watchlist",
    },
    "btn_alerts": {
        "uz": "🔔 Ogohlantirishlar",
        "ru": "🔔 Оповещения",
        "en": "🔔 Alerts",
    },
    "btn_settings": {
        "uz": "⚙️ Sozlamalar",
        "ru": "⚙️ Настройки",
        "en": "⚙️ Settings",
    },
    "btn_language": {
        "uz": "🌐 Til",
        "ru": "🌐 Язык",
        "en": "🌐 Language",
    },
    "btn_help": {
        "uz": "❓ Yordam",
        "ru": "❓ Помощь",
        "en": "❓ Help",
    },
    "btn_cancel": {
        "uz": "❌ Bekor qilish",
        "ru": "❌ Отмена",
        "en": "❌ Cancel",
    },
    "btn_confirm": {
        "uz": "✅ Tasdiqlash",
        "ru": "✅ Подтвердить",
        "en": "✅ Confirm",
    },
    "btn_remove": {
        "uz": "🗑 O'chirish",
        "ru": "🗑 Удалить",
        "en": "🗑 Remove",
    },
    "btn_set_alert": {
        "uz": "💰 Narx chegarasini belgilash",
        "ru": "💰 Установить порог цены",
        "en": "💰 Set Price Target",
    },
    # ── AI Advice ────────────────────────────────────────────────────
    "ai_thinking": {
        "uz": "🧠 AI tahlil qilmoqda...",
        "ru": "🧠 AI анализирует...",
        "en": "🧠 AI is analyzing...",
    },
    "ai_advice_header": {
        "uz": "🧠 <b>AI Maslahat</b>\n\n",
        "ru": "🧠 <b>AI Совет</b>\n\n",
        "en": "🧠 <b>AI Advice</b>\n\n",
    },
    "ai_error": {
        "uz": "❌ AI maslahat olishda xatolik yuz berdi. Keyinroq urinib ko'ring.",
        "ru": "❌ Ошибка при получении AI совета. Попробуйте позже.",
        "en": "❌ Error getting AI advice. Please try again later.",
    },
    # ── Favorites ────────────────────────────────────────────────────
    "favorites_empty": {
        "uz": "⭐ Saqlangan mahsulotlar yo'q.\n\nQidiruv natijalarida ⭐ tugmasini bosing.",
        "ru": "⭐ У вас нет сохранённых товаров.\n\nНажмите ⭐ в результатах поиска.",
        "en": "⭐ You have no saved products.\n\nPress ⭐ in search results to save.",
    },
    "favorites_header": {
        "uz": "⭐ <b>Saqlangan mahsulotlar</b> ({count} ta):",
        "ru": "⭐ <b>Избранное</b> ({count} товаров):",
        "en": "⭐ <b>Favorites</b> ({count} items):",
    },
    "product_saved": {
        "uz": "✅ Mahsulot saqlandi!",
        "ru": "✅ Товар сохранён!",
        "en": "✅ Product saved!",
    },
    "product_already_saved": {
        "uz": "ℹ️ Bu mahsulot allaqachon saqlangan.",
        "ru": "ℹ️ Этот товар уже сохранён.",
        "en": "ℹ️ This product is already saved.",
    },
    "product_removed": {
        "uz": "🗑 Mahsulot o'chirildi.",
        "ru": "🗑 Товар удалён.",
        "en": "🗑 Product removed.",
    },
    # ── Watchlist ────────────────────────────────────────────────────
    "watchlist_empty": {
        "uz": "👁 Kuzatilayotgan mahsulotlar yo'q.",
        "ru": "👁 Нет отслеживаемых товаров.",
        "en": "👁 No products in watchlist.",
    },
    "watchlist_added": {
        "uz": "✅ Mahsulot kuzatuvga qo'shildi!",
        "ru": "✅ Товар добавлен в список наблюдения!",
        "en": "✅ Product added to watchlist!",
    },
    # ── Alerts ───────────────────────────────────────────────────────
    "alert_prompt": {
        "uz": "💰 Xabardorlik uchun narx chegarasini kiriting (UZS):\n\nMisol: 14000000",
        "ru": "💰 Введите целевую цену для оповещения (сум):\n\nПример: 14000000",
        "en": "💰 Enter target price for alert (UZS):\n\nExample: 14000000",
    },
    "alert_set": {
        "uz": "✅ Xabardorlik o'rnatildi!\n\nNarx {price} UZS dan pastga tushganda sizni xabardor qilaman.",
        "ru": "✅ Оповещение установлено!\n\nЯ уведомлю вас, когда цена опустится ниже {price} сум.",
        "en": "✅ Alert set!\n\nI'll notify you when price drops below {price} UZS.",
    },
    "alert_invalid_price": {
        "uz": "❌ Noto'g'ri narx. Raqam kiriting (masalan: 14000000).",
        "ru": "❌ Неверная цена. Введите число (например: 14000000).",
        "en": "❌ Invalid price. Enter a number (e.g. 14000000).",
    },
    "alert_triggered": {
        "uz": "🔔 <b>Narx tushdi!</b>\n\n{product}\n\n💰 Hozirgi narx: {price} UZS\n🎯 Siz belgilagan chegara: {target} UZS",
        "ru": "🔔 <b>Цена снизилась!</b>\n\n{product}\n\n💰 Текущая цена: {price} сум\n🎯 Ваш порог: {target} сум",
        "en": "🔔 <b>Price dropped!</b>\n\n{product}\n\n💰 Current price: {price} UZS\n🎯 Your target: {target} UZS",
    },
    # ── Compare ──────────────────────────────────────────────────────
    "compare_select": {
        "uz": "📊 Solishtirilayotgan mahsulotlar ({count}/5):\n\n{products}\n\nYana mahsulot qo'shing yoki solishtiring.",
        "ru": "📊 Выбранные для сравнения ({count}/5):\n\n{products}\n\nДобавьте ещё или сравните.",
        "en": "📊 Selected for comparison ({count}/5):\n\n{products}\n\nAdd more or compare now.",
    },
    "compare_result": {
        "uz": "📊 <b>Mahsulotlar taqqoslash:</b>",
        "ru": "📊 <b>Сравнение товаров:</b>",
        "en": "📊 <b>Product Comparison:</b>",
    },
    "btn_do_compare": {
        "uz": "📊 Taqqosla",
        "ru": "📊 Сравнить",
        "en": "📊 Compare Now",
    },
    "btn_clear_compare": {
        "uz": "🗑 Tozalash",
        "ru": "🗑 Очистить",
        "en": "🗑 Clear",
    },
    # ── OCR ──────────────────────────────────────────────────────────
    "ocr_processing": {
        "uz": "📸 Screenshot tahlil qilinmoqda...",
        "ru": "📸 Анализируем скриншот...",
        "en": "📸 Analyzing screenshot...",
    },
    "ocr_found": {
        "uz": "📸 Rasmdan topildi: <b>{product}</b>\n\nQidirilmoqda...",
        "ru": "📸 Из изображения найдено: <b>{product}</b>\n\nИщем...",
        "en": "📸 Found from image: <b>{product}</b>\n\nSearching...",
    },
    "ocr_failed": {
        "uz": "❌ Rasmdan mahsulot aniqlanmadi. Mahsulot nomini matn ko'rinishida yuboring.",
        "ru": "❌ Не удалось определить товар из изображения. Отправьте название текстом.",
        "en": "❌ Could not detect product from image. Please send the product name as text.",
    },
    # ── Settings ─────────────────────────────────────────────────────
    "settings_menu": {
        "uz": "⚙️ <b>Sozlamalar</b>\n\nHozirgi til: {language}",
        "ru": "⚙️ <b>Настройки</b>\n\nТекущий язык: {language}",
        "en": "⚙️ <b>Settings</b>\n\nCurrent language: {language}",
    },
    # ── Help ─────────────────────────────────────────────────────────
    "help_text": {
        "uz": "❓ <b>Yordam</b>\n\n"
              "📌 <b>Qidirish usullari:</b>\n"
              "• Mahsulot nomini yozing (masalan: iPhone 17 Pro)\n"
              "• URL manzilini yuboring\n"
              "• Screenshot tashlang\n\n"
              "📌 <b>Asosiy buyruqlar:</b>\n"
              "/start - Botni qayta ishga tushirish\n"
              "/search - Qidirish\n"
              "/favorites - Saqlangan mahsulotlar\n"
              "/watchlist - Kuzatilayotgan mahsulotlar\n"
              "/alerts - Ogohlantirishlar\n"
              "/language - Tilni o'zgartirish\n"
              "/help - Yordam",
        "ru": "❓ <b>Помощь</b>\n\n"
              "📌 <b>Способы поиска:</b>\n"
              "• Введите название товара (например: iPhone 17 Pro)\n"
              "• Отправьте ссылку на товар\n"
              "• Пришлите скриншот\n\n"
              "📌 <b>Основные команды:</b>\n"
              "/start - Перезапустить бота\n"
              "/search - Поиск\n"
              "/favorites - Избранное\n"
              "/watchlist - Список наблюдения\n"
              "/alerts - Оповещения\n"
              "/language - Сменить язык\n"
              "/help - Помощь",
        "en": "❓ <b>Help</b>\n\n"
              "📌 <b>Search methods:</b>\n"
              "• Type a product name (e.g. iPhone 17 Pro)\n"
              "• Send a product URL\n"
              "• Send a screenshot\n\n"
              "📌 <b>Main commands:</b>\n"
              "/start - Restart bot\n"
              "/search - Search\n"
              "/favorites - Saved products\n"
              "/watchlist - Watchlist\n"
              "/alerts - Alerts\n"
              "/language - Change language\n"
              "/help - Help",
    },
    # ── Errors ───────────────────────────────────────────────────────
    "error_generic": {
        "uz": "❌ Xatolik yuz berdi. Iltimos keyinroq urinib ko'ring.",
        "ru": "❌ Произошла ошибка. Пожалуйста, попробуйте позже.",
        "en": "❌ An error occurred. Please try again later.",
    },
    "error_banned": {
        "uz": "🚫 Siz bloklangansiz.",
        "ru": "🚫 Вы заблокированы.",
        "en": "🚫 You are banned.",
    },
    "error_user_limit": {
        "uz": "⚠️ Bot hozircha yangi foydalanuvchilarni qabul qilmayapti. Keyinroq urinib ko'ring.",
        "ru": "⚠️ Бот временно не принимает новых пользователей. Попробуйте позже.",
        "en": "⚠️ Bot is not accepting new users at this time. Please try later.",
    },
    "error_rate_limit": {
        "uz": "⏳ Juda ko'p so'rov. {seconds} soniyadan keyin urinib ko'ring.",
        "ru": "⏳ Слишком много запросов. Попробуйте через {seconds} секунд.",
        "en": "⏳ Too many requests. Try again in {seconds} seconds.",
    },
    "error_cooldown": {
        "uz": "⏳ Iltimos {seconds} soniya kuting.",
        "ru": "⏳ Подождите {seconds} секунд.",
        "en": "⏳ Please wait {seconds} seconds.",
    },
    # ── Admin ────────────────────────────────────────────────────────
    "admin_panel": {
        "uz": "👑 <b>Admin Panel</b>",
        "ru": "👑 <b>Панель администратора</b>",
        "en": "👑 <b>Admin Panel</b>",
    },
    "admin_stats": {
        "uz": "📊 <b>Statistika:</b>\n\n"
              "👥 Jami foydalanuvchilar: {total_users}\n"
              "✅ Faol foydalanuvchilar: {active_users}\n"
              "🔍 Jami qidiruvlar: {total_searches}\n"
              "🔔 Faol ogohlantirishlar: {total_alerts}\n"
              "⭐ Saqlangan mahsulotlar: {total_favorites}\n"
              "🚫 Bloklangan: {banned_users}",
        "ru": "📊 <b>Статистика:</b>\n\n"
              "👥 Всего пользователей: {total_users}\n"
              "✅ Активных: {active_users}\n"
              "🔍 Всего поисков: {total_searches}\n"
              "🔔 Активных оповещений: {total_alerts}\n"
              "⭐ Сохранённых товаров: {total_favorites}\n"
              "🚫 Заблокированных: {banned_users}",
        "en": "📊 <b>Statistics:</b>\n\n"
              "👥 Total users: {total_users}\n"
              "✅ Active users: {active_users}\n"
              "🔍 Total searches: {total_searches}\n"
              "🔔 Active alerts: {total_alerts}\n"
              "⭐ Saved products: {total_favorites}\n"
              "🚫 Banned users: {banned_users}",
    },
    "admin_broadcast_prompt": {
        "uz": "📢 Barcha foydalanuvchilarga xabar yuboring:",
        "ru": "📢 Отправьте сообщение для рассылки:",
        "en": "📢 Send message for broadcast:",
    },
    "admin_broadcast_done": {
        "uz": "✅ Xabar {count} ta foydalanuvchiga yuborildi.",
        "ru": "✅ Сообщение отправлено {count} пользователям.",
        "en": "✅ Message sent to {count} users.",
    },
    "admin_ban_prompt": {
        "uz": "🚫 Bloklash uchun foydalanuvchi ID sini kiriting:",
        "ru": "🚫 Введите ID пользователя для блокировки:",
        "en": "🚫 Enter user ID to ban:",
    },
    "admin_banned": {
        "uz": "✅ Foydalanuvchi {user_id} bloklandi.",
        "ru": "✅ Пользователь {user_id} заблокирован.",
        "en": "✅ User {user_id} banned.",
    },
    "admin_unbanned": {
        "uz": "✅ Foydalanuvchi {user_id} blokdan chiqarildi.",
        "ru": "✅ Пользователь {user_id} разблокирован.",
        "en": "✅ User {user_id} unbanned.",
    },
    "admin_not_authorized": {
        "uz": "⛔ Ruxsat yo'q.",
        "ru": "⛔ Нет доступа.",
        "en": "⛔ Not authorized.",
    },
    "btn_broadcast": {
        "uz": "📢 Xabar yuborish",
        "ru": "📢 Рассылка",
        "en": "📢 Broadcast",
    },
    "btn_stats": {
        "uz": "📊 Statistika",
        "ru": "📊 Статистика",
        "en": "📊 Statistics",
    },
    "btn_ban_user": {
        "uz": "🚫 Foydalanuvchini bloklash",
        "ru": "🚫 Заблокировать",
        "en": "🚫 Ban User",
    },
    "btn_unban_user": {
        "uz": "✅ Blokdan chiqarish",
        "ru": "✅ Разблокировать",
        "en": "✅ Unban User",
    },
}


def t(key: str, lang: str = "uz", **kwargs) -> str:
    """
    Translate a key to the given language.
    Falls back to Uzbek, then English if not found.
    """
    lang = lang if lang in ("uz", "ru", "en") else "uz"

    translations = TRANSLATIONS.get(key, {})
    text = translations.get(lang) or translations.get("uz") or translations.get("en") or key

    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass

    return text


def detect_language(telegram_lang_code: Optional[str]) -> str:
    """Map Telegram language code to supported language."""
    if not telegram_lang_code:
        return "uz"
    code = telegram_lang_code.lower()
    if code.startswith("ru"):
        return "ru"
    if code.startswith("en"):
        return "en"
    if code.startswith("uz"):
        return "uz"
    return "uz"

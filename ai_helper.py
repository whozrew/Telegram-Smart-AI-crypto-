import re
from typing import Dict

# Mahalliy mukammal offline bilimlar bazasi
KNOWLEDGE_BASE = {
    "spot": "🕌 **Spot Savdo nima va nega halol?**\nSpot savdo - bu aktivni (masalan, BTC) to'liq naqd pulga sotib olish va unga haqiqiy egalik qilishdir. Leveraj (yelkari) va qarz ishlatilmaydi. Sizda bor pul yo'qolmaydi, faqat aktiv narxi o'zgaradi. Shuning uchun Islom ulamolari spot savdoni halol deb hisoblashadi.",
    "futures": "⚠️ **Fyuchers (Futures) va Leveraj nega harom?**\nFyuchers va kaldıraç (leverage) savdosida siz aslida yo'q pulni qarzga olib, garov evaziga savdo qilasiz. Bu jarayonda foiz (ribo), yuqori darajadagi g'arar (noaniqlik) va qimor (maysir) elementlari aralashadi. Shuning uchun bu turdagi savdo Islom moliyasi qoidalariga ko'ra mutlaqo taqiqlangan.",
    "rsi": "📈 **RSI (Relative Strength Index):**\nAktivning haddan tashqari sotib olingan (70 dan yuqori) yoki sotilganligini (30 dan past) o'lchaydigan ko'rsatkich. Tizimimizda RSI 50-65 oralig'ida bo'lsa, bu halol yuksalish trendini kuchli ekanligini anglatadi.",
    "macd": "📊 **MACD Indikatori:**\nTrendning yo'nalishi va kuchini ko'rsatuvchi indikator. MACD chizig'i Signal chizig'ini pastdan tepaga kesib o'tsa, bu xarid uchun kuchli signal hisoblanadi.",
    "order block": "🎯 **Order Block (OB):**\nYirik institutlar va smart money (aqlli pullar) o'z pozitsiyalarini yig'ib olgan narx zonalari. Bullish Order Block - bu kuchli o'sishdan oldingi oxirgi tushish shamidir va bu zona kelajakda kuchli tayanch (support) bo'lib xizmat qiladi.",
    "fvg": "🔍 **Fair Value Gap (FVG):**\nBozordagi muvozanatning buzilishi natijasida grafikda qolgan bo'shliq (Imbalance). Narx kelajakda magnit kabi ushbu FVG bo'shlig'ini to'ldirish uchun qaytib keladi.",
    "bos": "📉 **BOS (Break Of Structure):**\nNarxning joriy trend yo'nalishidagi eng oxirgi cho'qqi (high) yoki tubni (low) buzib, o'sha tomonga harakatini davom ettirishi. Bu trend davomiyligini tasdiqlaydi.",
    "choch": "🔄 **CHoCH (Change Of Character):**\nTrend yo'nalishining tubdan o'zgarishi signali. Masalan, tushayotgan bozor strukturasi buzilib, birinchi marta yangi baland cho'qqi hosil qilsa, CHoCH yuz bergan hisoblanadi va trend o'sishga o'zgaradi.",
    "risk": "🛡️ **Risk Boshqaruvi va Pozitsiya Hajmi:**\nHech qachon bir bitimga umumiy kapitalingizning 2-5% dan ortig'ini tikmang. Spot tradingda ham Stop Loss darajasiga amal qilish capital preservation (kapitalni saqlab qolish) uchun juda muhimdir."
}

def get_education_menu_text() -> str:
    return (
        "🤖 **AI Yordamchi offline ta'lim tizimiga xush kelibsiz!**\n\n"
        "Quyidagi tugmalar orqali Islomiy kripto qoidalari va zamonaviy Price Action / SMC tahlillarini mukammal o'rganishingiz mumkin.\n\n"
        "Shuningdek, quyi menyudan `🔍 Savol Berish` tugmasini bosib, qiziqtirgan indikator nomini (masalan: rsi, fvg, bos) yozib yuborishingiz mumkin."
    )

def search_knowledge_base(query: str) -> str:
    query = query.lower().strip()
    for key, text in KNOWLEDGE_BASE.items():
        if key in query or query in key:
            return text
    return "❌ Kechirasiz, ushbu mavzu bo'yicha ma'lumot topilmadi. Kalit so'zlarni to'g'ri yozganingizga ishonch hosil qiling (Masalan: rsi, macd, fvg, spot, futures)."

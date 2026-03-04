"""
pcdropsali_bot.py
البوت الكامل المتوافق مع Python 3.13 و Railway
يستخدم python-telegram-bot v20 (async)
"""

import logging
import os
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ─── الإعدادات الأساسية ───────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# نمط للكشف عن روابط AliExpress
ALIEXPRESS_PATTERN = re.compile(
    r"https?://(www\.)?(aliexpress\.com|s\.click\.aliexpress\.com|a\.aliexpress\.com)\S*",
    re.IGNORECASE,
)

# الفئات للقائمة الرئيسية
CATEGORIES = [
    ("🖥️ بطاقات الجرافيكس", "cat_gpu"),
    ("⚙️ المعالجات",         "cat_cpu"),
    ("💾 أقراص SSD",          "cat_ssd"),
    ("🖥️ تجميعات PC",         "cat_builds"),
]

# ─── دوال AliExpress (جاهزة للتطوير لاحقاً) ─────────────────────────────────
def build_affiliate_link(url: str) -> str:
    """تحويل الرابط إلى رابط أفلييت - سيتم ربطه بالـ API لاحقاً"""
    tracking_id = os.getenv("TRACKING_ID", "")
    if not tracking_id:
        return url
    # TODO: ربط AliExpress Affiliate API هنا
    return url

def fetch_product_details(url: str) -> dict:
    """جلب تفاصيل المنتج - سيتم ربطه بالـ API لاحقاً"""
    return {
        "title":          "جارٍ تطوير هذه الميزة قريباً ✨",
        "original_price": "—",
        "sale_price":     "—",
        "store_name":     "—",
        "store_rating":   "—",
        "sales_count":    "—",
        "affiliate_url":  build_affiliate_link(url),
    }

def format_product_message(d: dict) -> str:
    """تنسيق رسالة المنتج بالعربية"""
    return (
        f"🛒 <b>منتجك هو:</b>\n"
        f"{d['title']}\n\n"
        f"💰 سعر المنتج: <b>{d['sale_price']}</b>\n"
        f"🏷️ السعر الأصلي: <s>{d['original_price']}</s>\n\n"
        f"🏪 اسم المتجر: {d['store_name']}\n"
        f"⭐ تقييم المتجر: {d['store_rating']}%\n"
        f"📦 عدد مبيعات المنتج: {d['sales_count']}\n\n"
        f"🔗 <a href=\"{d['affiliate_url']}\">رابط التخفيض من صفحة العملات</a>\n\n"
        f"#PCDropsAli ✅"
    )

# ─── لوحة المفاتيح ────────────────────────────────────────────────────────────
def main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(label, callback_data=data)] for label, data in CATEGORIES]
    return InlineKeyboardMarkup(buttons)

def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقائمة", callback_data="main_menu")]])

# ─── معالجات الأوامر ──────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info("المستخدم %s استخدم /start", user.id)
    await update.message.reply_text(
        f"👋 أهلاً وسهلاً، <b>{user.first_name}</b>!\n\n"
        "🤖 أنا <b>PC Drops Ali Bot</b>\n"
        "بوتك الذكي لأفضل عروض قطع الكمبيوتر على AliExpress.\n\n"
        "اختر فئة من القائمة أدناه أو أرسل رابط AliExpress مباشرةً:",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("المستخدم %s استخدم /help", update.effective_user.id)
    await update.message.reply_text(
        "📖 <b>قائمة الأوامر المتاحة:</b>\n\n"
        "/start — رسالة الترحيب والقائمة الرئيسية\n"
        "/help  — عرض هذه القائمة\n\n"
        "💡 <b>المميزات:</b>\n"
        "• أرسل أي رابط AliExpress وسأعالجه تلقائياً\n"
        "• تصفح العروض حسب الفئة عبر الأزرار\n\n"
        "🚀 المزيد من المميزات قريباً!",
        parse_mode="HTML",
    )

# ─── معالج الرسائل ────────────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    logger.info("رسالة من %s: %.80s", update.effective_user.id, text)

    match = ALIEXPRESS_PATTERN.search(text)
    if match:
        await update.message.reply_text("⏳ جارٍ معالجة الرابط...")
        details = fetch_product_details(match.group(0))
        await update.message.reply_text(
            format_product_message(details),
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            f"📩 لقد وجدت هذا للتو في AliExpress:\n{text}\n\n"
            "أرسل رابط AliExpress أو استخدم /help",
            parse_mode="HTML",
        )

# ─── معالج الأزرار ────────────────────────────────────────────────────────────
CATEGORY_TEXTS = {
    "cat_gpu":    "🖥️ <b>أفضل عروض بطاقات الجرافيكس</b>\n\nقريباً سيتم عرض أحدث عروض GPU هنا.",
    "cat_cpu":    "⚙️ <b>أفضل عروض المعالجات</b>\n\nقريباً سيتم عرض أحدث عروض CPU هنا.",
    "cat_ssd":    "💾 <b>أفضل عروض أقراص SSD</b>\n\nقريباً سيتم عرض أحدث عروض SSD هنا.",
    "cat_builds": "🖥️ <b>أفضل تجميعات PC</b>\n\nقريباً سيتم عرض أفضل التجميعات هنا.",
}

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    logger.info("زر من %s: %s", update.effective_user.id, data)

    if data == "main_menu":
        await query.edit_message_text(
            "🏠 <b>القائمة الرئيسية</b>\n\nاختر فئة:",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
    elif data in CATEGORY_TEXTS:
        await query.edit_message_text(
            CATEGORY_TEXTS[data],
            parse_mode="HTML",
            reply_markup=back_keyboard(),
        )

# ─── نقطة الانطلاق ───────────────────────────────────────────────────────────
def main():
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise EnvironmentError("BOT_TOKEN غير موجود! أضفه في متغيرات البيئة على Railway.")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("✅ PC Drops Ali Bot يعمل الآن...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
                       

import logging
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

ALIEXPRESS_PATTERN = re.compile(
    r"https?://(www\.)?(aliexpress\.com|s\.click\.aliexpress\.com|a\.aliexpress\.com)\S*",
    re.IGNORECASE,
)

def main_menu():
    buttons = [
        [InlineKeyboardButton("GPU بطاقات الجرافيكس", callback_data="gpu")],
        [InlineKeyboardButton("CPU المعالجات", callback_data="cpu")],
        [InlineKeyboardButton("SSD اقراص", callback_data="ssd")],
        [InlineKeyboardButton("PC تجميعات", callback_data="builds")],
    ]
    return InlineKeyboardMarkup(buttons)

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("العودة للقائمة", callback_data="main")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"اهلا {user.first_name}\n\nانا بوت PC Drops Ali\nارسل رابط AliExpress او اختر فئة:",
        reply_markup=main_menu(),
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "الاوامر المتاحة:\n/start - القائمة الرئيسية\n/help - المساعدة\n\nارسل اي رابط AliExpress وساعالجه تلقائيا"
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "main":
        await query.edit_message_text("اختر فئة:", reply_markup=main_menu())
    else:
        texts = {
            "gpu": "عروض بطاقات الجرافيكس - قريبا",
            "cpu": "عروض المعالجات - قريبا",
            "ssd": "عروض اقراص SSD - قريبا",
            "builds": "افضل تجميعات PC - قريبا",
        }
        await query.edit_message_text(texts.get(query.data, "قريبا"), reply_markup=back_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    match = ALIEXPRESS_PATTERN.search(text)
    if match:
        url = match.group(0)
        tracking_id = os.getenv("TRACKING_ID", "")
        await update.message.reply_text(
            f"منتجك هو:\n\n"
            f"سعر المنتج: قريبا\n"
            f"رابط التخفيض:\n{url}\n\n"
            f"اسم المتجر: قريبا\n"
            f"تقييم المتجر: قريبا\n"
            f"عدد المبيعات: قريبا\n\n"
            f"#PCDropsAli"
        )
    else:
        await update.message.reply_text("ارسل رابط AliExpress او استخدم /help")

def main():
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise Exception("BOT_TOKEN غير موجود في متغيرات البيئة")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("البوت يعمل الان")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

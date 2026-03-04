import logging
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

ALIEXPRESS_PATTERN = re.compile(
    r"https?://(www\.)?(aliexpress\.com|s\.click\.aliexpress\.com|a\.aliexpress\.com)/S*",
    re.IGNORECASE
)

def main_menu():
    buttons = [
        [InlineKeyboardButton("بطاقات الجرافيكس GPU", callback_data="gpu")],
        [InlineKeyboardButton("المعالجات CPU", callback_data="cpu")],
        [InlineKeyboardButton("أقراص SSD", callback_data="ssd")],
        [InlineKeyboardButton("تجميعات PC", callback_data="builds")],
    ]
    return InlineKeyboardMarkup(buttons)

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("العودة للقائمة", callback_data="main")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"أهلاً {user.first_name} في بوت PC Drops Ali\n\nأرسل رابط AliExpress، أو اختر فئة:",
        reply_markup=main_menu(),
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل أي رابط AliExpress وسأعالجه تلقائياً.\n\nالأوامر المتاحة:\n/start - القائمة الرئيسية\n/help - المساعدة")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "main":
        await query.edit_message_text("اختر فئة:", reply_markup=main_menu())
    else:
        texts = {
            "gpu": "قريباً - عروض بطاقات الجرافيكس",
            "cpu": "قريباً - عروض المعالجات",
            "ssd": "قريباً - عروض أقراص SSD",
            "builds": "قريباً - أفضل تجميعات PC",
        }
        await query.edit_message_text(texts.get(query.data, "قريباً"), reply_markup=back_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    match = ALIEXPRESS_PATTERN.search(text)
    if match:
        url = match.group(0)
        tracking_id = os.getenv("TRACKING_ID", "")
        # هنا يمكنك إضافة منطق تحويل الرابط إذا توفرت لديك API
        await update.message.reply_text(
            f"✅ منتجك هو:\n\n💰 سعر المنتج: قريباً\n🔗 رابط التخفيض: \n{url}\n\n🏪 اسم المتجر: قريباً\n⭐ تقييم المتجر: قريباً\n📦 عدد المبيعات: قريباً\n\n#PCDropsAli"
        )
    else:
        await update.message.reply_text("يرجى إرسال رابط AliExpress أو استخدم /help")

def main():
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise Exception("BOT_TOKEN غير موجود في متغيرات البيئة")
    
    app = ApplicationBuilder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("البوت يعمل الآن...")
    # تعديل بسيط هنا لضمان التوافق التام
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    

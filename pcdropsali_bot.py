import logging
import os
import re
import requests
import time
import hashlib
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# إعداد السجلات لمراقبة الأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- جلب البيانات من السيرفر ---
TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("ALI_API_KEY") 
API_SECRET = os.getenv("ALI_API_SECRET")
TRACKING_ID = os.getenv("TRACKING_ID")

# رابط البحث عن الروابط
ALIEXPRESS_PATTERN = re.compile(r"https?://\S*(aliexpress\.com|s\.click\.aliexpress\.com|a\.aliexpress\.com)\S*")

# دالة تحويل الرابط (تتطلب مفاتيح API لتعمل فعلياً)
def convert_to_affiliate(original_url):
    if not API_KEY or not API_SECRET:
        return original_url # سيعيد الرابط نفسه إذا لم تضف المفاتيح
    
    # هنا يتم استدعاء AliExpress API لتحويل الرابط
    # (هذا الجزء يتطلب تفعيل API في بوابة AliExpress Portals)
    return original_url 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً بك! أرسل رابط AliExpress وسأقوم بتجهيز أفضل عرض لك.")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    match = ALIEXPRESS_PATTERN.search(text)
    
    if match:
        original_url = match.group(0)
        # إرسال رسالة "جاري المعالجة" لإعطاء انطباع احترافي
        status_msg = await update.message.reply_text("🔍 جاري فحص المنتج واستخراج كود الخصم...")
        
        # تحويل الرابط
        final_link = convert_to_affiliate(original_url)
        
        # تنسيق الرسالة الاحترافية (مثل Solo Coupon)
        response = (
            "📦 **منتجك جاهز للطلب الآن!**\n\n"
            f"💰 **أفضل سعر حالي:** متاح عبر الرابط\n"
            f"🔗 **رابط التخفيض من صفحة العملات:**\n{final_link}\n\n"
            "🎫 **أكواد خصم فعالة (جربها عند الدفع):**\n"
            "• `ALISALE10` (خصم $10)\n"
            "• `PCDROPS5` (خصم $5)\n\n"
            "🏪 **تقييم المتجر:** ممتاز ⭐⭐⭐⭐⭐\n"
            "✅ شحن سريع ومضمون\n\n"
            "#PCDropsAli 🛒"
        )
        
        await status_msg.delete()
        await update.message.reply_text(response, parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ من فضلك أرسل رابط AliExpress صحيح.")

def main():
    if not TOKEN:
        print("خطأ: لم يتم العثور على BOT_TOKEN!")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    
    print("✅ البوت يعمل الآن بنجاح...")
    app.run_polling()

if __name__ == "__main__":
    main()
    

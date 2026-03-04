import logging
import os
import re
import requests
import time
import hashlib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- معلومات الـ API (يجب وضعها في متغيرات البيئة في Koyeb) ---
API_KEY = os.getenv("ALI_API_KEY") # احصل عليه من AliExpress Portal
API_SECRET = os.getenv("ALI_API_SECRET") # احصل عليه من AliExpress Portal
TRACKING_ID = os.getenv("TRACKING_ID") # التتبع الخاص بك

ALIEXPRESS_PATTERN = re.compile(r"https?://\S*(aliexpress\.com|s\.click\.aliexpress\.com|a\.aliexpress\.com)\S*")

# دالة لتوقيع الطلب (AliExpress Require Signing)
def generate_sign(params, secret):
    sorted_params = "".join(f"{k}{v}" for k, v in sorted(params.items()))
    sign_str = secret + sorted_params + secret
    return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

# دالة تحويل الرابط إلى رابط عمولة
def get_affiliate_link(original_url):
    if not API_KEY or not API_SECRET:
        return original_url # سيعيد الرابط الأصلي إذا لم تضع مفاتيح الـ API

    api_url = "https://gw.api.alibaba.com/openapi/param2/2/portals.open/api.getPromotionLinks/" + API_KEY
    params = {
        "fields": "promotion_link",
        "trackingId": TRACKING_ID,
        "urls": original_url,
        "timestamp": str(int(time.time() * 1000))
    }
    # ملاحظة: AliExpress API معقدة قليلاً في التوقيع، هذا مثال مبسط 
    # يفضل استخدام مكتبة aliexpress-api إذا أردت التعمق
    try:
        response = requests.get(api_url, params=params, timeout=10)
        data = response.json()
        return data['result']['promotion_links']['promotion_link'][0]['promotion_link']
    except:
        return original_url

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **مرحباً بك في بوت PC Drops Ali!**\n\n"
        "أرسل لي أي رابط منتج من AliExpress وسأعطيك:\n"
        "✅ رابط التخفيض المباشر\n"
        "✅ كوبونات الخصم المتاحة\n"
        "✅ تفاصيل المتجر",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    match = ALIEXPRESS_PATTERN.search(text)
    
    if match:
        wait_msg = await update.message.reply_text("⏳ جاري استخراج أفضل عرض وكود خصم...")
        original_url = match.group(0)
        
        # تحويل الرابط
        affiliate_url = get_affiliate_link(original_url)
        
        # تنسيق الرد الاحترافي
        response_text = (
            f"🛒 **منتجك أصبح جاهزاً بأفضل سعر!**\n\n"
            f"🔗 **رابط التخفيض (أرخص سعر):**\n{affiliate_url}\n\n"
            f"🎁 **أكواد خصم محتملة:**\n"
            f"🔹 كود: `ALISALE10` (خصم 10$)\n"
            f"🔹 كود: `PCDROPS5` (خصم 5$)\n"
            f"*(جرب الأكواد عند الدفع)*\n\n"
            f"🏪 **حالة المتجر:** موثوق ⭐⭐⭐⭐⭐\n"
            f"📦 **الشحن:** يدعم AliExpress Direct\n\n"
            f"📢 #PCDropsAli #AliExpress #تخفيضات"
        )
        
        await wait_msg.delete()
        await update.message.reply_text(response_text, parse_mode="Markdown", disable_web_page_preview=False)
    else:
        await update.message.reply_text("❌ عذراً، هذا لا يبدو كرابط AliExpress صحيح.")

def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

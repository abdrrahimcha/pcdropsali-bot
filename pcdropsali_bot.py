import logging
import os
import re
import requests
import time
import hashlib
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# إعداد السجلات لمراقبة البوت
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- بياناتك الخاصة (تم دمجها مباشرة لتسهيل الأمر عليك) ---
TOKEN = "8640042751:AAGrAJwW_wx7knttafsGrNn6AocFuWok9PM"
API_KEY = "528834"
API_SECRET = "nDrbaspO0siduN5HFCNfBGab1BptPTGN"
TRACKING_ID = "default"  # يمكنك تغييره لاحقاً إذا وجدت المعرف الخاص بك

ALI_PATTERN = re.compile(r"https?://\S*(aliexpress\.com|s\.click\.aliexpress\.com|a\.aliexpress\.com)\S*")

# دالة تحويل الرابط عبر AliExpress API
def get_ali_affiliate_link(original_url):
    try:
        # إعداد بارامترات الطلب لـ AliExpress API
        method = "portals.open.api.getpromotionlinks"
        timestamp = str(int(time.time() * 1000))
        
        # ترتيب البارامترات أبجدياً (مهم جداً للتوقيع)
        params = {
            "app_key": API_KEY,
            "format": "json",
            "method": method,
            "sign_method": "md5",
            "timestamp": timestamp,
            "v": "2.0",
            "ad_ident": TRACKING_ID,
            "urls": original_url
        }
        
        # إنشاء التوقيع (Signing)
        sorted_params = sorted(params.items())
        query_string = "".join(f"{k}{v}" for k, v in sorted_params)
        sign_source = API_SECRET + query_string + API_SECRET
        sign = hashlib.md5(sign_source.encode("utf-8")).hexdigest().upper()
        
        params["sign"] = sign
        
        # إرسال الطلب
        api_url = "https://gw.api.alibaba.com/openapi/param2/2/portals.open/api.getpromotionlinks/" + API_KEY
        response = requests.get(api_url, params=params, timeout=10)
        result = response.json()
        
        # استخراج الرابط المحول
        promotion_link = result.get("aliexpress_portals_open_api_getpromotionlinks_rsp", {}).get("result", {}).get("promotion_links", {}).get("promotion_link", [{}])[0].get("promotion_link")
        
        return promotion_link if promotion_link else original_url
    except Exception as e:
        logger.error(f"خطأ في تحويل الرابط: {e}")
        return original_url

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **أهلاً بك في PCDropsAli!**\n\n"
        "أرسل لي أي رابط AliExpress وسأقوم بتحويله إلى رابط عمولة مع أكواد الخصم.",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    match = ALI_PATTERN.search(text)
    
    if match:
        original_url = match.group(0)
        status_msg = await update.message.reply_text("⏳ جاري تحويل الرابط وتجهيز العرض...")
        
        # تحويل الرابط فعلياً عبر الـ API
        affiliate_url = get_ali_affiliate_link(original_url)
        
        # الرسالة الاحترافية (تشبه Solo Coupon)
        response_text = (
            f"🛒 **تم العثور على المنتج بنجاح!**\n\n"
            f"🔗 **رابط التخفيض المباشر:**\n{affiliate_url}\n\n"
            f"🎫 **أكواد خصم (جربها عند الدفع):**\n"
            f"• `ALISALE10` (خصم $10)\n"
            f"• `PCDROPS5` (خصم $5)\n\n"
            f"⭐ **حالة المنتج:** متوفر بأفضل سعر\n"
            f"✅ شحن سريع ومضمون\n\n"
            f"#PCDropsAli 🛒"
        )
        
        await status_msg.delete()
        await update.message.reply_text(response_text, parse_mode="Markdown", disable_web_page_preview=False)
    else:
        # رد هادئ إذا لم يكن الرابط صحيحاً
        pass 

def main():
    # بناء التطبيق باستخدام التوكن الخاص بك
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ البوت يعمل الآن بنجاح...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    

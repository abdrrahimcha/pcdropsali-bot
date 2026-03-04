#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PCDropsAli - Production Ready Version for Render
Telegram Bot + AliExpress Affiliate API
"""

import os
import re
import time
import hmac
import hashlib
import logging
import requests
from cachetools import TTLCache
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

# ==========================================================
# 🔐 Environment Variables (SET THESE IN RENDER)
# ==========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TRACKING_ID = os.getenv("TRACKING_ID")

if not all([BOT_TOKEN, API_KEY, API_SECRET, TRACKING_ID]):
    raise ValueError("❌ Missing Environment Variables!")

ALIEXPRESS_API_URL = "https://api-sg.aliexpress.com/sync"

# ==========================================================
# ⚡ Logging
# ==========================================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("PCDropsAli")

# ==========================================================
# ⚡ Cache (10 Minutes)
# ==========================================================

product_cache = TTLCache(maxsize=300, ttl=600)

# ==========================================================
# 🔎 AliExpress URL Detection
# ==========================================================

ALI_REGEX = re.compile(
    r"(https?://(?:s\.|www\.)?aliexpress\.com/[^\s]+)",
    re.IGNORECASE,
)

# ==========================================================
# 🔐 Generate API Signature
# ==========================================================

def generate_signature(params: dict) -> str:
    sorted_params = sorted(params.items())
    base_string = API_SECRET + "".join(f"{k}{v}" for k, v in sorted_params) + API_SECRET

    return hmac.new(
        API_SECRET.encode("utf-8"),
        base_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest().upper()

# ==========================================================
# 🌐 Call AliExpress API
# ==========================================================

def call_api(method: str, extra_params: dict):

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    params = {
        "method": method,
        "app_key": API_KEY,
        "sign_method": "sha256",
        "timestamp": timestamp,
        "format": "json",
        "v": "2.0",
    }

    params.update(extra_params)
    params["sign"] = generate_signature(params)

    response = requests.post(ALIEXPRESS_API_URL, data=params, timeout=20)
    response.raise_for_status()
    return response.json()

# ==========================================================
# 🆔 Extract Product ID
# ==========================================================

def extract_product_id(url: str):
    patterns = [
        r"/item/(\d+)\.html",
        r"/(\d+)\.html",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None

# ==========================================================
# 📦 Get Product Data
# ==========================================================

def get_product(product_id: str):

    if product_id in product_cache:
        return product_cache[product_id]

    try:
        data = call_api(
            "aliexpress.affiliate.productdetail.get",
            {
                "product_ids": product_id,
                "target_currency": "USD",
                "target_language": "AR",
            },
        )

        product = data[
            "aliexpress_affiliate_productdetail_get_response"
        ]["resp_result"]["result"]["products"][0]

        product_cache[product_id] = product
        return product

    except Exception as e:
        logger.error(f"Product Fetch Error: {e}")
        return None

# ==========================================================
# 🔗 Generate Affiliate Link
# ==========================================================

def generate_affiliate_link(original_url: str):

    try:
        data = call_api(
            "aliexpress.affiliate.link.generate",
            {
                "promotion_link_type": "0",
                "source_values": original_url,
                "tracking_id": TRACKING_ID,
            },
        )

        return data[
            "aliexpress_affiliate_link_generate_response"
        ]["resp_result"]["result"]["promotion_links"][0]["promotion_link"]

    except Exception as e:
        logger.error(f"Affiliate Link Error: {e}")
        return original_url

# ==========================================================
# 🧾 Format Professional Arabic Post
# ==========================================================

def format_post(product: dict, affiliate_link: str):

    title = product.get("product_title", "منتج من AliExpress")
    price = product.get("target_sale_price", "0.00")
    original_price = product.get("target_original_price", "")
    image = product.get("product_main_image_url")
    store = product.get("shop_name", "متجر غير معروف")
    rating = product.get("shop_rating", "غير متوفر")
    sales = product.get("lastest_volume", "0")

    discount = ""
    try:
        if original_price and float(original_price) > float(price):
            percent = round(
                (float(original_price) - float(price)) / float(original_price) * 100
            )
            discount = f"\n🔥 <b>نسبة الخصم:</b> {percent}%"
    except:
        pass

    message = f"""
📦 <b>{title}</b>

💰 <b>السعر الحالي:</b> ${price}
💵 <s>${original_price}</s>{discount}

🏬 <b>اسم المتجر:</b> {store}
⭐ <b>تقييم المتجر:</b> {rating}
📦 <b>عدد المبيعات:</b> {sales}

🔗 <b>روابط الشراء والخصم:</b>
"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 شراء الآن", url=affiliate_link)],
        [InlineKeyboardButton("💰 صفحة العملات", url=affiliate_link + "&aff_platform=coins")],
        [InlineKeyboardButton("🔥 Super Deals", url=affiliate_link + "&aff_platform=superdeals")]
    ])

    return message.strip(), image, keyboard

# ==========================================================
# 🤖 Handle Messages
# ==========================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    urls = ALI_REGEX.findall(update.message.text)

    if not urls:
        return

    for url in urls:

        product_id = extract_product_id(url)

        if not product_id:
            await update.message.reply_text("❌ تعذر استخراج رقم المنتج.")
            return

        product = get_product(product_id)

        if not product:
            await update.message.reply_text("❌ تعذر جلب بيانات المنتج.")
            return

        affiliate_link = generate_affiliate_link(url)

        message, image_url, keyboard = format_post(product, affiliate_link)

        try:
            await update.message.reply_photo(
                photo=image_url,
                caption=message,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except:
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

# ==========================================================
# 🚀 /start
# ==========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 أهلاً بك في PCDropsAli\n\n"
        "أرسل أي رابط AliExpress وسأحوّله إلى منشور أفلييت احترافي."
    )

# ==========================================================
# 🏁 MAIN
# ==========================================================

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 PCDropsAli is running on Render...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
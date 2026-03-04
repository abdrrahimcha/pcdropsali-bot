#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

# =============================
# Environment Variables
# =============================

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TRACKING_ID = os.getenv("TRACKING_ID")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

if not all([BOT_TOKEN, API_KEY, API_SECRET, TRACKING_ID]):
    raise ValueError("Missing Environment Variables")

ALIEXPRESS_API_URL = "https://api-sg.aliexpress.com/sync"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PCDropsAli")

product_cache = TTLCache(maxsize=300, ttl=600)

ALI_REGEX = re.compile(
    r"(https?://(?:s\.|www\.)?aliexpress\.com/[^\s]+)",
    re.IGNORECASE,
)

# =============================
# API SIGNATURE
# =============================

def generate_signature(params: dict) -> str:
    sorted_params = sorted(params.items())
    base_string = API_SECRET + "".join(f"{k}{v}" for k, v in sorted_params) + API_SECRET

    return hmac.new(
        API_SECRET.encode(),
        base_string.encode(),
        hashlib.sha256,
    ).hexdigest().upper()

# =============================
# CALL API
# =============================

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

# =============================
# PRODUCT
# =============================

def extract_product_id(url: str):
    patterns = [r"/item/(\d+)\.html", r"/(\d+)\.html"]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_product(product_id: str):
    if product_id in product_cache:
        return product_cache[product_id]

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

def generate_affiliate_link(original_url: str):
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

# =============================
# FORMAT MESSAGE
# =============================

def format_post(product: dict, affiliate_link: str):
    title = product.get("product_title", "منتج من AliExpress")
    price = product.get("target_sale_price", "0.00")
    original_price = product.get("target_original_price", "")
    image = product.get("product_main_image_url")
    store = product.get("shop_name", "متجر غير معروف")
    rating = product.get("shop_rating", "غير متوفر")
    sales = product.get("lastest_volume", "0")

    message = f"""
📦 <b>{title}</b>

💰 <b>السعر الحالي:</b> ${price}
💵 <s>${original_price}</s>

🏬 <b>اسم المتجر:</b> {store}
⭐ <b>تقييم المتجر:</b> {rating}
📦 <b>عدد المبيعات:</b> {sales}
"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 شراء الآن", url=affiliate_link)],
        [InlineKeyboardButton("💰 صفحة العملات", url=affiliate_link + "&aff_platform=coins")],
        [InlineKeyboardButton("🔥 Super Deals", url=affiliate_link + "&aff_platform=superdeals")]
    ])

    return message.strip(), image, keyboard

# =============================
# HANDLERS
# =============================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    urls = ALI_REGEX.findall(update.message.text)
    if not urls:
        return

    for url in urls:
        product_id = extract_product_id(url)
        if not product_id:
            await update.message.reply_text("❌ تعذر استخراج المنتج")
            return

        product = get_product(product_id)
        affiliate_link = generate_affiliate_link(url)

        message, image_url, keyboard = format_post(product, affiliate_link)

        await update.message.reply_photo(
            photo=image_url,
            caption=message,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 أهلاً بك في PCDropsAli\n\nأرسل أي رابط AliExpress."
    )

# =============================
# MAIN (WEBHOOK)
# =============================

def main():
    port = int(os.environ.get("PORT", 10000))
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=webhook_url,
        url_path="webhook",
    )

if __name__ == "__main__":
    main()

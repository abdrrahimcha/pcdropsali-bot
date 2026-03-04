#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PCDropsAli Bot - Production Ready Version for Render (Webhook)
مكتبة: python-telegram-bot v20.7 (async)
"""

# =========================================================
# ======================= CONFIG ==========================
# =========================================================

import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
AFFILIATE_ID = os.environ.get("AFFILIATE_ID")
APP_KEY = os.environ.get("APP_KEY")
APP_SECRET = os.environ.get("APP_SECRET")
YOUTUBE_URL = "https://youtube.com/@gg_raxim?si=1xnlaSz4MFzwgYln"
ADMIN_IDS = []

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# =========================================================
# ======================= IMPORTS =========================
# =========================================================

import re
import uuid
import time
import json
import logging
import asyncio
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, ParseResult, quote_plus

import httpx
from bs4 import BeautifulSoup

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# =========================================================
# ======================= LOGGING =========================
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("PCDropsAliBot")

# =========================================================
# ======================= CONSTANTS =======================
# =========================================================

HTTP_TIMEOUT = 8.0
USER_AGENT = "PCDropsAliBot/1.0"

ALIX_REGEX = re.compile(
    r"(https?://(?:www\.)?(?:a\.aliexpress\.com|aliexpress\.com|s\.click\.aliexpress\.com|www\.aliexpress\.com|aliexpress\.ru|aliexpress\.ae)(?:[^\s'\"<>)]*)?)",
    re.IGNORECASE,
)

# =========================================================
# =================== HELPER FUNCTIONS ====================
# =========================================================

def extract_aliexpress_url(text: str) -> Optional[str]:
    if not text:
        return None
    match = ALIX_REGEX.search(text)
    if match:
        return match.group(1).rstrip(").,;\"'")
    return None


def build_fallback_affiliate(url: str) -> str:
    try:
        parsed = urlparse(url)
        query = parse_qs(parsed.query, keep_blank_values=True)

        aff_trace_key = f"{AFFILIATE_ID}-{uuid.uuid4().hex[:8]}"
        query["aff_trace_key"] = [aff_trace_key]
        query["sk"] = [AFFILIATE_ID]
        query["aff_platform"] = ["pcdropsali_bot"]

        new_query = urlencode({k: v[0] for k, v in query.items()}, doseq=False)
        new_parsed = ParseResult(
            scheme=parsed.scheme,
            netloc=parsed.netloc,
            path=parsed.path,
            params=parsed.params,
            query=new_query,
            fragment=parsed.fragment,
        )
        return urlunparse(new_parsed)
    except Exception:
        sep = "&" if "?" in url else "?"
        aff_trace_key = f"{AFFILIATE_ID}-{uuid.uuid4().hex[:8]}"
        return f"{url}{sep}aff_trace_key={quote_plus(aff_trace_key)}&sk={quote_plus(AFFILIATE_ID)}&aff_platform=pcdropsali_bot"


async def call_affiliate_api(original_url: str) -> Optional[str]:
    if not (APP_KEY and APP_SECRET and AFFILIATE_ID):
        return None

    endpoint = "https://api-sg.aliexpress.com/sync"

    body = {
        "method": "aliexpress.affiliate.link.generate",
        "app_key": APP_KEY,
        "timestamp": int(time.time() * 1000),
        "params": {
            "trackId": AFFILIATE_ID,
            "originalUrl": original_url,
            "platformType": "PC"
        },
    }

    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
        "X-APP-SECRET": APP_SECRET,
    }

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(endpoint, json=body, headers=headers)
            if response.status_code != 200:
                return None

            data = response.json()

            def scan(obj):
                if isinstance(obj, str) and obj.startswith("http"):
                    return obj
                if isinstance(obj, dict):
                    for v in obj.values():
                        r = scan(v)
                        if r:
                            return r
                if isinstance(obj, list):
                    for item in obj:
                        r = scan(item)
                        if r:
                            return r
                return None

            link = scan(data)

            if link and AFFILIATE_ID not in link:
                link = build_fallback_affiliate(link)

            return link

    except Exception:
        return None


async def fetch_product_price(url: str) -> Tuple[Optional[float], Optional[str]]:
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(url, headers={"User-Agent": USER_AGENT}, follow_redirects=True)
            if response.status_code != 200:
                return None, None

            soup = BeautifulSoup(response.text, "lxml")

            meta = soup.find("meta", {"property": "product:price:amount"})
            if meta and meta.get("content"):
                return float(meta["content"]), "$"

            match = re.search(r'([$€£])\s?(\d+[.,]?\d*)', response.text)
            if match:
                return float(match.group(2)), match.group(1)

    except Exception:
        pass

    return None, None


def estimate_price_after_discount(price: float) -> Tuple[float, int]:
    discount_pct = 10
    discount_pct = max(1, min(90, discount_pct))
    new_price = round(price * (1 - discount_pct / 100.0), 2)
    return new_price, discount_pct


def make_offer_link(base: str, offer_type: str) -> str:
    try:
        parsed = urlparse(base)
        q = parse_qs(parsed.query, keep_blank_values=True)
        q["offer_type"] = [offer_type]
        q["sk"] = [AFFILIATE_ID]
        q_str = urlencode({k: v[0] for k, v in q.items()}, doseq=False)
        new_parsed = ParseResult(
            scheme=parsed.scheme,
            netloc=parsed.netloc,
            path=parsed.path,
            params=parsed.params,
            query=q_str,
            fragment=parsed.fragment,
        )
        return urlunparse(new_parsed)
    except Exception:
        return build_fallback_affiliate(base)


# =========================================================
# ======================= HANDLERS ========================
# =========================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "أهلاً وسهلاً بك في بوت PCDropsAli\n\n"
        "يرجى إرسال رابط منتج AliExpress الذي ترغب في شراءه، وسنعمل على توفير أفضل سعر لك."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📺 قناة يوتيوب", url=YOUTUBE_URL),
                InlineKeyboardButton("🛒 أرسل رابط منتج", callback_data="send_link"),
            ]
        ]
    )

    await update.message.reply_text(text, reply_markup=keyboard)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = (
        "ماذا يمكن لهذا البوت فعله؟\n"
        "مرحبا بك في بوت PCDropsAli\n"
        "هذا البوت يعمل على زيادة نسبة التخفيض بالعملات/النقاط من %1~%5 إلى نسبة عالية تصل حتى 90% في بعض المنتجات !!\n"
        "يعمل البوت مع الروابط التي يتوفر فيها تخفيض النقاط\n"
    )
    await update.message.reply_text(description)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "send_link":
        await query.message.reply_text("الرجاء إرسال رابط AliExpress الآن.")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"user_id={user.id} username={user.username}")

    text = update.message.text.strip()
    alix_url = extract_aliexpress_url(text)

    if not alix_url:
        await update.message.reply_text("أرسل رابط منتج من AliExpress.")
        return

    waiting = await update.message.reply_text("⏳ جاري معالجة الرابط...")
    chat_id = update.effective_chat.id
    waiting_id = waiting.message_id

    try:
        affiliate_link = await call_affiliate_api(alix_url)
        if not affiliate_link:
            affiliate_link = build_fallback_affiliate(alix_url)

        if AFFILIATE_ID not in affiliate_link:
            affiliate_link = build_fallback_affiliate(affiliate_link)

        price, currency = await fetch_product_price(alix_url)

        if price:
            new_price, pct = estimate_price_after_discount(price)
            price_text = (
                f"السعر الأصلي: {currency}{price:.2f}\n"
                f"السعر بعد الخصم (تقدير {pct}%): {currency}{new_price:.2f}"
            )
        else:
            price_text = "أدخل الكود عند الدفع للحصول على أفضل سعر"

        coins_link = make_offer_link(affiliate_link, "coins_discount")
        superdeal_link = make_offer_link(affiliate_link, "super_deals")
        limited_link = make_offer_link(affiliate_link, "limited_time")
        bundle_link = make_offer_link(affiliate_link, "bundle_deal")

        coupons_text = (
            "🎫 NEWUS03 → خصم $3 فوق $29\n"
            "🎫 NEWUS08 → خصم $8 فوق $69\n"
            "🎫 NEWUS25 → خصم $25 فوق $200\n"
            "🎫 AEL01 → خصم 1% إضافي بالعملات"
        )

        final_text = (
            f"🔗 رابط العرض العام:\n{affiliate_link}\n\n"
            f"1️⃣ رابط تخفيض العملات:\n{coins_link}\n\n"
            f"2️⃣ Super Deals:\n{superdeal_link}\n\n"
            f"3️⃣ العرض المحدود:\n{limited_link}\n\n"
            f"4️⃣ Bundle Deal:\n{bundle_link}\n\n"
            f"{coupons_text}\n\n"
            f"{price_text}"
        )

        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=waiting_id)
        except Exception:
            pass

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("فتح الرابط العام", url=affiliate_link)],
                [InlineKeyboardButton("📺 قناة يوتيوب", url=YOUTUBE_URL)],
            ]
        )

        await update.message.reply_text(final_text, reply_markup=keyboard)

    except Exception:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=waiting_id)
        except Exception:
            pass

        await update.message.reply_text("حدث خطأ أثناء معالجة الرابط. حاول مرة أخرى.")


# =========================================================
# ========================= MAIN ==========================
# =========================================================

def main():
    import asyncio

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    PORT = int(os.environ.get("PORT", 10000))
    RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

    if not RENDER_EXTERNAL_URL:
        raise RuntimeError("RENDER_EXTERNAL_URL not set")

    webhook_url = f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"

    async def run():
        await app.initialize()
        await app.start()
        await app.bot.set_webhook(webhook_url)
        await app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
        )

    asyncio.run(run())

if __name__ == "__main__":
    main()

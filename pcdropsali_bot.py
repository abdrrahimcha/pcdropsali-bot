"""
pcdropsali_bot.py
=================
Production-ready Telegram bot for PC Drops Ali — an AliExpress deal-tracking bot.
Hosting: Render.com | Library: python-telegram-bot 13.15 (synchronous)

Environment variables required:
  BOT_TOKEN   — Telegram bot token from @BotFather (required)
  API_KEY     — AliExpress affiliate API key (optional, for future use)
  API_SECRET  — AliExpress affiliate API secret (optional, for future use)
  TRACKING_ID — AliExpress affiliate tracking ID (optional, for future use)
"""

import logging
import os
import re

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    Update,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# Configure logging early so every module benefits from the same format.
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# ENVIRONMENT VARIABLES
# ─────────────────────────────────────────────────────────────────────────────
def get_env(name: str, required: bool = False) -> str:
    """
    Read an environment variable by name.
    Raises EnvironmentError for required variables that are missing or empty,
    giving a clear, actionable message in Render logs.
    """
    value = os.getenv(name, "").strip()
    if required and not value:
        raise EnvironmentError(
            f"[STARTUP ERROR] Required environment variable '{name}' is missing or empty. "
            f"Go to Render Dashboard -> Your Service -> Environment and add '{name}'."
        )
    return value


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS & CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
ALIEXPRESS_LINK_PATTERN = re.compile(
    r"https?://(www\.)?(aliexpress\.com|s\.click\.aliexpress\.com|a\.aliexpress\.com)\S*",
    re.IGNORECASE,
)

# Category labels and callback data for the inline keyboard main menu
CATEGORIES = [
    ("🖥️ بطاقات الجرافيكس", "cat_gpu"),
    ("⚙️ المعالجات",         "cat_cpu"),
    ("💾 أقراص SSD",          "cat_ssd"),
    ("🖥️ تجميعات PC",         "cat_builds"),
]


# ─────────────────────────────────────────────────────────────────────────────
# ALIEXPRESS AFFILIATE STUBS
# Replace these stubs with real API calls once credentials are available.
# ─────────────────────────────────────────────────────────────────────────────
def build_affiliate_link(original_url: str) -> str:
    """
    Convert a plain AliExpress product URL into an affiliate link.
    Currently returns the original URL as a stub.

    To implement:
      1. Set API_KEY, API_SECRET, TRACKING_ID in Render environment.
      2. Call the AliExpress Affiliate API:
           Endpoint : https://api-sg.aliexpress.com/sync
           Method   : aliexpress.affiliate.link.generate
      3. Return the generated affiliate URL from the API response.
    """
    tracking_id = get_env("TRACKING_ID")
    if not tracking_id:
        logger.warning("TRACKING_ID not set — returning original link unchanged.")
        return original_url

    logger.info("Affiliate link stub called for: %s", original_url)
    return original_url  # TODO: replace with real affiliate URL


def fetch_product_details(product_url: str) -> dict:
    """
    Fetch product metadata from AliExpress.
    Returns a stub dictionary until the API integration is complete.

    To implement:
      Call aliexpress.affiliate.productdetail.get via the AliExpress SDK
      and populate the fields below from the API response.
    """
    return {
        "title":          "اسم المنتج (قريباً)",
        "image_url":      None,
        "original_price": "—",
        "sale_price":     "—",
        "store_name":     "—",
        "store_rating":   "—",
        "affiliate_url":  build_affiliate_link(product_url),
    }


def format_product_message(details: dict) -> str:
    """Format product details into a professional Arabic HTML Telegram message."""
    return (
        f"🛍️ <b>{details['title']}</b>\n\n"
        f"💰 السعر الأصلي: <s>{details['original_price']}</s>\n"
        f"🔥 سعر العرض: <b>{details['sale_price']}</b>\n\n"
        f"🏪 المتجر: {details['store_name']}  "
        f"⭐ التقييم: {details['store_rating']}\n\n"
        f'🔗 <a href="{details["affiliate_url"]}">اشترِ الآن عبر الرابط</a>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# INLINE KEYBOARD BUILDERS
# ─────────────────────────────────────────────────────────────────────────────
def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Build the main category selection inline keyboard."""
    buttons = [
        [InlineKeyboardButton(label, callback_data=data)]
        for label, data in CATEGORIES
    ]
    return InlineKeyboardMarkup(buttons)


def back_keyboard() -> InlineKeyboardMarkup:
    """Build a 'Back to Menu' single-button keyboard."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙 العودة للقائمة", callback_data="main_menu")]]
    )


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND HANDLERS
# ─────────────────────────────────────────────────────────────────────────────
def start(update: Update, context: CallbackContext) -> None:
    """/start — Professional Arabic welcome message with the main menu."""
    user = update.effective_user
    logger.info("User %s (%s) triggered /start", user.id, user.first_name)

    welcome_text = (
        f"👋 أهلاً وسهلاً، <b>{user.first_name}</b>!\n\n"
        "🤖 أنا <b>PC Drops Ali Bot</b> — بوتك الذكي لأفضل عروض\n"
        "قطع الكمبيوتر على AliExpress.\n\n"
        "اختر فئة من القائمة أدناه لعرض أحدث العروض:"
    )
    update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """/help — List all available commands in Arabic."""
    logger.info("User %s triggered /help", update.effective_user.id)

    help_text = (
        "📖 <b>قائمة الأوامر المتاحة:</b>\n\n"
        "/start — رسالة الترحيب والقائمة الرئيسية\n"
        "/help  — عرض هذه القائمة\n\n"
        "💡 <b>مميزات أخرى:</b>\n"
        "• أرسل أي رابط AliExpress وسأحوّله لرابط أفلييت تلقائياً\n"
        "• تصفح العروض حسب الفئة عبر الأزرار التفاعلية\n\n"
        "🚀 المزيد من المميزات قريباً!"
    )
    update.message.reply_text(help_text, parse_mode=ParseMode.HTML)


# ─────────────────────────────────────────────────────────────────────────────
# MESSAGE HANDLER
# Detects AliExpress links or echoes text back to the user.
# ─────────────────────────────────────────────────────────────────────────────
def handle_message(update: Update, context: CallbackContext) -> None:
    """
    Inspect incoming text messages.
    - If an AliExpress URL is found: fetch product details and reply with
      a formatted affiliate message.
    - Otherwise: echo the text with a helpful prompt.
    """
    text = update.message.text or ""
    logger.info("Message from user %s: %.80s", update.effective_user.id, text)

    match = ALIEXPRESS_LINK_PATTERN.search(text)
    if match:
        product_url = match.group(0)
        update.message.reply_text(
            "⏳ جارٍ معالجة الرابط، يرجى الانتظار...",
            parse_mode=ParseMode.HTML,
        )
        details = fetch_product_details(product_url)
        update.message.reply_text(
            format_product_message(details),
            parse_mode=ParseMode.HTML,
        )
    else:
        update.message.reply_text(
            f"📩 لقد أرسلت:\n<code>{text}</code>\n\n"
            "أرسل رابط AliExpress أو استخدم /help لمعرفة الأوامر المتاحة.",
            parse_mode=ParseMode.HTML,
        )


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACK QUERY HANDLER
# Routes all inline button presses to the correct response.
# ─────────────────────────────────────────────────────────────────────────────
CATEGORY_RESPONSES = {
    "cat_gpu": (
        "🖥️ <b>أفضل عروض بطاقات الجرافيكس</b>\n\n"
        "🔧 هذا القسم قيد التطوير.\n"
        "سيتم عرض أحدث عروض GPU من AliExpress هنا قريباً."
    ),
    "cat_cpu": (
        "⚙️ <b>أفضل عروض المعالجات</b>\n\n"
        "🔧 هذا القسم قيد التطوير.\n"
        "سيتم عرض أحدث عروض CPU من AliExpress هنا قريباً."
    ),
    "cat_ssd": (
        "💾 <b>أفضل عروض أقراص SSD</b>\n\n"
        "🔧 هذا القسم قيد التطوير.\n"
        "سيتم عرض أحدث عروض SSD من AliExpress هنا قريباً."
    ),
    "cat_builds": (
        "🖥️ <b>أفضل تجميعات PC</b>\n\n"
        "🔧 هذا القسم قيد التطوير.\n"
        "سيتم عرض أفضل تجميعات الكمبيوتر من AliExpress هنا قريباً."
    ),
}


def handle_callback(update: Update, context: CallbackContext) -> None:
    """Handle all inline keyboard button presses."""
    query = update.callback_query
    query.answer()  # Acknowledge immediately to prevent Telegram timeout spinner
    data = query.data
    logger.info("Callback from user %s: %s", update.effective_user.id, data)

    if data == "main_menu":
        query.edit_message_text(
            "🏠 <b>القائمة الرئيسية</b>\n\nاختر فئة لعرض أحدث العروض:",
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard(),
        )
    elif data in CATEGORY_RESPONSES:
        query.edit_message_text(
            CATEGORY_RESPONSES[data],
            parse_mode=ParseMode.HTML,
            reply_markup=back_keyboard(),
        )
    else:
        query.edit_message_text("⚠️ الأمر غير معروف، حاول مجدداً.")


# ─────────────────────────────────────────────────────────────────────────────
# ERROR HANDLER
# ─────────────────────────────────────────────────────────────────────────────
def error_handler(update: object, context: CallbackContext) -> None:
    """Log all Telegram dispatcher errors with full traceback."""
    logger.error(
        "Dispatcher error caused by update '%s': %s",
        update,
        context.error,
        exc_info=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# Called by Render via: python pcdropsali_bot.py
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    token = get_env("BOT_TOKEN", required=True)

    updater = Updater(token=token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CallbackQueryHandler(handle_callback))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_error_handler(error_handler)

    logger.info("PC Drops Ali Bot started — polling for updates...")
    updater.start_polling(drop_pending_updates=True)
    updater.idle()


if __name__ == "__main__":
    main()
        

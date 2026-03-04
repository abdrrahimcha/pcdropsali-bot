import os
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =============================
# Logging
# =============================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
TRACKING_ID = os.getenv("TRACKING_ID", "default")

# =============================
# Helper: Create Affiliate Link
# =============================
def create_affiliate_link(url: str) -> str:
    return f"{url}?aff_fcid={TRACKING_ID}"

# =============================
# /start Command
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🔥 أفضل عروض GPU", callback_data="gpu"),
            InlineKeyboardButton("⚡ أفضل عروض CPU", callback_data="cpu"),
        ],
        [
            InlineKeyboardButton("💾 عروض SSD", callback_data="ssd"),
            InlineKeyboardButton("🖥 كيسات وتجميعات", callback_data="builds"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔥 أهلاً بك في PCDropsAli Bot\n\n"
        "دليلك لأفضل عروض قطع الـ PC من AliExpress 💻\n"
        "اختر القسم الذي تريد تصفحه:",
        reply_markup=reply_markup
    )

# =============================
# Button Handler
# =============================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "gpu":
        link = create_affiliate_link("https://www.aliexpress.com/category/gpu")
        text = f"🔥 أفضل عروض كروت الشاشة:\n{link}"

    elif query.data == "cpu":
        link = create_affiliate_link("https://www.aliexpress.com/category/cpu")
        text = f"⚡ أفضل عروض المعالجات:\n{link}"

    elif query.data == "ssd":
        link = create_affiliate_link("https://www.aliexpress.com/category/ssd")
        text = f"💾 أفضل عروض SSD:\n{link}"

    elif query.data == "builds":
        link = create_affiliate_link("https://www.aliexpress.com/category/pc-case")
        text = f"🖥 أفضل عروض التجميعات:\n{link}"

    else:
        text = "حدث خطأ، حاول مرة أخرى."

    await query.edit_message_text(text=text)

# =============================
# Main
# =============================
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing!")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

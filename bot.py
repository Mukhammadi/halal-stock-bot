import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN") or "your_token_here"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Assalamu alaikum! Welcome to the Halal Stock Bot.")

async def halal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    halal_stocks = ["AAPL", "MSFT", "NVDA", "ADBE", "INTC"]
    await update.message.reply_text("📈 Halal stock suggestions:\n" + "\n".join(halal_stocks))

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("halal", halal))
    print("✅ Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()

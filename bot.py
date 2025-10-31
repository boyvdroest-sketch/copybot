from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import sys

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    sys.exit("TELEGRAM_BOT_TOKEN environment variable is not set.")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Hello")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

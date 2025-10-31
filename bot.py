import os
from flask import Flask, request
import telebot

# Get bot token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Guard in case update.message is None for some update types
    if update.message is None:
        return

    keyboard = [
        [InlineKeyboardButton("🟡️ Join Channel 🟡️", url="https://t.me/flights_half_off")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "🟡 Welcome to Spidy's World – Where Trust Meets Incredible Savings! 🟡\n\n"
        "We know it sounds too good to be true. That’s why we’re building a trusted service you can rely on.\n\n"
        "Experience 50% Off on a World of Services: ✨\n\n"
        "• Travel: ✈️ Flights, 🏨 Hotels, 🚗 Rentals, 🚁 Helicopters\n"
        "• Lifestyle: 🍽️ Dining, 🎫 Events, 🎢 Six Flags, 🛒 Groceries\n"
        "• Essentials: 🚆 Train Passes, 💳 Bills, 🎓 School Fees, 🏥 Hospital Bills\n\n"
        "One Platform. Endless Possibilities. Real Savings.\n\n"
        "We’re your one-stop partner for making your money go further.\n\n"
        "Ready to unlock your deals?\n"
        "Join our official channel to get started\n"
        "With trust,\n"
        "Your Friend, @yrfrnd_spidy\n"
    )


@app.route('/')
def home():
    return "Bot is running!"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = request.get_data().decode("utf-8")
    update_obj = telebot.types.Update.de_json(update)
    bot.process_new_updates([update_obj])
    return "OK", 200

if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("⚠️ TELEGRAM_BOT_TOKEN environment variable is required")
    
    # Set webhook
    try:
        bot.remove_webhook()
        # For Replit/Render deployment
        replit_domain = os.environ.get("REPLIT_DEV_DOMAIN")
        render_domain = os.environ.get("RENDER_EXTERNAL_URL")
        
        if replit_domain:
            webhook_url = f"https://{replit_domain}/{TOKEN}"
        elif render_domain:
            webhook_url = f"{render_domain}/{TOKEN}"
        else:
            webhook_url = None
            
        if webhook_url:
            bot.set_webhook(url=webhook_url)
            print(f"✅ Webhook set to: {webhook_url}")
        else:
            print("⚠️ No domain found for webhook")
            
    except Exception as e:
        print(f"⚠️ Webhook setup error: {e}")
    
    print("🚀 Bot is running!")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

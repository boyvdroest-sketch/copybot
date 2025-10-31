import os
from flask import Flask, request
import telebot
from telebot import types

# Get bot token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def start_command(message):
    # Guard in case message is None
    if message is None:
        return

    # Create an inline keyboard with 3 buttons
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    button_channel = types.InlineKeyboardButton("🟡 Join Channel", url="https://t.me/flights_half_off")
    button_website = types.InlineKeyboardButton("🌐 Visit Website", url="https://rb.gy/jrr1lb")
    button_contact = types.InlineKeyboardButton("💬 Contact Admin", url="https://t.me/yrfrnd_spidy")
    keyboard.add(button_channel, button_website, button_contact)

    message_text = (
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
        
    )

    bot.send_message(message.chat.id, message_text, reply_markup=keyboard)

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
            webhook_url = None;
            
        if webhook_url:
            bot.set_webhook(url=webhook_url)
            print(f"✅ Webhook set to: {webhook_url}")
        else:
            print("⚠️ No domain found for webhook")
            
    except Exception as e:
        print(f"⚠️ Webhook setup error: {e}")
    
    print("🚀 Bot is running!")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

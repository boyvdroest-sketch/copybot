import os
from flask import Flask, request
import telebot
from telebot import types

# Get bot token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Add your admin user ID here
ADMIN_ID = 7179248383  # Replace with your actual Telegram user ID

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Simple in-memory storage for broadcast (will reset on restart)
users_set = set()

@bot.message_handler(commands=['start'])
def start_command(message):
    if message is None:
        return

    user = message.from_user
    # Add user to broadcast list
    users_set.add(user.id)

    # Create an inline keyboard with 3 buttons
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    button_channel = types.InlineKeyboardButton("🟡 Join Channel", url="https://t.me/flights_half_off")
    button_website = types.InlineKeyboardButton("🌐 Visit Website", url="https://rb.gy/jrr1lb")
    button_contact = types.InlineKeyboardButton("💬 Contact Admin", url="https://t.me/yrfrnd_spidy")
    keyboard.add(button_channel, button_website, button_contact)

    message_text = (
        "🟡 Welcome to Spidy's World – Where Trust Meets Incredible Savings! 🟡\n\n"
        "We know it sounds too good to be true. That's why we're building a trusted service you can rely on.\n\n"
        "Experience 50% Off on a World of Services: ✨\n\n"
        "• Travel: ✈️ Flights, 🏨 Hotels, 🚗 Rentals, 🚁 Helicopters\n"
        "• Lifestyle: 🍽️ Dining, 🎫 Events, 🎢 Six Flags, 🛒 Groceries\n"
        "• Essentials: 🚆 Train Passes, 💳 Bills, 🎓 School Fees, 🏥 Hospital Bills\n\n"
        "One Platform. Endless Possibilities. Real Savings.\n\n"
        "We're your one-stop partner for making your money go further.\n\n"
        "Ready to unlock your deals?\n"
        "Join our official channel to get started\n"
        "With trust,\n"
    )

    bot.send_message(message.chat.id, message_text, reply_markup=keyboard)

@bot.message_handler(commands=['stats'])
def stats_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    user_count = len(users_set)
    bot.send_message(ADMIN_ID, f"📊 Bot Statistics:\n\n👥 Total Users: {user_count}")

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    # Ask admin for broadcast message
    msg = bot.send_message(ADMIN_ID, "📢 Please enter your broadcast message:")
    bot.register_next_step_handler(msg, process_broadcast_message)

def process_broadcast_message(message):
    broadcast_text = message.text
    users = list(users_set)
    success_count = 0
    fail_count = 0
    
    # Send initial status
    status_msg = bot.send_message(ADMIN_ID, f"📤 Starting broadcast to {len(users)} users...")
    
    for user_id in users:
        try:
            bot.send_message(user_id, f"📢 Announcement:\n\n{broadcast_text}")
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"Failed to send to {user_id}: {e}")
    
    # Update status
    bot.edit_message_text(
        f"✅ Broadcast Completed!\n\n"
        f"✅ Successful: {success_count}\n"
        f"❌ Failed: {fail_count}\n"
        f"📊 Total: {len(users)}",
        ADMIN_ID,
        status_msg.message_id
    )

# Handler for ALL messages - tell users to contact admin directly
@bot.message_handler(func=lambda message: True)
def all_messages_handler(message):
    # Add user to broadcast list when they send any message
    users_set.add(message.from_user.id)
    
    # Don't respond to admin's own messages
    if message.from_user.id == ADMIN_ID:
        return
    
    # For all user messages, tell them to contact admin directly
    contact_text = (
        "💬 For direct communication, please contact admin directly:\n\n"
        "👤 Admin: @yrfrnd_spidy\n"
        "📢 Channel: @flights_half_off\n\n"
        "We'll respond to you as soon as possible!"
    )
    
    bot.reply_to(message, contact_text)

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

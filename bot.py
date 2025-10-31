import os
from flask import Flask, request
import telebot
from telebot import types

# Get bot token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Add your admin user ID here
ADMIN_ID = 7016264130  # Replace with your actual Telegram user ID

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Store user info for replies
user_messages = {}

@bot.message_handler(commands=['start'])
def start_command(message):
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

@bot.message_handler(func=lambda message: message.text and message.text.lower() == "hello")
def hello_handler(message):
    user = message.from_user
    user_info = f"User: {user.first_name} {user.last_name or ''} (@{user.username or 'No username'})"
    
    # Store message info for admin replies
    user_messages[message.message_id] = {
        'user_id': user.id,
        'user_info': user_info
    }
    
    # Forward the "hello" message to admin with reply button
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📨 Reply", callback_data=f"reply_{message.message_id}"))
    
    forward_text = f"👋 Someone said hello!\n\n{user_info}\nUser ID: {user.id}\n\nMessage: '{message.text}'"
    
    bot.send_message(ADMIN_ID, forward_text, reply_markup=keyboard)
    
    # Also reply to the user
    bot.reply_to(message, "👋 Hello! I've notified the admin. They'll get back to you soon!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def reply_callback_handler(call):
    message_id = int(call.data.split('_')[1])
    
    if message_id in user_messages:
        user_data = user_messages[message_id]
        
        # Ask admin to type the reply
        msg = bot.send_message(ADMIN_ID, f"💬 Type your reply for user {user_data['user_info']}:")
        
        # Register next step handler for admin's reply
        bot.register_next_step_handler(msg, process_admin_reply, user_data['user_id'])
    else:
        bot.answer_callback_query(call.id, "❌ Message data expired")

def process_admin_reply(message, user_id):
    try:
        # Send admin's reply to the user
        bot.send_message(user_id, f"📨 Message from admin:\n\n{message.text}")
        bot.reply_to(message, "✅ Reply sent successfully!")
    except Exception as e:
        bot.reply_to(message, f"❌ Failed to send reply: {str(e)}")

# Handler for other messages (optional)
@bot.message_handler(func=lambda message: True)
def other_messages_handler(message):
    # You can modify this to handle other specific messages or ignore them
    if message.chat.id != ADMIN_ID:  # Don't reply to admin's own messages
        bot.reply_to(message, "Please use /start to see our services or say 'hello' to contact admin!")

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

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

# Store user info for replies and broadcast
user_messages = {}
broadcast_users = set()
user_chat_states = {}  # Track user conversation states

@bot.message_handler(commands=['start'])
def start_command(message):
    if message is None:
        return

    # Add user to broadcast list
    user_id = message.from_user.id
    broadcast_users.add(user_id)
    
    # Reset chat state
    user_chat_states[user_id] = 'started'

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

# ===== BROADCAST FEATURE =====
@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ This command is for admin only!")
        return
    
    if len(broadcast_users) == 0:
        bot.reply_to(message, "❌ No users in broadcast list!")
        return
    
    # Ask admin for broadcast message
    msg = bot.send_message(
        ADMIN_ID, 
        f"📢 Broadcast to {len(broadcast_users)} users\n\nPlease enter your broadcast message:"
    )
    bot.register_next_step_handler(msg, process_broadcast_message)

def process_broadcast_message(message):
    # Prevent multiple broadcasts from same message
    if hasattr(message, 'is_broadcast_processed') and message.is_broadcast_processed:
        return
    message.is_broadcast_processed = True
    
    broadcast_text = message.text
    users = list(broadcast_users)
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
        f"📊 Total Users: {len(users)}",
        ADMIN_ID,
        status_msg.message_id
    )

@bot.message_handler(commands=['stats'])
def stats_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    user_count = len(broadcast_users)
    bot.send_message(ADMIN_ID, f"📊 Bot Statistics:\n\n👥 Total Users: {user_count}")

# ===== CHAT HANDLERS =====
@bot.message_handler(func=lambda message: message.text and message.text.lower().startswith('hello'))
def hello_handler(message):
    user = message.from_user
    user_id = user.id
    
    # Add user to broadcast list
    broadcast_users.add(user_id)
    
    # Set chat state
    user_chat_states[user_id] = 'waiting_for_admin'
    
    user_info = f"User: {user.first_name} {user.last_name or ''} (@{user.username or 'No username'})"
    
    # Store message info for admin replies
    user_messages[message.message_id] = {
        'user_id': user.id,
        'user_info': user_info,
        'original_message': message.text
    }
    
    # Forward the "hello" message to admin with reply button
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📨 Reply", callback_data=f"reply_{message.message_id}"))
    
    forward_text = f"👋 Someone said hello!\n\n{user_info}\nUser ID: {user.id}\n\nMessage: '{message.text}'"
    
    bot.send_message(ADMIN_ID, forward_text, reply_markup=keyboard)
    
    # Reply to the user ONLY ONCE
    bot.reply_to(message, "👋 Hello! I've notified the admin. They'll get back to you soon!\n\nYou can continue chatting here and the admin will see your messages.")

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

# Handler for forwarding user messages to admin (enable chatting)
@bot.message_handler(func=lambda message: True)
def all_messages_handler(message):
    user = message.from_user
    user_id = user.id
    
    # Don't process admin's own messages
    if user_id == ADMIN_ID:
        return
    
    # Add user to broadcast list
    broadcast_users.add(user_id)
    
    # If user has started a chat (said hello before), forward their messages to admin
    if user_chat_states.get(user_id) == 'waiting_for_admin' and message.text:
        user_info = f"User: {user.first_name} {user.last_name or ''} (@{user.username or 'No username'})"
        
        # Store message info
        user_messages[message.message_id] = {
            'user_id': user_id,
            'user_info': user_info,
            'original_message': message.text
        }
        
        # Forward message to admin with reply button
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("📨 Reply", callback_data=f"reply_{message.message_id}"))
        
        forward_text = f"💬 New message from user:\n\n{user_info}\nUser ID: {user_id}\n\nMessage: '{message.text}'"
        
        bot.send_message(ADMIN_ID, forward_text, reply_markup=keyboard)
        
        # Let user know their message was received (only if it's not a hello message)
        if not message.text.lower().startswith('hello'):
            bot.reply_to(message, "✅ Message received! Admin will reply soon.")

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

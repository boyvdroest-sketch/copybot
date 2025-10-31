import os, sqlite3, random, string
from flask import Flask, request
import telebot
from telebot import types

# === CONFIG ===
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8429489568:AAFKr_Izu1GBiM_SOYvT_90VPZGj2ZJfm68"
)
BOT_USERNAME = "sunwinuss_bot"
CHANNELS = ["@thaoluangamekm", "@trumbaogamea", "@gamevuicothuong"]
DB_FILE = "users.db"
INVITE_REWARD = 6000
MIN_WITHDRAW = 30000
ADMIN_IDS = [7179248383]
# ==============

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ===== DB =====
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            invited_count INTEGER DEFAULT 0,
            referrer_id INTEGER
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id, referrer_id=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    exists = c.fetchone()
    if not exists:
        c.execute("INSERT INTO users (user_id, balance, invited_count, referrer_id) VALUES (?, 0, 0, ?)", (user_id, referrer_id))
    conn.commit()
    conn.close()

def reward_referrer(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("SELECT referrer_id FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    
    if result and result[0]:
        referrer_id = result[0]
        try:
            c.execute("SELECT user_id FROM users WHERE user_id=?", (referrer_id,))
            if not c.fetchone():
                c.execute("INSERT INTO users (user_id, balance, invited_count, referrer_id) VALUES (?, 0, 0, NULL)", (referrer_id,))
            
            c.execute("UPDATE users SET invited_count = invited_count + 1 WHERE user_id=?", (referrer_id,))
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (INVITE_REWARD, referrer_id))
            
            conn.commit()
            conn.close()
            return referrer_id
        except Exception:
            pass
    
    conn.commit()
    conn.close()
    return None

def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, balance, invited_count FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def generate_giftcode():
    letters = random.choices(string.ascii_uppercase, k=8)
    digits = random.choices(string.digits, k=4)
    code_list = letters + digits
    random.shuffle(code_list)
    return "".join(code_list)

# ===== Handlers =====
@bot.message_handler(commands=['start'])
def start_handler(message):
    user = message.from_user
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    referrer_id = None
    
    if args:
        ref = args[0]
        if ref.isdigit() and str(ref) != str(user.id):
            referrer_id = int(ref)
            bot.send_message(message.chat.id, f"🎉 Bạn được người dùng {referrer_id} mời tham gia bot!")
    
    add_user(user.id, referrer_id)
    links = "\n".join([f"🔗 {ch}" for ch in CHANNELS])
    text = (
        "🌟 Chào mừng bạn đến với Bot! 🌟\n\n"
        "Để sử dụng bot, vui lòng tham gia tất cả các nhóm/kênh sau:\n"
        f"{links}\n\n"
        "📌 Nhấn nút 'Xác Minh' sau khi tham gia đầy đủ!"
    )
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("✅ Xác Minh", callback_data="verify"))
    bot.send_message(message.chat.id, text, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify_handler(call):
    user_id = call.from_user.id
    
    not_joined = []
    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_joined.append(ch)
        except Exception:
            not_joined.append(ch)
    
    if not_joined:
        bot.edit_message_text(
            f"❌ Bạn chưa tham gia đủ! Vui lòng join các nhóm sau:\n" +
            "\n".join(not_joined),
            call.message.chat.id,
            call.message.message_id
        )
    else:
        # Thưởng tiền cho người mời
        referrer_id = reward_referrer(user_id)
        
        # Lấy thông tin số dư
        user_data = get_user(user_id)
        if user_data:
            uid, balance, invited_count = user_data
        else:
            balance = 0
        
        welcome_text = (
            "🎉 Chào mừng bạn quay trở lại! 🎉\n"
            f"💰 Số dư hiện tại: {balance} đồng\n"
            "🔥 Tiếp tục mời bạn bè để nhận thêm phần thưởng hấp dẫn!"
        )
        
        # Tạo menu
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row("👤 Tài Khoản", "👥 Mời Bạn Bè")
        keyboard.row("🎮 LINK GAME", "💸 Đổi Code")
        
        bot.edit_message_text(welcome_text, call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "📌 Đây là menu chính của bạn:", reply_markup=keyboard)
        
        # Thông báo cho người mời
        if referrer_id:
            try:
                bot.send_message(
                    referrer_id,
                    f"🎉 Bạn vừa nhận được {INVITE_REWARD} đồng từ việc mời thành viên mới! 💰"
                )
            except Exception:
                pass

@bot.message_handler(func=lambda message: message.text == "👥 Mời Bạn Bè")
def invite_handler(message):
    user = message.from_user
    link = f"https://t.me/{BOT_USERNAME}?start={user.id}"
    
    text = (
        f"💰 Thưởng: {INVITE_REWARD:,}đ/người\n"
        f"🔗 Link: `{link}`"
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "👤 Tài Khoản")
def account_handler(message):
    user = message.from_user
    data = get_user(user.id)
    if data:
        uid, balance, invited_count = data
        text = (
            f"👤 Tài Khoản của bạn\n\n"
            f"🆔 ID: {uid}\n"
            f"💰 Số dư: {balance} VNĐ\n"
            f"👥 Đã mời: {invited_count} người"
        )
    else:
        text = "⚠️ Bạn chưa có dữ liệu trong hệ thống!"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: message.text == "🎮 LINK GAME")
def link_game_handler(message):
    bot.send_message(message.chat.id, "🌐 Link Game: https://sunwin.us")

@bot.message_handler(func=lambda message: message.text == "💸 Đổi Code")
def redeem_code_handler(message):
    user = message.from_user
    data = get_user(user.id)
    if not data:
        bot.send_message(message.chat.id, "⚠️ Bạn chưa có dữ liệu trong hệ thống!")
        return
    
    uid, balance, invited_count = data
    if balance < MIN_WITHDRAW:
        bot.send_message(message.chat.id, "❌ Bạn chưa đủ số dư!\n👉 Hãy mời thêm bạn bè để nhận code.")
    else:
        bot.send_message(
            message.chat.id,
            f"✅ Bạn đủ điều kiện rút!\n\n"
            f"👉 Vui lòng nhập lệnh theo mẫu:\n"
            f"/rutcode <tennhanvat> <sotien>\n\n"
            f"Ví dụ: /rutcode abcxyz 30000\n"
            f"(Min rút {MIN_WITHDRAW})"
        )

@bot.message_handler(commands=['rutcode'])
def rutcode_handler(message):
    user = message.from_user
    args = message.text.split()[1:]
    
    if len(args) < 2:
        bot.send_message(message.chat.id, "⚠️ Sai cú pháp!\nDùng: /rutcode <tennhanvat> <sotien>")
        return
    
    name = args[0]
    try:
        amount = int(args[1])
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ Số tiền phải là số!")
        return
    
    if amount < MIN_WITHDRAW:
        bot.send_message(message.chat.id, f"❌ Min rút là {MIN_WITHDRAW}")
        return
    
    data = get_user(user.id)
    if not data:
        bot.send_message(message.chat.id, "⚠️ Bạn chưa có dữ liệu trong hệ thống!")
        return
    
    uid, balance, invited_count = data
    if balance < amount:
        bot.send_message(message.chat.id, "❌ Bạn không đủ số dư để rút!")
        return
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, uid))
    conn.commit()
    conn.close()
    
    code = generate_giftcode()
    
    bot.send_message(
        message.chat.id,
        f"🎉 Yêu cầu rút thành công!\n\n"
        f"👤 Nhân vật: {name}\n"
        f"💸 Số tiền: {amount}\n"
        f"🔑 Giftcode của bạn: {code}\n\n"
        f"✅ Cảm ơn bạn đã sử dụng dịch vụ."
    )

@bot.message_handler(commands=['addmoney'])
def admin_add_money(message):
    user = message.from_user
    
    if user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❌ Bạn không có quyền sử dụng lệnh này!")
        return
    
    args = message.text.split()[1:]
    if len(args) < 2:
        bot.send_message(message.chat.id, "⚠️ Sai cú pháp!\nDùng: /addmoney <user_id> <sotien>")
        return
    
    try:
        target_user_id = int(args[0])
        amount = int(args[1])
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ User ID và số tiền phải là số!")
        return
    
    if amount <= 0:
        bot.send_message(message.chat.id, "❌ Số tiền phải lớn hơn 0!")
        return
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("SELECT user_id FROM users WHERE user_id=?", (target_user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id, balance, invited_count, referrer_id) VALUES (?, 0, 0, NULL)", (target_user_id,))
    
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, target_user_id))
    c.execute("SELECT balance FROM users WHERE user_id=?", (target_user_id,))
    new_balance = c.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    bot.send_message(
        message.chat.id,
        f"✅ Đã bơm {amount} đồng cho user {target_user_id}\n"
        f"💰 Số dư mới: {new_balance} đồng"
    )
    
    try:
        bot.send_message(
            target_user_id,
            f"🎉 Bạn đã được admin tặng {amount} đồng! 💰\n💳 Số dư hiện tại: {new_balance} đồng"
        )
    except Exception:
        bot.send_message(message.chat.id, "⚠️ Không thể gửi thông báo đến user (có thể user chưa start bot)")

@bot.message_handler(commands=['userinfo'])
def admin_user_info(message):
    user = message.from_user
    
    if user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❌ Bạn không có quyền sử dụng lệnh này!")
        return
    
    args = message.text.split()[1:]
    if len(args) < 1:
        bot.send_message(message.chat.id, "⚠️ Sai cú pháp!\nDùng: /userinfo <user_id>")
        return
    
    try:
        target_user_id = int(args[0])
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ User ID phải là số!")
        return
    
    user_data = get_user(target_user_id)
    if not user_data:
        bot.send_message(message.chat.id, "❌ Không tìm thấy user trong hệ thống!")
        return
    
    uid, balance, invited_count = user_data
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT referrer_id FROM users WHERE user_id=?", (target_user_id,))
    result = c.fetchone()
    referrer_id = result[0] if result and result[0] else "Không có"
    conn.close()
    
    bot.send_message(
        message.chat.id,
        f"👤 Thông tin User {uid}\n\n"
        f"💰 Số dư: {balance} đồng\n"
        f"👥 Đã mời: {invited_count} người\n"
        f"🔗 Được mời bởi: {referrer_id}"
    )

# ===== Flask Routes =====
@app.route('/')
def home():
    return "Bot is running on Replit!"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = request.get_data().decode("utf-8")
    update_obj = telebot.types.Update.de_json(update)
    bot.process_new_updates([update_obj])
    return "OK", 200

if __name__ == "__main__":
    init_db()
    
    if not TOKEN or TOKEN == "PUT-YOUR-TOKEN-HERE":
        raise SystemExit("⚠️ Chưa cấu hình TELEGRAM_BOT_TOKEN.")
    
    # Get domain (support both Replit and Render)
    replit_domain = os.environ.get("REPLIT_DEV_DOMAIN")
    render_domain = os.environ.get("RENDER_EXTERNAL_URL")
    
    if replit_domain:
        webhook_url = f"https://{replit_domain}/{TOKEN}"
    elif render_domain:
        webhook_url = f"{render_domain}/{TOKEN}"
    else:
        webhook_url = None
    
    if webhook_url:
        try:
            # Remove existing webhook first
            print("🔄 Removing existing webhook...")
            bot.remove_webhook()
            
            # Set new webhook
            print(f"🔗 Setting webhook to: {webhook_url}")
            result = bot.set_webhook(url=webhook_url)
            
            if result:
                print(f"✅ Webhook successfully set to: {webhook_url}")
                
                # Verify webhook info
                webhook_info = bot.get_webhook_info()
                print(f"📊 Webhook Info:")
                print(f"   - URL: {webhook_info.url}")
                print(f"   - Pending updates: {webhook_info.pending_update_count}")
                print(f"   - Max connections: {webhook_info.max_connections}")
                if webhook_info.last_error_date:
                    print(f"   - Last error: {webhook_info.last_error_message}")
            else:
                print("❌ Failed to set webhook")
                
        except Exception as e:
            print(f"⚠️ Webhook setup error: {e}")
            print("🔄 Bot will continue running but may not receive updates properly")
    else:
        print("⚠️ No platform domain found (REPLIT_DEV_DOMAIN or RENDER_EXTERNAL_URL), webhook not set")
        print("💡 Bot will still run but may need manual webhook configuration")
    
    print("🚀 Bot is running with webhook!")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

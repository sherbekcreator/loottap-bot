import telebot
import sqlite3
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from flask import Flask
from threading import Thread

# --- UYG'OTKICH (WEB SERVER) SOZLAMALARI ---
app = Flask(__name__)

@app.route('/')
def main():
    return "LootTap Bot Serveri 100% Jangovar Holatda!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    server = Thread(target=run)
    server.start()
# ------------------------------------------

# Sizning API kalitingiz
TOKEN = '8610358967:AAHAoZ6UKbjouwpdYnJHirdzRgRLIL5i2BI'
bot = telebot.TeleBot(TOKEN)

# FAQAT SHU KANAL STARTDA MAJBURIY SO'RALADI
CHANNELS = [
    {"name": "NIKSOTAMAN", "id": "@niksotaman", "url": "https://t.me/niksotaman"}
]

# NGROK HAVOLANGIZNI SHU YERGA QO'YASIZ
WEB_APP_URL = "https://oblivion-lisp-stable.ngrok-free.dev" 

# --- 1. MA'LUMOTLAR BAZASI ---
conn = sqlite3.connect('loottap.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        score INTEGER DEFAULT 0,
        energy INTEGER DEFAULT 1000,
        referrals INTEGER DEFAULT 0,
        unlocked_ref INTEGER DEFAULT 0
    )
''')

# Eski bazani avtomatik yangilash (Agar ustunlar yo'q bo'lsa, o'zi qo'shadi)
try:
    cursor.execute("ALTER TABLE users ADD COLUMN upg_tap INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE users ADD COLUMN upg_energy INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE users ADD COLUMN upg_regen INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE users ADD COLUMN daily_limit INTEGER DEFAULT 15000")
    conn.commit()
except Exception:
    pass # Agar ustunlar allaqachon mavjud bo'lsa, xatolik bermaydi

conn.commit()

# --- 2. REYTINGLARNI JSON FAYLGA YOZISH ---
def update_rating_json():
    cursor.execute("SELECT first_name, score FROM users ORDER BY score DESC LIMIT 100")
    top_users = [{"username": row[0] if row[0] else "Unknown", "loot": row[1]} for row in cursor.fetchall()]
    with open("rating.json", "w", encoding="utf-8") as f:
        json.dump(top_users, f)
        
    cursor.execute("SELECT first_name, referrals FROM users WHERE referrals > 0 ORDER BY referrals DESC LIMIT 100")
    top_refs = [{"username": row[0] if row[0] else "Unknown", "refs": row[1]} for row in cursor.fetchall()]
    with open("ref_rating.json", "w", encoding="utf-8") as f:
        json.dump(top_refs, f)

def check_sub(user_id):
    for channel in CHANNELS:
        try:
            status = bot.get_chat_member(channel['id'], user_id).status
            if status in ['left', 'kicked']:
                return False
        except Exception:
            return False
    return True

def force_sub_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    for ch in CHANNELS:
        markup.add(InlineKeyboardButton(text=ch['name'], url=ch['url']))
    markup.add(InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription"))
    return markup

def main_menu_markup(user_id):
    # MA'LUMOTLARNI BAZADAN OLISH VA WEB APPGA JO'NATISH
    cursor.execute("SELECT score, energy, upg_tap, upg_energy, upg_regen, daily_limit FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        score, energy, upg_tap, upg_energy, upg_regen, daily_limit = row
    else:
        score, energy, upg_tap, upg_energy, upg_regen, daily_limit = (0, 1000, 0, 0, 0, 15000)

    markup = InlineKeyboardMarkup()
    # URL orqali ma'lumotlarni HTMLga xavfsiz uzatamiz
    full_url = f"{WEB_APP_URL}?userid={user_id}&score={score}&energy={energy}&tap={upg_tap}&eng={upg_energy}&reg={upg_regen}&limit={daily_limit}"
    webapp = WebAppInfo(url=full_url)
    markup.add(InlineKeyboardButton(text="⚡️ > BOSHLASH <", web_app=webapp))
    return markup

# --- 3. BAZAGA SAQLASH VA XARIDLAR ---
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    text = message.text

    if len(text.split()) > 1:
        param = text.split()[1]
        
        # REFERRAL
        if param.startswith('ref_'):
            try:
                inviter_id = int(param.split('_')[1])
                cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
                if not cursor.fetchone() and inviter_id != user_id:
                    cursor.execute('INSERT INTO users (user_id, first_name) VALUES (?, ?)', (user_id, first_name))
                    cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id = ?", (inviter_id,))
                    conn.commit()
                    update_rating_json()
                    bot.send_message(inviter_id, f"🎉 Tabriklaymiz! Sizning taklifingiz bilan **{first_name}** botga qo'shildi!")
            except Exception:
                pass

        # BARCHA MA'LUMOTLARNI SAQLASH
        elif param.startswith('save_'):
            try:
                parts = param.split('_')
                if len(parts) >= 7:
                    new_score = int(parts[1])
                    new_energy = int(parts[2])
                    new_tap = int(parts[3])
                    new_eng = int(parts[4])
                    new_reg = int(parts[5])
                    new_limit = int(parts[6])
                    
                    cursor.execute('INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?, ?)', (user_id, first_name))
                    cursor.execute('''UPDATE users SET score=?, energy=?, upg_tap=?, upg_energy=?, upg_regen=?, daily_limit=? WHERE user_id=?''',
                                   (new_score, new_energy, new_tap, new_eng, new_reg, new_limit, user_id))
                    conn.commit()
                    update_rating_json()
                    
                    bot.send_message(message.chat.id, f"✅ O'yin holati muvaffaqiyatli saqlandi!\n\nJoriy hisobingiz: {new_score} 💎\n\nIlovani qayta ochish uchun quyidagi tugmani bosing.", reply_markup=main_menu_markup(user_id))
            except Exception:
                pass
            return 
            
        # LOOT ORQALI XARID
        elif param.startswith('withdraw_'):
            try:
                parts = param.split('_')
                w_type, price, new_score = parts[1].upper(), int(parts[2]), int(parts[3])
                game_id = parts[4] if len(parts) > 4 else "Noma'lum"
                game_nick = parts[5] if len(parts) > 5 else "Noma'lum"
                
                cursor.execute('INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?, ?)', (user_id, first_name))
                cursor.execute("UPDATE users SET score = ? WHERE user_id = ?", (new_score, user_id))
                conn.commit()
                update_rating_json()
                
                admin_id = 8361233416
                admin_msg = (f"🔔 **Yangi LOOT xarid so'rovi!**\n\n👤 O'yinchi: {first_name} ({username})\n🆔 Telegram ID: `{user_id}`\n\n🛒 Xarid turi: **{w_type}**\n🎮 O'yin ID: `{game_id}`\n🥷 O'yin NIK: {game_nick}\n\n💰 Sarflandi: {price} loot\n💎 Qoldiq: {new_score} loot\n\n⚠️ Admin, 24 soat ichida bajarilsin!")
                bot.send_message(admin_id, admin_msg, parse_mode='Markdown')
                
                msg = (f"🎉 So'rovingiz qabul qilindi!\n\n💳 Xarid: {w_type}\n🎮 O'yin ID: {game_id}\n💰 Sarflandi: {price} loot\n\n✅ 24 soat ichida hisobingizga tushadi!\n🙏 O'yinimizni tanlaganingiz uchun rahmat, omad!")
                bot.send_message(message.chat.id, msg, reply_markup=main_menu_markup(user_id))
            except Exception:
                bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.")
            return

        # DO'STLAR ORQALI XARID
        elif param.startswith('refwithdraw_'):
            try:
                parts = param.split('_')
                w_type = parts[1].upper()
                req_friends = int(parts[2])
                game_id = parts[3]
                game_nick = parts[4]

                cursor.execute("SELECT referrals, score, unlocked_ref FROM users WHERE user_id = ?", (user_id,))
                user_data = cursor.fetchone()
                
                if user_data:
                    refs, current_score, unlocked_ref = user_data[0], user_data[1], user_data[2]
                    
                    if unlocked_ref == 0:
                        if current_score >= 10000000:
                            cursor.execute("UPDATE users SET unlocked_ref = 1 WHERE user_id = ?", (user_id,))
                            conn.commit()
                        else:
                            bot.send_message(message.chat.id, "❌ **Xatolik! Ruxsat yo'q!**\n\nFiribgarlikni oldini olish maqsadida, do'stlar orqali valyuta olishingiz uchun birinchi marta hisobingizda kamida **10 mln loot** yig'ishingiz shart.\n\n*(Siz bir marta 10 mlnga yetganingizdan so'ng, bu cheklov butunlay va umrbod olib tashlanadi!)*", reply_markup=main_menu_markup(user_id))
                            return
                        
                    if refs < req_friends:
                        bot.send_message(message.chat.id, f"❌ **Xatolik!**\nSizda yetarli do'stlar yo'q!\nKerak: {req_friends} ta. Sizda: {refs} ta.", reply_markup=main_menu_markup(user_id))
                        return

                    cursor.execute("UPDATE users SET referrals = referrals - ? WHERE user_id = ?", (req_friends, user_id))
                    conn.commit()
                    update_rating_json()

                    admin_id = 8361233416
                    admin_msg = (f"🤝 **Yangi DO'STLAR orqali xarid so'rovi!**\n\n👤 O'yinchi: {first_name} ({username})\n🆔 Telegram ID: `{user_id}`\n\n🎁 Sovg'a: **{w_type}**\n👥 Sarflandi: {req_friends} ta do'st\n🎮 O'yin ID: `{game_id}`\n🥷 O'yin NIK: {game_nick}\n\n⚠️ Admin, 24 soat ichida bajarilsin!")
                    bot.send_message(admin_id, admin_msg, parse_mode='Markdown')
                    
                    msg = (f"🎉 Qo'shgan do'stlaringiz uchun so'rov qabul qilindi!\n\n🎁 Yutuq: {w_type}\n👥 Sarflandi: {req_friends} ta do'st\n\n✅ 24 soat ichida hisobingizga tushadi!\n🙏 O'yinimizni tanlaganingiz uchun rahmat, omad!")
                    bot.send_message(message.chat.id, msg, reply_markup=main_menu_markup(user_id))
                else:
                    bot.send_message(message.chat.id, "❌ Avval botni ishga tushiring.", reply_markup=main_menu_markup(user_id))
            except Exception as e:
                pass
            return

    # Oddiy start
    cursor.execute('INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?, ?)', (user_id, first_name))
    conn.commit()
    update_rating_json()

    if check_sub(user_id):
        msg_text = (f"👋, {first_name}!\n"
                    f"🎮 PUBG UC ishlash endi juda oson!\n"
                    f"Bot orqali ochko (point) to'plang va ularni UC yoki Almazga almashtiring 💎\n\n"
                    f"🔥 Qanday ishlaydi?\n"
                    f"• Botga kiring\n"
                    f"• Vazifalarni bajaring ✅\n"
                    f"• Loot to'plang 💰\n"
                    f"• UC va Almazga almashtiring 🎁\n\n"
                    f"⚡️ Tez | Oson | Ishonchli\n\n"
                    f"🎯 Do'stlaringizni taklif qiling va tekinga yutuq oling!")
        bot.send_message(message.chat.id, msg_text, reply_markup=main_menu_markup(user_id))
    else:
        msg_text = "⚠️ **Majburiy obuna talab qilinadi!**\n\nDavom etish uchun quyidagi kanalga a'zo bo'ling 👇"
        bot.send_message(message.chat.id, msg_text, reply_markup=force_sub_markup(), parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def callback_check(call):
    if check_sub(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        cursor.execute('INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?, ?)', (call.from_user.id, call.from_user.first_name))
        conn.commit()
        update_rating_json()
        
        msg_text = (f"👋, {call.from_user.first_name}!\n"
                    f"🎮 PUBG UC ishlash endi juda oson!\n"
                    f"Bot orqali ochko (point) to'plang va ularni UC yoki Almazga almashtiring 💎\n\n"
                    f"🔥 Qanday ishlaydi?\n"
                    f"• Botga kiring\n"
                    f"• Vazifalarni bajaring ✅\n"
                    f"• Loot to'plang 💰\n"
                    f"• UC va Almazga almashtiring 🎁\n\n"
                    f"⚡️ Tez | Oson | Ishonchli\n\n"
                    f"🎯 Do'stlaringizni taklif qiling va tekinga yutuq oling!")
        bot.send_message(call.message.chat.id, msg_text, reply_markup=main_menu_markup(call.from_user.id))
    else:
        bot.answer_callback_query(call.id, "❌ Hali kanalga obuna bo'lmadingiz!", show_alert=True)

# --- FAKAT DO'STLARNI TOZALASH (SINOV UCHUN) ---
@bot.message_handler(commands=['clear_refs'])
def clear_refs(message):
    if message.from_user.id == 8361233416: 
        cursor.execute("UPDATE users SET referrals = 0")
        conn.commit()
        update_rating_json()
        bot.send_message(message.chat.id, "✅ Barcha test qilingan do'stlar nollashtirildi! (Lootlar saqlanib qoldi)")

print("💎 LootTap Bot serveri ishga tushdi! Baza muvaffaqiyatli ulandi...")
keep_alive() # Mana shu bizning ko'rinmas uyg'otkichimiz
bot.infinity_polling()

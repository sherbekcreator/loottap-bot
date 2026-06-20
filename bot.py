import telebot
import sqlite3
import json
import os
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from flask import Flask, send_from_directory, make_response
from threading import Thread

# --- UYG'OTKICH VA REYTING TARQATUVCHI ---
app = Flask(__name__)

@app.route('/')
def main():
    return "LootTap Bot Serveri 100% Jangovar Holatda!"

@app.route('/<path:path>')
def serve_file(path):
    if not os.path.exists(path):
        update_rating_json()
        
    response = make_response(send_from_directory('.', path))
    response.headers['Access-Control-Allow-Origin'] = '*' 
    return response

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    server = Thread(target=run)
    server.start()

# --- SOZLAMALAR ---
TOKEN = '8877117409:AAGfojWHm28yWeYIWwMDp7sb_WJ3p9mLcu8'
bot = telebot.TeleBot(TOKEN)

WEB_APP_URL = "https://sherbekcreator.github.io/loottap-bot/"
START_IMAGE_URL = "https://raw.githubusercontent.com/sherbekcreator/loottap-bot/main/banner.jpg"

# ⚠️ ADMINLAR RO'YXATI (Sizning va Ibod akaning ID raqamlari)
ADMIN_IDS = [8361233416, 942670016] 

# --- MAJBURIY OBUNA KANALLARI ---
# 1. Telegram kanallar (Bot bularning barchasida ADMIN bo'lishi shart!)
REQUIRED_TG_CHANNELS = [
    ("@ibodmarket", "IBOD MARKET TG", "https://t.me/ibodmarket"),
    ("@iboduc_service", "IBOD UC SERVICE TG", "https://t.me/iboduc_service"),
    ("@ibod_tournament", "IBOD TOURNAMENT TG", "https://t.me/ibod_tournament"),
    ("@etoSHEYXpubg", "SHEYX PUBG TG", "https://t.me/etoSHEYXpubg"),
    ("@ibodmashka_pubg", "IBOD MASHKA TG", "https://t.me/ibodmashka_pubg")
]

# 2. Boshqa tarmoqlar (YouTube = YT, Instagram = INS)
OTHER_CHANNELS = [
    ("SHEYX PUBG YT", "https://youtube.com/@etosheyxpubgm?si=7u6mMJ8I_8Eg896Q"),
    ("IBOD MASHENNA YT", "https://youtube.com/@ibodmashkapubgm?si=EbTppdqyNQu2KBp9"),
    ("IBOD TAP YT", "https://youtube.com/@ibodtap?si=c-X79pYo5t83xx_r"),
    ("IBOD MASHENNA INS", "https://www.instagram.com/ibodmashennik"),
    ("IBOD MARKET INS", "https://www.instagram.com/ibod_market")
]

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

try:
    cursor.execute("ALTER TABLE users ADD COLUMN upg_tap INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE users ADD COLUMN upg_energy INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE users ADD COLUMN upg_regen INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE users ADD COLUMN daily_limit INTEGER DEFAULT 15000")
    conn.commit()
except Exception:
    pass 

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

def main_menu_markup(user_id):
    cursor.execute("SELECT score, energy, upg_tap, upg_energy, upg_regen, daily_limit FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        score, energy, upg_tap, upg_energy, upg_regen, daily_limit = row
    else:
        score, energy, upg_tap, upg_energy, upg_regen, daily_limit = (0, 1000, 0, 0, 0, 15000)

    markup = InlineKeyboardMarkup()
    full_url = f"{WEB_APP_URL}?userid={user_id}&score={score}&energy={energy}&tap={upg_tap}&eng={upg_energy}&reg={upg_regen}&limit={daily_limit}"
    webapp = WebAppInfo(url=full_url)
    markup.add(InlineKeyboardButton(text="⚡️ > BOSHLASH <", web_app=webapp))
    return markup

def check_all_subs(user_id):
    for channel in REQUIRED_TG_CHANNELS:
        try:
            member = bot.get_chat_member(channel[0], user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception:
            return False
    return True

def sub_menu_markup(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    
    all_channels = []
    for ch in REQUIRED_TG_CHANNELS:
        all_channels.append({'type': 'tg', 'id': ch[0], 'name': ch[1], 'url': ch[2]})
    for ch in OTHER_CHANNELS:
        all_channels.append({'type': 'other', 'name': ch[0], 'url': ch[1]})
        
    for i, ch in enumerate(all_channels, 1):
        btn_text = f"[{i}] {ch['name']}"
        if ch['type'] == 'tg':
            try:
                member = bot.get_chat_member(ch['id'], user_id)
                if member.status in ['member', 'administrator', 'creator']:
                    btn_text = f"✅ {ch['name']}"
            except Exception:
                pass
        buttons.append(InlineKeyboardButton(text=btn_text, url=ch['url']))
        
    markup.add(*buttons)
    markup.add(InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub"))
    return markup

# --- 3. BAZAGA SAQLASH VA XARIDLAR ---
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    text = message.text

    cursor.execute('INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?, ?)', (user_id, first_name))
    conn.commit()

    if len(text.split()) > 1:
        param = text.split()[1]

        if param.startswith('ref_'):
            try:
                inviter_id = int(param.split('_')[1])
                cursor.execute("SELECT score FROM users WHERE user_id = ?", (user_id,))
                user_score = cursor.fetchone()
                
                if user_score and user_score[0] == 0 and inviter_id != user_id:
                    cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id = ?", (inviter_id,))
                    conn.commit()
                    update_rating_json()
                    bot.send_message(inviter_id, f"🎉 Tabriklaymiz! Sizning taklifingiz bilan **{first_name}** botga qo'shildi!")
            except Exception:
                pass

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

                    cursor.execute('''UPDATE users SET score=?, energy=?, upg_tap=?, upg_energy=?, upg_regen=?, daily_limit=? WHERE user_id=?''',
                                   (new_score, new_energy, new_tap, new_eng, new_reg, new_limit, user_id))
                    conn.commit()
                    update_rating_json()

                    bot.send_message(message.chat.id, f"✅ O'yin holati muvaffaqiyatli saqlandi!\n\nJoriy hisobingiz: {new_score} 💎\n\nIlovani qayta ochish uchun quyidagi tugmani bosing.", reply_markup=main_menu_markup(user_id))
            except Exception:
                pass
            return

        elif param.startswith('withdraw_'):
            try:
                parts = param.split('_')
                w_type, price, new_score = parts[1].upper(), int(parts[2]), int(parts[3])
                game_id = parts[4] if len(parts) > 4 else "Noma'lum"
                game_nick = parts[5] if len(parts) > 5 else "Noma'lum"

                cursor.execute("UPDATE users SET score = ? WHERE user_id = ?", (new_score, user_id))
                conn.commit()
                update_rating_json()

                admin_msg = (f"🔔 **Yangi LOOT xarid so'rovi!**\n\n👤 O'yinchi: {first_name} ({username})\n🆔 Telegram ID: `{user_id}`\n\n🛒 Xarid turi: **{w_type}**\n🎮 O'yin ID: `{game_id}`\n🥷 O'yin NIK: {game_nick}\n\n💰 Sarflandi: {price} loot\n💎 Qoldiq: {new_score} loot\n\n⚠️ Admin, 24 soat ichida bajarilsin!")
                bot.send_message(ADMIN_IDS[0], admin_msg, parse_mode='Markdown')

                msg = (f"🎉 So'rovingiz qabul qilindi!\n\n💳 Xarid: {w_type}\n🎮 O'yin ID: {game_id}\n💰 Sarflandi: {price} loot\n\n✅ 24 soat ichida hisobingizga tushadi!\n🙏 O'yinimizni tanlaganingiz uchun rahmat, omad!")
                bot.send_message(message.chat.id, msg, reply_markup=main_menu_markup(user_id))
            except Exception:
                bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.")
            return

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

                    admin_msg = (f"🤝 **Yangi DO'STLAR orqali xarid so'rovi!**\n\n👤 O'yinchi: {first_name} ({username})\n🆔 Telegram ID: `{user_id}`\n\n🎁 Sovg'a: **{w_type}**\n👥 Sarflandi: {req_friends} ta do'st\n🎮 O'yin ID: `{game_id}`\n🥷 O'yin NIK: {game_nick}\n\n⚠️ Admin, 24 soat ichida bajarilsin!")
                    bot.send_message(ADMIN_IDS[0], admin_msg, parse_mode='Markdown')

                    msg = (f"🎉 Qo'shgan do'stlaringiz uchun so'rov qabul qilindi!\n\n🎁 Yutuq: {w_type}\n👥 Sarflandi: {req_friends} ta do'st\n\n✅ 24 soat ichida hisobingizga tushadi!\n🙏 O'yinimizni tanlaganingiz uchun rahmat, omad!")
                    bot.send_message(message.chat.id, msg, reply_markup=main_menu_markup(user_id))
                else:
                    bot.send_message(message.chat.id, "❌ Avval botni ishga tushiring.", reply_markup=main_menu_markup(user_id))
            except Exception as e:
                pass
            return

    # START BOSILGANDA MAJBURIY OBUNANI TEKSHIRISH (RASM BILAN)
    if not check_all_subs(user_id):
        caption_text = "⚠️ Majburiy obuna talab qilinadi!\n\nDavom etish uchun kanallarga obuna bo'ling! 👇"
        try:
            bot.send_photo(message.chat.id, photo=START_IMAGE_URL, caption=caption_text, reply_markup=sub_menu_markup(user_id))
        except Exception:
            bot.send_message(message.chat.id, caption_text, reply_markup=sub_menu_markup(user_id))
        return

    # Agar allaqachon a'zo bo'lgan bo'lsa (Muvaffaqiyatli asosiy start menyusi - BU YERDA HAM RASM CHIQADI)
    msg_text = (f"👋, {first_name}!\n"
                f"🎮 PUBG UC ishlash endi juda oson!\n"
                f"Bot orqali Loot to'plang va ularni UC ga almashtiring 💎\n\n"
                f"🔥 Qanday ishlaydi?\n"
                f"• Botga kiring\n"
                f"• Vazifalarni bajaring ✅\n"
                f"• Loot to'plang 💰\n"
                f"• UC yutib oling 🎁\n\n"
                f"⚡️ Tez | Oson | Ishonchli\n\n"
                f"🎯 Do'stlaringizni taklif qiling va yanada ko'proq loot yig'ing!")
    try:
        bot.send_photo(message.chat.id, photo=START_IMAGE_URL, caption=msg_text, reply_markup=main_menu_markup(user_id))
    except Exception:
        bot.send_message(message.chat.id, msg_text, reply_markup=main_menu_markup(user_id))

# --- MAJBURIY OBUNANI TEKSHIRISH TUGMASI (Dinamik ✅ qo'yish) ---
@bot.callback_query_handler(func=lambda call: call.data == 'check_sub')
def check_sub_callback(call):
    user_id = call.from_user.id
    first_name = call.from_user.first_name
    
    if check_all_subs(user_id):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
            
        # TASDIQLAGANDAN SO'NG HAM RASM BILAN CHIQADI
        msg_text = (f"🎉 Obuna tasdiqlandi!\n\n"
                    f"👋 Xush kelibsiz, {first_name}!\n"
                    f"👇 Botni ishga tushirish uchun quyidagi tugmani bosing:")
        try:
            bot.send_photo(call.message.chat.id, photo=START_IMAGE_URL, caption=msg_text, reply_markup=main_menu_markup(user_id))
        except Exception:
            bot.send_message(call.message.chat.id, msg_text, reply_markup=main_menu_markup(user_id))
    else:
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=sub_menu_markup(user_id))
        except Exception:
            pass 
            
        bot.answer_callback_query(call.id, "❌ Hali barcha kanallarga a'zo bo'lmadingiz! ➕ bo'lib turganlarga kiring.", show_alert=True)

# --- IBOD AKA UCHUN MAXSUS STATISTIKA BUYRUG'I ---
@bot.message_handler(commands=['ibod'])
def ibod_stats(message):
    if message.from_user.id in ADMIN_IDS:
        cursor.execute("SELECT COUNT(user_id) FROM users")
        total_users = cursor.fetchone()[0]
        
        bot.reply_to(message, f"📊 **IBOD TAP STATISTIKASI:**\n\n👥 Botdagi jami o'yinchilar: **{total_users}** ta.\n🔥 Biz to'xtamayapmiz, olg'a!")
    else:
        bot.reply_to(message, "❌ Sizda bu buyruqni ishlatish huquqi yo'q.")

# --- HAQIQIY ADMIN PANEL (SHERBEK UCHUN) ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id in ADMIN_IDS:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"))
        markup.add(InlineKeyboardButton("📨 Hammaga xabar yuborish", callback_data="admin_broadcast"))
        
        bot.send_message(message.chat.id, "🛡 **Admin Panelga xush kelibsiz!**\nQuyidagi menyudan kerakli bo'limni tanlang:", reply_markup=markup)
    else:
        bot.reply_to(message, "❌ Siz admin emassiz!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_callbacks(call):
    if call.from_user.id not in ADMIN_IDS:
        return
        
    if call.data == "admin_stats":
        cursor.execute("SELECT COUNT(user_id) FROM users")
        total_users = cursor.fetchone()[0]
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"📊 **Umumiy Statistika:**\n👥 Botdagi foydalanuvchilar: {total_users} ta")
        
    elif call.data == "admin_broadcast":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "📨 Yubormoqchi bo'lgan xabaringizni yozing (rasmli yoki matnli bo'lishi mumkin).\n\nBekor qilish uchun /cancel yozing.")
        bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "❌ Rassilka bekor qilindi.")
        return
        
    bot.send_message(message.chat.id, "⏳ Xabar yuborilmoqda, kuting...")
    
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    
    success = 0
    fail = 0
    
    for user in users:
        try:
            bot.copy_message(user[0], message.chat.id, message.message_id)
            success += 1
            time.sleep(0.05)
        except Exception:
            fail += 1
            
    bot.send_message(message.chat.id, f"✅ **Rassilka yakunlandi!**\n\n🟢 Yetib bordi: {success} ta\n🔴 Bloklaganlar: {fail} ta")

# --- MAXFIY ADMIN KOMANDASI (Qo'lda boshqarish) ---
@bot.message_handler(commands=['give'])
def give_loot_admin(message):
    if message.from_user.id not in ADMIN_IDS:
        return 

    try:
        args = message.text.split()
        target_id = int(args[1])
        amount = int(args[2])

        cursor.execute("SELECT score FROM users WHERE user_id=?", (target_id,))
        result = cursor.fetchone()

        if result:
            new_score = result[0] + amount
            cursor.execute("UPDATE users SET score=? WHERE user_id=?", (new_score, target_id))
            conn.commit()
            update_rating_json()
            bot.reply_to(message, f"✅ Muvaffaqiyatli!\n🆔 {target_id} egasiga {amount} loot qo'shildi.\n💎 Umumiy hisob: {new_score}")
        else:
            bot.reply_to(message, "❌ Foydalanuvchi bazadan topilmadi!")

    except Exception as e:
        bot.reply_to(message, "⚠️ Xato format!\nTo'g'ri usul: /give ID MIQDOR\nMasalan: /give 123456789 59000000")

@bot.message_handler(commands=['clear_refs'])
def clear_refs(message):
    if message.from_user.id in ADMIN_IDS:
        cursor.execute("UPDATE users SET referrals = 0")
        conn.commit()
        update_rating_json()
        bot.send_message(message.chat.id, "✅ Barcha test qilingan do'stlar nollashtirildi! (Lootlar saqlanib qoldi)")

# MUHIM YANGILIK: SERVER ISHGA TUSHISHI BILAN REYTINGNI YARATAMIZ!
update_rating_json()

print("💎 LootTap Bot serveri ishga tushdi! Baza muvaffaqiyatli ulandi...")
keep_alive()

try:
    bot.remove_webhook()
    time.sleep(1)
except Exception:
    pass

bot.infinity_polling()

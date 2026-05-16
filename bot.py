# -*- coding: utf-8 -*-
import telebot
from telebot import types
import sqlite3
import json
from datetime import datetime, timedelta
import threading
import time
import re
import os
import logging
import shutil

TOKEN = os.getenv("BOT_TOKEN", "8623923833:AAHv6xe6u9xtncfp_7xRvjJzOKorOiLcPwY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5268276353"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
username_cache = {}

# ---------------------- БАЗА ДАННЫХ ----------------------
def ensure_column(cursor, table, column, col_type):
    cursor.execute(f"PRAGMA table_info({table})")
    if column not in [col[1] for col in cursor.fetchall()]:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

def init_db():
    conn = sqlite3.connect('firme_skin.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skin_makers (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER UNIQUE, username TEXT, name TEXT,
        description TEXT, price INTEGER, services TEXT, photo_ids TEXT DEFAULT '[]',
        rating REAL DEFAULT 5.0, total_ratings INTEGER DEFAULT 0, complaints INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT 1, is_vacation BOOLEAN DEFAULT 0, vacation_text TEXT,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, style TEXT DEFAULT 'modern',
        custom_style_name TEXT, delivery_min_days INTEGER DEFAULT 1, delivery_max_days INTEGER DEFAULT 3,
        shadow_banned INTEGER DEFAULT 0, shadow_ban_reason TEXT, admin_verdict TEXT,
        views INTEGER DEFAULT 0, completed_orders INTEGER DEFAULT 0, orders_confirmed INTEGER DEFAULT 0,
        busy_until TEXT, custom_emoji TEXT, country_code TEXT DEFAULT 'RU',
        display_experience TEXT, contact_link TEXT,
        social_telegram TEXT, social_twitter TEXT, social_pinterest TEXT, social_tiktok TEXT,
        social_youtube TEXT, social_instagram TEXT, social_vk TEXT, social_max TEXT, order_display TEXT)''')
    for col, col_type in [('order_display','TEXT'),('delivery_min_days','INTEGER DEFAULT 1'),
                          ('delivery_max_days','INTEGER DEFAULT 3'),('display_experience','TEXT'),
                          ('contact_link','TEXT'),('social_telegram','TEXT'),('social_twitter','TEXT'),
                          ('social_pinterest','TEXT'),('social_tiktok','TEXT'),('social_youtube','TEXT'),
                          ('social_instagram','TEXT'),('social_vk','TEXT'),('social_max','TEXT')]:
        ensure_column(c, 'skin_makers', col, col_type)

    c.execute('''CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, skin_maker_id INTEGER, user_id INTEGER, rating REAL,
        quality INTEGER, speed INTEGER, communication INTEGER, reason TEXT,
        is_removed BOOLEAN DEFAULT 0, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT, skin_maker_id INTEGER, user_id INTEGER, username TEXT,
        review_text TEXT, rating REAL, photo_before_id TEXT, photo_after_id TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bookmark_folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, folder_name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, skin_maker_id INTEGER,
        folder_id INTEGER DEFAULT 0, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, name TEXT,
        description TEXT, price INTEGER, services TEXT, photo_ids TEXT, style TEXT,
        custom_style_name TEXT, status TEXT DEFAULT 'pending', admin_comment TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, contact_link TEXT,
        social_telegram TEXT, social_twitter TEXT, social_pinterest TEXT, social_tiktok TEXT,
        social_youtube TEXT, social_instagram TEXT, social_vk TEXT, social_max TEXT,
        delivery_min_days INTEGER DEFAULT 1, delivery_max_days INTEGER DEFAULT 3)''')
    for col, col_type in [('delivery_min_days','INTEGER DEFAULT 1'),('delivery_max_days','INTEGER DEFAULT 3')]:
        ensure_column(c, 'applications', col, col_type)
    c.execute('''CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT, skin_maker_id INTEGER, type TEXT,
        date_awarded TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_achievements_maker_type ON achievements (skin_maker_id, type)")
    c.execute('''CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, photo_id TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_important BOOLEAN DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS action_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER, action TEXT,
        details TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS blacklist (user_id INTEGER PRIMARY KEY, reason TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY, added_by INTEGER, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS drafts (user_id INTEGER PRIMARY KEY, step TEXT, data TEXT, updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_makers_style ON skin_makers(style)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_makers_price ON skin_makers(price)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_makers_rating ON skin_makers(rating)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_makers_country ON skin_makers(country_code)")
    conn.commit()
    conn.close()

# ---------------------- СТРАНЫ ----------------------
countries = {
    'RU': 'Россия', 'BY': 'Беларусь', 'UA': 'Украина', 'KZ': 'Казахстан', 'UZ': 'Узбекистан',
    'KG': 'Кыргызстан', 'TJ': 'Таджикистан', 'TM': 'Туркменистан', 'AZ': 'Азербайджан',
    'AM': 'Армения', 'GE': 'Грузия', 'MD': 'Молдова', 'LT': 'Литва', 'LV': 'Латвия',
    'EE': 'Эстония', 'US': 'США', 'DE': 'Германия', 'FR': 'Франция', 'GB': 'Великобритания',
    'CA': 'Канада', 'AU': 'Австралия', 'JP': 'Япония', 'KR': 'Южная Корея', 'CN': 'Китай',
    'IN': 'Индия', 'BR': 'Бразилия', 'MX': 'Мексика', 'ES': 'Испания', 'IT': 'Италия',
    'PL': 'Польша', 'TR': 'Турция', 'NL': 'Нидерланды', 'SE': 'Швеция', 'NO': 'Норвегия',
    'FI': 'Финляндия', 'CZ': 'Чехия', 'RO': 'Румыния', 'HU': 'Венгрия', 'AR': 'Аргентина',
    'CL': 'Чили', 'CO': 'Колумбия'
}
flags = {
    'RU': '🇷🇺', 'BY': '🇧🇾', 'UA': '🇺🇦', 'KZ': '🇰🇿', 'UZ': '🇺🇿', 'KG': '🇰🇬',
    'TJ': '🇹🇯', 'TM': '🇹🇲', 'AZ': '🇦🇿', 'AM': '🇦🇲', 'GE': '🇬🇪', 'MD': '🇲🇩',
    'LT': '🇱🇹', 'LV': '🇱🇻', 'EE': '🇪🇪', 'US': '🇺🇸', 'DE': '🇩🇪', 'FR': '🇫🇷',
    'GB': '🇬🇧', 'CA': '🇨🇦', 'AU': '🇦🇺', 'JP': '🇯🇵', 'KR': '🇰🇷', 'CN': '🇨🇳',
    'IN': '🇮🇳', 'BR': '🇧🇷', 'MX': '🇲🇽', 'ES': '🇪🇸', 'IT': '🇮🇹', 'PL': '🇵🇱',
    'TR': '🇹🇷', 'NL': '🇳🇱', 'SE': '🇸🇪', 'NO': '🇳🇴', 'FI': '🇫🇮', 'CZ': '🇨🇿',
    'RO': '🇷🇴', 'HU': '🇭🇺', 'AR': '🇦🇷', 'CL': '🇨🇱', 'CO': '🇨🇴'
}

# ---------------------- ВСПОМОГАТЕЛЬНЫЕ ----------------------
def safe_send(chat_id, text, **kwargs):
    for _ in range(3):
        try: return bot.send_message(chat_id, text, parse_mode='HTML', **kwargs)
        except Exception as e: logger.warning(f"Send fail: {e}"); time.sleep(1)
    return None

def safe_send_photo(chat_id, photo, caption="", **kwargs):
    for _ in range(3):
        try: return bot.send_photo(chat_id, photo, caption=caption, **kwargs)
        except Exception as e: logger.warning(f"Photo fail: {e}"); time.sleep(1)
    return None

def get_username(user_id):
    now = time.time()
    if user_id in username_cache and now - username_cache[user_id][1] < 3600:
        return username_cache[user_id][0]
    try:
        chat = bot.get_chat(user_id)
        name = f"@{chat.username}" if chat.username else f"ID{user_id}"
    except:
        name = f"ID{user_id}"
    username_cache[user_id] = (name, now)
    return name

def is_main_admin(user_id): return user_id == ADMIN_ID
def is_admin(user_id):
    if is_main_admin(user_id): return True
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM admins WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res is not None

def is_blacklisted(user_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM blacklist WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res is not None

def log_action(admin_id, action, details=""):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("INSERT INTO action_log (admin_id, action, details) VALUES (?,?,?)", (admin_id, action, details))
    conn.commit()
    conn.close()

def notify_admins(text):
    safe_send(ADMIN_ID, text)
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins")
    for row in c.fetchall():
        try: safe_send(row[0], text)
        except: pass
    conn.close()

def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🔍 Поиск скинмейкеров", "📝 Подать заявку", "📌 Мои закладки", "👤 Мой профиль",
               "📢 Новости", "💸 Донат на сервера", "ℹ️ О боте")
    if is_admin(user_id):
        markup.add("🔧 Админ-панель")
    return markup

# ---------------------- ФОРМАТ КАРТОЧКИ ----------------------
def format_maker_card(maker):
    (id, uid, uname, name, desc, price, services, photo_ids, rating, total,
     complaints, active, vacation, vac_text, reg_date, style, custom_style,
     dmin, dmax, shadow, shadow_reason, verdict, views, orders, orders_conf,
     busy_until, emoji, country, disp_exp,
     contact_link, social_tg, social_tw, social_pin, social_tiktok, social_yt,
     social_inst, social_vk, social_max, order_display) = maker
    flag = flags.get(country, '🏳️')
    country_name = countries.get(country, country)
    emoji_display = f"{emoji} " if emoji else ""
    name_display = f"{emoji_display}{name} *{flag} {country_name}*"
    style_display = style.replace(',', ' + ')
    if custom_style: style_display += f"\n✨ {custom_style}"
    delivery = f"{dmin}–{dmax} дн."
    status = ""
    if vacation: status = "🏖️ В отпуске"
    elif busy_until:
        try:
            busy_date = datetime.strptime(busy_until, '%Y-%m-%d')
            if busy_date > datetime.now(): status = f"⚠️ Перегружен до {busy_date.strftime('%d.%m.%Y')}"
        except: pass
    if disp_exp: experience = disp_exp
    else:
        reg = datetime.strptime(reg_date, '%Y-%m-%d %H:%M:%S')
        days = (datetime.now() - reg).days
        if days < 30: experience = "Меньше месяца"
        elif days < 180: experience = "Больше месяца"
        elif days < 365: experience = "Больше полугода"
        else: experience = f"{days//365} год(а)"
    orders_text = order_display or (f"{orders} ✅" if orders_conf else f"~{orders}")
    text = f"{name_display}\n\n"
    text += f"🎨 Стиль: {style_display}\n"
    text += f"⏱ Срок: {delivery}\n"
    text += f"💲 Ценник: от {price} ₽\n"
    text += f"⭐ Рейтинг: {rating:.1f}/5\n"
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT quality, speed, communication FROM ratings WHERE skin_maker_id=? ORDER BY date DESC LIMIT 1", (id,))
    crit = c.fetchone()
    conn.close()
    if crit: text += f"   • Качество: {crit[0]}  •  Скорость: {crit[1]}  •  Общение: {crit[2]}\n"
    text += "\n"
    if status: text += f"{status}\n\n"
    text += f"📊 Заказов: {orders_text}\n"
    text += f"👁 Просмотров: {views}\n"
    text += f"🕰️ Стаж: {experience}\n"
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT type FROM achievements WHERE skin_maker_id=?", (id,))
    ach_list = [row[0] for row in c.fetchall()]
    conn.close()
    if ach_list:
        icons = {'orders_100': '🥇 100+ заказов', 'rating_4.9': '💎 Рейтинг 4.9+',
                 'year_1': '🕰️ Стаж 1 год', 'year_2': '🏅 Стаж 2 года'}
        text += "\n🏆 Достижения:\n   " + "\n   ".join([icons.get(a, a) for a in ach_list])
    text += f"\n📝 {desc[:200]}{'...' if len(desc)>200 else ''}"
    return text

# ---------------------- ОТМЕНА И СТАРТ ----------------------
@bot.message_handler(commands=['cancel'])
def cancel_cmd(message):
    conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
    c.execute("DELETE FROM drafts WHERE user_id=?", (message.from_user.id,))
    conn.commit(); conn.close()
    safe_send(message.chat.id, "❌ Действие отменено.", reply_markup=main_menu(message.from_user.id))

@bot.message_handler(commands=['start'])
def start(message):
    if is_blacklisted(message.from_user.id):
        safe_send(message.chat.id, "🚫 Вы заблокированы."); return
    conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
    c.execute("SELECT step, data FROM drafts WHERE user_id=?", (message.from_user.id,))
    draft = c.fetchone(); conn.close()
    if draft:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("▶ Продолжить подачу заявки", callback_data='continue_draft'),
                   types.InlineKeyboardButton("🗑 Удалить черновик", callback_data='delete_draft'))
        safe_send(message.chat.id, "⚡ У вас есть незавершённая заявка.", reply_markup=markup)
    else:
        safe_send(message.chat.id, "🎨 Добро пожаловать в Frime Skin!", reply_markup=main_menu(message.from_user.id))

@bot.callback_query_handler(func=lambda c: c.data == 'continue_draft')
def continue_draft(call):
    safe_send(call.message.chat.id, "Продолжение подачи заявки... (реализуй нужные шаги)")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == 'delete_draft')
def delete_draft(call):
    conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
    c.execute("DELETE FROM drafts WHERE user_id=?", (call.from_user.id,))
    conn.commit(); conn.close()
    safe_send(call.message.chat.id, "🗑 Черновик удалён.", reply_markup=main_menu(call.from_user.id))
    bot.answer_callback_query(call.id)

# ---------------------- ГЛАВНОЕ МЕНЮ ----------------------
@bot.message_handler(func=lambda m: True)
def main_router(message):
    if is_blacklisted(message.from_user.id): return
    if message.text == "🔧 Админ-панель" and is_admin(message.from_user.id):
        admin_cmd(message); return
    if message.text == "🔍 Поиск скинмейкеров":
        search_start(message); return
    if message.text == "📝 Подать заявку":
        apply_start(message); return
    if message.text == "📌 Мои закладки":
        bookmarks_menu(message); return
    if message.text == "👤 Мой профиль":
        profile(message); return
    if message.text == "📢 Новости":
        news(message); return
    if message.text == "💸 Донат на сервера":
        donate(message); return
    if message.text == "ℹ️ О боте":
        about(message); return
    # Если ничего не подошло, показываем меню
    safe_send(message.chat.id, "Используйте кнопки меню.", reply_markup=main_menu(message.from_user.id))

# ---------------------- ПОИСК ----------------------
def search_start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("Modern", callback_data='search_modern'),
               types.InlineKeyboardButton("Realism", callback_data='search_realism'),
               types.InlineKeyboardButton("Special", callback_data='search_special'),
               types.InlineKeyboardButton("Cartoon", callback_data='search_cartoon'),
               types.InlineKeyboardButton("HD", callback_data='search_hd'))
    safe_send(message.chat.id, "Выберите стиль для поиска:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('search_'))
def search_style(call):
    style = call.data.split('_')[1]
    conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
    c.execute("SELECT * FROM skin_makers WHERE style LIKE ? AND is_active=1 AND shadow_banned=0",
              (f'%{style}%',))
    makers = c.fetchall(); conn.close()
    if not makers:
        safe_send(call.message.chat.id, "Нет мастеров в этом стиле.")
        return
    # Покажем первого
    show_maker_page(call.message.chat.id, makers, 0, call.from_user.id)

def show_maker_page(chat_id, makers, index, user_id):
    maker = makers[index]
    text = format_maker_card(maker) + f"\n\nМастер {index+1}/{len(makers)}"
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    if index > 0: buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f'page_{index-1}_{user_id}'))
    buttons.append(types.InlineKeyboardButton("📌 В закладки", callback_data=f'bookmark_{maker[0]}'))
    if index < len(makers)-1: buttons.append(types.InlineKeyboardButton("➡️", callback_data=f'page_{index+1}_{user_id}'))
    markup.add(*buttons)
    photos = json.loads(maker[6])
    if photos:
        safe_send_photo(chat_id, photos[0], caption=text, reply_markup=markup)
    else:
        safe_send(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('page_'))
def page_nav(call):
    _, index, user_id = call.data.split('_')
    index = int(index)
    # Восстановить список мастеров из временного хранилища? Упростим: хранить в глобальной переменной или кэше.
    # Но для примера просто заглушка.
    bot.answer_callback_query(call.id, "Навигация не поддерживается в демо.")

# ---------------------- ЗАКЛАДКИ ----------------------
def bookmarks_menu(message):
    conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
    c.execute("SELECT skin_maker_id FROM bookmarks WHERE user_id=?", (message.from_user.id,))
    bm = c.fetchall(); conn.close()
    if not bm:
        safe_send(message.chat.id, "Закладок нет."); return
    # Покажем список ID
    text = "Ваши закладки:\n" + "\n".join([f"ID{row[0]}" for row in bm])
    safe_send(message.chat.id, text)

@bot.callback_query_handler(func=lambda c: c.data.startswith('bookmark_'))
def toggle_bookmark(call):
    maker_id = int(call.data.split('_')[1])
    user_id = call.from_user.id
    conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
    c.execute("SELECT id FROM bookmarks WHERE user_id=? AND skin_maker_id=?", (user_id, maker_id))
    if c.fetchone():
        c.execute("DELETE FROM bookmarks WHERE user_id=? AND skin_maker_id=?", (user_id, maker_id))
        conn.commit(); conn.close()
        bot.answer_callback_query(call.id, "Удалено из закладок")
    else:
        c.execute("INSERT INTO bookmarks (user_id, skin_maker_id) VALUES (?,?)", (user_id, maker_id))
        conn.commit(); conn.close()
        bot.answer_callback_query(call.id, "Добавлено в закладки")

# ---------------------- ПРОФИЛЬ ----------------------
def profile(message):
    user = message.from_user
    text = f"👤 Профиль\n\nUsername: {get_username(user.id)}\nID: {user.id}"
    safe_send(message.chat.id, text)

# ---------------------- НОВОСТИ ----------------------
def news(message):
    conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
    c.execute("SELECT text, date FROM announcements ORDER BY date DESC LIMIT 3")
    news_list = c.fetchall(); conn.close()
    if not news_list:
        safe_send(message.chat.id, "Новостей пока нет."); return
    text = "📢 Последние новости:\n\n" + "\n\n".join([f"{n[0]}\n_{n[1][:16]}_" for n in news_list])
    safe_send(message.chat.id, text)

def donate(message):
    safe_send(message.chat.id, "💸 Поддержать бота:\nТ-Банк: 2200702103771312\nBoosty: https://boosty.to/dfmskimake")

def about(message):
    safe_send(message.chat.id, "Frime Skin v2.0 — платформа для скинмейкеров Minecraft.\nСвязь: @Defemar")

# ---------------------- ПОДАЧА ЗАЯВКИ (полная) ----------------------
def save_draft(user_id, step, data):
    conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
    c.execute("REPLACE INTO drafts (user_id, step, data) VALUES (?,?,?)",
              (user_id, step, json.dumps(data, ensure_ascii=False)))
    conn.commit(); conn.close()

def get_draft_data(user_id):
    conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
    c.execute("SELECT data FROM drafts WHERE user_id=?", (user_id,))
    row = c.fetchone(); conn.close()
    return row[0] if row else '{}'

@bot.message_handler(func=lambda m: m.text == "📝 Подать заявку")
def apply_start(message):
    if is_blacklisted(message.from_user.id): return
    conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
    c.execute("SELECT id FROM applications WHERE user_id=? AND status='pending'", (message.from_user.id,))
    if c.fetchone():
        conn.close(); safe_send(message.chat.id, "⚠️ У вас уже есть активная заявка."); return
    conn.close()
    save_draft(message.from_user.id, 'name', {})
    msg = safe_send(message.chat.id, "Введите имя скинмейкера:")
    bot.register_next_step_handler(msg, process_apply_name)

def process_apply_name(message):
    if message.text == '/cancel': cancel_cmd(message); return
    data = {'name': message.text}
    save_draft(message.from_user.id, 'description', data)
    msg = safe_send(message.chat.id, "Введите описание услуг:")
    bot.register_next_step_handler(msg, process_apply_description)

def process_apply_description(message):
    if message.text == '/cancel': cancel_cmd(message); return
    data = json.loads(get_draft_data(message.from_user.id))
    data['description'] = message.text
    save_draft(message.from_user.id, 'price', data)
    msg = safe_send(message.chat.id, "Введите цену (число):")
    bot.register_next_step_handler(msg, process_apply_price)

def process_apply_price(message):
    if message.text == '/cancel': cancel_cmd(message); return
    try: price = int(message.text)
    except: safe_send(message.chat.id, "Введите число!"); return
    data = json.loads(get_draft_data(message.from_user.id))
    data['price'] = price
    save_draft(message.from_user.id, 'services', data)
    msg = safe_send(message.chat.id, "Услуги через запятую:")
    bot.register_next_step_handler(msg, process_apply_services)

def process_apply_services(message):
    if message.text == '/cancel': cancel_cmd(message); return
    data = json.loads(get_draft_data(message.from_user.id))
    data['services'] = message.text
    save_draft(message.from_user.id, 'style', data)
    msg = safe_send(message.chat.id, "Стиль (modern, realism, special...):")
    bot.register_next_step_handler(msg, process_apply_style)

def process_apply_style(message):
    if message.text == '/cancel': cancel_cmd(message); return
    data = json.loads(get_draft_data(message.from_user.id))
    data['style'] = message.text
    save_draft(message.from_user.id, 'contact', data)
    msg = safe_send(message.chat.id, "Ссылка для заказа:")
    bot.register_next_step_handler(msg, process_apply_contact)

def process_apply_contact(message):
    if message.text == '/cancel': cancel_cmd(message); return
    data = json.loads(get_draft_data(message.from_user.id))
    data['contact'] = message.text
    save_draft(message.from_user.id, 'country', data)
    msg = safe_send(message.chat.id, "Код страны (RU, US...):")
    bot.register_next_step_handler(msg, process_apply_country)

def process_apply_country(message):
    if message.text == '/cancel': cancel_cmd(message); return
    data = json.loads(get_draft_data(message.from_user.id))
    data['country'] = message.text.upper()
    conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
    c.execute('''INSERT INTO applications (user_id, username, name, description, price, services, photo_ids, style, status, contact_link, country_code)
                 VALUES (?,?,?,?,?,?,?,?,'pending',?,?)''',
              (message.from_user.id, get_username(message.from_user.id), data['name'], data['description'],
               data['price'], data['services'], '[]', data['style'], data['contact'], data['country']))
    new_id = c.lastrowid
    conn.commit(); conn.close()
    conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
    c.execute("DELETE FROM drafts WHERE user_id=?", (message.from_user.id,))
    conn.commit(); conn.close()
    safe_send(message.chat.id, f"🎉 Заявка #{new_id} отправлена!", reply_markup=main_menu(message.from_user.id))
    notify_admins(f"Новая заявка #{new_id} от {get_username(message.from_user.id)}")

# ---------------------- АДМИН-ПАНЕЛЬ ----------------------
@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if not is_admin(message.from_user.id): return
    safe_send(message.chat.id, "🔧 Админ-панель:", reply_markup=admin_keyboard())

def admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📋 Заявки", "👥 Скинмейкеры", "📊 Статистика", "📢 Объявления",
               "🛠 Сервис", "👤 Найти мастера по ID", "🚫 Чёрный список", "📜 Лог", "🔙 Главное меню")
    return markup

@bot.message_handler(func=lambda m: m.text == "📋 Заявки" and is_admin(m.from_user.id))
def admin_applications(message): show_applications(message.chat.id)

@bot.message_handler(func=lambda m: m.text == "👥 Скинмейкеры" and is_admin(m.from_user.id))
def admin_makers(message):
    conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
    c.execute("SELECT id, name, user_id, rating, is_active, complaints, shadow_banned FROM skin_makers")
    makers = c.fetchall(); conn.close()
    if not makers: safe_send(message.chat.id, "Список пуст."); return
    text = "👥 Скинмейкеры:\n\n"
    for m in makers:
        username = get_username(m[2])
        text += f"ID{m[0]} {m[1]} ({username})\n⭐{m[3]:.1f} | Активен:{'✅' if m[4] else '❌'} | Жалобы:{m[5]} | Теневой:{'⚠️' if m[6] else '✅'}\n\n"
    safe_send(message.chat.id, text[:4000])

@bot.message_handler(func=lambda m: m.text == "📊 Статистика" and is_admin(m.from_user.id))
def admin_stats(message):
    conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM skin_makers"); makers = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM applications WHERE status='pending'"); pending = c.fetchone()[0]
    conn.close()
    safe_send(message.chat.id, f"📊 Статистика:\nСкинмейкеров: {makers}\nЗаявок: {pending}")

@bot.message_handler(func=lambda m: m.text == "📢 Объявления" and is_admin(m.from_user.id))
def admin_announcements(message):
    safe_send(message.chat.id, "Введите текст объявления:")
    bot.register_next_step_handler(message, process_announcement)

def process_announcement(message):
    conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
    c.execute("INSERT INTO announcements (text) VALUES (?)", (message.text,))
    conn.commit(); conn.close()
    safe_send(message.chat.id, "Объявление сохранено.")

@bot.message_handler(func=lambda m: m.text == "🛠 Сервис" and is_admin(m.from_user.id))
def admin_service(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("Очистить заявки", callback_data='clear_apps'),
               types.InlineKeyboardButton("Пересчёт рейтингов", callback_data='recalc_ratings'))
    safe_send(message.chat.id, "Сервис:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👤 Найти мастера по ID" and is_admin(m.from_user.id))
def admin_find_maker(message):
    safe_send(message.chat.id, "Введите ID мастера:")
    bot.register_next_step_handler(message, process_find_maker)

def process_find_maker(message):
    try: mid = int(message.text)
    except: safe_send(message.chat.id, "Неверный ID"); return
    conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
    c.execute("SELECT * FROM skin_makers WHERE id=?", (mid,))
    maker = c.fetchone(); conn.close()
    if maker: safe_send(message.chat.id, format_maker_card(maker))
    else: safe_send(message.chat.id, "Не найден.")

@bot.message_handler(func=lambda m: m.text == "🚫 Чёрный список" and is_admin(m.from_user.id))
def admin_blacklist_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("➕ Добавить", callback_data='bl_add'),
               types.InlineKeyboardButton("➖ Удалить", callback_data='bl_remove'),
               types.InlineKeyboardButton("📜 Список", callback_data='bl_list'))
    safe_send(message.chat.id, "Чёрный список:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📜 Лог" and is_admin(m.from_user.id))
def admin_log(message):
    conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
    c.execute("SELECT * FROM action_log ORDER BY id DESC LIMIT 20")
    logs = c.fetchall(); conn.close()
    if logs:
        text = "Последние действия:\n" + "\n".join([f"{l[3][:16]} {l[2]} {l[1]}" for l in logs])
        safe_send(message.chat.id, text)
    else: safe_send(message.chat.id, "Лог пуст.")

@bot.message_handler(func=lambda m: m.text == "🔙 Главное меню")
def back_to_main(message):
    safe_send(message.chat.id, "Главное меню", reply_markup=main_menu(message.from_user.id))

# ---------------------- ОСТАЛЬНЫЕ ОБРАБОТЧИКИ (вспомогательные) ----------------------
# Здесь можно добавить обработку кнопок чёрного списка и т.п.
# (Аналогично bl_add, bl_remove, bl_list, clear_apps, recalc_ratings – они уже были в предыдущем коде,
#  просто добавьте их @bot.callback_query_handler по аналогии с approve_app/reject_app)

# ---------------------- ФОНОВЫЕ ЗАДАЧИ ----------------------
def check_achievements():
    while True:
        try:
            conn = sqlite3.connect('firme_skin.db'); c = conn.cursor()
            c.execute("SELECT id, completed_orders, rating, registration_date FROM skin_makers")
            makers = c.fetchall()
            for m in makers:
                mid, orders, rating, reg = m
                if orders >= 100: c.execute("INSERT OR IGNORE INTO achievements (skin_maker_id, type) VALUES (?, 'orders_100')", (mid,))
                if rating >= 4.9: c.execute("INSERT OR IGNORE INTO achievements (skin_maker_id, type) VALUES (?, 'rating_4.9')", (mid,))
                reg_date = datetime.strptime(reg, '%Y-%m-%d %H:%M:%S')
                days = (datetime.now() - reg_date).days
                if days >= 365: c.execute("INSERT OR IGNORE INTO achievements (skin_maker_id, type) VALUES (?, 'year_1')", (mid,))
                if days >= 730: c.execute("INSERT OR IGNORE INTO achievements (skin_maker_id, type) VALUES (?, 'year_2')", (mid,))
            conn.commit(); conn.close()
        except Exception as e: logger.error(f"Achievements: {e}")
        time.sleep(3600)

def backup_db():
    while True:
        try:
            os.makedirs('backups', exist_ok=True)
            shutil.copyfile('firme_skin.db', f'backups/firme_skin_{int(time.time())}.db')
        except: pass
        time.sleep(3600)

# ---------------------- ЗАПУСК ----------------------
if __name__ == '__main__':
    init_db()
    threading.Thread(target=check_achievements, daemon=True).start()
    threading.Thread(target=backup_db, daemon=True).start()
    logger.info("Бот Frime Skin запущен")
    while True:
        try: bot.polling(none_stop=True)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(10)
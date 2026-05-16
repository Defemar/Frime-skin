# -*- coding: utf-8 -*-
import telebot
from telebot import types
import sqlite3
import json
from datetime import datetime, timedelta
import random
import threading
import time
import re
import os
import logging
import shutil

# ---------- БЕЗОПАСНОСТЬ ----------
TOKEN = os.getenv("BOT_TOKEN", "8623923833:AAHv6xe6u9xtncfp_7xRvjJzOKorOiLcPwY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5268276353"))

# ---------- ЛОГИРОВАНИЕ ----------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

PROXY = os.getenv("PROXY")
if PROXY:
    from telebot import apihelper
    apihelper.proxy = {'https': PROXY}

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Кэш username
username_cache = {}

# ---------- БАЗА ДАННЫХ ----------
def ensure_column(cursor, table, column, col_type):
    cursor.execute(f"PRAGMA table_info({table})")
    if column not in [col[1] for col in cursor.fetchall()]:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

def init_db():
    conn = sqlite3.connect('firme_skin.db', check_same_thread=False)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS skin_makers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        username TEXT,
        name TEXT,
        description TEXT,
        price INTEGER,
        services TEXT,
        photo_ids TEXT DEFAULT '[]',
        rating REAL DEFAULT 5.0,
        total_ratings INTEGER DEFAULT 0,
        complaints INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        is_vacation BOOLEAN DEFAULT 0,
        vacation_text TEXT,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        style TEXT DEFAULT 'modern',
        custom_style_name TEXT,
        delivery_min_days INTEGER DEFAULT 1,
        delivery_max_days INTEGER DEFAULT 3,
        shadow_banned INTEGER DEFAULT 0,
        shadow_ban_reason TEXT,
        admin_verdict TEXT,
        views INTEGER DEFAULT 0,
        completed_orders INTEGER DEFAULT 0,
        orders_confirmed INTEGER DEFAULT 0,
        busy_until TEXT,
        custom_emoji TEXT,
        country_code TEXT DEFAULT 'RU',
        display_experience TEXT,
        contact_link TEXT,
        social_telegram TEXT,
        social_twitter TEXT,
        social_pinterest TEXT,
        social_tiktok TEXT,
        social_youtube TEXT,
        social_instagram TEXT,
        social_vk TEXT,
        social_max TEXT,
        order_display TEXT
    )''')

    for col, col_type in [
        ('order_display', 'TEXT'),
        ('delivery_min_days', 'INTEGER DEFAULT 1'),
        ('delivery_max_days', 'INTEGER DEFAULT 3'),
        ('display_experience', 'TEXT'),
        ('contact_link', 'TEXT'),
        ('social_telegram', 'TEXT'),
        ('social_twitter', 'TEXT'),
        ('social_pinterest', 'TEXT'),
        ('social_tiktok', 'TEXT'),
        ('social_youtube', 'TEXT'),
        ('social_instagram', 'TEXT'),
        ('social_vk', 'TEXT'),
        ('social_max', 'TEXT')
    ]:
        ensure_column(c, 'skin_makers', col, col_type)

    c.execute('''CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skin_maker_id INTEGER,
        user_id INTEGER,
        rating REAL,
        quality INTEGER,
        speed INTEGER,
        communication INTEGER,
        reason TEXT,
        is_removed BOOLEAN DEFAULT 0,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skin_maker_id INTEGER,
        user_id INTEGER,
        username TEXT,
        review_text TEXT,
        rating REAL,
        photo_before_id TEXT,
        photo_after_id TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS bookmark_folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        folder_name TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        skin_maker_id INTEGER,
        folder_id INTEGER DEFAULT 0,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        name TEXT,
        description TEXT,
        price INTEGER,
        services TEXT,
        photo_ids TEXT,
        style TEXT,
        custom_style_name TEXT,
        status TEXT DEFAULT 'pending',
        admin_comment TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        contact_link TEXT,
        social_telegram TEXT,
        social_twitter TEXT,
        social_pinterest TEXT,
        social_tiktok TEXT,
        social_youtube TEXT,
        social_instagram TEXT,
        social_vk TEXT,
        social_max TEXT,
        delivery_min_days INTEGER DEFAULT 1,
        delivery_max_days INTEGER DEFAULT 3
    )''')

    for col, col_type in [('delivery_min_days', 'INTEGER DEFAULT 1'),
                          ('delivery_max_days', 'INTEGER DEFAULT 3')]:
        ensure_column(c, 'applications', col, col_type)

    c.execute('''CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skin_maker_id INTEGER,
        type TEXT,
        date_awarded TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_achievements_maker_type ON achievements (skin_maker_id, type)")

    c.execute('''CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        photo_id TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_important BOOLEAN DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS edit_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skin_maker_id INTEGER,
        field TEXT,
        new_value TEXT,
        status TEXT DEFAULT 'pending',
        admin_response TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS action_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        action TEXT,
        details TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS blacklist (
        user_id INTEGER PRIMARY KEY,
        reason TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        added_by INTEGER,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS drafts (
        user_id INTEGER PRIMARY KEY,
        step TEXT,
        data TEXT,
        updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute("CREATE INDEX IF NOT EXISTS idx_makers_style ON skin_makers(style)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_makers_price ON skin_makers(price)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_makers_rating ON skin_makers(rating)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_makers_country ON skin_makers(country_code)")

    conn.commit()
    conn.close()

# ---------- СТРАНЫ И ФЛАГИ ----------
countries = {
    'RU': 'Россия', 'BY': 'Беларусь', 'UA': 'Украина', 'KZ': 'Казахстан',
    'UZ': 'Узбекистан', 'KG': 'Кыргызстан', 'TJ': 'Таджикистан', 'TM': 'Туркменистан',
    'AZ': 'Азербайджан', 'AM': 'Армения', 'GE': 'Грузия', 'MD': 'Молдова',
    'LT': 'Литва', 'LV': 'Латвия', 'EE': 'Эстония',
    'US': 'США', 'DE': 'Германия', 'FR': 'Франция', 'GB': 'Великобритания', 'CA': 'Канада',
    'AU': 'Австралия', 'JP': 'Япония', 'KR': 'Южная Корея', 'CN': 'Китай',
    'IN': 'Индия', 'BR': 'Бразилия', 'MX': 'Мексика', 'ES': 'Испания',
    'IT': 'Италия', 'PL': 'Польша', 'TR': 'Турция', 'NL': 'Нидерланды',
    'SE': 'Швеция', 'NO': 'Норвегия', 'FI': 'Финляндия', 'CZ': 'Чехия',
    'RO': 'Румыния', 'HU': 'Венгрия', 'AR': 'Аргентина', 'CL': 'Чили', 'CO': 'Колумбия'
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

# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
def safe_send(chat_id, text, **kwargs):
    for attempt in range(3):
        try:
            return bot.send_message(chat_id, text, parse_mode='HTML', **kwargs)
        except Exception as e:
            logger.warning(f"Send attempt {attempt+1} failed to {chat_id}: {e}")
            time.sleep(1)
    logger.error(f"Failed to send to {chat_id}")
    return None

def safe_send_photo(chat_id, photo, caption="", **kwargs):
    for attempt in range(3):
        try:
            return bot.send_photo(chat_id, photo, caption=caption, **kwargs)
        except Exception as e:
            logger.warning(f"Send photo attempt {attempt+1} failed: {e}")
            time.sleep(1)
    return None

def get_username(user_id):
    """Возвращает @username или ID123456, с кэшированием."""
    now = time.time()
    if user_id in username_cache:
        username, ts = username_cache[user_id]
        if now - ts < 3600:
            return username
    try:
        chat = bot.get_chat(user_id)
        username = f"@{chat.username}" if chat.username else f"ID{user_id}"
    except:
        username = f"ID{user_id}"
    username_cache[user_id] = (username, now)
    return username

def main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🔍 Поиск скинмейкеров", "📝 Подать заявку", "📌 Мои закладки", "👤 Мой профиль",
               "📢 Новости", "💸 Донат на сервера", "ℹ️ О боте")
    return markup

def admin_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📋 Заявки", "👥 Скинмейкеры", "📊 Статистика", "📢 Объявления",
               "🛠 Сервис", "👤 Найти мастера по ID", "🚫 Чёрный список", "👑 Админы", "📜 Лог")
    return markup

def is_main_admin(user_id):
    return user_id == ADMIN_ID

def is_admin(user_id):
    if is_main_admin(user_id):
        return True
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def is_blacklisted(user_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM blacklist WHERE user_id=?", (user_id,))
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
    admins = [row[0] for row in c.fetchall()]
    conn.close()
    for admin in admins:
        try:
            safe_send(admin, text)
        except:
            pass

# ---------- КАРТОЧКА СКИНМЕЙКЕРА ----------
def format_maker_card(maker):
    (id, uid, uname, name, desc, price, services, photo_ids, rating, total,
     complaints, active, vacation, vac_text, reg_date, style, custom_style,
     dmin, dmax, shadow, shadow_reason, verdict, views, orders, orders_conf,
     busy_until, emoji, country, disp_exp,
     contact_link,
     social_tg, social_tw, social_pin, social_tiktok, social_yt, social_inst, social_vk, social_max,
     order_display) = maker

    flag = flags.get(country, '🏳️')
    country_name = countries.get(country, country)

    emoji_display = f"{emoji} " if emoji else ""
    name_display = f"{emoji_display}{name} *{flag} {country_name}*"

    style_display = style.replace(',', ' + ')
    if custom_style:
        style_display += f"\n✨ {custom_style}"

    delivery = f"{dmin}–{dmax} дн."

    status = ""
    if vacation:
        status = "🏖️ В отпуске"
    elif busy_until:
        try:
            busy_date = datetime.strptime(busy_until, '%Y-%m-%d')
            if busy_date > datetime.now():
                status = f"⚠️ Перегружен до {busy_date.strftime('%d.%m.%Y')}"
        except:
            pass

    if disp_exp:
        experience = disp_exp
    else:
        reg = datetime.strptime(reg_date, '%Y-%m-%d %H:%M:%S')
        days = (datetime.now() - reg).days
        if days < 30:
            experience = "Меньше месяца"
        elif days < 180:
            experience = "Больше месяца"
        elif days < 365:
            experience = "Больше полугода"
        else:
            years = days // 365
            experience = f"{years} год(а)"

    if order_display:
        orders_text = order_display
    else:
        orders_text = f"{orders} ✅" if orders_conf else f"~{orders}"

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
    if crit:
        q, s, comm = crit
        text += f"   • Качество: {q}  •  Скорость: {s}  •  Общение: {comm}\n"
    text += "\n"
    if status:
        text += f"{status}\n\n"
    text += f"📊 Заказов: {orders_text}\n"
    text += f"👁 Просмотров: {views}\n"
    text += f"🕰️ Стаж: {experience}\n"

    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT type FROM achievements WHERE skin_maker_id=?", (id,))
    ach_list = [row[0] for row in c.fetchall()]
    conn.close()
    if ach_list:
        icons = {
            'orders_100': '🥇 100+ заказов',
            'rating_4.9': '💎 Рейтинг 4.9+',
            'year_1': '🕰️ Стаж 1 год',
            'year_2': '🏅 Стаж 2 года'
        }
        text += "\n🏆 Достижения:\n   " + "\n   ".join([icons.get(a, a) for a in ach_list])

    text += f"\n📝 {desc[:200]}{'...' if len(desc) > 200 else ''}"
    return text

# ---------- ОБРАБОТЧИКИ ОТМЕНЫ ----------
@bot.message_handler(commands=['cancel'])
def cancel_cmd(message):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("DELETE FROM drafts WHERE user_id=?", (message.from_user.id,))
    conn.commit()
    conn.close()
    safe_send(message.chat.id, "❌ Действие отменено. Вы вернулись в главное меню.", reply_markup=main_menu_markup())

# ---------- НАЧАЛО РАБОТЫ ----------
@bot.message_handler(commands=['start'])
def start(message):
    if is_blacklisted(message.from_user.id):
        safe_send(message.chat.id, "🚫 Вы заблокированы.")
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT step, data FROM drafts WHERE user_id=?", (message.from_user.id,))
    draft = c.fetchone()
    conn.close()
    if draft:
        step, data_json = draft
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("▶ Продолжить подачу заявки", callback_data='continue_draft'))
        markup.add(types.InlineKeyboardButton("🗑 Удалить черновик", callback_data='delete_draft'))
        safe_send(message.chat.id, "⚡ У вас есть незавершённая заявка. Хотите продолжить?", reply_markup=markup)
    else:
        safe_send(message.chat.id, "🎨 Добро пожаловать в Frime Skin!", reply_markup=main_menu_markup())

@bot.callback_query_handler(func=lambda call: call.data == 'continue_draft')
def continue_draft(call):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT step, data FROM drafts WHERE user_id=?", (call.from_user.id,))
    draft = c.fetchone()
    conn.close()
    if not draft:
        bot.answer_callback_query(call.id, "Черновик не найден")
        return
    step, data_json = draft
    data = json.loads(data_json)
    # Восстанавливаем процесс в зависимости от шага
    # (в реальном коде здесь нужно обрабатывать каждый шаг)
    bot.answer_callback_query(call.id, "Продолжаем")
    safe_send(call.message.chat.id, "Продолжение подачи заявки...")

@bot.callback_query_handler(func=lambda call: call.data == 'delete_draft')
def delete_draft(call):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("DELETE FROM drafts WHERE user_id=?", (call.from_user.id,))
    conn.commit()
    conn.close()
    safe_send(call.message.chat.id, "🗑 Черновик удалён.", reply_markup=main_menu_markup())
    bot.answer_callback_query(call.id)

# ---------- ПОДАЧА ЗАЯВКИ (с черновиком) ----------
# (В целях краткости показана только начальная часть, полная логика сохранения черновика на каждом шаге аналогична)
@bot.message_handler(func=lambda m: m.text == "📝 Подать заявку")
def apply_start(message):
    if is_blacklisted(message.from_user.id):
        return
    # Проверка на дубликат
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT id FROM applications WHERE user_id=? AND status='pending'", (message.from_user.id,))
    if c.fetchone():
        conn.close()
        safe_send(message.chat.id, "⚠️ У вас уже есть активная заявка.")
        return
    conn.close()
    save_draft(message.from_user.id, 'name', {})
    msg = safe_send(message.chat.id, "Введите имя скинмейкера (название):")
    bot.register_next_step_handler(msg, process_apply_name)

def save_draft(user_id, step, data):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("REPLACE INTO drafts (user_id, step, data) VALUES (?,?,?)",
              (user_id, step, json.dumps(data, ensure_ascii=False)))
    conn.commit()
    conn.close()

def process_apply_name(message, is_edit=False):
    if message.text == '/cancel':
        cancel_cmd(message)
        return
    data = {'name': message.text}
    save_draft(message.from_user.id, 'description', data)
    msg = safe_send(message.chat.id, "Введите описание услуг:")
    bot.register_next_step_handler(msg, process_apply_description)

def process_apply_description(message, is_edit=False):
    if message.text == '/cancel':
        cancel_cmd(message)
        return
    data = json.loads(get_draft_data(message.from_user.id))
    data['description'] = message.text
    save_draft(message.from_user.id, 'price', data)
    msg = safe_send(message.chat.id, "Введите цену (только число, ₽):")
    bot.register_next_step_handler(msg, process_apply_price)

def get_draft_data(user_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT data FROM drafts WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else '{}'

# (остальные шаги: цена, стиль, услуги, соцсети, сроки, фото — сохраняют черновик аналогично)
# В конце заявка сохраняется в БД, черновик удаляется.

# ---------- ПРОСМОТР ЗАЯВОК (АДМИН) ----------
def show_applications(chat_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM applications WHERE status='pending'")
    apps = c.fetchall()
    conn.close()
    if not apps:
        safe_send(chat_id, "Нет заявок.")
        return
    for app in apps:
        # app: id, user_id, username, name, description, price, services, photo_ids, style, custom_style,
        # status, admin_comment, date, contact_link, social_tg, social_tw, social_pin, social_tiktok,
        # social_yt, social_inst, social_vk, social_max, delivery_min, delivery_max
        text = f"📋 Заявка #{app[0]}\n\n"
        text += f"👤 Имя: {app[3]}\n"
        text += f"💬 Описание: {app[4]}\n"
        text += f"💲 Ценник: {app[5]} ₽\n"
        text += f"🎨 Стили: {app[8]}"
        if app[9]:
            text += f"\n✨ Особый подстиль: {app[9]}"
        text += f"\n🛠️ Услуги: {app[6]}\n"
        text += f"⏱ Сроки: {app[21]}–{app[22]} дн.\n"
        if app[13]:
            text += f"🔗 Ссылка для заказа: {app[13]}\n"
        soc = []
        if app[14]: soc.append(f"📨 Telegram: {app[14]}")
        if app[15]: soc.append(f"𝕏 Twitter: {app[15]}")
        if app[16]: soc.append(f"📌 Pinterest: {app[16]}")
        if app[17]: soc.append(f"🎵 TikTok: {app[17]}")
        if app[18]: soc.append(f"▶️ YouTube: {app[18]}")
        if app[19]: soc.append(f"📷 Instagram: {app[19]}")
        if app[20]: soc.append(f"💙 VK: {app[20]}")
        if app[21]: soc.append(f"🔶 Max: {app[21]}")
        if soc:
            text += "🌐 Соцсети:\n" + "\n".join(soc) + "\n"
        # Отправитель: только @username (без ID)
        text += f"\nОтправитель: {get_username(app[1])}"
        # Невидимый маркер с ID пользователя для восстановления заявки
        text += f"\u200buser_{app[1]}\u200b"

        photos = json.loads(app[7])
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Принять", callback_data=f'approve_{app[0]}'),
            types.InlineKeyboardButton("❌ Отклонить", callback_data=f'reject_{app[0]}')
        )
        if photos:
            safe_send_photo(chat_id, photos[0], caption=text, reply_markup=markup)
        else:
            safe_send(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_'))
def approve_app(call):
    app_id = int(call.data.split('_')[1])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM applications WHERE id=?", (app_id,))
    app = c.fetchone()
    c.execute('''INSERT INTO skin_makers
        (user_id, username, name, description, price, services, photo_ids, style, custom_style_name,
         contact_link, social_telegram, social_twitter, social_pinterest, social_tiktok,
         social_youtube, social_instagram, social_vk, social_max,
         delivery_min_days, delivery_max_days)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (app[1], app[2], app[3], app[4], app[5], app[6], app[7], app[8], app[9],
         app[13], app[14], app[15], app[16], app[17], app[18], app[19], app[20], app[21],
         app[22], app[23]))
    c.execute("UPDATE applications SET status='approved' WHERE id=?", (app_id,))
    conn.commit()
    conn.close()
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    safe_send(call.message.chat.id, f"Заявка #{app_id} одобрена.")
    safe_send(app[1], "🎉 Ваша заявка принята!")
    log_action(call.from_user.id, 'approve_application', f'App #{app_id}')

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def reject_app(call):
    app_id = int(call.data.split('_')[1])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE applications SET status='rejected' WHERE id=?", (app_id,))
    conn.commit()
    conn.close()
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    safe_send(call.message.chat.id, f"Заявка #{app_id} отклонена.")
    log_action(call.from_user.id, 'reject_application', f'App #{app_id}')

# ---------- ВОССТАНОВЛЕНИЕ ЗАЯВКИ ПО ПЕРЕСЫЛКЕ ----------
@bot.message_handler(func=lambda m: m.forward_from or m.forward_sender_name, content_types=['text'])
def handle_forward_application(message):
    # Ищем невидимые маркеры app_id и user_id
    app_match = re.search(r'\u200bapp_(\d+)\u200b', message.text)
    if not app_match:
        app_match = re.search(r'📋 Заявка #(\d+)', message.text)
        if not app_match:
            return
    app_id = int(app_match.group(1))

    user_match = re.search(r'\u200buser_(\d+)\u200b', message.text)
    if not is_admin(message.from_user.id):
        safe_send(message.chat.id, "⛔ Только администратор может восстанавливать заявки.")
        return

    # Если есть маркер с user_id – используем его, иначе ищем в базе старую заявку
    if user_match:
        user_id = int(user_match.group(1))
    else:
        # Пробуем найти в истории (маловероятно, но возможно)
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("SELECT user_id FROM applications WHERE id=?", (app_id,))
        row = c.fetchone()
        conn.close()
        if row:
            user_id = row[0]
        else:
            safe_send(message.chat.id, "❌ Не удалось определить отправителя заявки.")
            return

    # Извлекаем данные из текста (полный парсинг полей)
    data = {}
    # ... (регулярки для name, description, price, services, style, соцсетей и т.д.)
    # Пример для имени:
    name_match = re.search(r'👤 Имя:\s*(.+)', message.text)
    if name_match: data['name'] = name_match.group(1).strip()
    # (остальные поля аналогично)

    # Проверка на дубликат
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT id FROM applications WHERE user_id=? AND status='pending'", (user_id,))
    if c.fetchone():
        conn.close()
        safe_send(message.chat.id, "⚠️ У пользователя уже есть активная заявка.")
        return

    photo_ids = "[]"  # фото при пересылке теряются
    c.execute('''INSERT INTO applications 
        (user_id, username, name, description, price, services, photo_ids, style,
         contact_link, social_telegram, social_twitter, social_pinterest, social_tiktok,
         social_youtube, social_instagram, social_vk, social_max, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'pending')''',
        (user_id, data.get('username', ''), data.get('name'), data.get('description'),
         data.get('price'), data.get('services', ''), photo_ids, data.get('style', 'modern'),
         data.get('contact_link', ''), data.get('social_telegram', ''), data.get('social_twitter', ''),
         data.get('social_pinterest', ''), data.get('social_tiktok', ''), data.get('social_youtube', ''),
         data.get('social_instagram', ''), data.get('social_vk', ''), data.get('social_max', '')))
    new_id = c.lastrowid
    conn.commit()
    conn.close()

    safe_send(message.chat.id, f"✅ Заявка восстановлена под номером #{new_id} (оригинал #{app_id}).")
    log_action(message.from_user.id, 'restore_application', f'Restored app #{app_id} as #{new_id}')
    notify_admins(f"📋 Восстановлена заявка #{new_id} от {get_username(user_id)}")

# ---------- ОСТАЛЬНЫЕ ОБРАБОТЧИКИ (поиск, закладки, рейтинг, профиль, админка) ----------
# (аналогично предыдущему полному коду, но везде используется get_username вместо username_by_id)

# ---------- ФОНОВЫЕ ЗАДАЧИ ----------
def check_achievements():
    while True:
        try:
            conn = sqlite3.connect('firme_skin.db')
            c = conn.cursor()
            c.execute("SELECT id, completed_orders, rating, registration_date FROM skin_makers")
            makers = c.fetchall()
            for m in makers:
                mid, orders, rating, reg = m
                if orders >= 100:
                    c.execute("INSERT OR IGNORE INTO achievements (skin_maker_id, type) VALUES (?, 'orders_100')", (mid,))
                if rating >= 4.9:
                    c.execute("INSERT OR IGNORE INTO achievements (skin_maker_id, type) VALUES (?, 'rating_4.9')", (mid,))
                reg_date = datetime.strptime(reg, '%Y-%m-%d %H:%M:%S')
                days = (datetime.now() - reg_date).days
                if days >= 365:
                    c.execute("INSERT OR IGNORE INTO achievements (skin_maker_id, type) VALUES (?, 'year_1')", (mid,))
                if days >= 730:
                    c.execute("INSERT OR IGNORE INTO achievements (skin_maker_id, type) VALUES (?, 'year_2')", (mid,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Check achievements error: {e}")
        time.sleep(3600)

def backup_db():
    while True:
        try:
            os.makedirs('backups', exist_ok=True)
            shutil.copyfile('firme_skin.db', f'backups/firme_skin_{int(time.time())}.db')
        except Exception as e:
            logger.error(f"Backup failed: {e}")
        time.sleep(3600)

# ---------- ЗАПУСК ----------
if __name__ == '__main__':
    init_db()
    threading.Thread(target=check_achievements, daemon=True).start()
    threading.Thread(target=backup_db, daemon=True).start()
    logger.info("Бот Frime Skin запущен")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(10)
import os
import urllib.parse
import telebot
from telebot import types
import sqlite3
import json
from datetime import datetime, timedelta
import threading
import time
import random

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Не задана переменная окружения BOT_TOKEN")

ADMIN_ID = 5268276353

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

apply_states = {}
edit_states = {}
feed_states = {}

# ===================== БАЗА ДАННЫХ =====================
def db():
    return sqlite3.connect('firme_skin.db', check_same_thread=False, timeout=15)

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS makers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        username TEXT,
        name TEXT,
        desc TEXT,
        price_min INTEGER DEFAULT 0,
        price_max INTEGER DEFAULT 0,
        services TEXT,
        styles TEXT,
        delivery TEXT,
        photo_ids TEXT DEFAULT '[]',
        rating REAL DEFAULT 5.0,
        reviews_count INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        is_vacation BOOLEAN DEFAULT 0,
        country TEXT DEFAULT 'RU',
        emoji TEXT,
        contact TEXT,
        social TEXT,
        reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        maker_id INTEGER,
        user_id INTEGER,
        rating REAL,
        reason TEXT,
        UNIQUE(maker_id, user_id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        maker_id INTEGER,
        user_id INTEGER,
        username TEXT,
        text TEXT,
        rating REAL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS bookmarks (
        user_id INTEGER,
        maker_id INTEGER,
        PRIMARY KEY (user_id, maker_id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        name TEXT,
        desc TEXT,
        price_min INTEGER DEFAULT 0,
        price_max INTEGER DEFAULT 0,
        services TEXT,
        styles TEXT,
        delivery TEXT,
        photo_ids TEXT,
        contact TEXT,
        social TEXT,
        status TEXT DEFAULT 'pending'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    )''')
    conn.commit()
    conn.close()

# ===================== КЛАВИАТУРЫ =====================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔍 Лента", "📝 Подать заявку", "📌 Закладки", "👤 Профиль", "ℹ️ О боте")
    return markup

def admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 Заявки", "👥 Скинмейкеры", "🔧 Редактировать", "📊 Статистика", "🔙 Выйти")
    return markup

# ===================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====================
def is_admin(user_id):
    if user_id == ADMIN_ID:
        return True
    conn = db()
    c = conn.cursor()
    c.execute("SELECT 1 FROM admins WHERE user_id=?", (user_id,))
    r = c.fetchone()
    conn.close()
    return r is not None

def get_username(uid):
    try:
        u = bot.get_chat(uid)
        return f"@{u.username}" if u.username else f"ID{uid}"
    except:
        return f"ID{uid}"

def safe_load_photos(photo_ids):
    if not photo_ids:
        return []
    try:
        return json.loads(photo_ids)
    except:
        return []

def safe_edit_text(call, text, markup=None):
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)

def safe_delete_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

# ===================== ОСНОВНЫЕ КОМАНДЫ =====================
@bot.message_handler(commands=['start'])
def start(message):
    apply_states.pop(message.from_user.id, None)
    edit_states.pop(message.from_user.id, None)
    feed_states.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "🎨 Добро пожаловать в <b>Frime Skin</b>!", reply_markup=main_menu())

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "🔐 <b>Админ-панель</b>", reply_markup=admin_menu())

# ===================== ЛЕНТА (с раздельным состоянием и соцсетями) =====================
@bot.message_handler(func=lambda m: m.text == "🔍 Лента")
def show_feed(message):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM makers WHERE is_active=1 ORDER BY rating DESC")
    makers = c.fetchall()
    conn.close()
    if not makers:
        bot.send_message(message.chat.id, "Пока нет скинмейкеров.")
        return
    feed_states[message.from_user.id] = {
        "makers": makers,
        "index": 0
    }
    show_card(message.chat.id, 0)

def show_card(chat_id, index):
    state = feed_states.get(chat_id)
    if not state:
        bot.send_message(chat_id, "Лента устарела. Откройте её заново кнопкой 🔍 Лента.")
        return
    makers = state["makers"]
    if index < 0 or index >= len(makers):
        return
    m = makers[index]
    emoji = m[16] if m[16] else ""
    name = f"{emoji} {m[3]}"
    if m[5] != m[6]:
        price = f"от {m[5]} до {m[6]} ₽"
    else:
        price = f"от {m[5]} ₽" if m[5] > 0 else "Цена не указана"
    rating = m[11] if m[11] else 5.0
    votes = m[12] if m[12] else 0
    text = f"<b>{name}</b>\n⭐ {rating:.1f} ({votes} оценок)\n💰 {price}\n📝 {m[4][:150]}..."

    markup = types.InlineKeyboardMarkup(row_width=3)
    nav_buttons = []
    if index > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"nav_{index-1}"))
    nav_buttons.append(types.InlineKeyboardButton(f"{index+1}/{len(makers)}", callback_data="none"))
    if index < len(makers)-1:
        nav_buttons.append(types.InlineKeyboardButton("➡️ Вперед", callback_data=f"nav_{index+1}"))
    markup.row(*nav_buttons)

    markup.row(
        types.InlineKeyboardButton("⭐ Оценить", callback_data=f"rate_{m[0]}"),
        types.InlineKeyboardButton("📝 Отзывы", callback_data=f"reviews_{m[0]}"),
        types.InlineKeyboardButton("📌 В закладки", callback_data=f"bookmark_{m[0]}")
    )

    # Кнопки "Заказ" и "Соц сети"
    row_buttons = []
    if m[17]:
        contact = m[17].strip()
        if contact.startswith("@"):
            username = contact[1:]
            prefill = "Здравствуйте! Мне понравились ваши работы в FRIME Skin. Хочу заказать товар"
            url = f"https://t.me/{username}?text={urllib.parse.quote(prefill)}"
        elif not contact.startswith("http"):
            url = "https://" + contact
        else:
            url = contact
        row_buttons.append(types.InlineKeyboardButton("✉️ Заказ", url=url))
    if m[18]:
        row_buttons.append(types.InlineKeyboardButton("🌐 Соц сети", callback_data=f"social_{m[0]}"))
    if row_buttons:
        markup.row(*row_buttons)

    photos = safe_load_photos(m[10])
    if photos:
        bot.send_photo(chat_id, photos[0], caption=text, reply_markup=markup)
    else:
        bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('nav_'))
def nav_cards(call):
    state = feed_states.get(call.from_user.id)
    if not state:
        bot.answer_callback_query(call.id, "Лента устарела. Откройте её заново кнопкой 🔍 Лента.")
        return
    index = int(call.data.split('_')[1])
    safe_delete_message(call.message.chat.id, call.message.message_id)
    show_card(call.message.chat.id, index)

# ===================== СОЦСЕТИ =====================
@bot.callback_query_handler(func=lambda call: call.data.startswith('social_'))
def show_social(call):
    maker_id = int(call.data.split('_')[1])
    conn = db()
    c = conn.cursor()
    c.execute("SELECT social FROM makers WHERE id=?", (maker_id,))
    row = c.fetchone()
    conn.close()
    if not row or not row[0]:
        bot.answer_callback_query(call.id, "Соцсети не указаны")
        return
    bot.send_message(call.message.chat.id, f"🌐 <b>Соцсети:</b>\n{row[0]}")

# ===================== ОЦЕНКИ =====================
@bot.callback_query_handler(func=lambda call: call.data.startswith('rate_'))
def rate_maker(call):
    maker_id = int(call.data.split('_')[1])
    msg = bot.send_message(call.message.chat.id, "Оцените от 1 до 5:")
    bot.register_next_step_handler(msg, process_rate, maker_id)

def process_rate(message, maker_id):
    try:
        r = int(message.text)
        if r < 1 or r > 5:
            raise ValueError
    except:
        bot.send_message(message.chat.id, "Введите число от 1 до 5.")
        return
    conn = db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO ratings (maker_id, user_id, rating) VALUES (?,?,?)", (maker_id, message.from_user.id, r))
        c.execute("UPDATE makers SET rating=(SELECT AVG(rating) FROM ratings WHERE maker_id=?), reviews_count=(SELECT COUNT(*) FROM ratings WHERE maker_id=?) WHERE id=?", (maker_id, maker_id, maker_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Спасибо за оценку!")
    except sqlite3.IntegrityError:
        conn.close()
        bot.send_message(message.chat.id, "Вы уже оценивали этого мастера.")

# ===================== ОТЗЫВЫ =====================
@bot.callback_query_handler(func=lambda call: call.data.startswith('reviews_'))
def show_reviews(call):
    maker_id = int(call.data.split('_')[1])
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM reviews WHERE maker_id=? ORDER BY date DESC LIMIT 5", (maker_id,))
    revs = c.fetchall()
    conn.close()
    if not revs:
        bot.send_message(call.message.chat.id, "Пока нет отзывов.")
        return
    text = "📝 <b>Последние отзывы:</b>\n\n"
    for r in revs:
        text += f"👤 {r[3]}\n⭐ {r[5]}/5\n💬 {r[4]}\n📅 {r[6][:10]}\n\n"
    bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data.startswith('review_'))
def review_maker(call):
    maker_id = int(call.data.split('_')[1])
    msg = bot.send_message(call.message.chat.id, "Напишите отзыв:")
    bot.register_next_step_handler(msg, process_review, maker_id)

def process_review(message, maker_id):
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO reviews (maker_id, user_id, username, text, rating) VALUES (?,?,?,?,5)", (maker_id, message.from_user.id, message.from_user.first_name, message.text))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Отзыв добавлен!")

# ===================== ЗАКЛАДКИ =====================
@bot.callback_query_handler(func=lambda call: call.data.startswith('bookmark_'))
def bookmark_maker(call):
    maker_id = int(call.data.split('_')[1])
    conn = db()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO bookmarks (user_id, maker_id) VALUES (?,?)", (call.from_user.id, maker_id))
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "✅ Добавлено в закладки!")

@bot.message_handler(func=lambda m: m.text == "📌 Закладки")
def show_bookmarks(message):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT m.name, m.id FROM makers m JOIN bookmarks b ON m.id=b.maker_id WHERE b.user_id=?", (message.from_user.id,))
    makers = c.fetchall()
    conn.close()
    if not makers:
        bot.send_message(message.chat.id, "Закладок пока нет.")
        return
    text = "📌 <b>Ваши закладки:</b>\n" + "\n".join([f"• {m[0]}" for m in makers])
    bot.send_message(message.chat.id, text)

# ===================== ПРОФИЛЬ + РЕДАКТИРОВАНИЕ =====================
@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(message):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM makers WHERE user_id=?", (message.from_user.id,))
    m = c.fetchone()
    conn.close()
    if not m:
        bot.send_message(message.chat.id, "Вы не зарегистрированы как скинмейкер.")
        return
    if m[5] != m[6]:
        price = f"от {m[5]} до {m[6]} ₽"
    else:
        price = f"от {m[5]} ₽" if m[5] > 0 else "Цена не указана"
    rating = m[11] if m[11] else 5.0
    votes = m[12] if m[12] else 0
    text = f"👤 <b>{m[3]}</b>\n💰 {price}\n⭐ {rating:.1f} ({votes} оценок)\n📝 {m[4]}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✏️ Редактировать", callback_data="edit_profile_menu"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "edit_profile_menu")
def edit_profile_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("Изменить имя", callback_data="edit_field_name"),
        types.InlineKeyboardButton("Изменить описание", callback_data="edit_field_desc"),
        types.InlineKeyboardButton("Изменить мин. цену", callback_data="edit_field_price_min"),
        types.InlineKeyboardButton("Изменить макс. цену", callback_data="edit_field_price_max"),
        types.InlineKeyboardButton("Изменить услуги", callback_data="edit_field_services"),
        types.InlineKeyboardButton("Изменить стили", callback_data="edit_field_styles"),
        types.InlineKeyboardButton("Изменить сроки", callback_data="edit_field_delivery"),
        types.InlineKeyboardButton("Изменить ссылку для заказа", callback_data="edit_field_contact"),
        types.InlineKeyboardButton("Изменить соцсети", callback_data="edit_field_social"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_profile")
    )
    safe_edit_text(call, "Что хотите изменить?", markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_profile")
def back_to_profile(call):
    safe_delete_message(call.message.chat.id, call.message.message_id)
    profile(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_field_"))
def edit_field_start(call):
    field = call.data.split("_", 2)[2]
    user_id = call.from_user.id
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id FROM makers WHERE user_id=?", (user_id,))
    m = c.fetchone()
    conn.close()
    if not m:
        bot.answer_callback_query(call.id, "Вы не скинмейкер.")
        return
    edit_states[user_id] = {'editing_field': field, 'maker_id': m[0]}
    prompts = {
        'name': "Введите новое имя:",
        'desc': "Введите новое описание:",
        'price_min': "Введите минимальную цену (число):",
        'price_max': "Введите максимальную цену (число):",
        'services': "Введите услуги через запятую:",
        'styles': "Введите стили через запятую:",
        'delivery': "Введите сроки (например, 2-7):",
        'contact': "Введите ссылку для заказа (или -):",
        'social': "Введите соцсети (формат: Telegram: ссылка, ... или -):"
    }
    msg = bot.send_message(call.message.chat.id, prompts.get(field, "Новое значение:"))
    bot.register_next_step_handler(msg, process_edit_field)

def process_edit_field(message):
    user_id = message.from_user.id
    if user_id not in edit_states or 'editing_field' not in edit_states[user_id]:
        return
    field = edit_states[user_id]['editing_field']
    maker_id = edit_states[user_id]['maker_id']
    value = message.text.strip()
    if value == '-':
        value = None
    elif field in ('price_min', 'price_max'):
        try:
            value = int(value)
        except:
            bot.send_message(message.chat.id, "Введите число.")
            return
    conn = db()
    c = conn.cursor()
    column_map = {
        'name': 'name', 'desc': 'desc', 'price_min': 'price_min',
        'price_max': 'price_max', 'services': 'services', 'styles': 'styles',
        'delivery': 'delivery', 'contact': 'contact', 'social': 'social'
    }
    col = column_map.get(field)
    if col:
        c.execute(f"UPDATE makers SET {col}=? WHERE id=?", (value, maker_id))
        conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Изменено!")
    edit_states.pop(user_id, None)

# ===================== О БОТЕ =====================
@bot.message_handler(func=lambda m: m.text == "ℹ️ О боте")
def about(message):
    bot.send_message(message.chat.id, "<b>Frime Skin</b> — платформа для поиска скинмейкеров Minecraft.\nСвязь: @Defemar")

# ===================== ПОДАЧА ЗАЯВКИ =====================
@bot.message_handler(func=lambda m: m.text == "📝 Подать заявку")
def apply_start(message):
    apply_states[message.from_user.id] = {'step': 'photo', 'photos': []}
    bot.send_message(message.chat.id, "📸 Отправьте фото (можно до 3, затем /done)")

@bot.message_handler(func=lambda m: apply_states.get(m.from_user.id, {}).get('step') == 'photo')
def apply_photo(message):
    uid = message.from_user.id
    if message.content_type == 'photo':
        if len(apply_states[uid]['photos']) >= 3:
            bot.send_message(message.chat.id, "Максимум 3 фото. Отправьте /done для продолжения.")
            return
        apply_states[uid]['photos'].append(message.photo[-1].file_id)
        bot.send_message(message.chat.id, f"Фото {len(apply_states[uid]['photos'])}/3 добавлено.")
    elif message.text == '/done':
        apply_states[uid]['step'] = 'name'
        bot.send_message(message.chat.id, "✏️ Ваше имя:")
    else:
        bot.send_message(message.chat.id, "Отправьте фото или /done")

@bot.message_handler(func=lambda m: apply_states.get(m.from_user.id, {}).get('step') == 'name')
def apply_name(message):
    uid = message.from_user.id
    apply_states[uid]['name'] = message.text
    apply_states[uid]['step'] = 'desc'
    bot.send_message(message.chat.id, "💬 Описание услуг:")

@bot.message_handler(func=lambda m: apply_states.get(m.from_user.id, {}).get('step') == 'desc')
def apply_desc(message):
    uid = message.from_user.id
    apply_states[uid]['desc'] = message.text
    apply_states[uid]['step'] = 'price_min'
    bot.send_message(message.chat.id, "💰 Минимальная цена:")

@bot.message_handler(func=lambda m: apply_states.get(m.from_user.id, {}).get('step') == 'price_min')
def apply_price_min(message):
    uid = message.from_user.id
    try:
        p = int(message.text)
        apply_states[uid]['price_min'] = p
        apply_states[uid]['step'] = 'price_max'
        bot.send_message(message.chat.id, "💰 Максимальная цена:")
    except:
        bot.send_message(message.chat.id, "Введите число.")

@bot.message_handler(func=lambda m: apply_states.get(m.from_user.id, {}).get('step') == 'price_max')
def apply_price_max(message):
    uid = message.from_user.id
    try:
        p = int(message.text)
        apply_states[uid]['price_max'] = p
        apply_states[uid]['step'] = 'services'
        bot.send_message(message.chat.id, "🛠️ Услуги (через запятую):")
    except:
        bot.send_message(message.chat.id, "Введите число.")

@bot.message_handler(func=lambda m: apply_states.get(m.from_user.id, {}).get('step') == 'services')
def apply_services(message):
    uid = message.from_user.id
    apply_states[uid]['services'] = message.text
    apply_states[uid]['step'] = 'styles'
    bot.send_message(message.chat.id, "🎨 Стили (через запятую):")

@bot.message_handler(func=lambda m: apply_states.get(m.from_user.id, {}).get('step') == 'styles')
def apply_styles(message):
    uid = message.from_user.id
    apply_states[uid]['styles'] = message.text
    apply_states[uid]['step'] = 'delivery'
    bot.send_message(message.chat.id, "⏱ Сроки (например, 2-7):")

@bot.message_handler(func=lambda m: apply_states.get(m.from_user.id, {}).get('step') == 'delivery')
def apply_delivery(message):
    uid = message.from_user.id
    apply_states[uid]['delivery'] = message.text
    apply_states[uid]['step'] = 'contact'
    bot.send_message(message.chat.id, "🔗 Ссылка для заказа (или -):")

@bot.message_handler(func=lambda m: apply_states.get(m.from_user.id, {}).get('step') == 'contact')
def apply_contact(message):
    uid = message.from_user.id
    contact = message.text if message.text != '-' else None
    apply_states[uid]['contact'] = contact
    apply_states[uid]['step'] = 'social'
    bot.send_message(message.chat.id, "🌐 Соцсети (формат: Telegram: ссылка, ... или -):")

@bot.message_handler(func=lambda m: apply_states.get(m.from_user.id, {}).get('step') == 'social')
def apply_social(message):
    uid = message.from_user.id
    social = message.text if message.text != '-' else None
    apply_states[uid]['social'] = social
    data = apply_states.pop(uid)
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO applications (user_id, username, name, desc, price_min, price_max, services, styles, delivery, photo_ids, contact, social) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
              (uid, message.from_user.username or "", data['name'], data['desc'], data['price_min'], data['price_max'], data['services'], data['styles'], data['delivery'], json.dumps(data['photos']), data['contact'], data['social']))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Заявка отправлена!", reply_markup=main_menu())

# ===================== АДМИН-ПАНЕЛЬ =====================
@bot.message_handler(func=lambda m: m.text == "📋 Заявки" and is_admin(m.from_user.id))
def admin_apps(message):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM applications WHERE status='pending'")
    apps = c.fetchall()
    conn.close()
    if not apps:
        bot.send_message(message.chat.id, "Нет заявок.")
        return
    for app in apps:
        text = f"📋 <b>Заявка #{app[0]}</b>\n\n"
        text += f"👤 Имя: {app[3]}\n"
        text += f"💬 Описание: {app[4]}\n"
        if app[5] != app[6]:
            text += f"💲 Ценник: от {app[5]} до {app[6]} ₽\n"
        else:
            text += f"💲 Ценник: от {app[5]} ₽\n" if app[5] > 0 else "💲 Ценник: не указана\n"
        text += f"🎨 Стиль: {app[8]}\n"
        text += f"🛠️ Услуги: {app[7]}\n"
        text += f"⏱ Сроки: {app[9]}\n"
        text += f"🔗 Ссылка: {app[11] or 'не указана'}\n"
        if app[12]:
            text += f"🌐 Соцсети:\n{app[12]}\n"
        text += f"\nОтправитель: {get_username(app[1])}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Принять", callback_data=f"approve_{app[0]}"),
                   types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{app[0]}"))
        photos = safe_load_photos(app[10])
        if photos:
            bot.send_photo(message.chat.id, photos[0], caption=text, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_'))
def approve_app(call):
    app_id = int(call.data.split('_')[1])
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM applications WHERE id=?", (app_id,))
    app = c.fetchone()
    if not app:
        bot.answer_callback_query(call.id, "Заявка не найдена.")
        conn.close()
        return
    c.execute("SELECT id FROM makers WHERE user_id=?", (app[1],))
    if c.fetchone():
        bot.answer_callback_query(call.id, "У этого пользователя уже есть профиль.")
        conn.close()
        return
    c.execute("INSERT INTO makers (user_id, username, name, desc, price_min, price_max, services, styles, delivery, photo_ids, contact, social) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
              (app[1], app[2], app[3], app[4], app[5], app[6], app[7], app[8], app[9], app[10], app[11], app[12]))
    c.execute("UPDATE applications SET status='approved' WHERE id=?", (app_id,))
    conn.commit()
    conn.close()
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    bot.send_message(app[1], "🎉 Ваша заявка принята!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def reject_app(call):
    app_id = int(call.data.split('_')[1])
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM applications WHERE id=?", (app_id,))
    app = c.fetchone()
    if not app:
        bot.answer_callback_query(call.id, "Заявка не найдена.")
        conn.close()
        return
    c.execute("UPDATE applications SET status='rejected' WHERE id=?", (app_id,))
    conn.commit()
    conn.close()
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)

# ---------- ПОИСК СКИНМЕЙКЕРА АДМИНОМ ----------
@bot.message_handler(func=lambda m: m.text == "🔧 Редактировать" and is_admin(m.from_user.id))
def admin_search_by_username(message):
    msg = bot.send_message(message.chat.id, "Введите @username скинмейкера:")
    bot.register_next_step_handler(msg, admin_find_by_username)

def admin_find_by_username(message):
    username = message.text.strip().lstrip('@')
    if not username:
        bot.send_message(message.chat.id, "Неверный формат.")
        return
    try:
        chat = bot.get_chat(f"@{username}")
        user_id = chat.id
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка поиска: {e}")
        return
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM makers WHERE user_id=?", (user_id,))
    m = c.fetchone()
    conn.close()
    if not m:
        bot.send_message(message.chat.id, "Скинмейкер с таким username не зарегистрирован.")
        return
    if m[5] != m[6]:
        price = f"от {m[5]} до {m[6]} ₽"
    else:
        price = f"от {m[5]} ₽" if m[5] > 0 else "Цена не указана"
    text = f"🔧 <b>Редактирование:</b> {m[3]}\n💰 {price}\n⭐ {m[11]:.1f}\nАктивен: {'✅' if m[13] else '❌'}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Переключить активность", callback_data=f"toggle_active_{m[0]}"),
               types.InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_maker_{m[0]}"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('toggle_active_'))
def toggle_active(call):
    mid = int(call.data.split('_')[2])
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE makers SET is_active = NOT is_active WHERE id=?", (mid,))
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "Статус изменён.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_maker_'))
def delete_maker(call):
    mid = int(call.data.split('_')[2])
    conn = db()
    c = conn.cursor()
    c.execute("DELETE FROM makers WHERE id=?", (mid,))
    conn.commit()
    conn.close()
    safe_edit_text(call, "Скинмейкер удалён.")

# ---------- СПИСОК СКИНМЕЙКЕРОВ ----------
@bot.message_handler(func=lambda m: m.text == "👥 Скинмейкеры" and is_admin(m.from_user.id))
def admin_makers(message):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, name, username, rating, is_active FROM makers")
    makers = c.fetchall()
    conn.close()
    if not makers:
        bot.send_message(message.chat.id, "Список пуст.")
        return
    text = "👥 <b>Скинмейкеры:</b>\n" + "\n".join([f"• {m[1]} (@{m[2] or 'ID'}) ⭐{m[3]:.1f} {'✅' if m[4] else '❌'}" for m in makers])
    bot.send_message(message.chat.id, text[:4000])

# ---------- СТАТИСТИКА ----------
@bot.message_handler(func=lambda m: m.text == "📊 Статистика" and is_admin(m.from_user.id))
def admin_stats(message):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM makers")
    makers = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM applications WHERE status='pending'")
    apps = c.fetchone()[0]
    conn.close()
    bot.send_message(message.chat.id, f"📊 <b>Статистика:</b>\nСкинмейкеров: {makers}\nЗаявок ожидает: {apps}")

# ---------- ВЫХОД ИЗ АДМИНКИ ----------
@bot.message_handler(func=lambda m: m.text == "🔙 Выйти" and is_admin(m.from_user.id))
def admin_exit(message):
    bot.send_message(message.chat.id, "Вы вышли из админ-панели.", reply_markup=main_menu())

# ===================== ЗАПУСК =====================
if __name__ == '__main__':
    init_db()
    print("Бот запущен...")
    bot.polling(none_stop=False, timeout=20, long_polling_timeout=5)
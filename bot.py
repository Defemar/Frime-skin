import telebot
from telebot import types
import sqlite3
import json
from datetime import datetime, timedelta
import threading
import time
import random

TOKEN = "8623923833:AAHv6xe6u9xtncfp_7xRvjJzOKorOiLcPwY"
ADMIN_ID = 5268276353

bot = telebot.TeleBot(TOKEN)

# ===================== БАЗА ДАННЫХ =====================
def init_db():
    conn = sqlite3.connect('firme_skin.db', check_same_thread=False)
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
        reason TEXT
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
    conn = sqlite3.connect('firme_skin.db')
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

# ===================== ОСНОВНЫЕ КОМАНДЫ =====================
@bot.message_handler(commands=['start'])
def start(message):
    user_states.pop(message.from_user.id, None)  # сброс состояния, если есть
    bot.send_message(message.chat.id, "🎨 Добро пожаловать в Frime Skin!", reply_markup=main_menu())

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "🔐 Админ-панель", reply_markup=admin_menu())

# ===================== ЛЕНТА =====================
@bot.message_handler(func=lambda m: m.text == "🔍 Лента")
def show_feed(message):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM makers WHERE is_active=1 ORDER BY rating DESC LIMIT 20")
    makers = c.fetchall()
    conn.close()
    if not makers:
        bot.send_message(message.chat.id, "Пока нет скинмейкеров.")
        return
    for m in makers:
        emoji = m[16] if m[16] else ""
        name = f"{emoji} {m[3]}".strip()
        if m[5] != m[6]:
            price = f"от {m[5]} до {m[6]} ₽"
        else:
            price = f"от {m[5]} ₽" if m[5] > 0 else "Цена не указана"
        text = f"{name}\n⭐ {m[11]:.1f} | 💰 {price}\n📝 {m[4][:100]}..."
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⭐ Оценить", callback_data=f"rate_{m[0]}"),
                   types.InlineKeyboardButton("📝 Отзыв", callback_data=f"review_{m[0]}"),
                   types.InlineKeyboardButton("📌 В закладки", callback_data=f"bookmark_{m[0]}"))
        if m[17]:
            contact = m[17].strip()
            if contact.startswith("@"):
                url = f"tg://resolve?domain={contact[1:]}"
            elif not contact.startswith("http"):
                url = "https://" + contact
            else:
                url = contact
            markup.add(types.InlineKeyboardButton("✉️ Заказ", url=url))
        photos = safe_load_photos(m[10])
        if photos:
            bot.send_photo(message.chat.id, photos[0], caption=text, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, text, reply_markup=markup)

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
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("INSERT INTO ratings (maker_id, user_id, rating) VALUES (?,?,?)", (maker_id, message.from_user.id, r))
    c.execute("UPDATE makers SET rating=(SELECT AVG(rating) FROM ratings WHERE maker_id=?), reviews_count=(SELECT COUNT(*) FROM ratings WHERE maker_id=?) WHERE id=?", (maker_id, maker_id, maker_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Спасибо за оценку!")

# ===================== ОТЗЫВЫ =====================
@bot.callback_query_handler(func=lambda call: call.data.startswith('review_'))
def review_maker(call):
    maker_id = int(call.data.split('_')[1])
    msg = bot.send_message(call.message.chat.id, "Напишите отзыв:")
    bot.register_next_step_handler(msg, process_review, maker_id)

def process_review(message, maker_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("INSERT INTO reviews (maker_id, user_id, username, text, rating) VALUES (?,?,?,?,5)", (maker_id, message.from_user.id, message.from_user.first_name, message.text))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Отзыв добавлен!")

# ===================== ЗАКЛАДКИ =====================
@bot.callback_query_handler(func=lambda call: call.data.startswith('bookmark_'))
def bookmark_maker(call):
    maker_id = int(call.data.split('_')[1])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO bookmarks (user_id, maker_id) VALUES (?,?)", (call.from_user.id, maker_id))
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "✅ Добавлено в закладки!")

@bot.message_handler(func=lambda m: m.text == "📌 Закладки")
def show_bookmarks(message):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT m.name, m.id FROM makers m JOIN bookmarks b ON m.id=b.maker_id WHERE b.user_id=?", (message.from_user.id,))
    makers = c.fetchall()
    conn.close()
    if not makers:
        bot.send_message(message.chat.id, "Закладок пока нет.")
        return
    text = "📌 Ваши закладки:\n" + "\n".join([f"• {m[0]}" for m in makers])
    bot.send_message(message.chat.id, text)

# ===================== ПРОФИЛЬ =====================
@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(message):
    conn = sqlite3.connect('firme_skin.db')
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
    text = f"👤 {m[3]}\n💰 {price}\n⭐ {m[11]:.1f}\n📝 {m[4]}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_profile"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "edit_profile")
def edit_profile(call):
    bot.send_message(call.message.chat.id, "Функция редактирования появится позже.")

# ===================== О БОТЕ =====================
@bot.message_handler(func=lambda m: m.text == "ℹ️ О боте")
def about(message):
    bot.send_message(message.chat.id, "Frime Skin — платформа для поиска скинмейкеров Minecraft.\nСвязь: @Defemar")

# ===================== ПОДАЧА ЗАЯВКИ =====================
user_states = {}
@bot.message_handler(func=lambda m: m.text == "📝 Подать заявку")
def apply_start(message):
    user_states[message.from_user.id] = {'step': 'photo', 'photos': []}
    bot.send_message(message.chat.id, "📸 Отправьте фото (можно до 3, затем /done)")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get('step') == 'photo')
def apply_photo(message):
    uid = message.from_user.id
    if message.content_type == 'photo':
        user_states[uid]['photos'].append(message.photo[-1].file_id)
        bot.send_message(message.chat.id, f"Фото {len(user_states[uid]['photos'])}/3 добавлено.")
    elif message.text == '/done':
        user_states[uid]['step'] = 'name'
        bot.send_message(message.chat.id, "✏️ Ваше имя:")
    else:
        bot.send_message(message.chat.id, "Отправьте фото или /done")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get('step') == 'name')
def apply_name(message):
    uid = message.from_user.id
    user_states[uid]['name'] = message.text
    user_states[uid]['step'] = 'desc'
    bot.send_message(message.chat.id, "💬 Описание услуг:")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get('step') == 'desc')
def apply_desc(message):
    uid = message.from_user.id
    user_states[uid]['desc'] = message.text
    user_states[uid]['step'] = 'price_min'
    bot.send_message(message.chat.id, "💰 Минимальная цена:")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get('step') == 'price_min')
def apply_price_min(message):
    uid = message.from_user.id
    try:
        p = int(message.text)
        user_states[uid]['price_min'] = p
        user_states[uid]['step'] = 'price_max'
        bot.send_message(message.chat.id, "💰 Максимальная цена:")
    except:
        bot.send_message(message.chat.id, "Введите число.")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get('step') == 'price_max')
def apply_price_max(message):
    uid = message.from_user.id
    try:
        p = int(message.text)
        user_states[uid]['price_max'] = p
        user_states[uid]['step'] = 'services'
        bot.send_message(message.chat.id, "🛠️ Услуги (через запятую, например: Скины, Модели):")
    except:
        bot.send_message(message.chat.id, "Введите число.")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get('step') == 'services')
def apply_services(message):
    uid = message.from_user.id
    user_states[uid]['services'] = message.text
    user_states[uid]['step'] = 'styles'
    bot.send_message(message.chat.id, "🎨 Стили (через запятую, например: modern, special, MonoRay):")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get('step') == 'styles')
def apply_styles(message):
    uid = message.from_user.id
    user_states[uid]['styles'] = message.text
    user_states[uid]['step'] = 'delivery'
    bot.send_message(message.chat.id, "⏱ Сроки (например: 2-7):")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get('step') == 'delivery')
def apply_delivery(message):
    uid = message.from_user.id
    user_states[uid]['delivery'] = message.text
    user_states[uid]['step'] = 'contact'
    bot.send_message(message.chat.id, "🔗 Ссылка для заказа (или -):")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get('step') == 'contact')
def apply_contact(message):
    uid = message.from_user.id
    contact = message.text if message.text != '-' else None
    user_states[uid]['contact'] = contact
    user_states[uid]['step'] = 'social'
    bot.send_message(message.chat.id, "🌐 Соцсети (формат: Telegram: ссылка, VK: ссылка... или -):")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get('step') == 'social')
def apply_social(message):
    uid = message.from_user.id
    social = message.text if message.text != '-' else None
    user_states[uid]['social'] = social
    data = user_states.pop(uid)
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("INSERT INTO applications (user_id, username, name, desc, price_min, price_max, services, styles, delivery, photo_ids, contact, social) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
              (uid, message.from_user.username or "", data['name'], data['desc'], data['price_min'], data['price_max'], data['services'], data['styles'], data['delivery'], json.dumps(data['photos']), data['contact'], data['social']))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Заявка отправлена!", reply_markup=main_menu())

# ===================== АДМИН-ПАНЕЛЬ =====================
@bot.message_handler(func=lambda m: m.text == "📋 Заявки" and is_admin(m.from_user.id))
def admin_apps(message):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM applications WHERE status='pending'")
    apps = c.fetchall()
    conn.close()
    if not apps:
        bot.send_message(message.chat.id, "Нет заявок.")
        return
    for app in apps:
        text = f"📋 Заявка #{app[0]}\n\n"
        text += f"👤 Имя: {app[3]}\n"
        text += f"💬 Описание: {app[4]}\n"
        if app[5] != app[6]:
            text += f"💲 Ценник: от {app[5]} до {app[6]} ₽\n"
        else:
            text += f"💲 Ценник: от {app[5]} ₽\n" if app[5] > 0 else "💲 Ценник: не указана\n"
        text += f"🎨 Стиль: {app[8]}\n"
        text += f"🛠️ Услуги: {app[7]}\n"
        text += f"⏱ Сроки: {app[9]}\n"
        text += f"🔗 Ссылка: {app[10] or 'не указана'}\n"
        if app[11]:
            text += f"🌐 Соцсети:\n{app[11]}\n"
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
    conn = sqlite3.connect('firme_skin.db')
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
    conn = sqlite3.connect('firme_skin.db')
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

# ---------- ПОИСК СКИНМЕЙКЕРА АДМИНОМ ПО @USERNAME ----------
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
    conn = sqlite3.connect('firme_skin.db')
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
    text = f"🔧 Редактирование: {m[3]}\n💰 {price}\n⭐ {m[11]:.1f}\nАктивен: {'✅' if m[13] else '❌'}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Переключить активность", callback_data=f"toggle_active_{m[0]}"),
               types.InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_maker_{m[0]}"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('toggle_active_'))
def toggle_active(call):
    mid = int(call.data.split('_')[2])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE makers SET is_active = NOT is_active WHERE id=?", (mid,))
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "Статус изменён.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_maker_'))
def delete_maker(call):
    mid = int(call.data.split('_')[2])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("DELETE FROM makers WHERE id=?", (mid,))
    conn.commit()
    conn.close()
    bot.edit_message_text("Скинмейкер удалён.", call.message.chat.id, call.message.message_id)

# ---------- СПИСОК СКИНМЕЙКЕРОВ ----------
@bot.message_handler(func=lambda m: m.text == "👥 Скинмейкеры" and is_admin(m.from_user.id))
def admin_makers(message):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT id, name, username, rating, is_active FROM makers")
    makers = c.fetchall()
    conn.close()
    if not makers:
        bot.send_message(message.chat.id, "Список пуст.")
        return
    text = "👥 Скинмейкеры:\n" + "\n".join([f"• {m[1]} (@{m[2]}) ⭐{m[3]:.1f} {'✅' if m[4] else '❌'}" for m in makers])
    bot.send_message(message.chat.id, text[:4000])

# ---------- СТАТИСТИКА ----------
@bot.message_handler(func=lambda m: m.text == "📊 Статистика" and is_admin(m.from_user.id))
def admin_stats(message):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM makers")
    makers = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM applications WHERE status='pending'")
    apps = c.fetchone()[0]
    conn.close()
    bot.send_message(message.chat.id, f"📊 Статистика:\nСкинмейкеров: {makers}\nЗаявок ожидает: {apps}")

# ---------- ВЫХОД ИЗ АДМИНКИ ----------
@bot.message_handler(func=lambda m: m.text == "🔙 Выйти" and is_admin(m.from_user.id))
def admin_exit(message):
    bot.send_message(message.chat.id, "Вы вышли из админ-панели.", reply_markup=main_menu())

# ===================== ЗАПУСК =====================
if __name__ == '__main__':
    init_db()
    print("Бот запущен...")
    bot.polling(none_stop=True)
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
import shutil

TOKEN = "8623923833:AAHv6xe6u9xtncfp_7xRvjJzOKorOiLcPwY"
ADMIN_ID = 5268276353

PROXY = None
if PROXY:
    from telebot import apihelper
    apihelper.proxy = {'https': PROXY}

bot = telebot.TeleBot(TOKEN)
bot.current_makers = []
bot.current_filter = 'popular_formula'
bot.current_filter_value = None

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
        price_min INTEGER DEFAULT 0,
        price_max INTEGER DEFAULT 0,
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

    try: c.execute("ALTER TABLE skin_makers ADD COLUMN price_min INTEGER DEFAULT 0")
    except: pass
    try: c.execute("ALTER TABLE skin_makers ADD COLUMN price_max INTEGER DEFAULT 0")
    except: pass
    try: c.execute("ALTER TABLE skin_makers ADD COLUMN order_display TEXT")
    except: pass

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
        price_min INTEGER DEFAULT 0,
        price_max INTEGER DEFAULT 0,
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

    try: c.execute("ALTER TABLE applications ADD COLUMN price_min INTEGER DEFAULT 0")
    except: pass
    try: c.execute("ALTER TABLE applications ADD COLUMN price_max INTEGER DEFAULT 0")
    except: pass

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

    conn.commit()
    conn.close()

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
    'RU': '🇷🇺', 'BY': '🇧🇾', 'UA': '🇺🇦', 'KZ': '🇰🇿',
    'UZ': '🇺🇿', 'KG': '🇰🇬', 'TJ': '🇹🇯', 'TM': '🇹🇲',
    'AZ': '🇦🇿', 'AM': '🇦🇲', 'GE': '🇬🇪', 'MD': '🇲🇩',
    'LT': '🇱🇹', 'LV': '🇱🇻', 'EE': '🇪🇪',
    'US': '🇺🇸', 'DE': '🇩🇪', 'FR': '🇫🇷', 'GB': '🇬🇧', 'CA': '🇨🇦',
    'AU': '🇦🇺', 'JP': '🇯🇵', 'KR': '🇰🇷', 'CN': '🇨🇳',
    'IN': '🇮🇳', 'BR': '🇧🇷', 'MX': '🇲🇽', 'ES': '🇪🇸',
    'IT': '🇮🇹', 'PL': '🇵🇱', 'TR': '🇹🇷', 'NL': '🇳🇱',
    'SE': '🇸🇪', 'NO': '🇳🇴', 'FI': '🇫🇮', 'CZ': '🇨🇿',
    'RO': '🇷🇴', 'HU': '🇭🇺', 'AR': '🇦🇷', 'CL': '🇨🇱', 'CO': '🇨🇴'
}

def main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🔍 Поиск скинмейкеров", "📝 Подать заявку", "📌 Мои закладки", "👤 Мой профиль",
               "📢 Новости", "💸 Донат на сервера", "ℹ️ О боте")
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
    bot.send_message(ADMIN_ID, text)
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins")
    admins = [row[0] for row in c.fetchall()]
    conn.close()
    for admin in admins:
        try: bot.send_message(admin, text)
        except: pass

def username_by_id(user_id):
    try:
        user = bot.get_chat(user_id)
        return f"@{user.username}" if user.username else f"ID{user_id}"
    except:
        return f"ID{user_id}"

def parse_username_or_id(text):
    text = text.strip().lstrip('@')
    if text.isdigit():
        return int(text), None
    else:
        return None, text

def format_maker_card(maker):
    (id, uid, uname, name, desc, price, price_min, price_max, services, photo_ids,
     rating, total, complaints, active, vacation, vac_text, reg_date,
     style, custom_style, dmin, dmax, shadow, shadow_reason, verdict,
     views, orders, orders_conf, busy_until, emoji, country, disp_exp,
     contact_link, social_tg, social_tw, social_pin, social_tiktok,
     social_yt, social_inst, social_vk, social_max, order_display) = maker

    if rating is None: rating = 5.0
    flag = flags.get(country, '🏳️')
    country_name = countries.get(country, country)
    emoji_display = f"{emoji} " if emoji else ""
    name_display = f"{emoji_display}{name} *{flag} {country_name}*"
    style_display = style.replace(',', ' + ')
    if custom_style: style_display += f"\n✨ {custom_style}"
    delivery = f"{dmin}–{dmax} дн."
    status = ""
    if vacation:
        status = "🏖️ В отпуске"
    elif busy_until:
        try:
            busy_date = datetime.strptime(busy_until, '%Y-%m-%d')
            if busy_date > datetime.now():
                status = f"⚠️ Перегружен до {busy_date.strftime('%d.%m.%Y')}"
        except: pass
    if disp_exp: experience = disp_exp
    else:
        reg = datetime.strptime(reg_date, '%Y-%m-%d %H:%M:%S')
        days = (datetime.now() - reg).days
        if days < 30: experience = "Меньше месяца"
        elif days < 180: experience = "Больше месяца"
        elif days < 365: experience = "Больше полугода"
        else: experience = f"{days // 365} год(а)"
    if order_display: orders_text = order_display
    else: orders_text = f"{orders} ✅" if orders_conf else f"~{orders}"

    if price_min and price_max and price_min != price_max:
        price_text = f"от {price_min} до {price_max} ₽"
    elif price:
        price_text = f"от {price} ₽"
    else:
        price_text = "не указана"

    text = f"{name_display}\n\n"
    text += f"🎨 Стиль: {style_display}\n"
    text += f"⏱ Срок: {delivery}\n"
    text += f"💲 Ценник: {price_text}\n"
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
    text += f"\n📝 {desc[:200]}{'...' if len(desc) > 200 else ''}"
    return text

def get_makers_by_filter(filter_type, value=None, limit=30):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    query = "SELECT * FROM skin_makers WHERE is_active=1 AND complaints < 4"
    params = ()
    if filter_type == 'style' and value:
        query += " AND style LIKE ?"
        params = (f"%{value}%",)
    elif filter_type == 'service' and value:
        query += " AND services LIKE ?"
        params = (f"%{value}%",)
    if filter_type in ('standard', 'newbies', 'popular', 'style', 'service'):
        query += " ORDER BY rating DESC, total_ratings DESC"
    elif filter_type == 'price_asc':
        query += " ORDER BY price ASC"
    elif filter_type == 'price_desc':
        query += " ORDER BY price DESC"
    c.execute(query, params)
    makers = c.fetchall()
    conn.close()
    filtered = []
    for m in makers:
        style = m[17] if m[17] else ''
        if style.strip() == 'namemc':
            if random.random() > 0.1: continue
        if m[20]:
            if random.random() > 0.1: continue
        filtered.append(m)
        if len(filtered) >= limit: break
    if filter_type == 'popular_formula':
        filtered.sort(key=lambda m: (m[9] or 5.0) * (1 + (m[10] or 0) * 0.1), reverse=True)
    return filtered

def show_card(chat_id, index):
    if not bot.current_makers:
        bot.send_message(chat_id, "😔 Скинмейкеры не найдены.")
        return
    makers = bot.current_makers
    if index < 0 or index >= len(makers): return
    maker = makers[index]
    text = format_maker_card(maker)
    photo_ids = json.loads(maker[8])
    markup = types.InlineKeyboardMarkup(row_width=3)
    nav_buttons = []
    if index > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f'nav_{index-1}'))
    nav_buttons.append(types.InlineKeyboardButton(f"{index+1}/{len(makers)}", callback_data='none'))
    if index < len(makers)-1:
        nav_buttons.append(types.InlineKeyboardButton("➡️ Вперед", callback_data=f'nav_{index+1}'))
    markup.row(*nav_buttons)
    if maker[31]:
        url = maker[31].strip()
        if not url.startswith('http'):
            if url.startswith('@'): url = f"https://t.me/{url[1:]}"
            elif url.startswith('t.me/'): url = f"https://{url}"
            else: url = f"https://t.me/{url}"
        markup.row(types.InlineKeyboardButton("✉️ Заказ", url=url))
    markup.row(
        types.InlineKeyboardButton("⭐ Оценить", callback_data=f'rate_{maker[0]}'),
        types.InlineKeyboardButton("📝 Отзывы", callback_data=f'reviews_{maker[0]}'),
        types.InlineKeyboardButton("📌 В закладки", callback_data=f'bookmark_{maker[0]}')
    )
    markup.row(
        types.InlineKeyboardButton("🌐 Соц сети", callback_data=f'social_{maker[0]}'),
        types.InlineKeyboardButton("🖼️ Галерея", callback_data=f'gallery_{maker[0]}')
    )
    markup.row(types.InlineKeyboardButton("⚙️ Фильтры", callback_data='filter_menu'))
    if photo_ids:
        bot.send_photo(chat_id, photo_ids[0], caption=text, reply_markup=markup)
    else:
        bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('nav_'))
def nav_cards(call):
    try:
        index = int(call.data.split('_')[1])
        if not bot.current_makers:
            bot.answer_callback_query(call.id, "Список пуст.")
            return
        if index < 0 or index >= len(bot.current_makers):
            bot.answer_callback_query(call.id, "Некорректный индекс.")
            return
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_card(call.message.chat.id, index)
    except Exception as e:
        bot.answer_callback_query(call.id, f"Ошибка: {e}")

@bot.message_handler(commands=['start'])
def start(message):
    if is_blacklisted(message.from_user.id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы.")
        return
    bot.send_message(message.chat.id, "🎨 Добро пожаловать в Frime Skin!", reply_markup=main_menu_markup())

@bot.message_handler(commands=['help'])
def help_command(message):
    text = ("📋 Доступные команды:\n"
            "/start — главное меню\n"
            "/help — это сообщение\n"
            "/cancel — отменить подачу заявки\n"
            "/done — завершить загрузку фото\n\n"
            "Остальные действия выполняются через кнопки меню.")
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) > 1 and args[1] == 'secret' and len(args) > 2 and args[2] == 'command' and len(args) > 3 and args[3] == 'block':
        secret_text = ("🔐 Секретный блок команд:\n"
                       "/admin — админ-панель\n"
                       "/admin_applications — заявки\n"
                       "/admin_all_makers — все скинмейкеры\n"
                       "/admin_stats — статистика\n"
                       "/admin_announce — создать объявление\n"
                       "/admin_export — экспорт БД\n"
                       "/admin_shadow_ban <id> — теневой бан\n"
                       "/admin_unshadow <id> — снять теневой бан\n"
                       "/admin_blacklist <id> — в чёрный список\n"
                       "/admin_whitelist <id> — из чёрного списка\n"
                       "/admin_edit_requests — запросы правок\n"
                       "/admin_log — лог действий\n"
                       "/add_admin <id> — добавить админа (главный)\n"
                       "/remove_admin <id> — удалить админа (главный)\n"
                       "/list_admins — список админов\n"
                       "/admin_add_maker — добавить скинмейкера вручную")
        bot.send_message(message.chat.id, secret_text)
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📋 Заявки", "👥 Скинмейкеры", "✏️ Запросы правок", "⭐ Управление оценками",
               "📊 Статистика", "📢 Объявления", "📤 Экспорт БД", "💾 Сохранить БД",
               "⛔ Теневой бан", "🚫 Чёрный список", "👑 Админы", "➕ Добавить скинмейкера",
               "🔧 Ред. скинмейкера", "📝 Лог", "🔄 Пересчитать рейтинг", "🗂️ Очистить старые заявки",
               "🔙 Выйти")
    bot.send_message(message.chat.id, "🔐 Админ-панель", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🔍 Поиск скинмейкеров")
def search_cmd(message):
    bot.current_filter = 'popular_formula'
    bot.current_filter_value = None
    makers = get_makers_by_filter('popular_formula')
    if not makers:
        bot.send_message(message.chat.id, "😔 Скинмейкеры не найдены.")
        return
    bot.current_makers = makers
    show_card(message.chat.id, 0)

@bot.callback_query_handler(func=lambda call: call.data == 'filter_menu')
def filter_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💲 По цене (возр.)", callback_data='filter_price_asc'),
        types.InlineKeyboardButton("💲 По цене (убыв.)", callback_data='filter_price_desc'),
        types.InlineKeyboardButton("⭐ Популярное", callback_data='filter_popular_formula'),
        types.InlineKeyboardButton("🎨 По стилю", callback_data='filter_style_menu'),
        types.InlineKeyboardButton("🛠️ По услуге", callback_data='filter_service_menu'),
        types.InlineKeyboardButton("🔙 Закрыть", callback_data='close_filter')
    )
    bot.send_message(call.message.chat.id, "⚙️ Выберите фильтр:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('filter_'))
def filter_handler(call):
    data = call.data
    if data == 'filter_popular_formula':
        bot.current_filter = 'popular_formula'
        bot.current_filter_value = None
        makers = get_makers_by_filter('popular_formula')
    elif data == 'filter_price_asc':
        bot.current_filter = 'price_asc'
        makers = get_makers_by_filter('price_asc')
    elif data == 'filter_price_desc':
        bot.current_filter = 'price_desc'
        makers = get_makers_by_filter('price_desc')
    elif data == 'filter_style_menu':
        markup = types.InlineKeyboardMarkup(row_width=2)
        styles = ['modern', 'colorful', 'realism', 'namemc', 'special']
        for s in styles:
            markup.add(types.InlineKeyboardButton(s, callback_data=f'filter_style_{s}'))
        bot.send_message(call.message.chat.id, "Выберите стиль:", reply_markup=markup)
        return
    elif data == 'filter_service_menu':
        markup = types.InlineKeyboardMarkup(row_width=2)
        services = ['Скины', 'Модели', 'Текстуры', 'Рендер', '128x128', '256x256', '3D скины']
        for s in services:
            markup.add(types.InlineKeyboardButton(s, callback_data=f'filter_service_{s}'))
        bot.send_message(call.message.chat.id, "Выберите услугу:", reply_markup=markup)
        return
    elif data.startswith('filter_style_'):
        style = data.split('_', 2)[2]
        bot.current_filter = 'style'
        bot.current_filter_value = style
        makers = get_makers_by_filter('style', style)
    elif data.startswith('filter_service_'):
        service = data.split('_', 2)[2]
        bot.current_filter = 'service'
        bot.current_filter_value = service
        makers = get_makers_by_filter('service', service)
    else:
        return
    bot.delete_message(call.message.chat.id, call.message.message_id)
    if not makers:
        bot.send_message(call.message.chat.id, "😔 Ничего не найдено.")
        return
    bot.current_makers = makers
    show_card(call.message.chat.id, 0)

@bot.callback_query_handler(func=lambda call: call.data == 'close_filter')
def close_filter(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == 'back_main')
def back_main(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "🎨 Главное меню", reply_markup=main_menu_markup())

@bot.callback_query_handler(func=lambda call: call.data.startswith('gallery_'))
def gallery(call):
    maker_id = int(call.data.split('_')[1])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT photo_ids FROM skin_makers WHERE id=?", (maker_id,))
    row = c.fetchone()
    conn.close()
    if not row: return
    photos = json.loads(row[0])
    if not photos:
        bot.answer_callback_query(call.id, "Нет фото")
        return
    media = [types.InputMediaPhoto(pid) for pid in photos]
    bot.send_media_group(call.message.chat.id, media)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('social_'))
def show_social_links(call):
    maker_id = int(call.data.split('_')[1])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT social_telegram, social_twitter, social_pinterest, social_tiktok, social_youtube, social_instagram, social_vk, social_max FROM skin_makers WHERE id=?", (maker_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        bot.answer_callback_query(call.id, "Нет данных")
        return
    links = []
    if row[0]: links.append(("📨 Telegram", row[0]))
    if row[1]: links.append(("𝕏 Twitter", row[1]))
    if row[2]: links.append(("📌 Pinterest", row[2]))
    if row[3]: links.append(("🎵 TikTok", row[3]))
    if row[4]: links.append(("▶️ YouTube", row[4]))
    if row[5]: links.append(("📷 Instagram", row[5]))
    if row[6]: links.append(("💙 VK", row[6]))
    if row[7]: links.append(("🔶 Max (не рекомендуем)", row[7]))
    if not links:
        bot.answer_callback_query(call.id, "Соцсети не указаны")
        return
    markup = types.InlineKeyboardMarkup()
    for name, url in links:
        markup.add(types.InlineKeyboardButton(name, url=url))
    markup.add(types.InlineKeyboardButton("🔙 Закрыть", callback_data='close_social'))
    bot.send_message(call.message.chat.id, "🌐 Социальные сети скинмейкера:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'close_social')
def close_social(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('bookmark_'))
def bookmark_maker(call):
    maker_id = int(call.data.split('_')[1])
    user_id = call.from_user.id
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT id, folder_name FROM bookmark_folders WHERE user_id=?", (user_id,))
    folders = c.fetchall()
    conn.close()
    if not folders:
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("INSERT INTO bookmark_folders (user_id, folder_name) VALUES (?, 'Избранное')", (user_id,))
        conn.commit()
        folder_id = c.lastrowid
        conn.close()
        add_to_folder(user_id, maker_id, folder_id)
        bot.answer_callback_query(call.id, "Добавлено в 'Избранное'")
        return
    markup = types.InlineKeyboardMarkup()
    for f in folders:
        markup.add(types.InlineKeyboardButton(f[1], callback_data=f'addtofolder_{maker_id}_{f[0]}'))
    markup.add(types.InlineKeyboardButton("➕ Новая папка", callback_data=f'newfolder_{maker_id}'))
    bot.send_message(call.message.chat.id, "Выберите папку:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('addtofolder_'))
def add_to_existing_folder(call):
    _, maker_id, folder_id = call.data.split('_')
    add_to_folder(call.from_user.id, int(maker_id), int(folder_id))
    bot.answer_callback_query(call.id, "✅ Добавлено!")
    bot.delete_message(call.message.chat.id, call.message.message_id)

def add_to_folder(user_id, maker_id, folder_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("INSERT INTO bookmarks (user_id, skin_maker_id, folder_id) VALUES (?,?,?)", (user_id, maker_id, folder_id))
    conn.commit()
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith('newfolder_'))
def new_folder_prompt(call):
    maker_id = call.data.split('_')[1]
    msg = bot.send_message(call.message.chat.id, "Введите название папки:")
    bot.register_next_step_handler(msg, create_folder_and_add, maker_id)

def create_folder_and_add(message, maker_id):
    folder_name = message.text
    user_id = message.from_user.id
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("INSERT INTO bookmark_folders (user_id, folder_name) VALUES (?, ?)", (user_id, folder_name))
    folder_id = c.lastrowid
    conn.commit()
    conn.close()
    add_to_folder(user_id, int(maker_id), folder_id)
    bot.send_message(message.chat.id, f"Папка '{folder_name}' создана, мастер добавлен.")

@bot.message_handler(func=lambda m: m.text == "📌 Мои закладки")
def show_bookmarks(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT id, folder_name FROM bookmark_folders WHERE user_id=?", (user_id,))
    folders = c.fetchall()
    if not folders:
        bot.send_message(message.chat.id, "📌 У вас пока нет закладок")
        return
    text = "📌 Ваши закладки:\n"
    for f in folders:
        c.execute("SELECT sm.name FROM skin_makers sm JOIN bookmarks b ON sm.id = b.skin_maker_id WHERE b.folder_id=? AND b.user_id=?", (f[0], user_id))
        makers = c.fetchall()
        if makers:
            text += f"\n📁 {f[1]}:\n  " + "\n  ".join([m[0] for m in makers])
    conn.close()
    bot.send_message(message.chat.id, text if text else "📌 У вас пока нет закладок")

@bot.message_handler(func=lambda m: m.text == "💸 Донат на сервера")
def donate(message):
    text = ("💸 Донат на сервера\nПо желанию\n\n"
            "❤️ Поддержать бота:\n\n"
            "Т-Банк: 2200702103771312\n"
            "СБП: +79033799210\n"
            "Boosty: https://boosty.to/dfmskimake/about")
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "ℹ️ О боте")
def about(message):
    bot.send_message(message.chat.id, "Frime Skin — платформа для поиска скинмейкеров Minecraft. Версия 3.0\n\nСвязь: @Defemar")

# ПРОДОЛЖЕНИЕ В ЧАСТИ 2

@bot.message_handler(func=lambda m: m.text == "👤 Мой профиль")
def profile_main(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM skin_makers WHERE user_id=?", (user_id,))
    maker = c.fetchone()
    conn.close()
    if not maker:
        bot.send_message(message.chat.id, "Вы не зарегистрированы как скинмейкер. Подайте заявку или дождитесь её одобрения.")
        return
    text = "👤 Ваш профиль:\n\n"
    text += f"Имя: {maker[3]}\n"
    price_text = f"от {maker[5]} ₽" if maker[5] else "не указана"
    if maker[6] and maker[7]:
        price_text = f"от {maker[6]} до {maker[7]} ₽"
    text += f"Ценник: {price_text}\n"
    text += f"Стиль: {maker[17]}"
    if maker[18]: text += f"\n✨ {maker[18]}"
    text += f"\nСтрана: {countries.get(maker[28], maker[28])}\n"
    text += f"Эмодзи: {maker[27] or 'не задано'}\n"
    status_text = "🏖️ Отпуск" if maker[13] else ("⚠️ Перегружен до " + maker[26] if maker[26] else "Активен")
    text += f"Статус: {status_text}\n"
    order_text = maker[39] if len(maker) > 39 and maker[39] else f"{maker[24]} {'✅' if maker[25] else '~'}"
    text += f"Заказы: {order_text}\n"
    text += f"Просмотры: {maker[23]}\n"
    text += f"Рейтинг: {(maker[9] or 5.0):.1f}/5"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("✏️ Редактировать профиль", callback_data='edit_profile'),
        types.InlineKeyboardButton("🕰️ Изменить стаж", callback_data='edit_exp'),
        types.InlineKeyboardButton("📊 Изменить заказы", callback_data='edit_orders'),
        types.InlineKeyboardButton("💲 Изменить цены", callback_data='edit_prices'),
        types.InlineKeyboardButton("🎨 Изменить эмодзи", callback_data='edit_emoji'),
        types.InlineKeyboardButton("🌍 Изменить страну", callback_data='edit_country'),
        types.InlineKeyboardButton("🏖️ Режим отпуска", callback_data='toggle_vacation'),
        types.InlineKeyboardButton("⚠️ Указать занятость", callback_data='set_busy'),
        types.InlineKeyboardButton("📊 Статистика", callback_data='profile_stats'),
        types.InlineKeyboardButton("✉️ Запросить правку", callback_data='request_edit'),
        types.InlineKeyboardButton("🔙 В меню", callback_data='back_main')
    )
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'edit_profile')
def edit_profile_cb(call):
    user_id = call.from_user.id
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM skin_makers WHERE user_id=?", (user_id,))
    maker = c.fetchone()
    conn.close()
    if not maker:
        bot.answer_callback_query(call.id, "Вы не скинмейкер")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("Изменить имя", callback_data='edit_name'),
        types.InlineKeyboardButton("Изменить описание", callback_data='edit_desc'),
        types.InlineKeyboardButton("Изменить стиль", callback_data='edit_style'),
        types.InlineKeyboardButton("Изменить услуги", callback_data='edit_services'),
        types.InlineKeyboardButton("Изменить фото", callback_data='edit_photos'),
        types.InlineKeyboardButton("Изменить ссылку для заказа", callback_data='edit_contact'),
        types.InlineKeyboardButton("Изменить соцсети", callback_data='edit_social'),
        types.InlineKeyboardButton("⏱️ Изменить сроки", callback_data='edit_delivery'),
        types.InlineKeyboardButton("🔙 Назад", callback_data='back_to_profile')
    )
    bot.edit_message_text("Что вы хотите изменить?", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_profile')
def back_to_profile(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    profile_main(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'edit_name')
def edit_name_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите новое имя:")
    bot.register_next_step_handler(msg, process_edit_name)

def process_edit_name(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET name=? WHERE user_id=?", (message.text, user_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Имя обновлено.")

@bot.callback_query_handler(func=lambda call: call.data == 'edit_desc')
def edit_desc_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите новое описание:")
    bot.register_next_step_handler(msg, process_edit_desc)

def process_edit_desc(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET description=? WHERE user_id=?", (message.text, user_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Описание обновлено.")

@bot.callback_query_handler(func=lambda call: call.data == 'edit_style')
def edit_style_cb(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    styles = ['modern', 'colorful', 'realism', 'namemc', 'special']
    for s in styles:
        markup.add(types.InlineKeyboardButton(s, callback_data=f'set_style_{s}'))
    bot.send_message(call.message.chat.id, "Выберите стиль:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_style_'))
def set_style(call):
    style = call.data.split('_')[2]
    user_id = call.from_user.id
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET style=? WHERE user_id=?", (style, user_id))
    conn.commit()
    conn.close()
    bot.edit_message_text(f"✅ Стиль изменён на {style}", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == 'edit_services')
def edit_services_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите услуги через запятую (например: Скины, Модели):")
    bot.register_next_step_handler(msg, process_edit_services)

def process_edit_services(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET services=? WHERE user_id=?", (message.text, user_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Услуги обновлены.")

@bot.callback_query_handler(func=lambda call: call.data == 'edit_photos')
def edit_photos_cb(call):
    msg = bot.send_message(call.message.chat.id, "Отправьте новые фото (до 9, по одному, затем /done):")
    bot.register_next_step_handler(msg, process_edit_photos)

def process_edit_photos(message):
    if message.content_type == 'photo':
        user_id = message.from_user.id
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("UPDATE skin_makers SET photo_ids=? WHERE user_id=?", (json.dumps([message.photo[-1].file_id]), user_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Фото обновлено (заменено на одно).")
    else:
        bot.send_message(message.chat.id, "Отправьте фото или /done для пропуска.")

@bot.callback_query_handler(func=lambda call: call.data == 'edit_contact')
def edit_contact_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите новую ссылку для заказа:")
    bot.register_next_step_handler(msg, process_edit_contact)

def process_edit_contact(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET contact_link=? WHERE user_id=?", (message.text.strip(), user_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Ссылка обновлена.")

@bot.callback_query_handler(func=lambda call: call.data == 'edit_social')
def edit_social_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите соцсети в формате:\nTelegram: ссылка\n...\nMax: ссылка\n(можно '-' для пропуска):")
    bot.register_next_step_handler(msg, process_edit_social)

def process_edit_social(message):
    user_id = message.from_user.id
    text = message.text.strip()
    socials = {
        'social_telegram': None, 'social_twitter': None, 'social_pinterest': None,
        'social_tiktok': None, 'social_youtube': None, 'social_instagram': None,
        'social_vk': None, 'social_max': None
    }
    if text != '-':
        pairs = text.replace('\n', ',').split(',')
        for pair in pairs:
            if ':' in pair:
                key, val = pair.split(':', 1)
                key = key.strip().lower()
                val = val.strip()
                if 'tg' in key or 'telegram' in key: socials['social_telegram'] = val
                elif 'tw' in key or 'twitter' in key or 'x' in key: socials['social_twitter'] = val
                elif 'pin' in key or 'pinterest' in key: socials['social_pinterest'] = val
                elif 'tik' in key or 'tiktok' in key: socials['social_tiktok'] = val
                elif 'you' in key or 'youtube' in key: socials['social_youtube'] = val
                elif 'insta' in key or 'instagram' in key: socials['social_instagram'] = val
                elif 'vk' in key: socials['social_vk'] = val
                elif 'max' in key: socials['social_max'] = val
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute('''UPDATE skin_makers SET social_telegram=?, social_twitter=?, social_pinterest=?, social_tiktok=?, social_youtube=?, social_instagram=?, social_vk=?, social_max=? WHERE user_id=?''',
              (socials['social_telegram'], socials['social_twitter'], socials['social_pinterest'], socials['social_tiktok'],
               socials['social_youtube'], socials['social_instagram'], socials['social_vk'], socials['social_max'], user_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Соцсети обновлены.")

@bot.callback_query_handler(func=lambda call: call.data == 'edit_emoji')
def edit_emoji_cb(call):
    msg = bot.send_message(call.message.chat.id, "Отправьте один эмодзи для профиля (или '-' чтобы убрать):")
    bot.register_next_step_handler(msg, process_edit_emoji)

def process_edit_emoji(message):
    user_id = message.from_user.id
    text = message.text.strip()
    if text == '-': emoji = None
    else: emoji = text[0] if text else None
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET custom_emoji=? WHERE user_id=?", (emoji, user_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Эмодзи обновлён.")

@bot.callback_query_handler(func=lambda call: call.data == 'edit_country')
def edit_country_cb(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, name in countries.items():
        markup.add(types.InlineKeyboardButton(f"{flags[code]} {name}", callback_data=f'set_country_{code}'))
    bot.send_message(call.message.chat.id, "🌍 Выберите страну:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_country_'))
def set_country_cb(call):
    country_code = call.data.split('_')[2]
    user_id = call.from_user.id
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET country_code=? WHERE user_id=?", (country_code, user_id))
    conn.commit()
    conn.close()
    bot.edit_message_text(f"✅ Страна изменена на {flags[country_code]} {countries[country_code]}", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == 'edit_delivery')
def edit_delivery_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите минимальный срок выполнения (дней):")
    bot.register_next_step_handler(msg, process_edit_delivery_min)

def process_edit_delivery_min(message):
    try:
        dmin = int(message.text)
        if dmin < 1: raise ValueError
    except:
        msg = bot.send_message(message.chat.id, "❌ Введите целое число >0. Минимальный срок:")
        bot.register_next_step_handler(msg, process_edit_delivery_min)
        return
    msg = bot.send_message(message.chat.id, "Введите максимальный срок выполнения (дней):")
    bot.register_next_step_handler(msg, process_edit_delivery_max, dmin)

def process_edit_delivery_max(message, dmin):
    try:
        dmax = int(message.text)
        if dmax < dmin: raise ValueError
    except:
        msg = bot.send_message(message.chat.id, f"❌ Введите число ≥ {dmin}. Максимальный срок:")
        bot.register_next_step_handler(msg, process_edit_delivery_max, dmin)
        return
    user_id = message.from_user.id
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET delivery_min_days=?, delivery_max_days=? WHERE user_id=?", (dmin, dmax, user_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Сроки обновлены: {dmin}–{dmax} дн.")

@bot.callback_query_handler(func=lambda call: call.data == 'edit_exp')
def edit_exp_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите новый стаж (например, '2 года'):")
    bot.register_next_step_handler(msg, process_edit_exp)

def process_edit_exp(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET display_experience=? WHERE user_id=?", (message.text.strip(), user_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Стаж обновлён.")

@bot.callback_query_handler(func=lambda call: call.data == 'edit_orders')
def edit_orders_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите количество заказов (можно '500+'):")
    bot.register_next_step_handler(msg, process_edit_orders)

def process_edit_orders(message):
    user_id = message.from_user.id
    val = message.text.strip()
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    if val.isdigit():
        c.execute("UPDATE skin_makers SET completed_orders=?, orders_confirmed=1, order_display=NULL WHERE user_id=?", (int(val), user_id))
    else:
        c.execute("UPDATE skin_makers SET order_display=?, orders_confirmed=1 WHERE user_id=?", (val, user_id))
        nums = re.findall(r'\d+', val)
        if nums: c.execute("UPDATE skin_makers SET completed_orders=? WHERE user_id=?", (int(nums[0]), user_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Заказы обновлены: {val}")

@bot.callback_query_handler(func=lambda call: call.data == 'edit_prices')
def edit_prices_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите минимальную цену:")
    bot.register_next_step_handler(msg, process_edit_price_min)

def process_edit_price_min(message):
    try:
        pmin = int(message.text)
        user_id = message.from_user.id
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("UPDATE skin_makers SET price_min=? WHERE user_id=?", (pmin, user_id))
        conn.commit()
        conn.close()
        msg = bot.send_message(message.chat.id, "Введите максимальную цену:")
        bot.register_next_step_handler(msg, process_edit_price_max, user_id)
    except:
        msg = bot.send_message(message.chat.id, "❌ Введите число. Минимальная цена:")
        bot.register_next_step_handler(msg, process_edit_price_min)

def process_edit_price_max(message, user_id):
    try:
        pmax = int(message.text)
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("UPDATE skin_makers SET price_max=?, price=? WHERE user_id=?", (pmax, pmax, user_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Диапазон цен обновлён.")
    except:
        msg = bot.send_message(message.chat.id, "❌ Введите число. Максимальная цена:")
        bot.register_next_step_handler(msg, process_edit_price_max, user_id)

@bot.callback_query_handler(func=lambda call: call.data == 'toggle_vacation')
def toggle_vacation_cb(call):
    user_id = call.from_user.id
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT is_vacation FROM skin_makers WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        bot.answer_callback_query(call.id, "Ошибка")
        return
    new_state = 0 if row[0] else 1
    c.execute("UPDATE skin_makers SET is_vacation=? WHERE user_id=?", (new_state, user_id))
    conn.commit()
    conn.close()
    state_text = "включён" if new_state else "выключен"
    bot.answer_callback_query(call.id, f"Режим отпуска {state_text}.")

@bot.callback_query_handler(func=lambda call: call.data == 'set_busy')
def set_busy_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите дату, до которой заняты (ГГГГ-ММ-ДД) или '-' для снятия:")
    bot.register_next_step_handler(msg, process_busy_date)

def process_busy_date(message):
    user_id = message.from_user.id
    text = message.text.strip()
    if text == '-': date_str = None
    else:
        try:
            datetime.strptime(text, '%Y-%m-%d')
            date_str = text
        except:
            bot.send_message(message.chat.id, "Неверный формат. Используйте ГГГГ-ММ-ДД.")
            return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET busy_until=? WHERE user_id=?", (date_str, user_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Статус занятости обновлён.")

@bot.callback_query_handler(func=lambda call: call.data == 'profile_stats')
def profile_stats_cb(call):
    user_id = call.from_user.id
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT views, completed_orders, orders_confirmed, rating, total_ratings, order_display FROM skin_makers WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        bot.answer_callback_query(call.id, "Ошибка")
        return
    order_text = row[5] if row[5] else f"{row[1]} {'✅' if row[2] else '~'}"
    text = f"📊 Статистика:\n👁 Просмотров: {row[0]}\n📦 Заказов: {order_text}\n⭐ Рейтинг: {(row[3] or 5.0):.1f} (оценок: {row[4]})"
    bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data == 'request_edit')
def request_edit_cb(call):
    user_id = call.from_user.id
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT id FROM skin_makers WHERE user_id=?", (user_id,))
    maker = c.fetchone()
    conn.close()
    if not maker:
        bot.answer_callback_query(call.id, "Вы не скинмейкер")
        return
    msg = bot.send_message(call.message.chat.id, "Опишите, что нужно изменить (например: стаж на 2 года, заказов 150+):")
    bot.register_next_step_handler(msg, process_edit_request, maker[0])

def process_edit_request(message, maker_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("INSERT INTO edit_requests (skin_maker_id, field, new_value) VALUES (?,?,?)",
              (maker_id, 'custom', message.text))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "Запрос отправлен администратору.")
    notify_admins(f"📩 Запрос правок от скинмейкера ID{maker_id}: {message.text}")

user_states = {}

@bot.message_handler(func=lambda m: m.text == "📝 Подать заявку")
def apply_start(message):
    if is_blacklisted(message.from_user.id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы.")
        return
    user_id = message.from_user.id
    user_states[user_id] = {'photos': [], 'step': 'photo'}
    msg = bot.send_message(message.chat.id, "📸 Отправьте фото ваших работ (можно до 9, по одному, затем /done)\n❌ Для отмены отправьте /cancel в любой момент.")
    bot.register_next_step_handler(msg, process_apply_photo)

def check_cancel(message, next_func, *args):
    if message.text and message.text.strip() == '/cancel':
        user_id = message.from_user.id
        if user_id in user_states: del user_states[user_id]
        bot.send_message(message.chat.id, "❌ Подача заявки отменена.", reply_markup=main_menu_markup())
        return True
    return False

def process_apply_photo(message):
    if check_cancel(message, process_apply_photo): return
    user_id = message.from_user.id
    if message.content_type == 'photo':
        if len(user_states[user_id]['photos']) < 9:
            user_states[user_id]['photos'].append(message.photo[-1].file_id)
            bot.send_message(message.chat.id, f"✅ Фото {len(user_states[user_id]['photos'])}/9 добавлено.")
        else:
            bot.send_message(message.chat.id, "⚠️ Максимум 9 фото. Отправьте /done для продолжения.")
    elif message.text and message.text.startswith('/done'):
        if not user_states[user_id]['photos']:
            bot.send_message(message.chat.id, "❌ Отправьте хотя бы одно фото!")
            bot.register_next_step_handler(message, process_apply_photo)
            return
        user_states[user_id]['step'] = 'name'
        msg = bot.send_message(message.chat.id, "✏️ Введите ваше имя (никнейм):\n❌ /cancel — отмена")
        bot.register_next_step_handler(msg, process_apply_name)
        return
    else:
        bot.send_message(message.chat.id, "📸 Отправьте фото, /done для продолжения или /cancel для отмены.")
    msg = bot.send_message(message.chat.id, "Ожидаю следующее фото, /done или /cancel...")
    bot.register_next_step_handler(msg, process_apply_photo)

def process_apply_name(message):
    if check_cancel(message, process_apply_name): return
    user_id = message.from_user.id
    user_states[user_id]['name'] = message.text
    msg = bot.send_message(message.chat.id, "💬 Введите описание ваших услуг:\n❌ /cancel — отмена")
    bot.register_next_step_handler(msg, process_apply_description)

def process_apply_description(message):
    if check_cancel(message, process_apply_description): return
    user_id = message.from_user.id
    user_states[user_id]['description'] = message.text
    msg = bot.send_message(message.chat.id, "💲 Введите минимальную цену:\n❌ /cancel — отмена")
    bot.register_next_step_handler(msg, process_apply_price_min)

def process_apply_price_min(message):
    if check_cancel(message, process_apply_price_min): return
    try:
        pmin = int(message.text)
        user_id = message.from_user.id
        user_states[user_id]['price_min'] = pmin
        msg = bot.send_message(message.chat.id, "Введите максимальную цену:")
        bot.register_next_step_handler(msg, process_apply_price_max)
    except:
        msg = bot.send_message(message.chat.id, "❌ Введите число. Минимальная цена:")
        bot.register_next_step_handler(msg, process_apply_price_min)

def process_apply_price_max(message):
    if check_cancel(message, process_apply_price_max): return
    try:
        pmax = int(message.text)
        user_id = message.from_user.id
        user_states[user_id]['price_max'] = pmax
        user_states[user_id]['price'] = pmax
        markup = types.InlineKeyboardMarkup(row_width=2)
        styles = ['modern', 'colorful', 'realism', 'namemc', 'special']
        for s in styles: markup.add(types.InlineKeyboardButton(s, callback_data=f'applystyle_{s}'))
        markup.add(types.InlineKeyboardButton("✅ Готово", callback_data='applystyle_done'))
        markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data='apply_cancel'))
        user_states[user_id]['selected_styles'] = []
        bot.send_message(message.chat.id, "🎨 Выберите стиль (можно несколько):", reply_markup=markup)
    except:
        msg = bot.send_message(message.chat.id, "❌ Введите число. Максимальная цена:")
        bot.register_next_step_handler(msg, process_apply_price_max)

@bot.callback_query_handler(func=lambda call: call.data == 'apply_cancel')
def apply_cancel_cb(call):
    user_id = call.from_user.id
    if user_id in user_states: del user_states[user_id]
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "❌ Подача заявки отменена.", reply_markup=main_menu_markup())

@bot.callback_query_handler(func=lambda call: call.data.startswith('applystyle_'))
def apply_style_select(call):
    user_id = call.from_user.id
    if user_id not in user_states:
        bot.answer_callback_query(call.id, "Ошибка: начните заявку заново.")
        return
    style = call.data.split('_')[1]
    if style == 'done':
        if not user_states[user_id]['selected_styles']:
            bot.answer_callback_query(call.id, "Выберите хотя бы один стиль!")
            return
        selected = user_states[user_id]['selected_styles']
        if 'namemc' in selected and len(selected) > 1 and 'special' not in selected:
            bot.answer_callback_query(call.id, "NameMc может сочетаться только с special!")
            return
        bot.delete_message(call.message.chat.id, call.message.message_id)
        markup = types.InlineKeyboardMarkup(row_width=2)
        services = ['Скины', 'Модели', 'Текстуры', 'Рендер', '128x128', '256x256', '3D скины']
        for s in services: markup.add(types.InlineKeyboardButton(s, callback_data=f'applyservice_{s}'))
        markup.add(types.InlineKeyboardButton("✅ Готово", callback_data='applyservice_done'))
        markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data='apply_cancel'))
        user_states[user_id]['selected_services'] = []
        bot.send_message(call.message.chat.id, "🛠️ Выберите услуги:", reply_markup=markup)
    else:
        sel = user_states[user_id]['selected_styles']
        if style in sel: sel.remove(style)
        else: sel.append(style)
        bot.answer_callback_query(call.id, f"Выбрано: {', '.join(sel)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('applyservice_'))
def apply_service_select(call):
    user_id = call.from_user.id
    if user_id not in user_states:
        bot.answer_callback_query(call.id, "Ошибка: начните заявку заново.")
        return
    serv = call.data.split('_')[1]
    if serv == 'done':
        if not user_states[user_id]['selected_services']:
            bot.answer_callback_query(call.id, "Выберите хотя бы одну услугу!")
            return
        bot.delete_message(call.message.chat.id, call.message.message_id)
        msg = bot.send_message(call.message.chat.id, "🔗 Введите ссылку для заказа (Telegram-аккаунт, бот или канал). Если нет, отправьте '-'\n❌ /cancel — отмена")
        bot.register_next_step_handler(msg, process_apply_contact)
    else:
        sel = user_states[user_id]['selected_services']
        if serv in sel: sel.remove(serv)
        else: sel.append(serv)
        bot.answer_callback_query(call.id, f"Выбрано: {', '.join(sel)}")

def process_apply_contact(message):
    if check_cancel(message, process_apply_contact): return
    user_id = message.from_user.id
    if message.text == '-': user_states[user_id]['contact_link'] = None
    else: user_states[user_id]['contact_link'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введите минимальный срок выполнения (дней):\n❌ /cancel — отмена")
    bot.register_next_step_handler(msg, process_apply_delivery_min)

def process_apply_delivery_min(message):
    if check_cancel(message, process_apply_delivery_min): return
    try:
        dmin = int(message.text)
        if dmin < 1: raise ValueError
    except:
        msg = bot.send_message(message.chat.id, "❌ Введите целое число >0:")
        bot.register_next_step_handler(msg, process_apply_delivery_min)
        return
    user_states[message.from_user.id]['delivery_min'] = dmin
    msg = bot.send_message(message.chat.id, "Введите максимальный срок выполнения (дней):")
    bot.register_next_step_handler(msg, process_apply_delivery_max)

def process_apply_delivery_max(message):
    if check_cancel(message, process_apply_delivery_max): return
    try:
        dmax = int(message.text)
        dmin = user_states[message.from_user.id]['delivery_min']
        if dmax < dmin: raise ValueError
    except:
        msg = bot.send_message(message.chat.id, f"❌ Введите число ≥ {dmin}:")
        bot.register_next_step_handler(msg, process_apply_delivery_max)
        return
    user_states[message.from_user.id]['delivery_max'] = dmax
    msg = bot.send_message(message.chat.id, "Теперь укажите ссылки на соцсети (можно пропустить, отправив '-').\n"
                          "Вводите в формате:\nTelegram: ссылка\nTwitter: ссылка\nPinterest: ссылка\nTikTok: ссылка\n"
                          "YouTube: ссылка\nInstagram: ссылка\nVK: ссылка\nMax: ссылка\n\n"
                          "Или одной строкой через запятую. Для пропуска отправьте '-'\n❌ /cancel — отмена")
    bot.register_next_step_handler(msg, process_apply_social)

def process_apply_social(message):
    if check_cancel(message, process_apply_social): return
    user_id = message.from_user.id
    text = message.text.strip()
    socials = {'social_telegram': None, 'social_twitter': None, 'social_pinterest': None,
               'social_tiktok': None, 'social_youtube': None, 'social_instagram': None,
               'social_vk': None, 'social_max': None}
    if text != '-':
        pairs = text.replace('\n', ',').split(',')
        for pair in pairs:
            if ':' in pair:
                key, val = pair.split(':', 1)
                key = key.strip().lower()
                val = val.strip()
                if 'tg' in key or 'telegram' in key: socials['social_telegram'] = val
                elif 'tw' in key or 'twitter' in key or 'x' in key: socials['social_twitter'] = val
                elif 'pin' in key or 'pinterest' in key: socials['social_pinterest'] = val
                elif 'tik' in key or 'tiktok' in key: socials['social_tiktok'] = val
                elif 'you' in key or 'youtube' in key: socials['social_youtube'] = val
                elif 'insta' in key or 'instagram' in key: socials['social_instagram'] = val
                elif 'vk' in key: socials['social_vk'] = val
                elif 'max' in key: socials['social_max'] = val
    user_states[user_id].update(socials)
    data = user_states.pop(user_id)
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute('''INSERT INTO applications
        (user_id, username, name, description, price, price_min, price_max, services, photo_ids, style, custom_style_name,
         contact_link, social_telegram, social_twitter, social_pinterest, social_tiktok,
         social_youtube, social_instagram, social_vk, social_max,
         delivery_min_days, delivery_max_days)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (user_id, message.from_user.username or "", data['name'], data['description'],
         data.get('price', 0), data.get('price_min', 0), data.get('price_max', 0),
         ', '.join(data['selected_services']), json.dumps(data['photos']),
         ', '.join(data['selected_styles']), '',
         data.get('contact_link'), data.get('social_telegram'), data.get('social_twitter'),
         data.get('social_pinterest'), data.get('social_tiktok'), data.get('social_youtube'),
         data.get('social_instagram'), data.get('social_vk'), data.get('social_max'),
         data.get('delivery_min', 1), data.get('delivery_max', 3)))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Заявка отправлена! Ожидайте одобрения администратором.", reply_markup=main_menu_markup())
    notify_admins(f"📋 Новая заявка от @{message.from_user.username}")

# ПРОДОЛЖЕНИЕ В ЧАСТИ 3

def show_applications(chat_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM applications WHERE status='pending'")
    apps = c.fetchall()
    conn.close()
    if not apps:
        bot.send_message(chat_id, "Нет заявок.")
        return
    for app in apps:
        text = f"📋 Заявка #{app[0]}\n\n"
        text += f"👤 Имя: {app[3]}\n💬 Описание: {app[4]}\n"
        price_text = f"от {app[5]} ₽" if app[5] else "не указана"
        if app[6] and app[7]: price_text = f"от {app[6]} до {app[7]} ₽"
        text += f"💲 Ценник: {price_text}\n"
        text += f"🎨 Стили: {app[10]}"
        if app[11]: text += f"\n✨ Особый подстиль: {app[11]}"
        text += f"\n🛠️ Услуги: {app[8]}\n"
        text += f"⏱ Сроки: {app[24]}–{app[25]} дн.\n"
        if app[15]: text += f"🔗 Ссылка для заказа: {app[15]}\n"
        soc = []
        if app[16]: soc.append(f"📨 Telegram: {app[16]}")
        if app[17]: soc.append(f"𝕏 Twitter: {app[17]}")
        if app[18]: soc.append(f"📌 Pinterest: {app[18]}")
        if app[19]: soc.append(f"🎵 TikTok: {app[19]}")
        if app[20]: soc.append(f"▶️ YouTube: {app[20]}")
        if app[21]: soc.append(f"📷 Instagram: {app[21]}")
        if app[22]: soc.append(f"💙 VK: {app[22]}")
        if app[23]: soc.append(f"🔶 Max: {app[23]}")
        if soc: text += "🌐 Соцсети:\n" + "\n".join(soc) + "\n"
        text += f"\nОтправитель: {username_by_id(app[1])}"
        photos = json.loads(app[9])
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Принять", callback_data=f'approve_{app[0]}'),
            types.InlineKeyboardButton("❌ Отклонить", callback_data=f'reject_{app[0]}')
        )
        if photos: bot.send_photo(chat_id, photos[0], caption=text, reply_markup=markup)
        else: bot.send_message(chat_id, text, reply_markup=markup)

@bot.message_handler(commands=['admin_applications'])
def admin_applications_cmd(message):
    if not is_admin(message.from_user.id): return
    show_applications(message.chat.id)

@bot.message_handler(func=lambda m: m.text == "📋 Заявки" and is_admin(m.from_user.id))
def admin_applications_button(message):
    show_applications(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_'))
def approve_app(call):
    app_id = int(call.data.split('_')[1])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM applications WHERE id=?", (app_id,))
    app = c.fetchone()
    c.execute('''INSERT INTO skin_makers
        (user_id, username, name, description, price, price_min, price_max, services, photo_ids, style, custom_style_name,
         contact_link, social_telegram, social_twitter, social_pinterest, social_tiktok,
         social_youtube, social_instagram, social_vk, social_max,
         delivery_min_days, delivery_max_days)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (app[1], app[2], app[3], app[4], app[5], app[6], app[7], app[8], app[9], app[10], app[11],
         app[15], app[16], app[17], app[18], app[19], app[20], app[21], app[22], app[23],
         app[24], app[25]))
    c.execute("UPDATE applications SET status='approved' WHERE id=?", (app_id,))
    conn.commit()
    conn.close()
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    bot.send_message(call.message.chat.id, f"Заявка #{app_id} одобрена.")
    bot.send_message(app[1], "🎉 Ваша заявка принята!")
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
    bot.send_message(call.message.chat.id, f"Заявка #{app_id} отклонена.")
    log_action(call.from_user.id, 'reject_application', f'App #{app_id}')

@bot.message_handler(commands=['admin_all_makers'])
def admin_all_makers_cmd(message):
    if not is_admin(message.from_user.id): return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT id, name, user_id, rating, is_active, complaints, shadow_banned FROM skin_makers")
    makers = c.fetchall()
    conn.close()
    if not makers:
        bot.send_message(message.chat.id, "Список пуст.")
        return
    text = "👥 Скинмейкеры:\n\n"
    for m in makers:
        username = username_by_id(m[2])
        text += f"ID{m[0]} {m[1]} ({username})\n⭐{(m[3] or 5.0):.1f} | Активен:{'✅' if m[4] else '❌'} | Жалобы:{m[5]} | Теневой:{'⚠️' if m[6] else '✅'}\n\n"
    if len(text) > 4000:
        for i in range(0, len(text), 4000): bot.send_message(message.chat.id, text[i:i+4000])
    else: bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "👥 Скинмейкеры" and is_admin(m.from_user.id))
def admin_makers_button(message):
    admin_all_makers_cmd(message)

@bot.message_handler(commands=['admin_stats'])
def admin_stats_cmd(message):
    if not is_admin(message.from_user.id): return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM skin_makers")
    makers_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM skin_makers WHERE is_active=1")
    active_makers = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM applications WHERE status='pending'")
    pending = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM reviews")
    reviews_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ratings")
    ratings_count = c.fetchone()[0]
    c.execute("SELECT AVG(rating) FROM skin_makers")
    avg_rating = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM blacklist")
    blacklist_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM admins")
    admins_count = c.fetchone()[0]
    conn.close()
    text = "📊 Статистика:\n\n"
    text += f"• Скинмейкеров: {makers_count} (активных: {active_makers})\n"
    text += f"• Заявок ожидает: {pending}\n• Отзывов: {reviews_count}\n• Оценок: {ratings_count}\n"
    text += f"• Средний рейтинг: {avg_rating:.1f}\n• В чёрном списке: {blacklist_count}\n• Администраторов: {admins_count}"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "📊 Статистика" and is_admin(m.from_user.id))
def admin_stats_button(message):
    admin_stats_cmd(message)

@bot.message_handler(commands=['admin_announce'])
def admin_announce_cmd(message):
    if not is_admin(message.from_user.id): return
    msg = bot.send_message(message.chat.id, "Введите текст объявления:")
    bot.register_next_step_handler(msg, process_announce_text)

@bot.message_handler(func=lambda m: m.text == "📢 Объявления" and is_admin(m.from_user.id))
def admin_announce_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ Создать объявление", callback_data='create_announce'),
        types.InlineKeyboardButton("📋 Посмотреть все", callback_data='view_announcements'),
        types.InlineKeyboardButton("🗑️ Удалить последнее", callback_data='delete_last_announce')
    )
    bot.send_message(message.chat.id, "📢 Управление объявлениями:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'create_announce')
def create_announce_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите текст объявления:")
    bot.register_next_step_handler(msg, process_announce_text)

def process_announce_text(message):
    text = message.text
    msg = bot.send_message(message.chat.id, "Прикрепите фото (или /stop чтобы завершить без фото):")
    bot.register_next_step_handler(msg, process_announce_photo, text)

def process_announce_photo(message, text):
    photo_id = None
    if message.content_type == 'photo':
        photo_id = message.photo[-1].file_id
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("INSERT INTO announcements (text, photo_id) VALUES (?,?)", (text, photo_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "Объявление создано.")
        log_action(message.from_user.id, 'create_announcement')
    elif message.text and message.text.strip() == '/stop':
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("INSERT INTO announcements (text, photo_id) VALUES (?,?)", (text, None))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "Объявление создано (без фото).")
        log_action(message.from_user.id, 'create_announcement')
    else:
        msg = bot.send_message(message.chat.id, "Отправьте фото или /stop чтобы завершить без фото.")
        bot.register_next_step_handler(msg, process_announce_photo, text)

@bot.callback_query_handler(func=lambda call: call.data == 'view_announcements')
def view_announcements_cb(call):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT text, photo_id, date FROM announcements ORDER BY date DESC LIMIT 5")
    news = c.fetchall()
    conn.close()
    if not news:
        bot.send_message(call.message.chat.id, "Объявлений нет.")
        return
    for n in news:
        text = f"{n[0]}\n📅 {n[2][:10]}"
        if n[1]: bot.send_photo(call.message.chat.id, n[1], caption=text)
        else: bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data == 'delete_last_announce')
def delete_last_announce_cb(call):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("DELETE FROM announcements WHERE id = (SELECT MAX(id) FROM announcements)")
    conn.commit()
    conn.close()
    bot.send_message(call.message.chat.id, "✅ Последнее объявление удалено.")

@bot.message_handler(commands=['admin_export'])
def admin_export_cmd(message):
    if not is_admin(message.from_user.id): return
    conn = sqlite3.connect('firme_skin.db')
    with open('export_frime.csv', 'w', encoding='utf-8') as f:
        for line in conn.iterdump(): f.write('%s\n' % line)
    conn.close()
    bot.send_document(message.chat.id, open('export_frime.csv', 'rb'), caption="Дамп базы данных")
    log_action(message.from_user.id, 'export_db')

@bot.message_handler(func=lambda m: m.text == "💾 Сохранить БД" and is_admin(m.from_user.id))
def save_db(message):
    backup_name = f'firme_skin_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    shutil.copyfile('firme_skin.db', backup_name)
    bot.send_document(message.chat.id, open(backup_name, 'rb'), caption="✅ База данных сохранена.")
    log_action(message.from_user.id, 'save_db')

@bot.message_handler(commands=['admin_shadow_ban'])
def admin_shadow_ban_cmd(message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "Укажите ID: /admin_shadow_ban <id>")
        return
    maker_id = int(args[1])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET shadow_banned=1 WHERE id=?", (maker_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"Теневой бан применён к ID {maker_id}")
    log_action(message.from_user.id, 'shadow_ban', f'Maker {maker_id}')

@bot.message_handler(commands=['admin_unshadow'])
def admin_unshadow_cmd(message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "Укажите ID: /admin_unshadow <id>")
        return
    maker_id = int(args[1])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET shadow_banned=0 WHERE id=?", (maker_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"Теневой бан снят с ID {maker_id}")
    log_action(message.from_user.id, 'unshadow', f'Maker {maker_id}')

@bot.message_handler(func=lambda m: m.text == "⛔ Теневой бан" and is_admin(m.from_user.id))
def admin_shadow_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ Применить теневой бан", callback_data='apply_shadow'),
        types.InlineKeyboardButton("➖ Снять теневой бан", callback_data='remove_shadow'),
        types.InlineKeyboardButton("📋 Список забаненных", callback_data='list_shadow')
    )
    bot.send_message(message.chat.id, "⛔ Управление теневым баном:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'apply_shadow')
def apply_shadow_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите ID скинмейкера для теневого бана:")
    bot.register_next_step_handler(msg, process_apply_shadow)

def process_apply_shadow(message):
    try: maker_id = int(message.text)
    except:
        bot.send_message(message.chat.id, "ID должен быть числом.")
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET shadow_banned=1 WHERE id=?", (maker_id,))
    c.execute("SELECT name FROM skin_makers WHERE id=?", (maker_id,))
    maker = c.fetchone()
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Теневой бан применён к {maker[0]} (ID{maker_id}).")
    log_action(message.from_user.id, 'shadow_ban', f'Maker {maker_id}')

@bot.callback_query_handler(func=lambda call: call.data == 'remove_shadow')
def remove_shadow_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите ID скинмейкера для снятия теневого бана:")
    bot.register_next_step_handler(msg, process_remove_shadow)

def process_remove_shadow(message):
    try: maker_id = int(message.text)
    except:
        bot.send_message(message.chat.id, "ID должен быть числом.")
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET shadow_banned=0 WHERE id=?", (maker_id,))
    c.execute("SELECT name FROM skin_makers WHERE id=?", (maker_id,))
    maker = c.fetchone()
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Теневой бан снят с {maker[0]} (ID{maker_id}).")
    log_action(message.from_user.id, 'unshadow', f'Maker {maker_id}')

@bot.callback_query_handler(func=lambda call: call.data == 'list_shadow')
def list_shadow_cb(call):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM skin_makers WHERE shadow_banned=1")
    makers = c.fetchall()
    conn.close()
    if not makers:
        bot.send_message(call.message.chat.id, "Нет скинмейкеров с теневым баном.")
        return
    text = "⛔ Скинмейкеры с теневым баном:\n"
    for m in makers: text += f"ID{m[0]} — {m[1]}\n"
    bot.send_message(call.message.chat.id, text)

@bot.message_handler(commands=['admin_blacklist'])
def admin_blacklist_cmd(message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "Укажите ID: /admin_blacklist <id>")
        return
    user_id = int(args[1])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO blacklist (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"Пользователь {user_id} заблокирован.")
    log_action(message.from_user.id, 'blacklist', f'User {user_id}')

@bot.message_handler(commands=['admin_whitelist'])
def admin_whitelist_cmd(message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "Укажите ID: /admin_whitelist <id>")
        return
    user_id = int(args[1])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("DELETE FROM blacklist WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"Пользователь {user_id} разблокирован.")
    log_action(message.from_user.id, 'whitelist', f'User {user_id}')

@bot.message_handler(func=lambda m: m.text == "🚫 Чёрный список" and is_admin(m.from_user.id))
def admin_blacklist_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ Заблокировать", callback_data='add_blacklist'),
        types.InlineKeyboardButton("➖ Разблокировать", callback_data='remove_blacklist'),
        types.InlineKeyboardButton("📋 Список заблокированных", callback_data='list_blacklist')
    )
    bot.send_message(message.chat.id, "🚫 Управление чёрным списком:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'add_blacklist')
def add_blacklist_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите ID пользователя для блокировки:")
    bot.register_next_step_handler(msg, process_blacklist_add)

def process_blacklist_add(message):
    try: user_id = int(message.text)
    except:
        bot.send_message(message.chat.id, "ID должен быть числом.")
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO blacklist (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Пользователь {user_id} заблокирован.")
    log_action(message.from_user.id, 'blacklist_add', f'User {user_id}')

@bot.callback_query_handler(func=lambda call: call.data == 'remove_blacklist')
def remove_blacklist_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите ID пользователя для разблокировки:")
    bot.register_next_step_handler(msg, process_blacklist_remove)

def process_blacklist_remove(message):
    try: user_id = int(message.text)
    except:
        bot.send_message(message.chat.id, "ID должен быть числом.")
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("DELETE FROM blacklist WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Пользователь {user_id} разблокирован.")
    log_action(message.from_user.id, 'blacklist_remove', f'User {user_id}')

@bot.callback_query_handler(func=lambda call: call.data == 'list_blacklist')
def list_blacklist_cb(call):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM blacklist")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    if not users:
        bot.send_message(call.message.chat.id, "Чёрный список пуст.")
        return
    text = "🚫 Заблокированные пользователи:\n" + "\n".join(map(str, users))
    bot.send_message(call.message.chat.id, text)

@bot.message_handler(commands=['add_admin'])
def add_admin_cmd(message):
    if not is_main_admin(message.from_user.id):
        bot.send_message(message.chat.id, "🚫 Только главный администратор может добавлять админов.")
        return
    args = message.text.split()
    if len(args) != 2:
        bot.send_message(message.chat.id, "Использование: /add_admin <user_id>")
        return
    try: new_admin_id = int(args[1])
    except ValueError:
        bot.send_message(message.chat.id, "ID должен быть числом.")
        return
    if new_admin_id == ADMIN_ID:
        bot.send_message(message.chat.id, "Главный админ уже обладает всеми правами.")
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO admins (user_id, added_by) VALUES (?, ?)", (new_admin_id, message.from_user.id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Пользователь {new_admin_id} теперь администратор.")
    bot.send_message(new_admin_id, "🔐 Вам выданы права администратора в боте Frime Skin.")
    log_action(message.from_user.id, 'add_admin', f'Added {new_admin_id}')

@bot.message_handler(commands=['remove_admin'])
def remove_admin_cmd(message):
    if not is_main_admin(message.from_user.id):
        bot.send_message(message.chat.id, "🚫 Только главный администратор может удалять админов.")
        return
    args = message.text.split()
    if len(args) != 2:
        bot.send_message(message.chat.id, "Использование: /remove_admin <user_id>")
        return
    try: admin_id = int(args[1])
    except ValueError:
        bot.send_message(message.chat.id, "ID должен быть числом.")
        return
    if admin_id == ADMIN_ID:
        bot.send_message(message.chat.id, "Нельзя удалить главного администратора.")
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE user_id=?", (admin_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Пользователь {admin_id} лишён прав администратора.")
    bot.send_message(admin_id, "⚠️ Ваши права администратора в боте Frime Skin были отозваны.")
    log_action(message.from_user.id, 'remove_admin', f'Removed {admin_id}')

@bot.message_handler(commands=['list_admins'])
def list_admins_cmd(message):
    if not is_admin(message.from_user.id): return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins")
    admins = [row[0] for row in c.fetchall()]
    conn.close()
    text = "👑 Главный администратор: " + str(ADMIN_ID) + "\n"
    text += "👥 Дополнительные администраторы:\n" + ("\n".join(map(str, admins)) if admins else "нет")
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "👑 Админы" and is_admin(m.from_user.id))
def admin_admins_menu(message):
    list_admins_cmd(message)

@bot.message_handler(commands=['admin_add_maker'])
def admin_add_maker_cmd(message):
    if not is_admin(message.from_user.id): return
    msg = bot.send_message(message.chat.id, "Введите @username или ID скинмейкера:")
    bot.register_next_step_handler(msg, process_new_maker_username)

def process_new_maker_username(message):
    user_id, username = parse_username_or_id(message.text)
    if user_id is None and username is None:
        bot.send_message(message.chat.id, "Неверный формат. Введите @username или ID.")
        return
    if username:
        try:
            user = bot.get_chat(f"@{username}")
            user_id = user.id
            username = user.username
        except:
            bot.send_message(message.chat.id, "Не удалось найти пользователя.")
            return
    if user_id is None:
        bot.send_message(message.chat.id, "Неверный ID.")
        return
    user_states[message.from_user.id] = {'new_maker_user_id': user_id, 'new_maker_username': username or ""}
    msg = bot.send_message(message.chat.id, "Введите имя скинмейкера:")
    bot.register_next_step_handler(msg, process_new_maker_name)

def process_new_maker_name(message):
    user_states[message.from_user.id]['name'] = message.text
    msg = bot.send_message(message.chat.id, "Введите описание:")
    bot.register_next_step_handler(msg, process_new_maker_desc)

def process_new_maker_desc(message):
    user_states[message.from_user.id]['desc'] = message.text
    msg = bot.send_message(message.chat.id, "Введите минимальную цену:")
    bot.register_next_step_handler(msg, process_new_maker_price_min)

def process_new_maker_price_min(message):
    try:
        pmin = int(message.text)
        user_states[message.from_user.id]['price_min'] = pmin
        msg = bot.send_message(message.chat.id, "Введите максимальную цену:")
        bot.register_next_step_handler(msg, process_new_maker_price_max)
    except:
        msg = bot.send_message(message.chat.id, "❌ Введите число. Минимальная цена:")
        bot.register_next_step_handler(msg, process_new_maker_price_min)

def process_new_maker_price_max(message):
    try:
        pmax = int(message.text)
        data = user_states[message.from_user.id]
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute('''INSERT INTO skin_makers (user_id, username, name, description, price, price_min, price_max, services, style, contact_link)
                     VALUES (?,?,?,?,?,?,?,?,?,?)''',
                  (data['new_maker_user_id'], data['new_maker_username'], data['name'], data['desc'],
                   pmax, data['price_min'], pmax, '', 'modern', ''))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Скинмейкер добавлен.")
        log_action(message.from_user.id, 'add_maker', f'User {data["new_maker_user_id"]}')
    except:
        msg = bot.send_message(message.chat.id, "❌ Введите число. Максимальная цена:")
        bot.register_next_step_handler(msg, process_new_maker_price_max)

@bot.message_handler(func=lambda m: m.text == "➕ Добавить скинмейкера" and is_admin(m.from_user.id))
def admin_add_maker_button(message):
    admin_add_maker_cmd(message)

@bot.message_handler(func=lambda m: m.text == "🔧 Ред. скинмейкера" and is_admin(m.from_user.id))
def admin_edit_maker_button(message):
    msg = bot.send_message(message.chat.id, "Введите ID скинмейкера для редактирования:")
    bot.register_next_step_handler(msg, process_admin_edit_maker)

def process_admin_edit_maker(message):
    try: maker_id = int(message.text)
    except:
        bot.send_message(message.chat.id, "ID должен быть числом.")
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM skin_makers WHERE id=?", (maker_id,))
    maker = c.fetchone()
    conn.close()
    if not maker:
        bot.send_message(message.chat.id, "Скинмейкер не найден.")
        return
    text = f"🔧 Редактирование скинмейкера ID{maker_id}\n\n"
    text += f"Имя: {maker[3]}\nОписание: {maker[4]}\n"
    price_text = f"от {maker[5]} ₽" if maker[5] else "не указана"
    if maker[6] and maker[7]: price_text = f"от {maker[6]} до {maker[7]} ₽"
    text += f"Ценник: {price_text}\n"
    text += f"Стиль: {maker[17]}\nУслуги: {maker[8]}\nСтрана: {maker[28]}\n"
    text += f"Эмодзи: {maker[27] or 'нет'}\nСсылка для заказа: {maker[31] or 'нет'}\n"
    text += f"Сроки: {maker[19]}–{maker[20]} дн.\n"
    order_text = maker[39] if len(maker) > 39 and maker[39] else f"{maker[24]} {'✅' if maker[25] else '~'}"
    text += f"Заказы: {order_text}\nСтаж: {maker[29] or 'авто'}\n"
    text += f"Рейтинг: {(maker[9] or 5.0):.1f}\nАктивен: {'✅' if maker[12] else '❌'}\nТеневой бан: {'⚠️' if maker[21] else '✅'}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("✏️ Имя", callback_data=f'adm_edit_name_{maker_id}'),
        types.InlineKeyboardButton("✏️ Описание", callback_data=f'adm_edit_desc_{maker_id}'),
        types.InlineKeyboardButton("✏️ Цена", callback_data=f'adm_edit_price_{maker_id}'),
        types.InlineKeyboardButton("✏️ Стиль", callback_data=f'adm_edit_style_{maker_id}'),
        types.InlineKeyboardButton("✏️ Услуги", callback_data=f'adm_edit_services_{maker_id}'),
        types.InlineKeyboardButton("✏️ Страна", callback_data=f'adm_edit_country_{maker_id}'),
        types.InlineKeyboardButton("✏️ Эмодзи", callback_data=f'adm_edit_emoji_{maker_id}'),
        types.InlineKeyboardButton("✏️ Ссылка для заказа", callback_data=f'adm_edit_contact_{maker_id}'),
        types.InlineKeyboardButton("✏️ Сроки", callback_data=f'adm_edit_delivery_{maker_id}'),
        types.InlineKeyboardButton("✏️ Заказы", callback_data=f'adm_edit_orders_{maker_id}'),
        types.InlineKeyboardButton("✏️ Стаж", callback_data=f'adm_edit_exp_{maker_id}'),
        types.InlineKeyboardButton("🔄 Активность", callback_data=f'adm_toggle_active_{maker_id}'),
        types.InlineKeyboardButton("🗑️ Удалить", callback_data=f'adm_delete_maker_{maker_id}')
    )
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_name_'))
def adm_edit_name_cb(call):
    maker_id = int(call.data.split('_')[3])
    msg = bot.send_message(call.message.chat.id, "Введите новое имя:")
    bot.register_next_step_handler(msg, process_adm_edit_name, maker_id)

def process_adm_edit_name(message, maker_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET name=? WHERE id=?", (message.text, maker_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Имя обновлено.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_desc_'))
def adm_edit_desc_cb(call):
    maker_id = int(call.data.split('_')[3])
    msg = bot.send_message(call.message.chat.id, "Введите новое описание:")
    bot.register_next_step_handler(msg, process_adm_edit_desc, maker_id)

def process_adm_edit_desc(message, maker_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET description=? WHERE id=?", (message.text, maker_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Описание обновлено.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_price_'))
def adm_edit_price_cb(call):
    maker_id = int(call.data.split('_')[3])
    msg = bot.send_message(call.message.chat.id, "Введите новую цену:")
    bot.register_next_step_handler(msg, process_adm_edit_price, maker_id)

def process_adm_edit_price(message, maker_id):
    try:
        price = int(message.text)
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("UPDATE skin_makers SET price=? WHERE id=?", (price, maker_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Цена обновлена.")
    except:
        bot.send_message(message.chat.id, "❌ Введите число.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_style_'))
def adm_edit_style_cb(call):
    maker_id = int(call.data.split('_')[3])
    markup = types.InlineKeyboardMarkup(row_width=2)
    styles = ['modern', 'colorful', 'realism', 'namemc', 'special']
    for s in styles:
        markup.add(types.InlineKeyboardButton(s, callback_data=f'adm_set_style_{maker_id}_{s}'))
    bot.send_message(call.message.chat.id, "Выберите стиль:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_set_style_'))
def adm_set_style(call):
    _, _, maker_id, style = call.data.split('_')
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET style=? WHERE id=?", (style, int(maker_id)))
    conn.commit()
    conn.close()
    bot.edit_message_text("✅ Стиль обновлён.", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_services_'))
def adm_edit_services_cb(call):
    maker_id = int(call.data.split('_')[3])
    msg = bot.send_message(call.message.chat.id, "Введите услуги через запятую:")
    bot.register_next_step_handler(msg, process_adm_edit_services, maker_id)

def process_adm_edit_services(message, maker_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET services=? WHERE id=?", (message.text, maker_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Услуги обновлены.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_country_'))
def adm_edit_country_cb(call):
    maker_id = int(call.data.split('_')[3])
    markup = types.InlineKeyboardMarkup(row_width=2)
    for code, name in countries.items():
        markup.add(types.InlineKeyboardButton(f"{flags[code]} {name}", callback_data=f'adm_set_country_{maker_id}_{code}'))
    bot.send_message(call.message.chat.id, "Выберите страну:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_set_country_'))
def adm_set_country(call):
    _, _, maker_id, code = call.data.split('_')
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET country_code=? WHERE id=?", (code, int(maker_id)))
    conn.commit()
    conn.close()
    bot.edit_message_text(f"✅ Страна изменена на {flags[code]} {countries[code]}", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_emoji_'))
def adm_edit_emoji_cb(call):
    maker_id = int(call.data.split('_')[3])
    msg = bot.send_message(call.message.chat.id, "Отправьте один эмодзи (или '-' чтобы убрать):")
    bot.register_next_step_handler(msg, process_adm_edit_emoji, maker_id)

def process_adm_edit_emoji(message, maker_id):
    text = message.text.strip()
    emoji = None if text == '-' else text[0]
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET custom_emoji=? WHERE id=?", (emoji, maker_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Эмодзи обновлён.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_contact_'))
def adm_edit_contact_cb(call):
    maker_id = int(call.data.split('_')[3])
    msg = bot.send_message(call.message.chat.id, "Введите новую ссылку для заказа:")
    bot.register_next_step_handler(msg, process_adm_edit_contact, maker_id)

def process_adm_edit_contact(message, maker_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET contact_link=? WHERE id=?", (message.text.strip(), maker_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Ссылка обновлена.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_delivery_'))
def adm_edit_delivery_cb(call):
    maker_id = int(call.data.split('_')[3])
    msg = bot.send_message(call.message.chat.id, "Введите минимальный срок (дней):")
    bot.register_next_step_handler(msg, process_adm_delivery_min, maker_id)

def process_adm_delivery_min(message, maker_id):
    try:
        dmin = int(message.text)
        if dmin < 1: raise ValueError
    except:
        msg = bot.send_message(message.chat.id, "❌ Введите целое число >0:")
        bot.register_next_step_handler(msg, process_adm_delivery_min, maker_id)
        return
    msg = bot.send_message(message.chat.id, "Введите максимальный срок (дней):")
    bot.register_next_step_handler(msg, process_adm_delivery_max, maker_id, dmin)

def process_adm_delivery_max(message, maker_id, dmin):
    try:
        dmax = int(message.text)
        if dmax < dmin: raise ValueError
    except:
        msg = bot.send_message(message.chat.id, f"❌ Введите число ≥ {dmin}:")
        bot.register_next_step_handler(msg, process_adm_delivery_max, maker_id, dmin)
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET delivery_min_days=?, delivery_max_days=? WHERE id=?", (dmin, dmax, maker_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Сроки обновлены: {dmin}–{dmax} дн.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_orders_'))
def adm_edit_orders_cb(call):
    maker_id = int(call.data.split('_')[3])
    msg = bot.send_message(call.message.chat.id, "Введите количество заказов (можно '500+'):")
    bot.register_next_step_handler(msg, process_adm_edit_orders, maker_id)

def process_adm_edit_orders(message, maker_id):
    val = message.text.strip()
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    if val.isdigit():
        c.execute("UPDATE skin_makers SET completed_orders=?, orders_confirmed=1, order_display=NULL WHERE id=?", (int(val), maker_id))
    else:
        c.execute("UPDATE skin_makers SET order_display=?, orders_confirmed=1 WHERE id=?", (val, maker_id))
        nums = re.findall(r'\d+', val)
        if nums: c.execute("UPDATE skin_makers SET completed_orders=? WHERE id=?", (int(nums[0]), maker_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Заказы обновлены: {val}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_exp_'))
def adm_edit_exp_cb(call):
    maker_id = int(call.data.split('_')[3])
    msg = bot.send_message(call.message.chat.id, "Введите новый стаж (например, '2 года'):")
    bot.register_next_step_handler(msg, process_adm_edit_exp, maker_id)

def process_adm_edit_exp(message, maker_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET display_experience=? WHERE id=?", (message.text.strip(), maker_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Стаж обновлён.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_toggle_active_'))
def adm_toggle_active_cb(call):
    maker_id = int(call.data.split('_')[3])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT is_active FROM skin_makers WHERE id=?", (maker_id,))
    state = c.fetchone()[0]
    new_state = 0 if state else 1
    c.execute("UPDATE skin_makers SET is_active=? WHERE id=?", (new_state, maker_id))
    conn.commit()
    conn.close()
    action = "активирован" if new_state else "деактивирован"
    bot.send_message(call.message.chat.id, f"✅ Скинмейкер {action}.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_delete_maker_'))
def adm_delete_maker_cb(call):
    maker_id = int(call.data.split('_')[3])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("DELETE FROM skin_makers WHERE id=?", (maker_id,))
    conn.commit()
    conn.close()
    bot.send_message(call.message.chat.id, f"✅ Скинмейкер ID{maker_id} удалён.")

@bot.message_handler(commands=['admin_log'])
def admin_log_cmd(message):
    if not is_admin(message.from_user.id): return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM action_log ORDER BY date DESC LIMIT 20")
    logs = c.fetchall()
    conn.close()
    if not logs:
        bot.send_message(message.chat.id, "Лог пуст.")
        return
    text = "📝 Последние действия:\n\n"
    for l in logs:
        text += f"🕐 {l[3][:19]}\n👤 Админ ID{l[1]}\n🔧 {l[2]}\n\n"
    if len(text) > 4000:
        for i in range(0, len(text), 4000): bot.send_message(message.chat.id, text[i:i+4000])
    else: bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "📝 Лог" and is_admin(m.from_user.id))
def admin_log_button(message):
    admin_log_cmd(message)

@bot.message_handler(func=lambda m: m.text == "🔄 Пересчитать рейтинг" and is_admin(m.from_user.id))
def admin_recalc_all_ratings(message):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT id FROM skin_makers")
    makers = [row[0] for row in c.fetchall()]
    for mid in makers:
        c.execute("UPDATE skin_makers SET total_ratings=(SELECT COUNT(*) FROM ratings WHERE skin_maker_id=? AND is_removed=0), rating=COALESCE((SELECT AVG(rating) FROM ratings WHERE skin_maker_id=? AND is_removed=0), 5.0) WHERE id=?", (mid, mid, mid))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Рейтинг пересчитан для всех ({len(makers)}) скинмейкеров.")

@bot.message_handler(func=lambda m: m.text == "🗂️ Очистить старые заявки" and is_admin(m.from_user.id))
def admin_clean_applications(message):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("DELETE FROM applications WHERE status != 'pending'")
    deleted = c.rowcount
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Удалено {deleted} обработанных заявок.")

@bot.message_handler(func=lambda m: m.text == "🔙 Выйти" and is_admin(m.from_user.id))
def exit_admin(message):
    bot.send_message(message.chat.id, "Вы вышли из админ-панели.", reply_markup=main_menu_markup())

@bot.callback_query_handler(func=lambda call: call.data.startswith('rate_'))
def rate_start(call):
    maker_id = int(call.data.split('_')[1])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM skin_makers WHERE id=?", (maker_id,))
    owner = c.fetchone()[0]
    conn.close()
    if owner == call.from_user.id:
        bot.answer_callback_query(call.id, "Нельзя оценивать себя!")
        return
    if is_blacklisted(call.from_user.id):
        bot.answer_callback_query(call.id, "Вы заблокированы.")
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT id FROM ratings WHERE skin_maker_id=? AND user_id=?", (maker_id, call.from_user.id))
    existing = c.fetchone()
    conn.close()
    if existing:
        bot.answer_callback_query(call.id, "Вы уже оценивали этого мастера.")
        return
    bot.current_rate_maker = maker_id
    msg = bot.send_message(call.message.chat.id, "Оцените качество работы (1-5):")
    bot.register_next_step_handler(msg, process_quality)

def process_quality(message):
    try:
        q = int(message.text)
        if q < 1 or q > 5: raise ValueError
    except:
        msg = bot.send_message(message.chat.id, "Введите число от 1 до 5:")
        bot.register_next_step_handler(msg, process_quality)
        return
    bot.current_rate_quality = q
    msg = bot.send_message(message.chat.id, "Оцените скорость выполнения (1-5):")
    bot.register_next_step_handler(msg, process_speed)

def process_speed(message):
    try:
        s = int(message.text)
        if s < 1 or s > 5: raise ValueError
    except:
        msg = bot.send_message(message.chat.id, "Введите число от 1 до 5:")
        bot.register_next_step_handler(msg, process_speed)
        return
    bot.current_rate_speed = s
    msg = bot.send_message(message.chat.id, "Оцените общение (1-5):")
    bot.register_next_step_handler(msg, process_communication)

def process_communication(message):
    try:
        c_val = int(message.text)
        if c_val < 1 or c_val > 5: raise ValueError
    except:
        msg = bot.send_message(message.chat.id, "Введите число от 1 до 5:")
        bot.register_next_step_handler(msg, process_communication)
        return
    q = bot.current_rate_quality
    s = bot.current_rate_speed
    avg = round((q + s + c_val) / 3, 1)
    maker_id = bot.current_rate_maker
    user_id = message.from_user.id
    if avg <= 2.5:
        msg = bot.send_message(message.chat.id, "Почему вы поставили такую оценку? Напишите причину:")
        bot.register_next_step_handler(msg, lambda m: save_rating(m, maker_id, user_id, avg, q, s, c_val))
    else:
        save_rating(message, maker_id, user_id, avg, q, s, c_val, reason="")

def save_rating(message, maker_id, user_id, avg, q, s, c_val, reason=None):
    if reason is None: reason = message.text
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("DELETE FROM ratings WHERE skin_maker_id=? AND user_id=?", (maker_id, user_id))
    c.execute("INSERT INTO ratings (skin_maker_id, user_id, rating, quality, speed, communication, reason) VALUES (?,?,?,?,?,?,?)",
              (maker_id, user_id, avg, q, s, c_val, reason))
    c.execute("UPDATE skin_makers SET total_ratings=(SELECT COUNT(*) FROM ratings WHERE skin_maker_id=? AND is_removed=0), rating=COALESCE((SELECT AVG(rating) FROM ratings WHERE skin_maker_id=? AND is_removed=0), 5.0) WHERE id=?", (maker_id, maker_id, maker_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Спасибо за оценку!")
    if avg <= 2.5:
        who = username_by_id(user_id)
        notify_admins(f"⚠️ Низкая оценка ({avg}) мастеру ID{maker_id} от {who}\nПричина: {reason}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('reviews_'))
def show_reviews(call):
    maker_id = int(call.data.split('_')[1])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reviews WHERE skin_maker_id=? ORDER BY date DESC LIMIT 5", (maker_id,))
    reviews = c.fetchall()
    conn.close()
    if not reviews:
        bot.send_message(call.message.chat.id, "Отзывов пока нет.")
        return
    text = "📝 Последние отзывы:\n\n"
    for rev in reviews:
        text += f"👤 {rev[3]}\n⭐ Оценка: {rev[5]}/5\n💬 {rev[4]}\n"
        if rev[6] or rev[7]: text += "📸 (фото до/после)\n"
        text += f"📅 {rev[8][:10]}\n\n"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✍️ Оставить отзыв", callback_data=f'addreview_{maker_id}'))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('addreview_'))
def add_review_start(call):
    maker_id = int(call.data.split('_')[1])
    bot.current_review_maker = maker_id
    msg = bot.send_message(call.message.chat.id, "✍️ Напишите ваш отзыв:")
    bot.register_next_step_handler(msg, process_review_text)

def process_review_text(message):
    review_text = message.text
    bot.current_review_text = review_text
    msg = bot.send_message(message.chat.id, "📸 Прикрепите фото ДО (или отправьте '-' если нет):")
    bot.register_next_step_handler(msg, process_review_before)

def process_review_before(message):
    if message.content_type == 'photo': bot.current_review_before = message.photo[-1].file_id
    else: bot.current_review_before = None
    msg = bot.send_message(message.chat.id, "📸 Прикрепите фото ПОСЛЕ (или '-'):")
    bot.register_next_step_handler(msg, process_review_after)

def process_review_after(message):
    if message.content_type == 'photo': after_id = message.photo[-1].file_id
    else: after_id = None
    maker_id = bot.current_review_maker
    user_id = message.from_user.id
    username = message.from_user.first_name
    text = bot.current_review_text
    before = bot.current_review_before
    rating = 5
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("INSERT INTO reviews (skin_maker_id, user_id, username, review_text, rating, photo_before_id, photo_after_id) VALUES (?,?,?,?,?,?,?)",
              (maker_id, user_id, username, text, rating, before, after_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Отзыв добавлен!")

@bot.message_handler(func=lambda m: m.text == "📢 Новости")
def show_news(message):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT text, photo_id, date FROM announcements ORDER BY date DESC LIMIT 3")
    news = c.fetchall()
    conn.close()
    if not news:
        bot.send_message(message.chat.id, "Новостей пока нет.")
        return
    for n in news:
        text = f"{n[0]}\n📅 {n[2][:10]}"
        if n[1]: bot.send_photo(message.chat.id, n[1], caption=text)
        else: bot.send_message(message.chat.id, text)

def check_achievements():
    while True:
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("SELECT id, completed_orders, rating, registration_date FROM skin_makers")
        makers = c.fetchall()
        for m in makers:
            mid, orders, rating, reg = m
            if orders >= 100:
                c.execute("INSERT OR IGNORE INTO achievements (skin_maker_id, type) VALUES (?, 'orders_100')", (mid,))
            if rating is not None and rating >= 4.9:
                c.execute("INSERT OR IGNORE INTO achievements (skin_maker_id, type) VALUES (?, 'rating_4.9')", (mid,))
            reg_date = datetime.strptime(reg, '%Y-%m-%d %H:%M:%S')
            days = (datetime.now() - reg_date).days
            if days >= 365:
                c.execute("INSERT OR IGNORE INTO achievements (skin_maker_id, type) VALUES (?, 'year_1')", (mid,))
            if days >= 730:
                c.execute("INSERT OR IGNORE INTO achievements (skin_maker_id, type) VALUES (?, 'year_2')", (mid,))
        conn.commit()
        conn.close()
        time.sleep(3600)

if __name__ == '__main__':
    init_db()
    t = threading.Thread(target=check_achievements, daemon=True)
    t.start()
    print("Бот Frime Skin запущен...")
    bot.polling(none_stop=True)
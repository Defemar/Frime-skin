# Frime Skin Bot — Полная финальная версия (все функции, все исправления)
# Для запуска: pip install pyTelegramBotAPI
import telebot
from telebot import types
import sqlite3
import json
from datetime import datetime, timedelta
import random
import threading
import time
import re

# ---------- ТОКЕН И ГЛАВНЫЙ АДМИН ----------
TOKEN = "8623923833:AAHv6xe6u9xtncfp_7xRvjJzOKorOiLcPwY"
ADMIN_ID = 5268276353

PROXY = None
if PROXY:
    from telebot import apihelper
    apihelper.proxy = {'https': PROXY}

bot = telebot.TeleBot(TOKEN)
bot.current_makers = []

# ---------- БАЗА ДАННЫХ ----------
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
        social_max TEXT
    )''')

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
        social_max TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skin_maker_id INTEGER,
        type TEXT,
        date_awarded TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

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

# ---------- ДАННЫЕ СТРАН (СНГ и мир) ----------
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

# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
def main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        "🔍 Поиск скинмейкеров",
        "📝 Подать заявку",
        "📌 Мои закладки",
        "👤 Мой профиль",
        "📢 Новости",
        "💸 Донат на сервера",
        "ℹ️ О боте"
    )
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
        try:
            bot.send_message(admin, text)
        except:
            pass

# ---------- КАРТОЧКА СКИНМЕЙКЕРА ----------
def format_maker_card(maker):
    (id, uid, uname, name, desc, price, services, photo_ids, rating, total,
     complaints, active, vacation, vac_text, reg_date, style, custom_style,
     dmin, dmax, shadow, shadow_reason, verdict, views, orders, orders_conf,
     busy_until, emoji, country, disp_exp,
     contact_link,
     social_tg, social_tw, social_pin, social_tiktok, social_yt, social_inst, social_vk, social_max) = maker

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

    orders_display = f"{orders} ✅" if orders_conf else f"~{orders}"

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
    text += f"📊 Заказов: {orders_display}\n"
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

# ---------- ПОИСК С ФИЛЬТРАМИ ----------
def get_makers_by_filter(filter_type, limit=30):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    query = "SELECT * FROM skin_makers WHERE is_active=1 AND complaints < 4"
    if filter_type == 'standard':
        query += " ORDER BY rating DESC"
    elif filter_type == 'newbies':
        query += " ORDER BY registration_date DESC"
    elif filter_type == 'popular':
        query += " ORDER BY total_ratings DESC"
    elif filter_type == 'price_asc':
        query += " ORDER BY price ASC"
    elif filter_type == 'price_desc':
        query += " ORDER BY price DESC"
    c.execute(query)
    makers = c.fetchall()
    conn.close()

    filtered = []
    for m in makers:
        style = m[15] if m[15] else ''
        if style.strip() == 'namemc':
            if random.random() > 0.1:
                continue
        if m[19]:
            if random.random() > 0.1:
                continue
        filtered.append(m)
        if len(filtered) >= limit:
            break
    return filtered

def show_card(chat_id, index):
    if not hasattr(bot, 'current_makers') or not bot.current_makers:
        bot.send_message(chat_id, "😔 Скинмейкеры не найдены.")
        return
    makers = bot.current_makers
    if index < 0 or index >= len(makers):
        return
    maker = makers[index]
    text = format_maker_card(maker)
    photo_ids = json.loads(maker[7])
    markup = types.InlineKeyboardMarkup(row_width=3)
    nav_buttons = []
    if index > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f'nav_{index-1}'))
    nav_buttons.append(types.InlineKeyboardButton(f"{index+1}/{len(makers)}", callback_data='none'))
    if index < len(makers)-1:
        nav_buttons.append(types.InlineKeyboardButton("➡️ Вперед", callback_data=f'nav_{index+1}'))
    markup.row(*nav_buttons)
    if maker[29]:
        url = maker[29].strip()
        if not url.startswith('http'):
            if url.startswith('@'):
                url = f"https://t.me/{url[1:]}"
            elif url.startswith('t.me/'):
                url = f"https://{url}"
            else:
                url = f"https://t.me/{url}"
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
    if photo_ids:
        bot.send_photo(chat_id, photo_ids[0], caption=text, reply_markup=markup)
    else:
        bot.send_message(chat_id, text, reply_markup=markup)

# ---------- НАВИГАЦИЯ ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith('nav_'))
def nav_cards(call):
    try:
        index = int(call.data.split('_')[1])
        if not hasattr(bot, 'current_makers') or not bot.current_makers:
            bot.answer_callback_query(call.id, "Список пуст.")
            return
        if index < 0 or index >= len(bot.current_makers):
            bot.answer_callback_query(call.id, "Некорректный индекс.")
            return
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        show_card(call.message.chat.id, index)
    except Exception as e:
        bot.answer_callback_query(call.id, f"Ошибка: {e}")

# ---------- ОСНОВНЫЕ КОМАНДЫ ----------
@bot.message_handler(commands=['start'])
def start(message):
    if is_blacklisted(message.from_user.id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы.")
        return
    bot.send_message(message.chat.id, "🎨 Добро пожаловать в Frime Skin!", reply_markup=main_menu_markup())

@bot.message_handler(commands=['help'])
def help_command(message):
    text = (
        "📋 Доступные команды:\n"
        "/start — главное меню\n"
        "/help — это сообщение\n"
        "/admin — админ-панель\n"
        "/admin secret command block — секретный список команд"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) > 1 and args[1] == 'secret' and len(args) > 2 and args[2] == 'command' and len(args) > 3 and args[3] == 'block':
        secret_text = (
            "🔐 Секретный блок команд:\n"
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
            "/list_admins — список админов"
        )
        bot.send_message(message.chat.id, secret_text)
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        "📋 Заявки",
        "👥 Скинмейкеры",
        "✏️ Запросы правок",
        "⭐ Управление оценками",
        "📊 Статистика",
        "📢 Объявления",
        "📤 Экспорт БД",
        "⛔ Теневой бан",
        "🚫 Чёрный список",
        "👑 Админы",
        "🔧 Ред. скинмейкера",
        "📝 Лог",
        "🔄 Пересчитать рейтинг",
        "🗂️ Очистить старые заявки",
        "🔙 Выйти"
    )
    bot.send_message(message.chat.id, "🔐 Админ-панель", reply_markup=markup)

# ---------- ПОИСК ----------
@bot.message_handler(func=lambda m: m.text == "🔍 Поиск скинмейкеров")
def search_cmd(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔄 Стандартные", callback_data='filter_standard'),
        types.InlineKeyboardButton("🆕 Новички", callback_data='filter_newbies'),
        types.InlineKeyboardButton("⭐ Популярные", callback_data='filter_popular'),
        types.InlineKeyboardButton("💲 По цене (возр.)", callback_data='filter_price_asc'),
        types.InlineKeyboardButton("💲 По цене (убыв.)", callback_data='filter_price_desc'),
        types.InlineKeyboardButton("🔙 Назад", callback_data='back_main')
    )
    bot.send_message(message.chat.id, "🔍 Выберите фильтр:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('filter_'))
def filter_handler(call):
    filter_type = call.data.split('_')[1]
    makers = get_makers_by_filter(filter_type)
    if not makers:
        bot.edit_message_text("😔 Скинмейкеры не найдены", call.message.chat.id, call.message.message_id)
        return
    bot.current_makers = makers
    bot.current_index = 0
    bot.current_filter = filter_type
    bot.delete_message(call.message.chat.id, call.message.message_id)
    show_card(call.message.chat.id, 0)

@bot.callback_query_handler(func=lambda call: call.data == 'back_main')
def back_main(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "🎨 Главное меню", reply_markup=main_menu_markup())

# ---------- ГАЛЕРЕЯ И СОЦСЕТИ ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith('gallery_'))
def gallery(call):
    maker_id = int(call.data.split('_')[1])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT photo_ids FROM skin_makers WHERE id=?", (maker_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return
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

# ---------- ЗАКЛАДКИ ----------
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

# ---------- ДОНАТ ----------
@bot.message_handler(func=lambda m: m.text == "💸 Донат на сервера")
def donate(message):
    text = (
        "💸 Донат на сервера\n"
        "По желанию\n\n"
        "❤️ Поддержать бота:\n\n"
        "Т-Банк: 2200702103771312\n"
        "СБП: +79033799210\n"
        "Boosty: https://boosty.to/dfmskimake/about"
    )
    bot.send_message(message.chat.id, text)

# ---------- О БОТЕ ----------
@bot.message_handler(func=lambda m: m.text == "ℹ️ О боте")
def about(message):
    bot.send_message(message.chat.id, "Frime Skin — платформа для поиска скинмейкеров Minecraft. Версия 2.0\n\nСвязь: @Defemar")

# ---------- ПРОФИЛЬ СКИНМЕЙКЕРА ----------
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
    bot.current_profile_maker_id = maker[0]
    text = "👤 Ваш профиль:\n\n"
    text += f"Имя: {maker[3]}\n"
    text += f"Ценник: {maker[5]} ₽\n"
    text += f"Стиль: {maker[15]}"
    if maker[16]:
        text += f"\n✨ {maker[16]}"
    text += f"\nСтрана: {countries.get(maker[27], maker[27])}\n"
    text += f"Эмодзи: {maker[26] or 'не задано'}\n"
    status_text = "🏖️ Отпуск" if maker[12] else ("⚠️ Перегружен до " + maker[25] if maker[25] else "Активен")
    text += f"Статус: {status_text}\n"
    text += f"Заказы: {maker[23]} {'✅' if maker[24] else '~'}\n"
    text += f"Просмотры: {maker[22]}\n"
    text += f"Рейтинг: {maker[8]:.1f}/5"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("✏️ Редактировать профиль", callback_data='edit_profile'),
        types.InlineKeyboardButton("🎨 Изменить эмодзи", callback_data='edit_emoji'),
        types.InlineKeyboardButton("🌍 Изменить страну", callback_data='edit_country'),
        types.InlineKeyboardButton("🏖️ Режим отпуска", callback_data='toggle_vacation'),
        types.InlineKeyboardButton("⚠️ Указать занятость", callback_data='set_busy'),
        types.InlineKeyboardButton("📊 Статистика", callback_data='profile_stats'),
        types.InlineKeyboardButton("✉️ Запросить правку", callback_data='request_edit'),
        types.InlineKeyboardButton("🔙 В меню", callback_data='back_main')
    )
    bot.send_message(message.chat.id, text, reply_markup=markup)

# ---------- РЕДАКТИРОВАНИЕ ПРОФИЛЯ ----------
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
        types.InlineKeyboardButton("Изменить цену", callback_data='edit_price'),
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

@bot.callback_query_handler(func=lambda call: call.data == 'edit_price')
def edit_price_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите новый ценник (число >100):")
    bot.register_next_step_handler(msg, process_edit_price)

def process_edit_price(message):
    try:
        price = int(message.text)
        if price <= 100:
            raise ValueError
        user_id = message.from_user.id
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("UPDATE skin_makers SET price=? WHERE user_id=?", (price, user_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Ценник обновлён.")
    except:
        bot.send_message(message.chat.id, "❌ Введите число >100.")

@bot.callback_query_handler(func=lambda call: call.data == 'edit_emoji')
def edit_emoji_cb(call):
    msg = bot.send_message(call.message.chat.id, "Отправьте один эмодзи для вашего профиля (или '-' чтобы убрать):")
    bot.register_next_step_handler(msg, process_edit_emoji)

def process_edit_emoji(message):
    user_id = message.from_user.id
    text = message.text.strip()
    if text == '-':
        emoji = None
    else:
        emoji = text[0] if text else None
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET custom_emoji=? WHERE user_id=?", (emoji, user_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Эмодзи обновлён.")

@bot.callback_query_handler(func=lambda call: call.data == 'edit_country')
def edit_country_cb(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    country_list = list(countries.items())
    buttons = []
    for code, name in country_list:
        buttons.append(types.InlineKeyboardButton(f"{flags[code]} {name}", callback_data=f'set_country_{code}'))
    markup.add(*buttons)
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
    if text == '-':
        date_str = None
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
    c.execute("SELECT views, completed_orders, orders_confirmed, rating, total_ratings FROM skin_makers WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        bot.answer_callback_query(call.id, "Ошибка")
        return
    text = f"📊 Статистика:\n👁 Просмотров: {row[0]}\n📦 Заказов: {row[1]} {'✅' if row[2] else '~'}\n⭐ Рейтинг: {row[3]:.1f} (оценок: {row[4]})"
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
    msg = bot.send_message(call.message.chat.id, "Опишите, что нужно изменить (например: стаж на 2 года, заказов 150):")
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

# ---------- ПОДАЧА ЗАЯВКИ ----------
user_states = {}

@bot.message_handler(func=lambda m: m.text == "📝 Подать заявку")
def apply_start(message):
    if is_blacklisted(message.from_user.id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы.")
        return
    user_id = message.from_user.id
    user_states[user_id] = {'photos': [], 'step': 'photo'}
    msg = bot.send_message(message.chat.id, "📸 Отправьте фото ваших работ (можно до 9, по одному, затем /done):")
    bot.register_next_step_handler(msg, process_apply_photo)

def process_apply_photo(message):
    user_id = message.from_user.id
    if message.content_type == 'photo':
        if len(user_states[user_id]['photos']) < 9:
            user_states[user_id]['photos'].append(message.photo[-1].file_id)
        else:
            bot.send_message(message.chat.id, "Максимум 9 фото.")
    elif message.text and message.text.startswith('/done'):
        if not user_states[user_id]['photos']:
            bot.send_message(message.chat.id, "Отправьте хотя бы одно фото!")
            bot.register_next_step_handler(message, process_apply_photo)
            return
        user_states[user_id]['step'] = 'name'
        msg = bot.send_message(message.chat.id, "✏️ Введите ваше имя (никнейм):")
        bot.register_next_step_handler(msg, process_apply_name)
        return
    else:
        bot.send_message(message.chat.id, "Отправьте фото или команду /done")
    msg = bot.send_message(message.chat.id, "Отправьте ещё фото или /done")
    bot.register_next_step_handler(msg, process_apply_photo)

def process_apply_name(message):
    user_id = message.from_user.id
    user_states[user_id]['name'] = message.text
    msg = bot.send_message(message.chat.id, "💬 Введите описание ваших услуг:")
    bot.register_next_step_handler(msg, process_apply_description)

def process_apply_description(message):
    user_id = message.from_user.id
    user_states[user_id]['description'] = message.text
    msg = bot.send_message(message.chat.id, "💲 Введите ценник (должен быть выше 100):")
    bot.register_next_step_handler(msg, process_apply_price)

def process_apply_price(message):
    user_id = message.from_user.id
    try:
        price = int(message.text)
        if price <= 100:
            raise ValueError
    except:
        msg = bot.send_message(message.chat.id, "Ценник должен быть числом >100. Повторите:")
        bot.register_next_step_handler(msg, process_apply_price)
        return
    user_states[user_id]['price'] = price
    markup = types.InlineKeyboardMarkup(row_width=2)
    styles = ['modern', 'colorful', 'realism', 'namemc', 'special']
    for s in styles:
        markup.add(types.InlineKeyboardButton(s, callback_data=f'applystyle_{s}'))
    markup.add(types.InlineKeyboardButton("✅ Готово", callback_data='applystyle_done'))
    user_states[user_id]['selected_styles'] = []
    bot.send_message(message.chat.id, "🎨 Выберите стиль (можно несколько):", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('applystyle_'))
def apply_style_select(call):
    user_id = call.from_user.id
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
        for s in services:
            markup.add(types.InlineKeyboardButton(s, callback_data=f'applyservice_{s}'))
        markup.add(types.InlineKeyboardButton("✅ Готово", callback_data='applyservice_done'))
        user_states[user_id]['selected_services'] = []
        bot.send_message(call.message.chat.id, "🛠️ Выберите услуги:", reply_markup=markup)
    else:
        sel = user_states[user_id]['selected_styles']
        if style in sel:
            sel.remove(style)
        else:
            sel.append(style)
        bot.answer_callback_query(call.id, f"Выбрано: {', '.join(sel)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('applyservice_'))
def apply_service_select(call):
    user_id = call.from_user.id
    serv = call.data.split('_')[1]
    if serv == 'done':
        if not user_states[user_id]['selected_services']:
            bot.answer_callback_query(call.id, "Выберите хотя бы одну услугу!")
            return
        bot.delete_message(call.message.chat.id, call.message.message_id)
        msg = bot.send_message(call.message.chat.id, "🔗 Введите ссылку для заказа (Telegram-аккаунт, бот или канал). Если нет, отправьте '-'")
        bot.register_next_step_handler(msg, process_apply_contact)
    else:
        sel = user_states[user_id]['selected_services']
        if serv in sel:
            sel.remove(serv)
        else:
            sel.append(serv)
        bot.answer_callback_query(call.id, f"Выбрано: {', '.join(sel)}")

def process_apply_contact(message):
    user_id = message.from_user.id
    if message.text == '-':
        user_states[user_id]['contact_link'] = None
    else:
        user_states[user_id]['contact_link'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Теперь укажите ссылки на соцсети (можно пропустить, отправив '-').\n"
                          "Вводите в формате:\n"
                          "Telegram: ссылка\n"
                          "Twitter: ссылка\n"
                          "Pinterest: ссылка\n"
                          "TikTok: ссылка\n"
                          "YouTube: ссылка\n"
                          "Instagram: ссылка\n"
                          "VK: ссылка\n"
                          "Max: ссылка\n\n"
                          "Или одной строкой через запятую в формате 'TG: ссылка, TW: ссылка'. Для пропуска отправьте '-'")
    bot.register_next_step_handler(msg, process_apply_social)

def process_apply_social(message):
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
                if 'tg' in key or 'telegram' in key:
                    socials['social_telegram'] = val
                elif 'tw' in key or 'twitter' in key or 'x' in key:
                    socials['social_twitter'] = val
                elif 'pin' in key or 'pinterest' in key:
                    socials['social_pinterest'] = val
                elif 'tik' in key or 'tiktok' in key:
                    socials['social_tiktok'] = val
                elif 'you' in key or 'youtube' in key:
                    socials['social_youtube'] = val
                elif 'insta' in key or 'instagram' in key:
                    socials['social_instagram'] = val
                elif 'vk' in key:
                    socials['social_vk'] = val
                elif 'max' in key:
                    socials['social_max'] = val
    user_states[user_id].update(socials)
    data = user_states.pop(user_id)
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute('''INSERT INTO applications
        (user_id, username, name, description, price, services, photo_ids, style, custom_style_name,
         contact_link, social_telegram, social_twitter, social_pinterest, social_tiktok,
         social_youtube, social_instagram, social_vk, social_max)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (user_id, message.from_user.username or "", data['name'], data['description'],
         data['price'], ', '.join(data['selected_services']),
         json.dumps(data['photos']), ', '.join(data['selected_styles']), '',
         data.get('contact_link'), data.get('social_telegram'), data.get('social_twitter'),
         data.get('social_pinterest'), data.get('social_tiktok'), data.get('social_youtube'),
         data.get('social_instagram'), data.get('social_vk'), data.get('social_max')))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Заявка отправлена! Ожидайте одобрения администратором.")
    notify_admins(f"📋 Новая заявка от @{message.from_user.username}")

# ---------- ЗАЯВКИ (АДМИНКА) ----------
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
        text += f"👤 Имя: {app[3]}\n"
        text += f"💬 Описание: {app[4]}\n"
        text += f"💲 Ценник: {app[5]} ₽\n"
        text += f"🎨 Стили: {app[8]}"
        if app[9]:
            text += f"\n✨ Особый подстиль: {app[9]}"
        text += f"\n🛠️ Услуги: {app[6]}\n"
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
        text += f"\nОтправитель: @{app[2]} (ID {app[1]})"

        photos = json.loads(app[7])
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Принять", callback_data=f'approve_{app[0]}'),
            types.InlineKeyboardButton("❌ Отклонить", callback_data=f'reject_{app[0]}')
        )
        if photos:
            bot.send_photo(chat_id, photos[0], caption=text, reply_markup=markup)
        else:
            bot.send_message(chat_id, text, reply_markup=markup)

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
         social_youtube, social_instagram, social_vk, social_max)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (app[1], app[2], app[3], app[4], app[5], app[6], app[7], app[8], app[9],
         app[13], app[14], app[15], app[16], app[17], app[18], app[19], app[20], app[21]))
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

# ---------- АДМИН-ПАНЕЛЬ ОБРАБОТЧИКИ ----------
@bot.message_handler(func=lambda m: m.text == "📋 Заявки" and is_admin(m.from_user.id))
def admin_applications_button(message):
    show_applications(message.chat.id)

@bot.message_handler(func=lambda m: m.text == "👥 Скинмейкеры" and is_admin(m.from_user.id))
def admin_makers_button(message):
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
        text += f"ID{m[0]} {m[1]} (tg:{m[2]})\n⭐{m[3]:.1f} | Активен:{'✅' if m[4] else '❌'} | Жалобы:{m[5]} | Теневой:{'⚠️' if m[6] else '✅'}\n\n"
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            bot.send_message(message.chat.id, text[i:i+4000])
    else:
        bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "✏️ Запросы правок" and is_admin(m.from_user.id))
def admin_edit_requests_button(message):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM edit_requests WHERE status='pending'")
    reqs = c.fetchall()
    conn.close()
    if not reqs:
        bot.send_message(message.chat.id, "Нет запросов.")
        return
    for r in reqs:
        text = f"📩 Запрос #{r[0]}\nОт скинмейкера ID{r[1]}\nСуть: {r[3]}"
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Подтвердить", callback_data=f'approve_edit_{r[0]}'),
            types.InlineKeyboardButton("❌ Отклонить", callback_data=f'reject_edit_{r[0]}')
        )
        bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_edit_'))
def approve_edit(call):
    req_id = int(call.data.split('_')[2])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM edit_requests WHERE id=?", (req_id,))
    req = c.fetchone()
    if not req:
        bot.answer_callback_query(call.id, "Запрос не найден.")
        return
    text = req[3].lower()
    maker_id = req[1]
    numbers = re.findall(r'\d+', text)
    if 'заказ' in text or 'order' in text:
        if numbers:
            new_orders = int(numbers[0])
            c.execute("UPDATE skin_makers SET completed_orders=?, orders_confirmed=1 WHERE id=?", (new_orders, maker_id))
            bot.send_message(maker_id, f"✅ Ваш запрос одобрен. Количество заказов обновлено до {new_orders}.")
    elif 'стаж' in text or 'опыт' in text:
        if 'год' in text or 'лет' in text:
            c.execute("UPDATE skin_makers SET display_experience=? WHERE id=?", (req[3], maker_id))
            bot.send_message(maker_id, f"✅ Ваш запрос одобрен. Стаж обновлён на «{req[3]}».")
    else:
        bot.send_message(maker_id, "✅ Ваш запрос правок был рассмотрен администратором.")
    c.execute("UPDATE edit_requests SET status='approved', admin_response='Подтверждено' WHERE id=?", (req_id,))
    conn.commit()
    conn.close()
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    bot.send_message(call.message.chat.id, f"✅ Запрос #{req_id} подтверждён.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_edit_'))
def reject_edit(call):
    req_id = int(call.data.split('_')[2])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT skin_maker_id FROM edit_requests WHERE id=?", (req_id,))
    maker = c.fetchone()
    c.execute("UPDATE edit_requests SET status='rejected', admin_response='Отклонено' WHERE id=?", (req_id,))
    conn.commit()
    conn.close()
    if maker:
        bot.send_message(maker[0], "❌ Ваш запрос правок был отклонён администратором.")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    bot.send_message(call.message.chat.id, f"❌ Запрос #{req_id} отклонён.")

# ---------- УПРАВЛЕНИЕ ОЦЕНКАМИ ----------
@bot.message_handler(func=lambda m: m.text == "⭐ Управление оценками" and is_admin(m.from_user.id))
def admin_ratings_menu_button(message):
    msg = bot.send_message(message.chat.id, "Введите ID скинмейкера для просмотра его оценок:")
    bot.register_next_step_handler(msg, process_admin_ratings)

def process_admin_ratings(message):
    try:
        maker_id = int(message.text)
    except:
        bot.send_message(message.chat.id, "ID должен быть числом.")
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute('''SELECT r.id, r.rating, r.quality, r.speed, r.communication, r.reason, r.user_id, r.date 
                 FROM ratings r WHERE r.skin_maker_id=? AND r.is_removed=0 
                 ORDER BY r.date DESC LIMIT 10''', (maker_id,))
    ratings = c.fetchall()
    conn.close()
    if not ratings:
        bot.send_message(message.chat.id, f"Нет оценок для скинмейкера ID{maker_id}.")
        return
    text = f"📊 Оценки скинмейкера ID{maker_id}:\n\n"
    for r in ratings:
        text += f"ID оценки: {r[0]}\n⭐ Общая: {r[1]:.1f} | К:{r[2]} С:{r[3]} О:{r[4]}\n"
        if r[5]:
            text += f"💬 {r[5]}\n"
        text += f"👤 ID{r[6]} | 📅 {r[7][:10]}\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🗑️ Удалить оценку по ID", callback_data=f'delete_rating_menu_{maker_id}'),
        types.InlineKeyboardButton("🔄 Пересчитать рейтинг", callback_data=f'recalc_rating_{maker_id}')
    )
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_rating_menu_'))
def delete_rating_menu(call):
    maker_id = call.data.split('_')[3]
    msg = bot.send_message(call.message.chat.id, "Введите ID оценки, которую нужно удалить:")
    bot.register_next_step_handler(msg, process_delete_rating, maker_id)

def process_delete_rating(message, maker_id):
    try:
        rating_id = int(message.text)
    except:
        bot.send_message(message.chat.id, "ID должен быть числом.")
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE ratings SET is_removed=1 WHERE id=? AND skin_maker_id=?", (rating_id, maker_id))
    c.execute("UPDATE skin_makers SET total_ratings=(SELECT COUNT(*) FROM ratings WHERE skin_maker_id=? AND is_removed=0), rating=(SELECT AVG(rating) FROM ratings WHERE skin_maker_id=? AND is_removed=0) WHERE id=?", (maker_id, maker_id, maker_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Оценка #{rating_id} удалена. Рейтинг пересчитан.")
    log_action(message.from_user.id, 'delete_rating', f'Rating {rating_id} of maker {maker_id}')

@bot.callback_query_handler(func=lambda call: call.data.startswith('recalc_rating_'))
def recalc_rating_cb(call):
    maker_id = int(call.data.split('_')[2])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET total_ratings=(SELECT COUNT(*) FROM ratings WHERE skin_maker_id=? AND is_removed=0), rating=(SELECT AVG(rating) FROM ratings WHERE skin_maker_id=? AND is_removed=0) WHERE id=?", (maker_id, maker_id, maker_id))
    c.execute("SELECT rating, total_ratings FROM skin_makers WHERE id=?", (maker_id,))
    new_data = c.fetchone()
    conn.commit()
    conn.close()
    bot.send_message(call.message.chat.id, f"✅ Рейтинг пересчитан. Новый: {new_data[0]:.1f} (оценок: {new_data[1]})")

# ---------- СТАТИСТИКА ----------
@bot.message_handler(func=lambda m: m.text == "📊 Статистика" and is_admin(m.from_user.id))
def admin_stats_button(message):
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
    text += f"• Заявок ожидает: {pending}\n"
    text += f"• Отзывов: {reviews_count}\n"
    text += f"• Оценок: {ratings_count}\n"
    text += f"• Средний рейтинг: {avg_rating:.1f}\n"
    text += f"• В чёрном списке: {blacklist_count}\n"
    text += f"• Администраторов: {admins_count}"
    bot.send_message(message.chat.id, text)

# ---------- ОБЪЯВЛЕНИЯ ----------
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
        if n[1]:
            bot.send_photo(call.message.chat.id, n[1], caption=text)
        else:
            bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data == 'delete_last_announce')
def delete_last_announce_cb(call):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("DELETE FROM announcements WHERE id = (SELECT MAX(id) FROM announcements)")
    conn.commit()
    conn.close()
    bot.send_message(call.message.chat.id, "✅ Последнее объявление удалено.")

def process_announce_text(message):
    text = message.text
    msg = bot.send_message(message.chat.id, "Прикрепите фото (или отправьте /stop чтобы завершить без фото):")
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
        return

# ---------- ТЕНЕВОЙ БАН ----------
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
    try:
        maker_id = int(message.text)
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
    try:
        maker_id = int(message.text)
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
    for m in makers:
        text += f"ID{m[0]} — {m[1]}\n"
    bot.send_message(call.message.chat.id, text)

# ---------- ЧЁРНЫЙ СПИСОК ----------
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
    try:
        user_id = int(message.text)
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
    try:
        user_id = int(message.text)
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

# ---------- АДМИНЫ ----------
@bot.message_handler(func=lambda m: m.text == "👑 Админы" and is_admin(m.from_user.id))
def admin_admins_menu(message):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins")
    admins = [row[0] for row in c.fetchall()]
    conn.close()
    text = "👑 Главный администратор: " + str(ADMIN_ID) + "\n"
    text += "👥 Дополнительные администраторы:\n" + ("\n".join(map(str, admins)) if admins else "нет")
    if is_main_admin(message.from_user.id):
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("➕ Добавить админа", callback_data='add_admin_menu'),
            types.InlineKeyboardButton("➖ Удалить админа", callback_data='remove_admin_menu')
        )
        bot.send_message(message.chat.id, text, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data == 'add_admin_menu')
def add_admin_menu_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите ID пользователя, которого нужно сделать админом:")
    bot.register_next_step_handler(msg, process_add_admin)

def process_add_admin(message):
    try:
        new_admin_id = int(message.text)
    except:
        bot.send_message(message.chat.id, "ID должен быть числом.")
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO admins (user_id, added_by) VALUES (?, ?)", (new_admin_id, message.from_user.id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Пользователь {new_admin_id} теперь администратор.")
    bot.send_message(new_admin_id, "🔐 Вам выданы права администратора в боте Frime Skin.")

@bot.callback_query_handler(func=lambda call: call.data == 'remove_admin_menu')
def remove_admin_menu_cb(call):
    msg = bot.send_message(call.message.chat.id, "Введите ID администратора, которого нужно удалить:")
    bot.register_next_step_handler(msg, process_remove_admin)

def process_remove_admin(message):
    try:
        admin_id = int(message.text)
    except:
        bot.send_message(message.chat.id, "ID должен быть числом.")
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE user_id=?", (admin_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Администратор {admin_id} удалён.")
    bot.send_message(admin_id, "⚠️ Ваши права администратора были отозваны.")

# ---------- РЕДАКТИРОВАНИЕ СКИНМЕЙКЕРА ----------
@bot.message_handler(func=lambda m: m.text == "🔧 Ред. скинмейкера" and is_admin(m.from_user.id))
def admin_edit_maker_button(message):
    msg = bot.send_message(message.chat.id, "Введите ID скинмейкера для редактирования:")
    bot.register_next_step_handler(msg, process_admin_edit_maker)

def process_admin_edit_maker(message):
    try:
        maker_id = int(message.text)
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
    text += f"Имя: {maker[3]}\n"
    text += f"Описание: {maker[4]}\n"
    text += f"Ценник: {maker[5]}\n"
    text += f"Стиль: {maker[15]}\n"
    text += f"Заказы: {maker[23]} (подтв: {'✅' if maker[24] else '❌'})\n"
    text += f"Стаж: {maker[28] or 'авто'}\n"
    text += f"Рейтинг: {maker[8]:.1f}\n"
    text += f"Активен: {'✅' if maker[11] else '❌'}\n"
    text += f"Теневой бан: {'⚠️' if maker[19] else '✅'}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("✏️ Изменить имя", callback_data=f'adm_edit_name_{maker_id}'),
        types.InlineKeyboardButton("✏️ Изменить описание", callback_data=f'adm_edit_desc_{maker_id}'),
        types.InlineKeyboardButton("✏️ Изменить ценник", callback_data=f'adm_edit_price_{maker_id}'),
        types.InlineKeyboardButton("✏️ Изменить заказы", callback_data=f'adm_edit_orders_{maker_id}'),
        types.InlineKeyboardButton("✏️ Изменить стаж", callback_data=f'adm_edit_exp_{maker_id}'),
        types.InlineKeyboardButton("🔄 Переключить активность", callback_data=f'adm_toggle_active_{maker_id}'),
        types.InlineKeyboardButton("🗑️ Удалить скинмейкера", callback_data=f'adm_delete_maker_{maker_id}')
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
    msg = bot.send_message(call.message.chat.id, "Введите новый ценник:")
    bot.register_next_step_handler(msg, process_adm_edit_price, maker_id)

def process_adm_edit_price(message, maker_id):
    try:
        price = int(message.text)
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("UPDATE skin_makers SET price=? WHERE id=?", (price, maker_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Ценник обновлён.")
    except:
        bot.send_message(message.chat.id, "❌ Введите число.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_orders_'))
def adm_edit_orders_cb(call):
    maker_id = int(call.data.split('_')[3])
    msg = bot.send_message(call.message.chat.id, "Введите новое количество заказов:")
    bot.register_next_step_handler(msg, process_adm_edit_orders, maker_id)

def process_adm_edit_orders(message, maker_id):
    try:
        orders = int(message.text)
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("UPDATE skin_makers SET completed_orders=?, orders_confirmed=1 WHERE id=?", (orders, maker_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Количество заказов обновлено до {orders}.")
    except:
        bot.send_message(message.chat.id, "❌ Введите число.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_exp_'))
def adm_edit_exp_cb(call):
    maker_id = int(call.data.split('_')[3])
    msg = bot.send_message(call.message.chat.id, "Введите новый стаж (например: '2 года' или '-' для авто):")
    bot.register_next_step_handler(msg, process_adm_edit_exp, maker_id)

def process_adm_edit_exp(message, maker_id):
    text = message.text.strip()
    if text == '-':
        text = None
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET display_experience=? WHERE id=?", (text, maker_id))
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

# ---------- ЛОГ ----------
@bot.message_handler(func=lambda m: m.text == "📝 Лог" and is_admin(m.from_user.id))
def admin_log_button(message):
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
        for i in range(0, len(text), 4000):
            bot.send_message(message.chat.id, text[i:i+4000])
    else:
        bot.send_message(message.chat.id, text)

# ---------- ПЕРЕСЧЁТ РЕЙТИНГА ----------
@bot.message_handler(func=lambda m: m.text == "🔄 Пересчитать рейтинг" and is_admin(m.from_user.id))
def admin_recalc_all_ratings(message):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT id FROM skin_makers")
    makers = [row[0] for row in c.fetchall()]
    for mid in makers:
        c.execute("UPDATE skin_makers SET total_ratings=(SELECT COUNT(*) FROM ratings WHERE skin_maker_id=? AND is_removed=0), rating=(SELECT AVG(rating) FROM ratings WHERE skin_maker_id=? AND is_removed=0) WHERE id=?", (mid, mid, mid))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Рейтинг пересчитан для всех ({len(makers)}) скинмейкеров.")

# ---------- ОЧИСТКА ЗАЯВОК ----------
@bot.message_handler(func=lambda m: m.text == "🗂️ Очистить старые заявки" and is_admin(m.from_user.id))
def admin_clean_applications(message):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("DELETE FROM applications WHERE status != 'pending'")
    deleted = c.rowcount
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ Удалено {deleted} обработанных заявок.")

# ---------- ВЫХОД ----------
@bot.message_handler(func=lambda m: m.text == "🔙 Выйти" and is_admin(m.from_user.id))
def exit_admin(message):
    bot.send_message(message.chat.id, "Вы вышли из админ-панели.", reply_markup=main_menu_markup())

# ---------- ОЦЕНКИ ----------
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
        if q < 1 or q > 5:
            raise ValueError
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
        if s < 1 or s > 5:
            raise ValueError
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
        if c_val < 1 or c_val > 5:
            raise ValueError
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
    if reason is None:
        reason = message.text
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("DELETE FROM ratings WHERE skin_maker_id=? AND user_id=?", (maker_id, user_id))
    c.execute("INSERT INTO ratings (skin_maker_id, user_id, rating, quality, speed, communication, reason) VALUES (?,?,?,?,?,?,?)",
              (maker_id, user_id, avg, q, s, c_val, reason))
    c.execute("UPDATE skin_makers SET total_ratings=(SELECT COUNT(*) FROM ratings WHERE skin_maker_id=? AND is_removed=0), rating=(SELECT AVG(rating) FROM ratings WHERE skin_maker_id=? AND is_removed=0) WHERE id=?", (maker_id, maker_id, maker_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Спасибо за оценку!")
    if avg <= 2.5:
        notify_admins(f"⚠️ Низкая оценка ({avg}) мастеру ID{maker_id} от @{message.from_user.username}\nПричина: {reason}")

# ---------- ОТЗЫВЫ ----------
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
        if rev[6] or rev[7]:
            text += "📸 (фото до/после)\n"
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
    if message.content_type == 'photo':
        bot.current_review_before = message.photo[-1].file_id
    else:
        bot.current_review_before = None
    msg = bot.send_message(message.chat.id, "📸 Прикрепите фото ПОСЛЕ (или '-'):")
    bot.register_next_step_handler(msg, process_review_after)

def process_review_after(message):
    if message.content_type == 'photo':
        after_id = message.photo[-1].file_id
    else:
        after_id = None
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

# ---------- НОВОСТИ ----------
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
        if n[1]:
            bot.send_photo(message.chat.id, n[1], caption=text)
        else:
            bot.send_message(message.chat.id, text)

# ---------- ФОНОВАЯ ПРОВЕРКА ДОСТИЖЕНИЙ ----------
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
        time.sleep(3600)

# ---------- ЗАПУСК ----------
if __name__ == '__main__':
    init_db()
    t = threading.Thread(target=check_achievements, daemon=True)
    t.start()
    print("Бот Frime Skin запущен...")
    bot.polling(none_stop=True)
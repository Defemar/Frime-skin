import telebot
from telebot import types
import sqlite3
import json
from datetime import datetime, timedelta
import random
import threading
import time
import os

TOKEN = "8623923833:AAHv6xe6u9xtncfp_7xRvjJzOKorOiLcPwY"
ADMIN_ID = 5268276353

PROXY = None
if PROXY:
    from telebot import apihelper
    apihelper.proxy = {'https': PROXY}

bot = telebot.TeleBot(TOKEN)

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
        custom_emoji TEXT DEFAULT '🎨',
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

    c.execute('''CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        language TEXT DEFAULT 'ru'
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

    conn.commit()
    conn.close()

countries = {
    'RU': 'Россия', 'US': 'США', 'DE': 'Германия', 'UA': 'Украина', 'BY': 'Беларусь',
    'KZ': 'Казахстан', 'FR': 'Франция', 'GB': 'Великобритания', 'CA': 'Канада',
    'AU': 'Австралия', 'JP': 'Япония', 'KR': 'Южная Корея', 'CN': 'Китай',
    'IN': 'Индия', 'BR': 'Бразилия', 'MX': 'Мексика', 'ES': 'Испания',
    'IT': 'Италия', 'PL': 'Польша', 'TR': 'Турция', 'NL': 'Нидерланды',
    'SE': 'Швеция', 'NO': 'Норвегия', 'FI': 'Финляндия', 'CZ': 'Чехия',
    'RO': 'Румыния', 'HU': 'Венгрия', 'AR': 'Аргентина', 'CL': 'Чили', 'CO': 'Колумбия'
}
flags = {
    'RU': '🇷🇺', 'US': '🇺🇸', 'DE': '🇩🇪', 'UA': '🇺🇦', 'BY': '🇧🇾',
    'KZ': '🇰🇿', 'FR': '🇫🇷', 'GB': '🇬🇧', 'CA': '🇨🇦', 'AU': '🇦🇺',
    'JP': '🇯🇵', 'KR': '🇰🇷', 'CN': '🇨🇳', 'IN': '🇮🇳', 'BR': '🇧🇷',
    'MX': '🇲🇽', 'ES': '🇪🇸', 'IT': '🇮🇹', 'PL': '🇵🇱', 'TR': '🇹🇷',
    'NL': '🇳🇱', 'SE': '🇸🇪', 'NO': '🇳🇴', 'FI': '🇫🇮', 'CZ': '🇨🇿',
    'RO': '🇷🇴', 'HU': '🇭🇺', 'AR': '🇦🇷', 'CL': '🇨🇱', 'CO': '🇨🇴'
}

translations = {
    'ru': {
        'main_menu': "🎨 Главное меню",
        'search': "🔍 Поиск скинмейкеров",
        'apply': "📝 Подать заявку",
        'bookmarks': "📌 Мои закладки",
        'profile': "👤 Мой профиль",
        'about': "ℹ️ О боте",
        'news': "📢 Новости",
        'donate': "❤️ Поддержать бота",
        'language': "🌐 Язык",
        'back': "🔙 Назад",
        'rating': "⭐ Рейтинг",
        'reviews': "📝 Отзывы",
        'bookmark_add': "📌 В закладки",
        'gallery': "🖼️ Галерея",
        'order': "📊 Заказов",
        'views': "👁 Просмотров",
        'experience': "🕰️ Стаж",
        'vacation': "🏖️ В отпуске",
        'busy': "⚠️ Перегружен до",
        'search_filters': "🔍 Выберите фильтр:",
        'standard': "🔄 Стандартные",
        'newbies': "🆕 Новички",
        'popular': "⭐ Популярные",
        'price_asc': "💰 По цене (возр.)",
        'price_desc': "💰 По цене (убыв.)",
        'no_makers': "😔 Скинмейкеры не найдены",
        'prev': "⬅️ Назад",
        'next': "➡️ Вперед",
        'rate': "⭐ Оценить",
        'leave_review': "✍️ Оставить отзыв",
        'review_prompt': "✍️ Напишите ваш отзыв:",
        'review_saved': "✅ Отзыв успешно добавлен!",
        'bookmark_saved': "✅ Добавлено в закладки!",
        'already_bookmarked': "Уже в закладках!",
        'no_bookmarks': "📌 У вас пока нет закладок",
        'apply_photo': "📸 Отправьте фото ваших работ (можно до 9, по одному, затем /done):",
        'apply_name': "✏️ Введите ваше имя (никнейм):",
        'apply_desc': "💬 Введите описание ваших услуг:",
        'apply_price': "💰 Введите цену (должна быть выше 100):",
        'apply_style': "🎨 Выберите стиль (можно несколько):",
        'apply_services': "🛠️ Выберите услуги:",
        'apply_done': "✅ Заявка отправлена!",
        'edit_profile': "✏️ Редактировать профиль",
        'request_edit': "✉️ Запросить правку",
        'support': "❤️ Поддержать бота:\n\nТ-Банк: 2200702103771312\nСБП: +79033799210\nBoosty: https://boosty.to/dfmskimake/about",
        'language_changed': "🌐 Язык изменён на русский",
        'admin_panel': "🔐 Админ-панель",
        'applications': "📋 Заявки",
        'all_makers': "👥 Все скинмейкеры",
        'stats': "📊 Статистика",
        'announce': "📢 Создать объявление",
        'export': "📤 Экспорт БД"
    },
    'en': {
        'main_menu': "🎨 Main Menu",
        'search': "🔍 Find skin makers",
        'apply': "📝 Apply",
        'bookmarks': "📌 Bookmarks",
        'profile': "👤 My Profile",
        'about': "ℹ️ About",
        'news': "📢 News",
        'donate': "❤️ Support bot",
        'language': "🌐 Language",
        'back': "🔙 Back",
        'rating': "⭐ Rating",
        'reviews': "📝 Reviews",
        'bookmark_add': "📌 Bookmark",
        'gallery': "🖼️ Gallery",
        'order': "📊 Orders",
        'views': "👁 Views",
        'experience': "🕰️ Experience",
        'vacation': "🏖️ On vacation",
        'busy': "⚠️ Busy until",
        'search_filters': "🔍 Choose filter:",
        'standard': "🔄 Standard",
        'newbies': "🆕 Newbies",
        'popular': "⭐ Popular",
        'price_asc': "💰 Price (low to high)",
        'price_desc': "💰 Price (high to low)",
        'no_makers': "😔 No skin makers found",
        'prev': "⬅️ Previous",
        'next': "➡️ Next",
        'rate': "⭐ Rate",
        'leave_review': "✍️ Leave review",
        'review_prompt': "✍️ Write your review:",
        'review_saved': "✅ Review saved!",
        'bookmark_saved': "✅ Added to bookmarks!",
        'already_bookmarked': "Already bookmarked!",
        'no_bookmarks': "📌 No bookmarks yet",
        'apply_photo': "📸 Send photos of your work (up to 9, one by one, then /done):",
        'apply_name': "✏️ Enter your name (nickname):",
        'apply_desc': "💬 Enter description:",
        'apply_price': "💰 Enter price (must be above 100):",
        'apply_style': "🎨 Choose style (multiple):",
        'apply_services': "🛠️ Choose services:",
        'apply_done': "✅ Application submitted!",
        'edit_profile': "✏️ Edit profile",
        'request_edit': "✉️ Request edit",
        'support': "❤️ Support bot:\n\nT-Bank: 2200702103771312\nSBP: +79033799210\nBoosty: https://boosty.to/dfmskimake/about",
        'language_changed': "🌐 Language switched to English",
        'admin_panel': "🔐 Admin Panel",
        'applications': "📋 Applications",
        'all_makers': "👥 All makers",
        'stats': "📊 Statistics",
        'announce': "📢 Create announcement",
        'export': "📤 Export DB"
    }
}

def get_text(user_id, key):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT language FROM user_settings WHERE user_id=?", (user_id,))
    row = c.fetchone()
    lang = row[0] if row else 'ru'
    conn.close()
    return translations[lang].get(key, key)

def main_menu_markup(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton(get_text(user_id, 'search')),
        types.KeyboardButton(get_text(user_id, 'apply')),
        types.KeyboardButton(get_text(user_id, 'bookmarks')),
        types.KeyboardButton(get_text(user_id, 'profile')),
        types.KeyboardButton(get_text(user_id, 'news')),
        types.KeyboardButton(get_text(user_id, 'donate')),
        types.KeyboardButton(get_text(user_id, 'language')),
        types.KeyboardButton(get_text(user_id, 'about'))
    )
    return markup

def is_admin(user_id):
    return user_id == ADMIN_ID

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

def format_maker_card(maker, user_id):
    (id, uid, uname, name, desc, price, services, photo_ids, rating, total,
     complaints, active, vacation, vac_text, reg_date, style, custom_style,
     dmin, dmax, shadow, shadow_reason, verdict, views, orders, orders_conf,
     busy_until, emoji, country, disp_exp,
     contact_link,
     social_tg, social_tw, social_pin, social_tiktok, social_yt, social_inst, social_vk, social_max) = maker

    flag = flags.get(country, '🏳️')
    country_name = countries.get(country, country)

    name_display = f"{emoji} {name} *{flag} {country_name}*"

    style_display = style.replace(',', ' + ')
    if custom_style:
        style_display += f"\n✨ {custom_style}"

    delivery = f"{dmin}–{dmax} дн."

    status = ""
    if vacation:
        status = get_text(user_id, 'vacation')
    elif busy_until:
        try:
            busy_date = datetime.strptime(busy_until, '%Y-%m-%d')
            if busy_date > datetime.now():
                status = f"{get_text(user_id, 'busy')} {busy_date.strftime('%d.%m.%Y')}"
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
    text += f"💰 Цена: от {price} ₽\n"
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

bot.current_makers = []
bot.current_index = 0
bot.current_filter = 'standard'

def show_card(chat_id, index):
    makers = bot.current_makers
    if index < 0 or index >= len(makers):
        return
    maker = makers[index]
    text = format_maker_card(maker, chat_id)
    photo_ids = json.loads(maker[7])
    markup = types.InlineKeyboardMarkup(row_width=3)
    nav_buttons = []
    if index > 0:
        nav_buttons.append(types.InlineKeyboardButton(get_text(chat_id, 'prev'), callback_data=f'nav_{index-1}'))
    nav_buttons.append(types.InlineKeyboardButton(f"{index+1}/{len(makers)}", callback_data='none'))
    if index < len(makers)-1:
        nav_buttons.append(types.InlineKeyboardButton(get_text(chat_id, 'next'), callback_data=f'nav_{index+1}'))
    markup.row(*nav_buttons)
    if maker[29]:  # contact_link
        markup.row(types.InlineKeyboardButton("✉️ Заказ", url=maker[29]))
    markup.row(
        types.InlineKeyboardButton(get_text(chat_id, 'rating'), callback_data=f'rate_{maker[0]}'),
        types.InlineKeyboardButton(get_text(chat_id, 'reviews'), callback_data=f'reviews_{maker[0]}'),
        types.InlineKeyboardButton(get_text(chat_id, 'bookmark_add'), callback_data=f'bookmark_{maker[0]}')
    )
    markup.row(
        types.InlineKeyboardButton("🌐 Соц сети", callback_data=f'social_{maker[0]}'),
        types.InlineKeyboardButton(get_text(chat_id, 'gallery'), callback_data=f'gallery_{maker[0]}')
    )
    if photo_ids:
        bot.send_photo(chat_id, photo_ids[0], caption=text, reply_markup=markup)
    else:
        bot.send_message(chat_id, text, reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    if is_blacklisted(message.from_user.id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы.")
        return
    bot.send_message(message.chat.id, "🎨 Добро пожаловать в Frime Skin!", reply_markup=main_menu_markup(message.from_user.id))

@bot.message_handler(commands=['help'])
def help_command(message):
    text = "📋 Доступные команды:\n/start — главное меню\n/help — это сообщение\n/admin — админ-панель (только для администратора)"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) > 1 and args[1] == 'secret' and len(args) > 2 and args[2] == 'command' and len(args) > 3 and args[3] == 'block':
        secret_text = (
            "🔐 Секретный блок команд администратора:\n"
            "/admin — открыть админ-панель\n"
            "/admin_applications — список заявок\n"
            "/admin_all_makers — все скинмейкеры\n"
            "/admin_stats — статистика\n"
            "/admin_announce — создать объявление\n"
            "/admin_export — экспорт БД\n"
            "/admin_shadow_ban <id> — теневой бан\n"
            "/admin_unshadow <id> — снять теневой бан\n"
            "/admin_blacklist <id> — добавить в чёрный список\n"
            "/admin_whitelist <id> — убрать из чёрного списка\n"
            "/admin_edit_requests — запросы правок\n"
            "/admin_log — лог действий"
        )
        bot.send_message(message.chat.id, secret_text)
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        get_text(message.from_user.id, 'applications'),
        get_text(message.from_user.id, 'all_makers'),
        get_text(message.from_user.id, 'stats'),
        get_text(message.from_user.id, 'announce'),
        get_text(message.from_user.id, 'export'),
        "🔙 Выйти"
    )
    bot.send_message(message.chat.id, get_text(message.from_user.id, 'admin_panel'), reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == get_text(m.from_user.id, 'search'))
def search_cmd(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(get_text(message.from_user.id, 'standard'), callback_data='filter_standard'),
        types.InlineKeyboardButton(get_text(message.from_user.id, 'newbies'), callback_data='filter_newbies'),
        types.InlineKeyboardButton(get_text(message.from_user.id, 'popular'), callback_data='filter_popular'),
        types.InlineKeyboardButton(get_text(message.from_user.id, 'price_asc'), callback_data='filter_price_asc'),
        types.InlineKeyboardButton(get_text(message.from_user.id, 'price_desc'), callback_data='filter_price_desc'),
        types.InlineKeyboardButton(get_text(message.from_user.id, 'back'), callback_data='back_main')
    )
    bot.send_message(message.chat.id, get_text(message.from_user.id, 'search_filters'), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('filter_'))
def filter_handler(call):
    filter_type = call.data.split('_')[1]
    makers = get_makers_by_filter(filter_type)
    if not makers:
        bot.edit_message_text(get_text(call.from_user.id, 'no_makers'), call.message.chat.id, call.message.message_id)
        return
    bot.current_makers = makers
    bot.current_index = 0
    bot.current_filter = filter_type
    bot.delete_message(call.message.chat.id, call.message.message_id)
    show_card(call.message.chat.id, 0)

@bot.callback_query_handler(func=lambda call: call.data.startswith('nav_'))
def nav_cards(call):
    index = int(call.data.split('_')[1])
    bot.delete_message(call.message.chat.id, call.message.message_id)
    show_card(call.message.chat.id, index)

@bot.callback_query_handler(func=lambda call: call.data == 'back_main')
def back_main(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, get_text(call.from_user.id, 'main_menu'), reply_markup=main_menu_markup(call.from_user.id))

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

@bot.message_handler(func=lambda m: m.text == get_text(m.from_user.id, 'bookmarks'))
def show_bookmarks(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT id, folder_name FROM bookmark_folders WHERE user_id=?", (user_id,))
    folders = c.fetchall()
    if not folders:
        bot.send_message(message.chat.id, get_text(user_id, 'no_bookmarks'))
        return
    text = "📌 Ваши закладки:\n"
    for f in folders:
        c.execute("SELECT sm.name FROM skin_makers sm JOIN bookmarks b ON sm.id = b.skin_maker_id WHERE b.folder_id=? AND b.user_id=?", (f[0], user_id))
        makers = c.fetchall()
        if makers:
            text += f"\n📁 {f[1]}:\n  " + "\n  ".join([m[0] for m in makers])
    conn.close()
    bot.send_message(message.chat.id, text if text else get_text(user_id, 'no_bookmarks'))

@bot.message_handler(func=lambda m: m.text == get_text(m.from_user.id, 'donate'))
def donate(message):
    bot.send_message(message.chat.id, get_text(message.from_user.id, 'support'))

@bot.message_handler(func=lambda m: m.text == get_text(m.from_user.id, 'language'))
def language_toggle(message):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT language FROM user_settings WHERE user_id=?", (message.from_user.id,))
    row = c.fetchone()
    current = row[0] if row else 'ru'
    new_lang = 'en' if current == 'ru' else 'ru'
    c.execute("REPLACE INTO user_settings (user_id, language) VALUES (?, ?)", (message.from_user.id, new_lang))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, get_text(message.from_user.id, 'language_changed'), reply_markup=main_menu_markup(message.from_user.id))

@bot.message_handler(func=lambda m: m.text == get_text(m.from_user.id, 'about'))
def about(message):
    bot.send_message(message.chat.id, "Frime Skin — платформа для поиска скинмейкеров Minecraft. Версия 2.0")

@bot.message_handler(func=lambda m: m.text == get_text(m.from_user.id, 'profile'))
def profile(message):
    bot.send_message(message.chat.id, "Раздел в разработке.")

user_states = {}

@bot.message_handler(func=lambda m: m.text == get_text(m.from_user.id, 'apply'))
def apply_start(message):
    if is_blacklisted(message.from_user.id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы.")
        return
    user_id = message.from_user.id
    user_states[user_id] = {'photos': [], 'step': 'photo'}
    msg = bot.send_message(message.chat.id, get_text(user_id, 'apply_photo'))
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
        msg = bot.send_message(message.chat.id, get_text(user_id, 'apply_name'))
        bot.register_next_step_handler(msg, process_apply_name)
        return
    else:
        bot.send_message(message.chat.id, "Отправьте фото или команду /done")
    msg = bot.send_message(message.chat.id, "Отправьте ещё фото или /done")
    bot.register_next_step_handler(msg, process_apply_photo)

def process_apply_name(message):
    user_id = message.from_user.id
    user_states[user_id]['name'] = message.text
    msg = bot.send_message(message.chat.id, get_text(user_id, 'apply_desc'))
    bot.register_next_step_handler(msg, process_apply_description)

def process_apply_description(message):
    user_id = message.from_user.id
    user_states[user_id]['description'] = message.text
    msg = bot.send_message(message.chat.id, get_text(user_id, 'apply_price'))
    bot.register_next_step_handler(msg, process_apply_price)

def process_apply_price(message):
    user_id = message.from_user.id
    try:
        price = int(message.text)
        if price <= 100:
            raise ValueError
    except:
        msg = bot.send_message(message.chat.id, "Цена должна быть числом >100. Повторите:")
        bot.register_next_step_handler(msg, process_apply_price)
        return
    user_states[user_id]['price'] = price

    markup = types.InlineKeyboardMarkup(row_width=2)
    styles = ['modern', 'colorful', 'realism', 'namemc', 'special']
    for s in styles:
        markup.add(types.InlineKeyboardButton(s, callback_data=f'applystyle_{s}'))
    markup.add(types.InlineKeyboardButton("✅ Готово", callback_data='applystyle_done'))
    user_states[user_id]['selected_styles'] = []
    msg = bot.send_message(message.chat.id, get_text(user_id, 'apply_style'), reply_markup=markup)

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
        bot.send_message(call.message.chat.id, get_text(user_id, 'apply_services'), reply_markup=markup)
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
         json.dumps(data['photos']), ', '.join(data['selected_styles']), data.get('custom_style', ''),
         data.get('contact_link'), data.get('social_telegram'), data.get('social_twitter'),
         data.get('social_pinterest'), data.get('social_tiktok'), data.get('social_youtube'),
         data.get('social_instagram'), data.get('social_vk'), data.get('social_max')))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Заявка отправлена! Ожидайте одобрения администратором.")
    bot.send_message(ADMIN_ID, f"📋 Новая заявка от @{message.from_user.username}")

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
    c.execute("INSERT INTO ratings (skin_maker_id, user_id, rating, quality, speed, communication, reason) VALUES (?,?,?,?,?,?,?)",
              (maker_id, user_id, avg, q, s, c_val, reason))
    c.execute("UPDATE skin_makers SET total_ratings=total_ratings+1, rating=(SELECT AVG(rating) FROM ratings WHERE skin_maker_id=? AND is_removed=0) WHERE id=?", (maker_id, maker_id))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Спасибо за оценку!")
    if avg <= 2.5:
        bot.send_message(ADMIN_ID, f"⚠️ Низкая оценка ({avg}) мастеру ID{maker_id} от @{message.from_user.username}\nПричина: {reason}")

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
    markup.add(types.InlineKeyboardButton(get_text(call.from_user.id, 'leave_review'), callback_data=f'addreview_{maker_id}'))
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

@bot.message_handler(commands=['admin_applications'])
def admin_applications_cmd(message):
    if not is_admin(message.from_user.id):
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM applications WHERE status='pending'")
    apps = c.fetchall()
    conn.close()
    if not apps:
        bot.send_message(message.chat.id, "Нет заявок.")
        return
    for app in apps:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Принять", callback_data=f'approve_{app[0]}'),
            types.InlineKeyboardButton("❌ Отклонить", callback_data=f'reject_{app[0]}')
        )
        text = f"Заявка #{app[0]}\nИмя: {app[3]}\nЦена: {app[5]}\nСтиль: {app[8]}\nУслуги: {app[6]}"
        bot.send_message(message.chat.id, text, reply_markup=markup)

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
    log_action(ADMIN_ID, 'approve_application', f'App #{app_id}')

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
    log_action(ADMIN_ID, 'reject_application', f'App #{app_id}')

@bot.message_handler(commands=['admin_all_makers'])
def admin_all_makers_cmd(message):
    if not is_admin(message.from_user.id):
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT id, name, shadow_banned, is_active FROM skin_makers")
    makers = c.fetchall()
    conn.close()
    if not makers:
        bot.send_message(message.chat.id, "Нет скинмейкеров.")
        return
    text = "Список скинмейкеров:\n" + "\n".join([f"{m[0]}: {m[1]} (shadow: {m[2]}, active: {m[3]})" for m in makers])
    bot.send_message(message.chat.id, text[:4000])

@bot.message_handler(commands=['admin_stats'])
def admin_stats_cmd(message):
    if not is_admin(message.from_user.id):
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM skin_makers")
    makers_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM applications WHERE status='pending'")
    pending = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM reviews")
    reviews_count = c.fetchone()[0]
    conn.close()
    text = f"📊 Статистика:\n• Скинмейкеров: {makers_count}\n• Заявок ожидает: {pending}\n• Отзывов: {reviews_count}"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['admin_announce'])
def admin_announce_cmd(message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.send_message(message.chat.id, "Введите текст объявления:")
    bot.register_next_step_handler(msg, process_announce_text)

def process_announce_text(message):
    text = message.text
    msg = bot.send_message(message.chat.id, "Прикрепите фото (или /skip):")
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
    log_action(ADMIN_ID, 'create_announcement')

@bot.message_handler(commands=['admin_export'])
def admin_export_cmd(message):
    if not is_admin(message.from_user.id):
        return
    conn = sqlite3.connect('firme_skin.db')
    with open('export_frime.csv', 'w', encoding='utf-8') as f:
        for line in conn.iterdump():
            f.write('%s\n' % line)
    conn.close()
    bot.send_document(message.chat.id, open('export_frime.csv', 'rb'), caption="Дамп базы данных")
    log_action(ADMIN_ID, 'export_db')

@bot.message_handler(commands=['admin_shadow_ban'])
def admin_shadow_ban_cmd(message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "Укажите ID скинмейкера: /admin_shadow_ban <id>")
        return
    maker_id = int(args[1])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET shadow_banned=1 WHERE id=?", (maker_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"Теневой бан применён к ID {maker_id}")
    log_action(ADMIN_ID, 'shadow_ban', f'Maker {maker_id}')

@bot.message_handler(commands=['admin_unshadow'])
def admin_unshadow_cmd(message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "Укажите ID скинмейкера: /admin_unshadow <id>")
        return
    maker_id = int(args[1])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("UPDATE skin_makers SET shadow_banned=0 WHERE id=?", (maker_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"Теневой бан снят с ID {maker_id}")
    log_action(ADMIN_ID, 'unshadow', f'Maker {maker_id}')

@bot.message_handler(commands=['admin_blacklist'])
def admin_blacklist_cmd(message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "Укажите ID пользователя: /admin_blacklist <user_id>")
        return
    user_id = int(args[1])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO blacklist (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"Пользователь {user_id} добавлен в чёрный список.")
    log_action(ADMIN_ID, 'blacklist', f'User {user_id}')

@bot.message_handler(commands=['admin_whitelist'])
def admin_whitelist_cmd(message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "Укажите ID пользователя: /admin_whitelist <user_id>")
        return
    user_id = int(args[1])
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("DELETE FROM blacklist WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"Пользователь {user_id} удалён из чёрного списка.")
    log_action(ADMIN_ID, 'whitelist', f'User {user_id}')

@bot.message_handler(commands=['admin_edit_requests'])
def admin_edit_requests_cmd(message):
    if not is_admin(message.from_user.id):
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM edit_requests WHERE status='pending'")
    reqs = c.fetchall()
    conn.close()
    if not reqs:
        bot.send_message(message.chat.id, "Нет запросов правок.")
        return
    text = "Запросы правок:\n" + "\n".join([f"#{r[0]}: maker {r[1]}, {r[3]}" for r in reqs])
    bot.send_message(message.chat.id, text[:4000])

@bot.message_handler(commands=['admin_log'])
def admin_log_cmd(message):
    if not is_admin(message.from_user.id):
        return
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM action_log ORDER BY date DESC LIMIT 20")
    logs = c.fetchall()
    conn.close()
    if not logs:
        bot.send_message(message.chat.id, "Лог пуст.")
        return
    text = "Последние действия:\n" + "\n".join([f"{l[3][:19]}: {l[2]}" for l in logs])
    bot.send_message(message.chat.id, text[:4000])

@bot.message_handler(func=lambda m: m.text == get_text(m.from_user.id, 'news'))
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

@bot.message_handler(func=lambda m: m.text == get_text(m.from_user.id, 'request_edit'))
def request_edit(message):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT id FROM skin_makers WHERE user_id=?", (message.from_user.id,))
    maker = c.fetchone()
    conn.close()
    if not maker:
        bot.send_message(message.chat.id, "Вы не зарегистрированы как скинмейкер.")
        return
    msg = bot.send_message(message.chat.id, "Опишите, что нужно изменить (например: стаж на 2 года, заказов 150):")
    bot.register_next_step_handler(msg, process_edit_request, maker[0])

def process_edit_request(message, maker_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("INSERT INTO edit_requests (skin_maker_id, field, new_value) VALUES (?,?,?)",
              (maker_id, 'custom', message.text))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "Запрос отправлен администратору.")
    bot.send_message(ADMIN_ID, f"📩 Запрос правок от скинмейкера ID{maker_id}: {message.text}")

@bot.message_handler(func=lambda m: m.text == "🔙 Выйти" and is_admin(m.from_user.id))
def exit_admin(message):
    bot.send_message(message.chat.id, "Вы вышли из админ-панели.", reply_markup=main_menu_markup(message.from_user.id))

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

if __name__ == '__main__':
    init_db()
    t = threading.Thread(target=check_achievements, daemon=True)
    t.start()
    print("Бот Frime Skin запущен...")
    bot.polling(none_stop=True)
import sqlite3
import json
from datetime import datetime
import random
from telebot import types

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
    for col in ['price_min', 'price_max', 'order_display']:
        try: c.execute(f"ALTER TABLE skin_makers ADD COLUMN {col}")
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
    for col in ['price_min', 'price_max']:
        try: c.execute(f"ALTER TABLE applications ADD COLUMN {col}")
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
        if style.strip() == 'namemc' and random.random() > 0.1:
            continue
        if m[22] and random.random() > 0.1:
            continue
        filtered.append(m)
        if len(filtered) >= limit:
            break
    if filter_type == 'popular_formula':
        filtered.sort(
            key=lambda m: (float(m[9]) if m[9] else 5.0) * (1 + (int(m[10]) if m[10] else 0) * 0.1),
            reverse=True
        )
    return filtered

def format_maker_card(maker):
    from config import countries, flags
    (id, uid, uname, name, desc, price, price_min, price_max, services, photo_ids,
     rating, total, complaints, active, vacation, vac_text, reg_date,
     style, custom_style, dmin, dmax, shadow, shadow_reason, verdict,
     views, orders, orders_conf, busy_until, emoji, country, disp_exp,
     contact_link, social_tg, social_tw, social_pin, social_tiktok,
     social_yt, social_inst, social_vk, social_max, order_display) = maker
    try:
        rating = float(rating) if rating else 5.0
    except (TypeError, ValueError):
        rating = 5.0
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
        else: experience = f"{days // 365} год(а)"
    if order_display: orders_text = order_display
    else: orders_text = f"{orders} ✅" if orders_conf else f"~{orders}"
    if price_min and price_max and price_min != price_max:
        price_text = f"от {price_min} до {price_max} ₽"
    elif price: price_text = f"от {price} ₽"
    else: price_text = "не указана"
    text = f"{name_display}\n\n🎨 Стиль: {style_display}\n⏱ Срок: {delivery}\n💲 Ценник: {price_text}\n⭐ Рейтинг: {rating:.1f}/5\n"
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
    text += f"📊 Заказов: {orders_text}\n👁 Просмотров: {views}\n🕰️ Стаж: {experience}\n"
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

def get_application_by_id(app_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM applications WHERE id=?", (app_id,))
    app = c.fetchone()
    conn.close()
    return app

def show_applications(chat_id, bot, username_by_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT * FROM applications WHERE status='pending'")
    apps = c.fetchall()
    conn.close()
    if not apps:
        bot.send_message(chat_id, "Нет заявок.")
        return
    for app in apps:
        text = f"📋 Заявка #{app[0]}\n\n👤 Имя: {app[3]}\n💬 Описание: {app[4]}\n"
        price_text = f"от {app[5]} ₽" if app[5] else "не указана"
        if app[6] and app[7]:
            price_text = f"от {app[6]} до {app[7]} ₽"
        text += f"💲 Ценник: {price_text}\n🎨 Стиль: {app[10]}\n🛠️ Услуги: {app[8]}\n⏱ Сроки: {app[24]}–{app[25]} дн.\n"
        if app[15]:
            text += f"🔗 Ссылка: {app[15]}\n"
        soc = []
        if app[16]: soc.append(f"📨 Telegram: {app[16]}")
        if app[17]: soc.append(f"𝕏 Twitter: {app[17]}")
        if app[18]: soc.append(f"📌 Pinterest: {app[18]}")
        if app[19]: soc.append(f"🎵 TikTok: {app[19]}")
        if app[20]: soc.append(f"▶️ YouTube: {app[20]}")
        if app[21]: soc.append(f"📷 Instagram: {app[21]}")
        if app[22]: soc.append(f"💙 VK: {app[22]}")
        if app[23]: soc.append(f"🔶 Max: {app[23]}")
        if soc:
            text += "🌐 Соцсети:\n" + "\n".join(soc) + "\n"
        text += f"\nОтправитель: {username_by_id(bot, app[1])}"
        photos = json.loads(app[9]) if app[9] else []
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Принять", callback_data=f'approve_{app[0]}'),
                   types.InlineKeyboardButton("❌ Отклонить", callback_data=f'reject_{app[0]}'))
        if photos:
            bot.send_photo(chat_id, photos[0], caption=text, reply_markup=markup)
        else:
            bot.send_message(chat_id, text, reply_markup=markup)

def log_action(admin_id, action, details=""):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("INSERT INTO action_log (admin_id, action, details) VALUES (?,?,?)", (admin_id, action, details))
    conn.commit()
    conn.close()

def add_to_folder(user_id, maker_id, folder_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("INSERT INTO bookmarks (user_id, skin_maker_id, folder_id) VALUES (?,?,?)", (user_id, maker_id, folder_id))
    conn.commit()
    conn.close()
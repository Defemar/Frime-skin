import sqlite3
import json
from telebot import types
from database.models import get_makers_by_filter, format_maker_card, add_to_folder
from utils.keyboards import main_menu_markup
from utils.helpers import is_blacklisted, username_by_id, notify_admins

def register_user_handlers(bot):

    @bot.message_handler(commands=['start'])
    def start(message):
        if is_blacklisted(message.from_user.id):
            bot.send_message(message.chat.id, "🚫 Вы заблокированы.")
            return
        bot.send_message(message.chat.id, "🎨 Добро пожаловать в Frime Skin!", reply_markup=main_menu_markup())

    @bot.message_handler(commands=['help'])
    def help_cmd(message):
        bot.send_message(message.chat.id, "/start — главное меню\n/help — помощь\n/cancel — отмена заявки\n/done — завершить фото")

    # ===================== ЛЕНТА =====================
    @bot.message_handler(func=lambda m: m.text == "🔍 Лента")
    def search_cmd(message):
        bot.current_filter = 'popular_formula'
        makers = get_makers_by_filter('popular_formula')
        if not makers:
            bot.send_message(message.chat.id, "😔 Скинмейкеры не найдены.")
            return
        bot.current_makers = makers
        show_card(message.chat.id, 0)

    def show_card(chat_id, index):
        if not bot.current_makers:
            bot.send_message(chat_id, "😔 Скинмейкеры не найдены.")
            return
        makers = bot.current_makers
        if index < 0 or index >= len(makers):
            return
        maker = makers[index]
        text = format_maker_card(maker)
        photo_ids = json.loads(maker[8])
        markup = types.InlineKeyboardMarkup(row_width=3)
        nav = []
        if index > 0:
            nav.append(types.InlineKeyboardButton("⬅️", callback_data=f'nav_{index-1}'))
        nav.append(types.InlineKeyboardButton(f"{index+1}/{len(makers)}", callback_data='none'))
        if index < len(makers)-1:
            nav.append(types.InlineKeyboardButton("➡️", callback_data=f'nav_{index+1}'))
        markup.row(*nav)
        if maker[31]:
            url = maker[31].strip()
            if not url.startswith('http'):
                if url.startswith('@'):
                    url = f"https://t.me/{url[1:]}"
                elif url.startswith('t.me/'):
                    url = f"https://{url}"
                else:
                    url = f"https://t.me/{url}"
            markup.row(types.InlineKeyboardButton("✉️ Заказ", url=url))
        markup.row(types.InlineKeyboardButton("⭐ Оценить", callback_data=f'rate_{maker[0]}'),
                   types.InlineKeyboardButton("📝 Отзывы", callback_data=f'reviews_{maker[0]}'),
                   types.InlineKeyboardButton("📌 В закладки", callback_data=f'bookmark_{maker[0]}'))
        markup.row(types.InlineKeyboardButton("🌐 Соц сети", callback_data=f'social_{maker[0]}'),
                   types.InlineKeyboardButton("🖼️ Галерея", callback_data=f'gallery_{maker[0]}'))
        markup.row(types.InlineKeyboardButton("⚙️ Фильтры", callback_data='filter_menu'))
        if photo_ids:
            bot.send_photo(chat_id, photo_ids[0], caption=text, reply_markup=markup)
        else:
            bot.send_message(chat_id, text, reply_markup=markup)

    # ===================== ФИЛЬТРЫ =====================
    @bot.callback_query_handler(func=lambda call: call.data == 'filter_menu')
    def filter_menu(call):
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("💲 По цене (возр.)", callback_data='filter_price_asc'),
                   types.InlineKeyboardButton("💲 По цене (убыв.)", callback_data='filter_price_desc'),
                   types.InlineKeyboardButton("⭐ Популярное", callback_data='filter_popular_formula'),
                   types.InlineKeyboardButton("🎨 По стилю", callback_data='filter_style_menu'),
                   types.InlineKeyboardButton("🛠️ По услуге", callback_data='filter_service_menu'))
        bot.send_message(call.message.chat.id, "⚙️ Фильтры", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('filter_'))
    def filter_handler(call):
        data = call.data
        if data == 'filter_popular_formula':
            bot.current_filter = 'popular_formula'
            makers = get_makers_by_filter('popular_formula')
        elif data == 'filter_price_asc':
            bot.current_filter = 'price_asc'
            makers = get_makers_by_filter('price_asc')
        elif data == 'filter_price_desc':
            bot.current_filter = 'price_desc'
            makers = get_makers_by_filter('price_desc')
        elif data == 'filter_style_menu':
            markup = types.InlineKeyboardMarkup(row_width=2)
            for s in ['modern', 'colorful', 'realism', 'namemc', 'special']:
                markup.add(types.InlineKeyboardButton(s, callback_data=f'filter_style_{s}'))
            bot.send_message(call.message.chat.id, "Выберите стиль:", reply_markup=markup)
            return
        elif data == 'filter_service_menu':
            markup = types.InlineKeyboardMarkup(row_width=2)
            for s in ['Скины', 'Модели', 'Текстуры', 'Рендер', '128x128', '256x256', '3D скины']:
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

    @bot.callback_query_handler(func=lambda call: call.data == 'back_main')
    def back_main(call):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "🎨 Главное меню", reply_markup=main_menu_markup())

    @bot.callback_query_handler(func=lambda call: call.data.startswith('nav_'))
    def nav_cards(call):
        try:
            index = int(call.data.split('_')[1])
            if not bot.current_makers:
                return
            bot.delete_message(call.message.chat.id, call.message.message_id)
            show_card(call.message.chat.id, index)
        except:
            pass

    # ===================== ГАЛЕРЕЯ =====================
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

    # ===================== СОЦСЕТИ =====================
    @bot.callback_query_handler(func=lambda call: call.data.startswith('social_'))
    def show_social_links(call):
        maker_id = int(call.data.split('_')[1])
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("SELECT social_telegram, social_twitter, social_pinterest, social_tiktok, social_youtube, social_instagram, social_vk, social_max FROM skin_makers WHERE id=?", (maker_id,))
        row = c.fetchone()
        conn.close()
        if not row:
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

    # ===================== ЗАКЛАДКИ =====================
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

    # ===================== ДОНАТ =====================
    @bot.message_handler(func=lambda m: m.text == "💸 Донат на сервера")
    def donate(message):
        bot.send_message(message.chat.id, "💸 Донат на сервера\nПо желанию\n\n❤️ Поддержать бота:\n\nТ-Банк: 2200702103771312\nСБП: +79033799210\nBoosty: https://boosty.to/dfmskimake/about")

    # ===================== О БОТЕ =====================
    @bot.message_handler(func=lambda m: m.text == "ℹ️ О боте")
    def about(message):
        bot.send_message(message.chat.id, "Frime Skin — платформа для поиска скинмейкеров Minecraft.\nСвязь: @Defemar\n\nМы помогаем найти идеального мастера для вашего скина.")

    # ===================== ОЦЕНКИ =====================
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
        if c.fetchone():
            bot.answer_callback_query(call.id, "Вы уже оценивали.")
            conn.close()
            return
        conn.close()
        bot.current_rate_maker = maker_id
        bot.send_message(call.message.chat.id, "Оцените качество (1-5):")
        bot.register_next_step_handler(call.message, process_quality)

    def process_quality(message):
        try:
            q = int(message.text)
            if q < 1 or q > 5:
                raise ValueError
        except:
            bot.send_message(message.chat.id, "Введите число от 1 до 5:")
            bot.register_next_step_handler(message, process_quality)
            return
        bot.current_rate_quality = q
        bot.send_message(message.chat.id, "Оцените скорость (1-5):")
        bot.register_next_step_handler(message, process_speed)

    def process_speed(message):
        try:
            s = int(message.text)
            if s < 1 or s > 5:
                raise ValueError
        except:
            bot.send_message(message.chat.id, "Введите число от 1 до 5:")
            bot.register_next_step_handler(message, process_speed)
            return
        bot.current_rate_speed = s
        bot.send_message(message.chat.id, "Оцените общение (1-5):")
        bot.register_next_step_handler(message, process_communication)

    def process_communication(message):
        try:
            c_val = int(message.text)
            if c_val < 1 or c_val > 5:
                raise ValueError
        except:
            bot.send_message(message.chat.id, "Введите число от 1 до 5:")
            bot.register_next_step_handler(message, process_communication)
            return
        avg = round((bot.current_rate_quality + bot.current_rate_speed + c_val) / 3, 1)
        maker_id = bot.current_rate_maker
        user_id = message.from_user.id
        if avg <= 2.5:
            bot.send_message(message.chat.id, "Почему такая оценка? Напишите причину:")
            bot.register_next_step_handler(message, lambda m, mid=maker_id, uid=user_id, avg=avg, q=bot.current_rate_quality, s=bot.current_rate_speed, c=c_val: save_rating(m, mid, uid, avg, q, s, c))
        else:
            save_rating(message, maker_id, user_id, avg, bot.current_rate_quality, bot.current_rate_speed, c_val, reason="")

    def save_rating(message, maker_id, user_id, avg, q, s, c_val, reason=None):
        if reason is None:
            reason = message.text
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
            notify_admins(bot, f"⚠️ Низкая оценка ({avg}) мастеру ID{maker_id} от {username_by_id(bot, user_id)}\nПричина: {reason}")

    # ===================== ОТЗЫВЫ =====================
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
        text = "📝 Отзывы:\n\n"
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
        bot.current_review_maker = int(call.data.split('_')[1])
        bot.send_message(call.message.chat.id, "✍️ Напишите отзыв:")
        bot.register_next_step_handler(call.message, process_review_text)

    def process_review_text(message):
        bot.current_review_text = message.text
        bot.send_message(message.chat.id, "📸 Фото ДО (или '-'):")
        bot.register_next_step_handler(message, process_review_before)

    def process_review_before(message):
        if message.content_type == 'photo':
            bot.current_review_before = message.photo[-1].file_id
        else:
            bot.current_review_before = None
        bot.send_message(message.chat.id, "📸 Фото ПОСЛЕ (или '-'):")
        bot.register_next_step_handler(message, process_review_after)

    def process_review_after(message):
        if message.content_type == 'photo':
            after_id = message.photo[-1].file_id
        else:
            after_id = None
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("INSERT INTO reviews (skin_maker_id, user_id, username, review_text, rating, photo_before_id, photo_after_id) VALUES (?,?,?,?,?,?,?)",
                  (bot.current_review_maker, message.from_user.id, message.from_user.first_name, bot.current_review_text, 5, bot.current_review_before, after_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Отзыв добавлен!")

    # ===================== НОВОСТИ =====================
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
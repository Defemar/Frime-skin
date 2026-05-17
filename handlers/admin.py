import sqlite3
import json
import shutil
from datetime import datetime
from telebot import types
from database.models import show_applications, log_action, get_makers_by_filter, format_maker_card
from utils.keyboards import main_menu_markup, admin_panel_markup
from utils.helpers import is_admin, is_main_admin, is_blacklisted, username_by_id, notify_admins
import re

def register_admin_handlers(bot):

    # ===== ГЛАВНОЕ АДМИН-МЕНЮ =====
    @bot.message_handler(commands=['admin'])
    def admin_cmd(message):
        if not is_admin(message.from_user.id):
            return
        bot.send_message(message.chat.id, "🔐 Админ-панель", reply_markup=admin_panel_markup())

    # ===== ЗАЯВКИ =====
    @bot.message_handler(func=lambda m: m.text == "📋 Заявки" and is_admin(m.from_user.id))
    def admin_applications_button(message):
        show_applications(message.chat.id, bot, username_by_id)

    @bot.message_handler(commands=['admin_applications'])
    def admin_applications_cmd(message):
        if not is_admin(message.from_user.id):
            return
        show_applications(message.chat.id, bot, username_by_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('approve_'))
    def approve_app(call):
        app_id = int(call.data.split('_')[1])
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("SELECT * FROM applications WHERE id=?", (app_id,))
        app = c.fetchone()
        c.execute('''INSERT INTO skin_makers
            (user_id, username, name, description, price, price_min, price_max,
             services, photo_ids, style, contact_link, social_telegram, social_twitter,
             social_pinterest, social_tiktok, social_youtube, social_instagram,
             social_vk, social_max, delivery_min_days, delivery_max_days)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (app[1], app[2], app[3], app[4], app[5], app[6], app[7], app[8], app[9], app[10],
             app[15], app[16], app[17], app[18], app[19], app[20], app[21], app[22], app[23],
             app[24], app[25]))
        c.execute("UPDATE applications SET status='approved' WHERE id=?", (app_id,))
        conn.commit()
        conn.close()
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, f"✅ Заявка #{app_id} одобрена.")
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
        bot.send_message(call.message.chat.id, f"❌ Заявка #{app_id} отклонена.")
        log_action(call.from_user.id, 'reject_application', f'App #{app_id}')

    # ===== СКИНМЕЙКЕРЫ (СПИСОК) =====
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
            username = username_by_id(m[2])
            text += f"ID{m[0]} {m[1]} ({username})\n⭐{(m[3] or 5.0):.1f} | Активен:{'✅' if m[4] else '❌'} | Жалобы:{m[5]} | Теневой:{'⚠️' if m[6] else '✅'}\n\n"
        bot.send_message(message.chat.id, text[:4000])

    # ===== СТАТИСТИКА =====
    @bot.message_handler(func=lambda m: m.text == "📊 Статистика" and is_admin(m.from_user.id))
    def admin_stats_button(message):
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM skin_makers"); makers_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM skin_makers WHERE is_active=1"); active_makers = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM applications WHERE status='pending'"); pending = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM reviews"); reviews_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM ratings"); ratings_count = c.fetchone()[0]
        c.execute("SELECT AVG(rating) FROM skin_makers"); avg_rating = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM blacklist"); blacklist_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM admins"); admins_count = c.fetchone()[0]
        conn.close()
        text = f"📊 Статистика:\n\n• Скинмейкеров: {makers_count} (активных: {active_makers})\n• Заявок ожидает: {pending}\n• Отзывов: {reviews_count}\n• Оценок: {ratings_count}\n• Средний рейтинг: {avg_rating:.1f}\n• В чёрном списке: {blacklist_count}\n• Администраторов: {admins_count}"
        bot.send_message(message.chat.id, text)

    # ===== ОБЪЯВЛЕНИЯ =====
    @bot.message_handler(func=lambda m: m.text == "📢 Объявления" and is_admin(m.from_user.id))
    def admin_announce_menu(message):
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("➕ Создать", callback_data='create_announce'),
                   types.InlineKeyboardButton("📋 Посмотреть", callback_data='view_announcements'),
                   types.InlineKeyboardButton("🗑️ Удалить последнее", callback_data='delete_last_announce'))
        bot.send_message(message.chat.id, "📢 Управление объявлениями:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == 'create_announce')
    def create_announce_cb(call):
        bot.send_message(call.message.chat.id, "Введите текст объявления:")
        bot.register_next_step_handler(call.message, process_announce_text)

    def process_announce_text(message):
        text = message.text
        bot.send_message(message.chat.id, "Прикрепите фото (или /stop):")
        bot.register_next_step_handler(message, process_announce_photo, text)

    def process_announce_photo(message, text):
        photo_id = None
        if message.content_type == 'photo':
            photo_id = message.photo[-1].file_id
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("INSERT INTO announcements (text, photo_id) VALUES (?,?)", (text, photo_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Объявление создано.")
        log_action(message.from_user.id, 'create_announcement')

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
        bot.send_message(call.message.chat.id, "✅ Удалено.")

    # ===== ЭКСПОРТ И СОХРАНЕНИЕ БД =====
    @bot.message_handler(func=lambda m: m.text == "📤 Экспорт БД" and is_admin(m.from_user.id))
    def admin_export_button(message):
        conn = sqlite3.connect('firme_skin.db')
        with open('export_frime.csv', 'w', encoding='utf-8') as f:
            for line in conn.iterdump():
                f.write('%s\n' % line)
        conn.close()
        bot.send_document(message.chat.id, open('export_frime.csv', 'rb'), caption="Дамп базы данных")
        log_action(message.from_user.id, 'export_db')

    @bot.message_handler(func=lambda m: m.text == "💾 Сохранить БД" and is_admin(m.from_user.id))
    def save_db_button(message):
        backup_name = f'firme_skin_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copyfile('firme_skin.db', backup_name)
        bot.send_document(message.chat.id, open(backup_name, 'rb'), caption="✅ База сохранена.")
        log_action(message.from_user.id, 'save_db')

    # ===== ТЕНЕВОЙ БАН =====
    @bot.message_handler(func=lambda m: m.text == "⛔ Теневой бан" and is_admin(m.from_user.id))
    def admin_shadow_menu(message):
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("➕ Применить", callback_data='apply_shadow'),
                   types.InlineKeyboardButton("➖ Снять", callback_data='remove_shadow'),
                   types.InlineKeyboardButton("📋 Список", callback_data='list_shadow'))
        bot.send_message(message.chat.id, "⛔ Теневой бан:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == 'apply_shadow')
    def apply_shadow_cb(call):
        bot.send_message(call.message.chat.id, "Введите ID скинмейкера:")
        bot.register_next_step_handler(call.message, process_apply_shadow)

    def process_apply_shadow(message):
        try:
            maker_id = int(message.text)
        except:
            bot.send_message(message.chat.id, "ID должен быть числом."); return
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("UPDATE skin_makers SET shadow_banned=1 WHERE id=?", (maker_id,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Теневой бан применён к ID {maker_id}")
        log_action(message.from_user.id, 'shadow_ban', f'Maker {maker_id}')

    @bot.callback_query_handler(func=lambda call: call.data == 'remove_shadow')
    def remove_shadow_cb(call):
        bot.send_message(call.message.chat.id, "Введите ID скинмейкера:")
        bot.register_next_step_handler(call.message, process_remove_shadow)

    def process_remove_shadow(message):
        try:
            maker_id = int(message.text)
        except:
            bot.send_message(message.chat.id, "ID должен быть числом."); return
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("UPDATE skin_makers SET shadow_banned=0 WHERE id=?", (maker_id,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Теневой бан снят с ID {maker_id}")
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
        text = "⛔ Теневой бан:\n" + "\n".join([f"ID{m[0]} — {m[1]}" for m in makers])
        bot.send_message(call.message.chat.id, text)

    # ===== ЧЁРНЫЙ СПИСОК =====
    @bot.message_handler(func=lambda m: m.text == "🚫 Чёрный список" and is_admin(m.from_user.id))
    def admin_blacklist_menu(message):
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("➕ Заблокировать", callback_data='add_blacklist'),
                   types.InlineKeyboardButton("➖ Разблокировать", callback_data='remove_blacklist'),
                   types.InlineKeyboardButton("📋 Список", callback_data='list_blacklist'))
        bot.send_message(message.chat.id, "🚫 Чёрный список:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == 'add_blacklist')
    def add_blacklist_cb(call):
        bot.send_message(call.message.chat.id, "Введите ID пользователя:")
        bot.register_next_step_handler(call.message, process_blacklist_add)

    def process_blacklist_add(message):
        try:
            user_id = int(message.text)
        except:
            bot.send_message(message.chat.id, "ID должен быть числом."); return
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO blacklist (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Пользователь {user_id} заблокирован.")
        log_action(message.from_user.id, 'blacklist_add', f'User {user_id}')

    @bot.callback_query_handler(func=lambda call: call.data == 'remove_blacklist')
    def remove_blacklist_cb(call):
        bot.send_message(call.message.chat.id, "Введите ID пользователя:")
        bot.register_next_step_handler(call.message, process_blacklist_remove)

    def process_blacklist_remove(message):
        try:
            user_id = int(message.text)
        except:
            bot.send_message(message.chat.id, "ID должен быть числом."); return
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
        text = "🚫 Заблокированные:\n" + "\n".join(map(str, users))
        bot.send_message(call.message.chat.id, text)

    # ===== УПРАВЛЕНИЕ АДМИНАМИ =====
    @bot.message_handler(func=lambda m: m.text == "👑 Админы" and is_admin(m.from_user.id))
    def admin_admins_menu(message):
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("SELECT user_id FROM admins")
        admins = [row[0] for row in c.fetchall()]
        conn.close()
        text = f"👑 Главный: {ADMIN_ID}\n👥 Доп.: " + (", ".join(map(str, admins)) if admins else "нет")
        if is_main_admin(message.from_user.id):
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("➕ Добавить", callback_data='add_admin_menu'),
                       types.InlineKeyboardButton("➖ Удалить", callback_data='remove_admin_menu'))
            bot.send_message(message.chat.id, text, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, text)

    @bot.callback_query_handler(func=lambda call: call.data == 'add_admin_menu')
    def add_admin_menu_cb(call):
        bot.send_message(call.message.chat.id, "Введите ID нового админа:")
        bot.register_next_step_handler(call.message, process_add_admin)

    def process_add_admin(message):
        try:
            new_id = int(message.text)
        except:
            bot.send_message(message.chat.id, "ID должен быть числом."); return
        if new_id == ADMIN_ID:
            bot.send_message(message.chat.id, "Это главный админ."); return
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO admins (user_id, added_by) VALUES (?,?)", (new_id, message.from_user.id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Админ {new_id} добавлен.")
        bot.send_message(new_id, "🔐 Вам выданы права админа Frime Skin.")
        log_action(message.from_user.id, 'add_admin', f'Added {new_id}')

    @bot.callback_query_handler(func=lambda call: call.data == 'remove_admin_menu')
    def remove_admin_menu_cb(call):
        bot.send_message(call.message.chat.id, "Введите ID админа для удаления:")
        bot.register_next_step_handler(call.message, process_remove_admin)

    def process_remove_admin(message):
        try:
            admin_id = int(message.text)
        except:
            bot.send_message(message.chat.id, "ID должен быть числом."); return
        if admin_id == ADMIN_ID:
            bot.send_message(message.chat.id, "Нельзя удалить главного админа."); return
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("DELETE FROM admins WHERE user_id=?", (admin_id,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Админ {admin_id} удалён.")
        bot.send_message(admin_id, "⚠️ Ваши права админа отозваны.")
        log_action(message.from_user.id, 'remove_admin', f'Removed {admin_id}')

    # ===== ДОБАВЛЕНИЕ СКИНМЕЙКЕРА ВРУЧНУЮ =====
    @bot.message_handler(func=lambda m: m.text == "➕ Добавить скинмейкера" and is_admin(m.from_user.id))
    def admin_add_maker_button(message):
        bot.send_message(message.chat.id, "Введите @username или ID:")
        bot.register_next_step_handler(message, process_new_maker_username)

    def process_new_maker_username(message):
        user_id, username = None, None
        txt = message.text.strip().lstrip('@')
        if txt.isdigit():
            user_id = int(txt)
        else:
            try:
                u = bot.get_chat(f"@{txt}")
                user_id = u.id
                username = u.username
            except:
                pass
        if not user_id:
            bot.send_message(message.chat.id, "Пользователь не найден.")
            return
        bot.temp_maker = {'user_id': user_id, 'username': username or ""}
        bot.send_message(message.chat.id, "Введите имя:")
        bot.register_next_step_handler(message, process_new_maker_name)

    def process_new_maker_name(message):
        bot.temp_maker['name'] = message.text
        bot.send_message(message.chat.id, "Введите описание:")
        bot.register_next_step_handler(message, process_new_maker_desc)

    def process_new_maker_desc(message):
        bot.temp_maker['desc'] = message.text
        bot.send_message(message.chat.id, "Введите минимальную цену:")
        bot.register_next_step_handler(message, process_new_maker_price_min)

    def process_new_maker_price_min(message):
        try:
            pmin = int(message.text)
            bot.temp_maker['price_min'] = pmin
            bot.send_message(message.chat.id, "Введите максимальную цену:")
            bot.register_next_step_handler(message, process_new_maker_price_max)
        except:
            bot.send_message(message.chat.id, "❌ Введите число."); return

    def process_new_maker_price_max(message):
        try:
            pmax = int(message.text)
            data = bot.temp_maker
            conn = sqlite3.connect('firme_skin.db')
            c = conn.cursor()
            c.execute('''INSERT INTO skin_makers (user_id, username, name, description, price, price_min, price_max)
                         VALUES (?,?,?,?,?,?,?)''',
                      (data['user_id'], data['username'], data['name'], data['desc'], pmax, data['price_min'], pmax))
            conn.commit()
            conn.close()
            bot.send_message(message.chat.id, "✅ Скинмейкер добавлен.")
            log_action(message.from_user.id, 'add_maker', f'User {data["user_id"]}')
        except:
            bot.send_message(message.chat.id, "❌ Введите число."); return

    # ===== РЕДАКТИРОВАНИЕ СКИНМЕЙКЕРА =====
    @bot.message_handler(func=lambda m: m.text == "🔧 Ред. скинмейкера" and is_admin(m.from_user.id))
    def admin_edit_maker_button(message):
        bot.send_message(message.chat.id, "Введите ID:")
        bot.register_next_step_handler(message, process_admin_edit_maker)

    def process_admin_edit_maker(message):
        try:
            maker_id = int(message.text)
        except:
            bot.send_message(message.chat.id, "ID должен быть числом."); return
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("SELECT * FROM skin_makers WHERE id=?", (maker_id,))
        maker = c.fetchone()
        conn.close()
        if not maker:
            bot.send_message(message.chat.id, "Скинмейкер не найден.")
            return
        text = f"🔧 ID{maker_id}\nИмя: {maker[3]}\nОписание: {maker[4]}\nЦена: {maker[5]}\nСтиль: {maker[17]}\nУслуги: {maker[8]}\nСтрана: {maker[29]}\nЭмодзи: {maker[28] or 'нет'}\nСсылка: {maker[31] or 'нет'}\nСроки: {maker[19]}–{maker[20]} дн.\nЗаказы: {maker[40] or maker[24]}\nСтаж: {maker[30] or 'авто'}\nАктивен: {'✅' if maker[12] else '❌'}\nТеневой: {'⚠️' if maker[22] else '✅'}"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("✏️ Имя", callback_data=f'adm_edit_name_{maker_id}'),
                   types.InlineKeyboardButton("✏️ Описание", callback_data=f'adm_edit_desc_{maker_id}'),
                   types.InlineKeyboardButton("✏️ Цена", callback_data=f'adm_edit_price_{maker_id}'),
                   types.InlineKeyboardButton("✏️ Стиль", callback_data=f'adm_edit_style_{maker_id}'),
                   types.InlineKeyboardButton("✏️ Услуги", callback_data=f'adm_edit_services_{maker_id}'),
                   types.InlineKeyboardButton("✏️ Страна", callback_data=f'adm_edit_country_{maker_id}'),
                   types.InlineKeyboardButton("✏️ Эмодзи", callback_data=f'adm_edit_emoji_{maker_id}'),
                   types.InlineKeyboardButton("✏️ Ссылка", callback_data=f'adm_edit_contact_{maker_id}'),
                   types.InlineKeyboardButton("✏️ Сроки", callback_data=f'adm_edit_delivery_{maker_id}'),
                   types.InlineKeyboardButton("✏️ Заказы", callback_data=f'adm_edit_orders_{maker_id}'),
                   types.InlineKeyboardButton("✏️ Стаж", callback_data=f'adm_edit_exp_{maker_id}'),
                   types.InlineKeyboardButton("🔄 Активность", callback_data=f'adm_toggle_active_{maker_id}'),
                   types.InlineKeyboardButton("🗑️ Удалить", callback_data=f'adm_delete_maker_{maker_id}'))
        bot.send_message(message.chat.id, text, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_name_'))
    def adm_edit_name_cb(call):
        mid = int(call.data.split('_')[3])
        bot.send_message(call.message.chat.id, "Введите новое имя:")
        bot.register_next_step_handler(call.message, lambda m, mid=mid: update_field('name', m.text, mid, m.chat.id))

    @bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_desc_'))
    def adm_edit_desc_cb(call):
        mid = int(call.data.split('_')[3])
        bot.send_message(call.message.chat.id, "Введите описание:")
        bot.register_next_step_handler(call.message, lambda m, mid=mid: update_field('description', m.text, mid, m.chat.id))

    @bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_price_'))
    def adm_edit_price_cb(call):
        mid = int(call.data.split('_')[3])
        bot.send_message(call.message.chat.id, "Введите цену:")
        bot.register_next_step_handler(call.message, lambda m, mid=mid: update_field('price', int(m.text) if m.text.isdigit() else None, mid, m.chat.id))

    @bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_style_'))
    def adm_edit_style_cb(call):
        mid = int(call.data.split('_')[3])
        markup = types.InlineKeyboardMarkup(row_width=2)
        for s in ['modern', 'colorful', 'realism', 'namemc', 'special']:
            markup.add(types.InlineKeyboardButton(s, callback_data=f'adm_set_style_{mid}_{s}'))
        bot.send_message(call.message.chat.id, "Выберите стиль:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('adm_set_style_'))
    def adm_set_style(call):
        _, _, mid, style = call.data.split('_')
        update_field('style', style, int(mid), call.message.chat.id, call=call)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_services_'))
    def adm_edit_services_cb(call):
        mid = int(call.data.split('_')[3])
        bot.send_message(call.message.chat.id, "Введите услуги:")
        bot.register_next_step_handler(call.message, lambda m, mid=mid: update_field('services', m.text, mid, m.chat.id))

    @bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_country_'))
    def adm_edit_country_cb(call):
        mid = int(call.data.split('_')[3])
        from config import countries, flags
        markup = types.InlineKeyboardMarkup(row_width=2)
        for code, name in countries.items():
            markup.add(types.InlineKeyboardButton(f"{flags[code]} {name}", callback_data=f'adm_set_country_{mid}_{code}'))
        bot.send_message(call.message.chat.id, "Выберите страну:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('adm_set_country_'))
    def adm_set_country(call):
        _, _, mid, code = call.data.split('_')
        update_field('country_code', code, int(mid), call.message.chat.id, call=call)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_emoji_'))
    def adm_edit_emoji_cb(call):
        mid = int(call.data.split('_')[3])
        bot.send_message(call.message.chat.id, "Отправьте эмодзи:")
        bot.register_next_step_handler(call.message, lambda m, mid=mid: update_field('custom_emoji', m.text.strip() if m.text.strip() != '-' else None, mid, m.chat.id))

    @bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_contact_'))
    def adm_edit_contact_cb(call):
        mid = int(call.data.split('_')[3])
        bot.send_message(call.message.chat.id, "Введите ссылку:")
        bot.register_next_step_handler(call.message, lambda m, mid=mid: update_field('contact_link', m.text.strip(), mid, m.chat.id))

    @bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_delivery_'))
    def adm_edit_delivery_cb(call):
        mid = int(call.data.split('_')[3])
        bot.send_message(call.message.chat.id, "Введите мин. срок:")
        bot.register_next_step_handler(call.message, lambda m, mid=mid: setattr(bot, 'tmp_dmin', int(m.text)) or bot.send_message(m.chat.id, "Введите макс. срок:") or bot.register_next_step_handler(m, lambda m2, mid=mid: update_delivery(mid, bot.tmp_dmin, int(m2.text), m2.chat.id)))

    def update_delivery(mid, dmin, dmax, chat_id):
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("UPDATE skin_makers SET delivery_min_days=?, delivery_max_days=? WHERE id=?", (dmin, dmax, mid))
        conn.commit()
        conn.close()
        bot.send_message(chat_id, "✅ Сроки обновлены.")

    def update_field(field, value, mid, chat_id, call=None):
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute(f"UPDATE skin_makers SET {field}=? WHERE id=?", (value, mid))
        conn.commit()
        conn.close()
        if call:
            bot.edit_message_text("✅ Обновлено.", call.message.chat.id, call.message.message_id)
        else:
            bot.send_message(chat_id, "✅ Обновлено.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_orders_'))
    def adm_edit_orders_cb(call):
        mid = int(call.data.split('_')[3])
        bot.send_message(call.message.chat.id, "Введите заказы (можно '500+'):")
        bot.register_next_step_handler(call.message, lambda m, mid=mid: update_orders(mid, m.text, m.chat.id))

    def update_orders(mid, val, chat_id):
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        if val.isdigit():
            c.execute("UPDATE skin_makers SET completed_orders=?, orders_confirmed=1, order_display=NULL WHERE id=?", (int(val), mid))
        else:
            c.execute("UPDATE skin_makers SET order_display=?, orders_confirmed=1 WHERE id=?", (val, mid))
            nums = re.findall(r'\d+', val)
            if nums:
                c.execute("UPDATE skin_makers SET completed_orders=? WHERE id=?", (int(nums[0]), mid))
        conn.commit()
        conn.close()
        bot.send_message(chat_id, f"✅ Заказы обновлены: {val}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_exp_'))
    def adm_edit_exp_cb(call):
        mid = int(call.data.split('_')[3])
        bot.send_message(call.message.chat.id, "Введите стаж:")
        bot.register_next_step_handler(call.message, lambda m, mid=mid: update_field('display_experience', m.text.strip(), mid, m.chat.id))

    @bot.callback_query_handler(func=lambda call: call.data.startswith('adm_toggle_active_'))
    def adm_toggle_active_cb(call):
        mid = int(call.data.split('_')[3])
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("SELECT is_active FROM skin_makers WHERE id=?", (mid,))
        state = c.fetchone()[0]
        c.execute("UPDATE skin_makers SET is_active=? WHERE id=?", (0 if state else 1, mid))
        conn.commit()
        conn.close()
        bot.send_message(call.message.chat.id, f"✅ {'Активирован' if not state else 'Деактивирован'}.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('adm_delete_maker_'))
    def adm_delete_maker_cb(call):
        mid = int(call.data.split('_')[3])
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("DELETE FROM skin_makers WHERE id=?", (mid,))
        conn.commit()
        conn.close()
        bot.send_message(call.message.chat.id, f"✅ Скинмейкер ID{mid} удалён.")

    # ===== ЛОГ =====
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
        text = "📝 Лог:\n\n" + "\n".join([f"{l[3][:19]} — {l[2]}" for l in logs])
        bot.send_message(message.chat.id, text[:4000])

    # ===== ПЕРЕСЧЁТ РЕЙТИНГА =====
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
        bot.send_message(message.chat.id, f"✅ Рейтинг пересчитан для {len(makers)} скинмейкеров.")

    # ===== ОЧИСТКА СТАРЫХ ЗАЯВОК =====
    @bot.message_handler(func=lambda m: m.text == "🗂️ Очистить старые заявки" and is_admin(m.from_user.id))
    def admin_clean_applications(message):
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("DELETE FROM applications WHERE status != 'pending'")
        deleted = c.rowcount
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Удалено {deleted} обработанных заявок.")

    # ===== ВЫХОД ИЗ АДМИНКИ =====
    @bot.message_handler(func=lambda m: m.text == "🔙 Выйти" and is_admin(m.from_user.id))
    def exit_admin(message):
        bot.send_message(message.chat.id, "Вы вышли из админ-панели.", reply_markup=main_menu_markup())

    # ===== УПРАВЛЕНИЕ ОЦЕНКАМИ (АДМИН) =====
    @bot.message_handler(func=lambda m: m.text == "⭐ Управление оценками" and is_admin(m.from_user.id))
    def admin_ratings_menu_button(message):
        bot.send_message(message.chat.id, "Введите ID скинмейкера для просмотра его оценок:")
        bot.register_next_step_handler(message, process_admin_ratings)

    def process_admin_ratings(message):
        try:
            maker_id = int(message.text)
        except:
            bot.send_message(message.chat.id, "ID должен быть числом."); return
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
        markup.add(types.InlineKeyboardButton("🗑️ Удалить оценку по ID", callback_data=f'delete_rating_menu_{maker_id}'),
                   types.InlineKeyboardButton("🔄 Пересчитать рейтинг", callback_data=f'recalc_rating_{maker_id}'))
        bot.send_message(message.chat.id, text, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('delete_rating_menu_'))
    def delete_rating_menu(call):
        maker_id = call.data.split('_')[3]
        bot.send_message(call.message.chat.id, "Введите ID оценки, которую нужно удалить:")
        bot.register_next_step_handler(call.message, process_delete_rating, maker_id)

    def process_delete_rating(message, maker_id):
        try:
            rating_id = int(message.text)
        except:
            bot.send_message(message.chat.id, "ID должен быть числом."); return
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("UPDATE ratings SET is_removed=1 WHERE id=? AND skin_maker_id=?", (rating_id, maker_id))
        c.execute("UPDATE skin_makers SET total_ratings=(SELECT COUNT(*) FROM ratings WHERE skin_maker_id=? AND is_removed=0), rating=COALESCE((SELECT AVG(rating) FROM ratings WHERE skin_maker_id=? AND is_removed=0), 5.0) WHERE id=?", (maker_id, maker_id, maker_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Оценка #{rating_id} удалена. Рейтинг пересчитан.")
        log_action(message.from_user.id, 'delete_rating', f'Rating {rating_id} of maker {maker_id}')

    @bot.callback_query_handler(func=lambda call: call.data.startswith('recalc_rating_'))
    def recalc_rating_cb(call):
        maker_id = int(call.data.split('_')[2])
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("UPDATE skin_makers SET total_ratings=(SELECT COUNT(*) FROM ratings WHERE skin_maker_id=? AND is_removed=0), rating=COALESCE((SELECT AVG(rating) FROM ratings WHERE skin_maker_id=? AND is_removed=0), 5.0) WHERE id=?", (maker_id, maker_id, maker_id))
        c.execute("SELECT rating, total_ratings FROM skin_makers WHERE id=?", (maker_id,))
        new_data = c.fetchone()
        conn.commit()
        conn.close()
        bot.send_message(call.message.chat.id, f"✅ Рейтинг пересчитан. Новый: {new_data[0]:.1f} (оценок: {new_data[1]})")

    # ===== ЗАПРОСЫ ПРАВОК =====
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
            markup.add(types.InlineKeyboardButton("✅ Подтвердить", callback_data=f'approve_edit_{r[0]}'),
                       types.InlineKeyboardButton("❌ Отклонить", callback_data=f'reject_edit_{r[0]}'))
            bot.send_message(message.chat.id, text, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('approve_edit_'))
    def approve_edit(call):
        req_id = int(call.data.split('_')[2])
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("SELECT * FROM edit_requests WHERE id=?", (req_id,))
        req = c.fetchone()
        if not req:
            bot.answer_callback_query(call.id, "Запрос не найден."); return
        text = req[3].lower()
        maker_id = req[1]
        import re
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
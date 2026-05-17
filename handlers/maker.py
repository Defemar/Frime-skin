import sqlite3
import json
import requests
import tempfile
import os
from datetime import datetime
import re
from telebot import types
from config import countries, flags
from utils.keyboards import main_menu_markup, apply_keyboard
from utils.helpers import is_blacklisted, notify_admins, notify_admins_with_markup

user_states = {}

def register_maker_handlers(bot):

    # ===================== ПРОФИЛЬ =====================
    @bot.message_handler(func=lambda m: m.text == "👤 Мой профиль")
    def profile_main(message):
        user_id = message.from_user.id
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("SELECT * FROM skin_makers WHERE user_id=?", (user_id,))
        maker = c.fetchone()
        conn.close()
        if not maker:
            bot.send_message(message.chat.id,
                             "Вы не зарегистрированы как скинмейкер. Подайте заявку или дождитесь её одобрения.")
            return
        if user_id not in user_states:
            user_states[user_id] = {}
        user_states[user_id]['maker_id'] = maker[0]

        text = "👤 Ваш профиль:\n\n"
        text += f"Имя: {maker[3]}\n"
        price_text = f"от {maker[5]} ₽" if maker[5] else "не указана"
        if maker[6] and maker[7]:
            price_text = f"от {maker[6]} до {maker[7]} ₽"
        text += f"Ценник: {price_text}\n"
        text += f"Стиль: {maker[17]}"
        if maker[18]: text += f"\n✨ {maker[18]}"
        text += f"\nСтрана: {countries.get(maker[29], maker[29])}\n"
        text += f"Эмодзи: {maker[28] or 'не задано'}\n"
        status_text = "🏖️ Отпуск" if maker[13] else ("⚠️ Перегружен до " + maker[26] if maker[26] else "Активен")
        text += f"Статус: {status_text}\n"
        order_text = maker[40] if len(maker) > 40 and maker[40] else f"{maker[24]} {'✅' if maker[25] else '~'}"
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

    # ===================== РЕДАКТИРОВАНИЕ ПРОФИЛЯ =====================
    @bot.callback_query_handler(func=lambda call: call.data == 'edit_profile')
    def edit_profile_cb(call):
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
        bot.send_message(call.message.chat.id, "Введите новое имя:")
        bot.register_next_step_handler(call.message, process_edit_name)

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
        bot.send_message(call.message.chat.id, "Введите новое описание:")
        bot.register_next_step_handler(call.message, process_edit_desc)

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
        for s in ['modern', 'colorful', 'realism', 'namemc', 'special']:
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
        bot.send_message(call.message.chat.id, "Введите услуги через запятую:")
        bot.register_next_step_handler(call.message, process_edit_services)

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
        bot.send_message(call.message.chat.id, "Отправьте новые фото (до 9, по одному, затем /done):")
        bot.register_next_step_handler(call.message, process_edit_photos)

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
        bot.send_message(call.message.chat.id, "Введите новую ссылку для заказа:")
        bot.register_next_step_handler(call.message, process_edit_contact)

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
        bot.send_message(call.message.chat.id, "Введите соцсети в формате:\nTelegram: ссылка\n...\nMax: ссылка\n(можно '-' для пропуска):")
        bot.register_next_step_handler(call.message, process_edit_social)

    def process_edit_social(message):
        user_id = message.from_user.id
        text = message.text.strip()
        socials = {'telegram': None, 'twitter': None, 'pinterest': None,
                   'tiktok': None, 'youtube': None, 'instagram': None,
                   'vk': None, 'max': None}
        if text != '-':
            pairs = text.replace('\n', ',').split(',')
            for pair in pairs:
                if ':' in pair:
                    key, val = pair.split(':', 1)
                    key = key.strip().lower(); val = val.strip()
                    if 'tg' in key or 'telegram' in key: socials['telegram'] = val
                    elif 'tw' in key or 'twitter' in key or 'x' in key: socials['twitter'] = val
                    elif 'pin' in key or 'pinterest' in key: socials['pinterest'] = val
                    elif 'tik' in key or 'tiktok' in key: socials['tiktok'] = val
                    elif 'you' in key or 'youtube' in key: socials['youtube'] = val
                    elif 'insta' in key or 'instagram' in key: socials['instagram'] = val
                    elif 'vk' in key: socials['vk'] = val
                    elif 'max' in key: socials['max'] = val
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute('''UPDATE skin_makers SET social_telegram=?, social_twitter=?, social_pinterest=?, social_tiktok=?,
                     social_youtube=?, social_instagram=?, social_vk=?, social_max=? WHERE user_id=?''',
                  (socials['telegram'], socials['twitter'], socials['pinterest'],
                   socials['tiktok'], socials['youtube'], socials['instagram'],
                   socials['vk'], socials['max'], user_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Соцсети обновлены.")

    @bot.callback_query_handler(func=lambda call: call.data == 'edit_emoji')
    def edit_emoji_cb(call):
        bot.send_message(call.message.chat.id, "Отправьте один эмодзи (или '-' чтобы убрать):")
        bot.register_next_step_handler(call.message, process_edit_emoji)

    def process_edit_emoji(message):
        user_id = message.from_user.id
        text = message.text.strip()
        emoji = None if text == '-' else text[0]
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
        bot.send_message(call.message.chat.id, "Введите минимальный срок (дней):")
        bot.register_next_step_handler(call.message, process_edit_delivery_min)

    def process_edit_delivery_min(message):
        try:
            dmin = int(message.text)
            if dmin < 1: raise ValueError
        except:
            bot.send_message(message.chat.id, "❌ Введите целое число >0:")
            bot.register_next_step_handler(message, process_edit_delivery_min)
            return
        bot.send_message(message.chat.id, "Введите максимальный срок (дней):")
        bot.register_next_step_handler(message, process_edit_delivery_max, dmin)

    def process_edit_delivery_max(message, dmin):
        try:
            dmax = int(message.text)
            if dmax < dmin: raise ValueError
        except:
            bot.send_message(message.chat.id, f"❌ Введите число ≥ {dmin}:")
            bot.register_next_step_handler(message, process_edit_delivery_max, dmin)
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
        bot.send_message(call.message.chat.id, "Введите новый стаж (например, '2 года'):")
        bot.register_next_step_handler(call.message, process_edit_exp)

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
        bot.send_message(call.message.chat.id, "Введите количество заказов (можно '500+'):")
        bot.register_next_step_handler(call.message, process_edit_orders)

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
        bot.send_message(call.message.chat.id, "Введите минимальную цену:")
        bot.register_next_step_handler(call.message, process_edit_price_min)

    def process_edit_price_min(message):
        try:
            pmin = int(message.text)
            user_id = message.from_user.id
            conn = sqlite3.connect('firme_skin.db')
            c = conn.cursor()
            c.execute("UPDATE skin_makers SET price_min=? WHERE user_id=?", (pmin, user_id))
            conn.commit()
            conn.close()
            bot.send_message(message.chat.id, "Введите максимальную цену:")
            bot.register_next_step_handler(message, process_edit_price_max, user_id)
        except:
            bot.send_message(message.chat.id, "❌ Введите число. Минимальная цена:")
            bot.register_next_step_handler(message, process_edit_price_min)

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
            bot.send_message(message.chat.id, "❌ Введите число. Максимальная цена:")
            bot.register_next_step_handler(message, process_edit_price_max, user_id)

    @bot.callback_query_handler(func=lambda call: call.data == 'toggle_vacation')
    def toggle_vacation_cb(call):
        user_id = call.from_user.id
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("SELECT is_vacation FROM skin_makers WHERE user_id=?", (user_id,))
        row = c.fetchone()
        if not row:
            bot.answer_callback_query(call.id, "Ошибка"); return
        new_state = 0 if row[0] else 1
        c.execute("UPDATE skin_makers SET is_vacation=? WHERE user_id=?", (new_state, user_id))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, f"Режим отпуска {'включён' if new_state else 'выключен'}.")

    @bot.callback_query_handler(func=lambda call: call.data == 'set_busy')
    def set_busy_cb(call):
        bot.send_message(call.message.chat.id, "Введите дату, до которой заняты (ГГГГ-ММ-ДД) или '-' для снятия:")
        bot.register_next_step_handler(call.message, process_busy_date)

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
            bot.answer_callback_query(call.id, "Ошибка"); return
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
            bot.answer_callback_query(call.id, "Вы не скинмейкер"); return
        bot.send_message(call.message.chat.id, "Опишите, что нужно изменить:")
        bot.register_next_step_handler(call.message, process_edit_request, maker[0])

    def process_edit_request(message, maker_id):
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("INSERT INTO edit_requests (skin_maker_id, field, new_value) VALUES (?,?,?)", (maker_id, 'custom', message.text))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "Запрос отправлен администратору.")
        notify_admins(bot, f"📩 Запрос правок от ID{maker_id}: {message.text}")

    # ===================== ПОДАЧА ЗАЯВКИ =====================
    @bot.message_handler(func=lambda m: m.text == "📝 Подать заявку")
    def apply_start(message):
        if is_blacklisted(message.from_user.id):
            bot.send_message(message.chat.id, "🚫 Вы заблокированы.")
            return
        user_id = message.from_user.id
        if user_id in user_states:
            del user_states[user_id]
        user_states[user_id] = {'photos': [], 'step': 'photo'}
        bot.send_message(message.chat.id,
                         "📸 Отправьте фото работ (можно до 9, по одному, затем /done)\n"
                         "❌ /cancel — отмена\n"
                         "🔗 Можете отправить прямую ссылку на .png/.jpg/.jpeg — бот скачает фото.",
                         reply_markup=apply_keyboard())
        bot.register_next_step_handler(message, process_apply_photo)

    def check_cancel(message):
        if message.text and message.text in ['/cancel', '❌ Отменить заявку']:
            uid = message.from_user.id
            if uid in user_states:
                del user_states[uid]
            bot.send_message(message.chat.id, "❌ Заявка отменена.", reply_markup=main_menu_markup())
            return True
        return False

    def process_apply_photo(message):
        if check_cancel(message):
            return
        user_id = message.from_user.id
        if message.content_type == 'photo':
            user_states[user_id]['photos'].append(message.photo[-1].file_id)
            bot.send_message(message.chat.id,
                             f"✅ Фото {len(user_states[user_id]['photos'])}/9 добавлено.",
                             reply_markup=apply_keyboard())
        elif message.text:
            if message.text.startswith('/done'):
                if not user_states[user_id]['photos']:
                    bot.send_message(message.chat.id, "❌ Отправьте хотя бы одно фото!")
                    bot.register_next_step_handler(message, process_apply_photo)
                    return
                user_states[user_id]['step'] = 'name'
                bot.send_message(message.chat.id, "✏️ Введите ваше имя (никнейм):",
                                 reply_markup=apply_keyboard())
                bot.register_next_step_handler(message, process_apply_name)
                return
            elif re.match(r'https?://\S+\.(png|jpg|jpeg)(\?\S*)?$', message.text, re.IGNORECASE):
                if len(user_states[user_id]['photos']) >= 9:
                    bot.send_message(message.chat.id, "⚠️ Максимум 9 фото. Отправьте /done.")
                    bot.register_next_step_handler(message, process_apply_photo)
                    return
                try:
                    response = requests.get(message.text, stream=True, timeout=10)
                    if response.status_code == 200:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                            tmp.write(response.content)
                            tmp_path = tmp.name
                        sent = bot.send_photo(message.chat.id, open(tmp_path, 'rb'))
                        file_id = sent.photo[-1].file_id
                        bot.delete_message(message.chat.id, sent.message_id)
                        os.unlink(tmp_path)
                        user_states[user_id]['photos'].append(file_id)
                        bot.send_message(message.chat.id,
                                         f"✅ Фото {len(user_states[user_id]['photos'])}/9 добавлено (из ссылки).",
                                         reply_markup=apply_keyboard())
                    else:
                        bot.send_message(message.chat.id, "❌ Не удалось загрузить фото по ссылке.")
                except Exception as e:
                    bot.send_message(message.chat.id, f"❌ Ошибка при загрузке фото: {e}")
            else:
                bot.send_message(message.chat.id, "📸 Отправьте фото, ссылку на изображение, /done или /cancel.",
                                 reply_markup=apply_keyboard())
        else:
            bot.send_message(message.chat.id, "📸 Отправьте фото, ссылку на изображение, /done или /cancel.",
                             reply_markup=apply_keyboard())
        bot.register_next_step_handler(message, process_apply_photo)

    def process_apply_name(message):
        if check_cancel(message):
            return
        user_id = message.from_user.id
        user_states[user_id]['name'] = message.text
        user_states[user_id]['step'] = 'description'
        bot.send_message(message.chat.id, "💬 Введите описание ваших услуг:", reply_markup=apply_keyboard())
        bot.register_next_step_handler(message, process_apply_description)

    def process_apply_description(message):
        if check_cancel(message):
            return
        user_id = message.from_user.id
        user_states[user_id]['description'] = message.text
        user_states[user_id]['step'] = 'price_min'
        bot.send_message(message.chat.id, "💲 Введите минимальную цену:", reply_markup=apply_keyboard())
        bot.register_next_step_handler(message, process_apply_price_min)

    def process_apply_price_min(message):
        if check_cancel(message):
            return
        try:
            pmin = int(message.text)
            user_id = message.from_user.id
            user_states[user_id]['price_min'] = pmin
            user_states[user_id]['step'] = 'price_max'
            bot.send_message(message.chat.id, "Введите максимальную цену:", reply_markup=apply_keyboard())
            bot.register_next_step_handler(message, process_apply_price_max)
        except ValueError:
            bot.send_message(message.chat.id, "❌ Введите целое число.", reply_markup=apply_keyboard())
            bot.register_next_step_handler(message, process_apply_price_min)

    def process_apply_price_max(message):
        if check_cancel(message):
            return
        try:
            pmax = int(message.text)
            user_id = message.from_user.id
            pmin = user_states[user_id].get('price_min', 0)
            if pmax < pmin:
                pmin, pmax = pmax, pmin
                user_states[user_id]['price_min'] = pmin
                bot.send_message(message.chat.id, "⚠️ Максимальная цена меньше минимальной. Значения поменяны местами.")
            user_states[user_id]['price_max'] = pmax
            user_states[user_id]['price'] = pmax
            user_states[user_id]['step'] = 'style'
            markup = types.InlineKeyboardMarkup(row_width=2)
            styles = ['modern', 'colorful', 'realism', 'namemc', 'special']
            for s in styles:
                markup.add(types.InlineKeyboardButton(s, callback_data=f'applystyle_{s}'))
            markup.add(types.InlineKeyboardButton("СВОЙ СТИЛЬ", callback_data='applystyle_custom'))
            markup.add(types.InlineKeyboardButton("✅ Готово", callback_data='applystyle_done'),
                       types.InlineKeyboardButton("❌ Отмена", callback_data='apply_cancel'))
            user_states[user_id]['selected_styles'] = []
            user_states[user_id]['custom_styles'] = []
            bot.send_message(message.chat.id, "🎨 Выберите стиль (можно несколько) или нажмите «СВОЙ СТИЛЬ»:", reply_markup=markup)
        except ValueError:
            bot.send_message(message.chat.id, "❌ Введите целое число.", reply_markup=apply_keyboard())
            bot.register_next_step_handler(message, process_apply_price_max)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('applystyle_'))
    def apply_style_select(call):
        uid = call.from_user.id
        if uid not in user_states or user_states[uid].get('step') != 'style':
            bot.answer_callback_query(call.id, "Ошибка: начните заявку заново.")
            return
        data = call.data
        if data == 'applystyle_done':
            selected = user_states[uid].get('selected_styles', [])
            custom = user_states[uid].get('custom_styles', [])
            if not selected and not custom:
                bot.answer_callback_query(call.id, "Выберите хотя бы один стиль!")
                return
            if 'namemc' in selected:
                allowed_set = {'namemc', 'special'}
                if set(selected) - allowed_set or custom:
                    bot.answer_callback_query(call.id, "NameMc можно сочетать только с special! Уберите другие стили.")
                    return
            bot.delete_message(call.message.chat.id, call.message.message_id)
            user_states[uid]['step'] = 'service'
            markup = types.InlineKeyboardMarkup(row_width=2)
            services = ['Скины', 'Модели', 'Текстуры', 'Рендер', '128x128', '256x256', '3D скины']
            for s in services:
                markup.add(types.InlineKeyboardButton(s, callback_data=f'applyservice_{s}'))
            markup.add(types.InlineKeyboardButton("✅ Готово", callback_data='applyservice_done'),
                       types.InlineKeyboardButton("❌ Отмена", callback_data='apply_cancel'))
            user_states[uid]['selected_services'] = []
            bot.send_message(call.message.chat.id, "🛠️ Выберите услуги:", reply_markup=markup)
        elif data == 'applystyle_custom':
            bot.answer_callback_query(call.id)
            msg = bot.send_message(call.message.chat.id, "Введите название вашего стиля (можно несколько слов через запятую):",
                                   reply_markup=apply_keyboard())
            bot.register_next_step_handler(msg, process_custom_style)
        else:
            style = data.split('_')[1]
            sel = user_states[uid].get('selected_styles', [])
            if style in sel:
                sel.remove(style)
            else:
                sel.append(style)
            user_states[uid]['selected_styles'] = sel
            custom = user_states[uid].get('custom_styles', [])
            all_selected = sel + custom
            bot.answer_callback_query(call.id, f"Выбрано: {', '.join(all_selected) if all_selected else 'ничего'}")

    def process_custom_style(message):
        if check_cancel(message):
            return
        uid = message.from_user.id
        if uid not in user_states or user_states[uid].get('step') != 'style':
            return
        custom_text = message.text.strip()
        if custom_text:
            if 'custom_styles' not in user_states[uid]:
                user_states[uid]['custom_styles'] = []
            user_states[uid]['custom_styles'].append(custom_text)
            bot.send_message(message.chat.id, f"✅ Стиль «{custom_text}» добавлен. Можете продолжить выбор или нажать «Готово».",
                             reply_markup=apply_keyboard())
            markup = types.InlineKeyboardMarkup(row_width=2)
            styles = ['modern', 'colorful', 'realism', 'namemc', 'special']
            for s in styles:
                markup.add(types.InlineKeyboardButton(s, callback_data=f'applystyle_{s}'))
            markup.add(types.InlineKeyboardButton("СВОЙ СТИЛЬ", callback_data='applystyle_custom'))
            markup.add(types.InlineKeyboardButton("✅ Готово", callback_data='applystyle_done'),
                       types.InlineKeyboardButton("❌ Отмена", callback_data='apply_cancel'))
            bot.send_message(message.chat.id, "🎨 Выберите ещё стиль или нажмите «Готово»:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ Введите название стиля.", reply_markup=apply_keyboard())
            bot.register_next_step_handler(message, process_custom_style)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('applyservice_'))
    def apply_service_select(call):
        uid = call.from_user.id
        if uid not in user_states or user_states[uid].get('step') != 'service':
            bot.answer_callback_query(call.id, "Ошибка: начните заявку заново.")
            return
        data = call.data
        if data == 'applyservice_done':
            if not user_states[uid].get('selected_services'):
                bot.answer_callback_query(call.id, "Выберите хотя бы одну услугу!")
                return
            bot.delete_message(call.message.chat.id, call.message.message_id)
            user_states[uid]['step'] = 'contact'
            bot.send_message(call.message.chat.id, "🔗 Введите ссылку для заказа (или '-'):", reply_markup=apply_keyboard())
            bot.register_next_step_handler(call.message, process_apply_contact)
        else:
            serv = data.split('_')[1]
            sel = user_states[uid].get('selected_services', [])
            if serv in sel:
                sel.remove(serv)
            else:
                sel.append(serv)
            user_states[uid]['selected_services'] = sel
            bot.answer_callback_query(call.id, f"Выбрано: {', '.join(sel)}")

    @bot.callback_query_handler(func=lambda call: call.data == 'apply_cancel')
    def apply_cancel_cb(call):
        uid = call.from_user.id
        if uid in user_states:
            del user_states[uid]
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "❌ Заявка отменена.", reply_markup=main_menu_markup())

    def process_apply_contact(message):
        if check_cancel(message):
            return
        uid = message.from_user.id
        user_states[uid]['contact_link'] = None if message.text == '-' else message.text.strip()
        user_states[uid]['step'] = 'delivery_min'
        bot.send_message(message.chat.id, "Введите минимальный срок (дней):", reply_markup=apply_keyboard())
        bot.register_next_step_handler(message, process_apply_delivery_min)

    def process_apply_delivery_min(message):
        if check_cancel(message):
            return
        try:
            dmin = int(message.text)
            if dmin < 1: raise ValueError
        except:
            bot.send_message(message.chat.id, "❌ Введите целое число >0:", reply_markup=apply_keyboard())
            bot.register_next_step_handler(message, process_apply_delivery_min)
            return
        uid = message.from_user.id
        user_states[uid]['delivery_min'] = dmin
        user_states[uid]['step'] = 'delivery_max'
        bot.send_message(message.chat.id, "Введите максимальный срок (дней):", reply_markup=apply_keyboard())
        bot.register_next_step_handler(message, process_apply_delivery_max)

    def process_apply_delivery_max(message):
        if check_cancel(message):
            return
        try:
            dmax = int(message.text)
            uid = message.from_user.id
            dmin = user_states[uid]['delivery_min']
            if dmax < dmin:
                dmin, dmax = dmax, dmin
                user_states[uid]['delivery_min'] = dmin
                bot.send_message(message.chat.id, "⚠️ Максимальный срок меньше минимального. Значения поменяны местами.")
        except:
            bot.send_message(message.chat.id, f"❌ Введите число ≥ {user_states[uid]['delivery_min']}:", reply_markup=apply_keyboard())
            bot.register_next_step_handler(message, process_apply_delivery_max)
            return
        uid = message.from_user.id
        user_states[uid]['delivery_max'] = dmax
        user_states[uid]['step'] = 'social'
        bot.send_message(message.chat.id,
                         "Теперь укажите ссылки на соцсети (можно пропустить, отправив '-').\n"
                         "Формат: Telegram: ссылка, Twitter: ссылка, ...\n"
                         "Можно одной строкой через запятую.",
                         reply_markup=apply_keyboard())
        bot.register_next_step_handler(message, process_apply_social)

    def process_apply_social(message):
        if check_cancel(message):
            return
        uid = message.from_user.id
        txt = message.text.strip()
        soc = {'telegram': None, 'twitter': None, 'pinterest': None, 'tiktok': None,
               'youtube': None, 'instagram': None, 'vk': None, 'max': None}
        if txt != '-':
            pairs = txt.replace('\n', ',').split(',')
            for pair in pairs:
                if ':' in pair:
                    k, v = pair.split(':', 1)
                    k = k.strip().lower(); v = v.strip()
                    if 'tg' in k or 'telegram' in k: soc['telegram'] = v
                    elif 'tw' in k or 'twitter' in k or 'x' in k: soc['twitter'] = v
                    elif 'pin' in k or 'pinterest' in k: soc['pinterest'] = v
                    elif 'tik' in k or 'tiktok' in k: soc['tiktok'] = v
                    elif 'you' in k or 'youtube' in k: soc['youtube'] = v
                    elif 'insta' in k or 'instagram' in k: soc['instagram'] = v
                    elif 'vk' in k: soc['vk'] = v
                    elif 'max' in k: soc['max'] = v
        data = user_states.pop(uid)
        final_styles = data.get('selected_styles', []) + data.get('custom_styles', [])
        final_styles = list(dict.fromkeys(final_styles))
        style_str = ', '.join(final_styles)

        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute('''INSERT INTO applications 
            (user_id, username, name, description, price, price_min, price_max,
             services, photo_ids, style, contact_link,
             social_telegram, social_twitter, social_pinterest, social_tiktok,
             social_youtube, social_instagram, social_vk, social_max,
             delivery_min_days, delivery_max_days)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (uid, message.from_user.username or "", data['name'], data['description'],
             data.get('price', 0), data.get('price_min', 0), data.get('price_max', 0),
             ', '.join(data.get('selected_services', [])), json.dumps(data.get('photos', [])),
             style_str, data.get('contact_link'),
             soc['telegram'], soc['twitter'], soc['pinterest'], soc['tiktok'],
             soc['youtube'], soc['instagram'], soc['vk'], soc['max'],
             data.get('delivery_min', 1), data.get('delivery_max', 3)))
        conn.commit()
        app_id = c.lastrowid
        conn.close()
        bot.send_message(message.chat.id, "✅ Заявка отправлена!", reply_markup=main_menu_markup())
        # Уведомление админов с кнопкой просмотра заявки
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📋 Просмотр заявки", callback_data=f'view_app_{app_id}'))
        notify_admins_with_markup(bot, f"📋 Новая заявка #{app_id} от @{message.from_user.username}", markup)
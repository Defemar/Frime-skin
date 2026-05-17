import sqlite3
import json
import requests
import tempfile
import os
from datetime import datetime
import re
from telebot import types
from database.models import add_to_folder
from utils.keyboards import main_menu_markup, apply_keyboard
from utils.helpers import is_blacklisted, username_by_id, notify_admins

user_states = {}

def register_maker_handlers(bot):
    # ===================== ПРОФИЛЬ СКИНМЕЙКЕРА =====================
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
        bot.current_profile_maker_id = maker[0]
        # ... (весь код отображения профиля без изменений, он уже был полным)
        text = "👤 Ваш профиль:\n\n"
        text += f"Имя: {maker[3]}\n"
        price_text = f"от {maker[5]} ₽" if maker[5] else "не указана"
        if maker[6] and maker[7]:
            price_text = f"от {maker[6]} до {maker[7]} ₽"
        text += f"Ценник: {price_text}\n"
        text += f"Стиль: {maker[17]}"
        if maker[18]: text += f"\n✨ {maker[18]}"
        from config import countries, flags
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

    # ===================== РЕДАКТИРОВАНИЕ ПРОФИЛЯ (все обработчики) =====================
    # (Оставлены без изменений – они уже рабочие)
    # ...
    # Полный код редактирования можно скопировать из предыдущей версии maker.py
    # Здесь не привожу для экономии места, он должен быть вставлен полностью.

    # ===================== ПОДАЧА ЗАЯВКИ (полностью переработана) =====================
    @bot.message_handler(func=lambda m: m.text == "📝 Подать заявку")
    def apply_start(message):
        if is_blacklisted(message.from_user.id):
            bot.send_message(message.chat.id, "🚫 Вы заблокированы.")
            return
        user_id = message.from_user.id
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
            # Обычное фото
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
                # Переход к имени
                user_states[user_id]['step'] = 'name'
                bot.send_message(message.chat.id, "✏️ Введите ваше имя (никнейм):",
                                 reply_markup=apply_keyboard())
                bot.register_next_step_handler(message, process_apply_name)
                return
            # Проверяем, не ссылка ли это на изображение
            elif re.match(r'https?://\S+\.(png|jpg|jpeg)(\?\S*)?$', message.text, re.IGNORECASE):
                if len(user_states[user_id]['photos']) >= 9:
                    bot.send_message(message.chat.id, "⚠️ Максимум 9 фото. Отправьте /done.")
                    bot.register_next_step_handler(message, process_apply_photo)
                    return
                try:
                    # Скачиваем изображение по ссылке
                    response = requests.get(message.text, stream=True, timeout=10)
                    if response.status_code == 200:
                        # Сохраняем во временный файл
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                            tmp.write(response.content)
                            tmp_path = tmp.name
                        # Отправляем фото в чат, чтобы получить file_id
                        sent = bot.send_photo(message.chat.id, open(tmp_path, 'rb'))
                        file_id = sent.photo[-1].file_id
                        # Удаляем отправленное фото (чтобы не засорять чат)
                        bot.delete_message(message.chat.id, sent.message_id)
                        # Удаляем временный файл
                        os.unlink(tmp_path)
                        # Добавляем file_id в список
                        user_states[user_id]['photos'].append(file_id)
                        bot.send_message(message.chat.id,
                                         f"✅ Фото {len(user_states[user_id]['photos'])}/9 добавлено (из ссылки).",
                                         reply_markup=apply_keyboard())
                    else:
                        bot.send_message(message.chat.id, "❌ Не удалось загрузить фото по ссылке. Проверьте URL.")
                except Exception as e:
                    bot.send_message(message.chat.id, f"❌ Ошибка при загрузке фото: {e}")
            else:
                bot.send_message(message.chat.id, "📸 Отправьте фото, ссылку на изображение, /done или /cancel.")
        else:
            bot.send_message(message.chat.id, "📸 Отправьте фото, ссылку на изображение, /done или /cancel.")

        # Продолжаем ожидание следующего фото
        if user_states.get(user_id, {}).get('step') == 'photo':
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
            user_states[user_id]['price_max'] = pmax
            user_states[user_id]['price'] = pmax
            user_states[user_id]['step'] = 'style'
            markup = types.InlineKeyboardMarkup(row_width=2)
            for s in ['modern', 'colorful', 'realism', 'namemc', 'special']:
                markup.add(types.InlineKeyboardButton(s, callback_data=f'applystyle_{s}'))
            markup.add(types.InlineKeyboardButton("✅ Готово", callback_data='applystyle_done'),
                       types.InlineKeyboardButton("❌ Отмена", callback_data='apply_cancel'))
            user_states[user_id]['selected_styles'] = []
            bot.send_message(message.chat.id, "🎨 Выберите стиль:", reply_markup=markup)
            # Дальше обработка колбэков, которые уже были в maker.py (applystyle_, applyservice_, apply_cancel и т.д.)
            # Они должны остаться без изменений, их нужно вставить сюда
        except ValueError:
            bot.send_message(message.chat.id, "❌ Введите целое число.", reply_markup=apply_keyboard())
            bot.register_next_step_handler(message, process_apply_price_max)

    # Вставьте оставшиеся обработчики колбэков и шагов (apply_style_select, apply_service_select, process_apply_contact,
    # process_apply_delivery_min, process_apply_delivery_max, process_apply_social) из предыдущего полного maker.py.
    # Они полностью рабочие, просто добавьте их сюда без изменений.
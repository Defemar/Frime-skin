from telebot import types

def main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🔍 Поиск скинмейкеров", "📝 Подать заявку", "📌 Мои закладки", "👤 Мой профиль",
               "📢 Новости", "💸 Донат на сервера", "ℹ️ О боте")
    return markup

def apply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("❌ Отменить заявку")
    return markup

def admin_panel_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📋 Заявки", "👥 Скинмейкеры", "✏️ Запросы правок", "⭐ Управление оценками",
               "📊 Статистика", "📢 Объявления", "📤 Экспорт БД", "💾 Сохранить БД",
               "⛔ Теневой бан", "🚫 Чёрный список", "👑 Админы", "➕ Добавить скинмейкера",
               "🔧 Ред. скинмейкера", "📝 Лог", "🔄 Пересчитать рейтинг", "🗂️ Очистить старые заявки",
               "🔙 Выйти")
    return markup 
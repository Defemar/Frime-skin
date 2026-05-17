import telebot
from config import TOKEN
from database.models import init_db
from handlers.user import register_user_handlers
from handlers.admin import register_admin_handlers
from handlers.maker import register_maker_handlers
import threading
import time
import sqlite3
from datetime import datetime

bot = telebot.TeleBot(TOKEN)
bot.current_makers = []
bot.current_filter = 'popular_formula'
bot.current_filter_value = None

init_db()
register_user_handlers(bot)
register_admin_handlers(bot)
register_maker_handlers(bot)

def check_achievements():
    while True:
        conn = sqlite3.connect('firme_skin.db')
        c = conn.cursor()
        c.execute("SELECT id, completed_orders, rating, registration_date FROM skin_makers")
        for m in c.fetchall():
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

threading.Thread(target=check_achievements, daemon=True).start()
print("Бот Frime Skin запущен...")
bot.polling(none_stop=True)
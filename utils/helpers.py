import sqlite3
from config import ADMIN_ID

def is_main_admin(user_id):
    return user_id == ADMIN_ID

def is_admin(user_id):
    if is_main_admin(user_id):
        return True
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins WHERE user_id=?", (user_id,))
    r = c.fetchone()
    conn.close()
    return r is not None

def is_blacklisted(user_id):
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM blacklist WHERE user_id=?", (user_id,))
    r = c.fetchone()
    conn.close()
    return r is not None

def username_by_id(bot, user_id):
    try:
        u = bot.get_chat(user_id)
        return f"@{u.username}" if u.username else f"ID{user_id}"
    except:
        return f"ID{user_id}"

def notify_admins(bot, text):
    bot.send_message(ADMIN_ID, text)
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins")
    for row in c.fetchall():
        try:
            bot.send_message(row[0], text)
        except:
            pass
    conn.close()

def notify_admins_with_markup(bot, text, markup):
    bot.send_message(ADMIN_ID, text, reply_markup=markup)
    conn = sqlite3.connect('firme_skin.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins")
    for row in c.fetchall():
        try:
            bot.send_message(row[0], text, reply_markup=markup)
        except:
            pass
    conn.close() 
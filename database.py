import sqlite3
import logging

logger = logging.getLogger(__name__)
conn = sqlite3.connect("capsule.db", check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        chat_id INTEGER
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        encrypted_message TEXT,
        open_time TEXT,
        status TEXT
    )''')
    # добавить chat_id если таблица уже существует
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN chat_id INTEGER")
        conn.commit()
    except:
        pass
    conn.commit()

def add_user(username, password, chat_id):
    cursor.execute("INSERT INTO users (username, password, chat_id) VALUES (?, ?, ?)", (username, password, chat_id))
    conn.commit()

def update_chat_id(username, chat_id):
    cursor.execute("UPDATE users SET chat_id=? WHERE username=?", (chat_id, username))
    conn.commit()

def get_user(username, password):
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return cursor.fetchone()

def get_chat_id(username):
    cursor.execute("SELECT chat_id FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    return result[0] if result else None

def user_exists(username):
    cursor.execute("SELECT 1 FROM users WHERE username=?", (username,))
    return cursor.fetchone() is not None

def save_message(sender, receiver, encrypted, open_time):
    cursor.execute("INSERT INTO messages (sender, receiver, encrypted_message, open_time, status) VALUES (?, ?, ?, ?, ?)",
                   (sender, receiver, encrypted, open_time, "pending"))
    conn.commit()

def get_available_capsules(receiver):
    cursor.execute("SELECT * FROM messages WHERE receiver=? AND status='pending'", (receiver,))
    return cursor.fetchall()

def get_all_pending_capsules():
    cursor.execute("SELECT * FROM messages WHERE status='pending'")
    return cursor.fetchall()

def mark_as_opened(msg_id):
    cursor.execute("UPDATE messages SET status='opened' WHERE id=?", (msg_id,))
    conn.commit()

def get_opened_capsules(receiver):
    cursor.execute("SELECT * FROM messages WHERE receiver=? AND status='opened'", (receiver,))
    return cursor.fetchall()
import sqlite3

conn = sqlite3.connect("capsule.db", check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        encrypted_message TEXT,
        open_time TEXT,
        status TEXT
    )''')
    conn.commit()

def add_user(username, password):
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()

def get_user(username, password):
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return cursor.fetchone()

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

def mark_as_opened(msg_id):
    cursor.execute("UPDATE messages SET status='opened' WHERE id=?", (msg_id,))
    conn.commit()

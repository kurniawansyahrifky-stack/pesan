import sqlite3

DB_NAME = "periodic_messages.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Tabel Utama untuk Menyimpan Multi Pesan (Pesan 1, Pesan 2, dst)
    c.execute('''CREATE TABLE IF NOT EXISTS periodic_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    chat_id INTEGER,
                    msg_text TEXT,
                    photo_path TEXT,
                    buttons_json TEXT,
                    start_hour INTEGER DEFAULT 0,
                    interval_type TEXT,
                    interval_val INTEGER,
                    status TEXT DEFAULT 'RUNNING',
                    last_msg_id INTEGER DEFAULT NULL
                )''')
    conn.commit()
    conn.close()

init_db()

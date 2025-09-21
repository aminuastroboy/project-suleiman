import sqlite3, json
from pathlib import Path
DB_PATH = Path(__file__).parent / "cbt_full.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no TEXT UNIQUE,
            name TEXT,
            email TEXT,
            password_hash TEXT,
            role TEXT,
            face_embedding TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            body TEXT,
            choice_a TEXT,
            choice_b TEXT,
            choice_c TEXT,
            choice_d TEXT,
            correct_choice TEXT,
            subject TEXT,
            difficulty TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            score INTEGER,
            total INTEGER,
            created_at TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER,
            question_id INTEGER,
            selected_choice TEXT,
            is_correct INTEGER
        )
    ''')
    conn.commit()
    # seed admin
    cur.execute("SELECT COUNT(*) as c FROM users WHERE role='admin'")
    if cur.fetchone()['c'] == 0:
        import hashlib
        h = hashlib.sha256('1234'.encode()).hexdigest()
        cur.execute("INSERT INTO users (reg_no,name,email,password_hash,role,face_embedding) VALUES (?,?,?,?,?,?)", 
                    ('ADMIN001','Administrator','admin@example.com',h,'admin',None))
        conn.commit()
    conn.close()

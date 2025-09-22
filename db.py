import sqlite3, hashlib
from pathlib import Path
DB_PATH = Path(__file__).parent / "cbt_full_hybrid.db"

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
    # seed admin if not exists
    cur.execute("SELECT COUNT(*) as c FROM users WHERE role='admin'")
    if cur.fetchone()['c'] == 0:
        h = hashlib.sha256('1234'.encode()).hexdigest()
        cur.execute("INSERT INTO users (reg_no, name, email, password_hash, role, face_embedding) VALUES (?,?,?,?,?,?)",
                    ('ADMIN001','Administrator','admin@example.com', h, 'admin', None))
        conn.commit()
    # seed students if not exists
    cur.execute("SELECT COUNT(*) as c FROM users WHERE role='student'")
    if cur.fetchone()['c'] == 0:
        sps = [
            ('S1001','Student One','s1001@example.com','pass1'),
            ('S1002','Student Two','s1002@example.com','pass2')
        ]
        for reg,name,email,pw in sps:
            h = hashlib.sha256(pw.encode()).hexdigest()
            cur.execute("INSERT OR IGNORE INTO users (reg_no,name,email,password_hash,role,face_embedding) VALUES (?,?,?,?,?,?)", (reg,name,email,h,'student', None))
        conn.commit()
    # seed questions
    cur.execute('SELECT COUNT(*) as c FROM questions')
    if cur.fetchone()['c'] == 0:
        qs = [
            ('Math Q1','What is 2+2?','1','2','3','4','D','Math','Easy'),
            ('Math Q2','What is 5*6?','11','30','20','25','B','Math','Easy'),
            ('Eng Q1','Choose synonym of happy','sad','joyful','angry','tired','B','English','Easy')
        ]
        for q in qs:
            cur.execute("INSERT INTO questions (title,body,choice_a,choice_b,choice_c,choice_d,correct_choice,subject,difficulty) VALUES (?,?,?,?,?,?,?,?,?)", q)
        conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()

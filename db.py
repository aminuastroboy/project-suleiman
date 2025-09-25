import sqlite3,bcrypt
from pathlib import Path
DB_PATH = Path(__file__).parent / "cbt_facepp_full.db"

def get_conn():
    conn=sqlite3.connect(DB_PATH)
    conn.row_factory=sqlite3.Row
    return conn

def init_db():
    conn=get_conn();cur=conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reg_no TEXT UNIQUE,
        name TEXT,
        email TEXT,
        password_hash BLOB,
        role TEXT,
        face_token TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS questions (
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
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        score INTEGER,
        total INTEGER,
        created_at TEXT
    )''')
    conn.commit()
    # seed admin
    cur.execute("SELECT COUNT(*) as c FROM users WHERE role='admin'")
    if cur.fetchone()['c']==0:
        h=bcrypt.hashpw("1234".encode(),bcrypt.gensalt())
        cur.execute("INSERT INTO users (reg_no,name,email,password_hash,role,face_token) VALUES (?,?,?,?,?,?)",("ADMIN001","Administrator","admin@example.com",h,"admin",None))
    # seed dummy students
    cur.execute("SELECT COUNT(*) as c FROM users WHERE role='student'")
    if cur.fetchone()['c']==0:
        sps=[("S1001","Student One","s1001@example.com","pass1"),("S1002","Student Two","s1002@example.com","pass2")]
        for reg,name,email,pw in sps:
            h=bcrypt.hashpw(pw.encode(),bcrypt.gensalt())
            cur.execute("INSERT OR IGNORE INTO users (reg_no,name,email,password_hash,role,face_token) VALUES (?,?,?,?,?,?)",(reg,name,email,h,"student",None))
    # seed questions
    cur.execute("SELECT COUNT(*) as c FROM questions")
    if cur.fetchone()['c']==0:
        qs=[("Math Q1","2+2?","1","2","3","4","D","Math","Easy"),
            ("Math Q2","5*6?","11","30","20","25","B","Math","Easy"),
            ("Eng Q1","Synonym of happy","sad","joyful","angry","tired","B","English","Easy")]
        for q in qs:
            cur.execute("INSERT INTO questions (title,body,choice_a,choice_b,choice_c,choice_d,correct_choice,subject,difficulty) VALUES (?,?,?,?,?,?,?,?,?)",q)
    conn.commit()
    conn.close()

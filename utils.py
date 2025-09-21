import sqlite3
from pathlib import Path
from PIL import Image, ImageOps
import numpy as np
import hashlib

DB_PATH = Path(__file__).parent / "cbt_app.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    return hash_password(password) == password_hash

def image_to_embedding(pil_image: Image.Image, size=(64,64)):
    img = ImageOps.fit(pil_image.convert('L'), size, method=Image.Resampling.LANCZOS)
    arr = np.asarray(img, dtype=np.float32)/255.0
    emb = arr.flatten()
    norm = np.linalg.norm(emb)+1e-8
    return (emb/norm).astype(np.float32)

def embedding_to_bytes(emb: np.ndarray) -> bytes:
    if emb is None:
        return None
    return emb.astype(np.float32).tobytes()

def bytes_to_embedding(b: bytes):
    if b is None:
        return None
    return np.frombuffer(b, dtype=np.float32)

def cosine_similarity(a,b):
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    denom = (np.linalg.norm(a)*np.linalg.norm(b)+1e-8)
    return float(np.dot(a,b)/denom)

def compare_embeddings(emb, stored_bytes, threshold=0.84):
    if stored_bytes is None or emb is None:
        return False,0.0
    db = bytes_to_embedding(stored_bytes)
    sim = cosine_similarity(emb,db)
    return (sim>=threshold), float(sim)

def init_db(seed=True):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT,
        reg_no TEXT UNIQUE,
        name TEXT,
        email TEXT,
        password_hash TEXT,
        face_embedding BLOB
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
    cur.execute('''CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attempt_id INTEGER,
        question_id INTEGER,
        selected_choice TEXT,
        is_correct INTEGER
    )''')
    conn.commit()
    if seed:
        cur.execute("SELECT COUNT(*) as c FROM users WHERE role='admin'")
        if cur.fetchone()['c']==0:
            cur.execute("INSERT INTO users (role, reg_no, name, email, password_hash, face_embedding) VALUES (?,?,?,?,?,?)",
                        ('admin','ADMIN001','Administrator','admin@example.com', hash_password('admin123'), None))
        cur.execute("SELECT COUNT(*) as c FROM users WHERE role='student'")
        if cur.fetchone()['c']==0:
            cur.execute("INSERT INTO users (role, reg_no, name, email, password_hash, face_embedding) VALUES (?,?,?,?,?,?)",
                        ('student','STU001','Alice','alice@example.com', hash_password('pass123'), None))
            cur.execute("INSERT INTO users (role, reg_no, name, email, password_hash, face_embedding) VALUES (?,?,?,?,?,?)",
                        ('student','STU002','Bob','bob@example.com', hash_password('pass123'), None))
        cur.execute("SELECT COUNT(*) as c FROM questions")
        if cur.fetchone()['c']==0:
            qlist=[
                ('Math Q1','What is 2 + 2?','1','2','3','4','D','Math','Easy'),
                ('AI Q1','Which language is most used for AI?','Java','C++','Python','Ruby','C','AI','Easy'),
                ('Geo Q1','Capital of Nigeria?','Lagos','Kano','Abuja','Port Harcourt','C','Geography','Easy')
            ]
            for q in qlist:
                cur.execute("INSERT INTO questions (title,body,choice_a,choice_b,choice_c,choice_d,correct_choice,subject,difficulty) VALUES (?,?,?,?,?,?,?,?,?)", q)
    conn.commit()
    conn.close()

def reset_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS answers")
    cur.execute("DROP TABLE IF EXISTS attempts")
    cur.execute("DROP TABLE IF EXISTS questions")
    cur.execute("DROP TABLE IF EXISTS users")
    conn.commit()
    conn.close()
    init_db(seed=True)

def add_student(reg_no,name,email,password_hash=None,face_bytes=None):
    conn = get_conn(); cur=conn.cursor()
    try:
        cur.execute("INSERT INTO users (role, reg_no, name, email, password_hash, face_embedding) VALUES (?,?,?,?,?,?)",
                    ('student',reg_no,name,email,password_hash,face_bytes))
        conn.commit(); return True
    except:
        return False
    finally:
        conn.close()

def get_user_by_reg(reg_no):
    conn = get_conn(); cur=conn.cursor()
    cur.execute("SELECT * FROM users WHERE reg_no=?",(reg_no,))
    row = cur.fetchone(); conn.close(); return row

def list_students():
    conn = get_conn(); cur=conn.cursor()
    cur.execute("SELECT * FROM users WHERE role='student'")
    rows = cur.fetchall(); conn.close(); return rows

def list_questions():
    conn = get_conn(); cur=conn.cursor()
    cur.execute("SELECT * FROM questions")
    rows = cur.fetchall(); conn.close(); return rows

def add_question(title,body,a,b,c,d,correct_choice,subject='General',difficulty='Medium'):
    conn = get_conn(); cur=conn.cursor()
    cur.execute("INSERT INTO questions (title,body,choice_a,choice_b,choice_c,choice_d,correct_choice,subject,difficulty) VALUES (?,?,?,?,?,?,?,?,?)",
                (title,body,a,b,c,d,correct_choice,subject,difficulty))
    conn.commit(); conn.close()

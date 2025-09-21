import sqlite3
from pathlib import Path
import hashlib
from PIL import Image, ImageOps
import numpy as np

DB_PATH = Path(__file__).parent / "cbt_extended.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def verify_password(pw: str, pw_hash: str) -> bool:
    if not pw_hash: return False
    return hash_password(pw) == pw_hash

def image_to_embedding(img: Image.Image, size=(64,64)):
    img = ImageOps.fit(img.convert('L'), size, method=Image.Resampling.LANCZOS)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    emb = arr.flatten()
    norm = np.linalg.norm(emb) + 1e-8
    return (emb / norm).astype(np.float32)

def embedding_to_bytes(emb: np.ndarray) -> bytes:
    return emb.astype(np.float32).tobytes()

def bytes_to_embedding(b: bytes) -> np.ndarray:
    if b is None:
        return None
    return np.frombuffer(b, dtype=np.float32)

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float32); b = np.asarray(b, dtype=np.float32)
    return float(np.dot(a,b) / (np.linalg.norm(a)*np.linalg.norm(b) + 1e-8))

def compare_embeddings(emb: np.ndarray, stored_bytes: bytes, threshold=0.85):
    if stored_bytes is None:
        return False, 0.0
    db = bytes_to_embedding(stored_bytes)
    sim = cosine_similarity(emb, db)
    return (sim >= threshold), sim

def init_db(seed_admin=True, seed_questions=True):
    conn = get_conn(); cur = conn.cursor()
    # users table: students + admins (role column)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            reg_no TEXT UNIQUE,
            name TEXT,
            email TEXT,
            password_hash TEXT,
            face_embedding BLOB
        )
    ''')
    # questions table
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
    # attempts + answers
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
    if seed_admin:
        cur.execute("SELECT COUNT(*) as c FROM users WHERE role='admin'")
        if cur.fetchone()['c'] == 0:
            admin_pw = hash_password('1234')
            cur.execute("INSERT INTO users (role, reg_no, name, email, password_hash, face_embedding) VALUES (?,?,?,?,?,?)",
                        ('admin', 'ADMIN001', 'Administrator', 'admin@example.com', admin_pw, None))
            conn.commit()
    # seed questions
    if seed_questions:
        cur.execute('SELECT COUNT(*) as c FROM questions')
        if cur.fetchone()['c'] == 0:
            sample = [
                ('Math Q1','What is 2+2?','1','2','3','4','D','Math','Easy'),
                ('Math Q2','What is 5*6?','11','30','20','25','B','Math','Easy'),
                ('Eng Q1','Choose synonym of happy','sad','joyful','angry','tired','B','English','Easy'),
            ]
            for s in sample:
                cur.execute("INSERT INTO questions (title,body,choice_a,choice_b,choice_c,choice_d,correct_choice,subject,difficulty) VALUES (?,?,?,?,?,?,?,?,?)", s)
            conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()

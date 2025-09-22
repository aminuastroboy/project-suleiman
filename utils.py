import hashlib, json
from db import get_conn
import numpy as np
from PIL import Image, ImageOps

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash

def get_user_by_reg(reg_no):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE reg_no=?', (reg_no,))
    row = cur.fetchone()
    conn.close()
    return row

def get_user_by_id(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE id=?', (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def add_student(reg_no, name, email, password, face_embedding_json=None):
    conn = get_conn()
    cur = conn.cursor()
    ph = hash_password(password) if password else None
    try:
        cur.execute('INSERT INTO users (reg_no,name,email,password_hash,role,face_embedding) VALUES (?,?,?,?,?,?)', (reg_no,name,email,ph,'student', face_embedding_json))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

def list_students():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE role='student'")
    rows = cur.fetchall()
    conn.close()
    return rows

def list_questions():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM questions')
    rows = cur.fetchall()
    conn.close()
    return rows

def add_question(title, body, a,b,c,d,correct,subject,difficulty):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT INTO questions (title,body,choice_a,choice_b,choice_c,choice_d,correct_choice,subject,difficulty) VALUES (?,?,?,?,?,?,?,?,?)', (title,body,a,b,c,d,correct,subject,difficulty))
    conn.commit()
    conn.close()
    return True

def update_user_face(reg_no, face_embedding_json):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('UPDATE users SET face_embedding=? WHERE reg_no=?', (face_embedding_json, reg_no))
    conn.commit()
    conn.close()

# Simple image embedding: grayscale 64x64 flattened normalized vector (prototype)
def image_to_embedding(img: Image.Image, size=(64,64)):
    img = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
    img = img.convert('L')
    arr = np.asarray(img, dtype=np.float32) / 255.0
    emb = arr.flatten()
    norm = np.linalg.norm(emb)
    if norm > 0:
        emb = emb / norm
    return emb

def compare_embeddings(emb1, emb2, threshold=0.90):
    emb1 = np.array(emb1, dtype=np.float32)
    emb2 = np.array(emb2, dtype=np.float32)
    if emb1.size == 0 or emb2.size == 0:
        return False
    sim = float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))
    return sim >= threshold

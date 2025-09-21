import hashlib, numpy as np, json
from db import get_conn
from PIL import Image, ImageOps

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash

def image_to_embedding(img: Image.Image) -> list:
    # convert to 64x64 grayscale flattened vector
    img = ImageOps.fit(img, (64,64)).convert('L')
    arr = np.array(img).astype('float32') / 255.0
    return arr.flatten().tolist()

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-8))

def get_user_by_reg(reg_no):
    conn = get_conn(); cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE reg_no=?',(reg_no,))
    row = cur.fetchone(); conn.close(); return row

def get_user_by_id(user_id):
    conn = get_conn(); cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE id=?',(user_id,))
    row = cur.fetchone(); conn.close(); return row

def add_student(reg_no, name, email, password=None, face_emb=None):
    conn = get_conn(); cur = conn.cursor()
    ph = hash_password(password) if password else None
    try:
        cur.execute('INSERT INTO users (reg_no,name,email,password_hash,role,face_embedding) VALUES (?,?,?,?,?,?)',
                    (reg_no,name,email,ph,'student', json.dumps(face_emb) if face_emb else None))
        conn.commit(); return True
    except Exception as e:
        return False
    finally: conn.close()

def list_students():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE role='student'")
    rows = cur.fetchall(); conn.close(); return rows

def list_questions():
    conn = get_conn(); cur = conn.cursor()
    cur.execute('SELECT * FROM questions')
    rows = cur.fetchall(); conn.close(); return rows

def add_question(title, body, a,b,c,d,correct,subject,difficulty):
    conn = get_conn(); cur = conn.cursor()
    cur.execute('INSERT INTO questions (title,body,choice_a,choice_b,choice_c,choice_d,correct_choice,subject,difficulty) VALUES (?,?,?,?,?,?,?,?,?)',
                (title,body,a,b,c,d,correct,subject,difficulty))
    conn.commit(); conn.close(); return True

import hashlib
from db import get_conn
import datetime

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

def add_student(reg_no, name, email, password):
    conn = get_conn()
    cur = conn.cursor()
    ph = hash_password(password)
    try:
        cur.execute('INSERT INTO users (reg_no,name,email,password_hash,role) VALUES (?,?,?,?,?)', (reg_no,name,email,ph,'student'))
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

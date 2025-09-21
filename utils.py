
import sqlite3

DB = "cbt_app.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (reg TEXT PRIMARY KEY, name TEXT, email TEXT, phone TEXT, password TEXT, face BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS questions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, a TEXT, b TEXT, c TEXT, d TEXT, correct TEXT)''')
    conn.commit()
    conn.close()

def add_student(reg, name, email, phone, password, face_bytes):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO students VALUES (?,?,?,?,?,?)", (reg, name, email, phone, password, face_bytes))
        conn.commit()
        ok = True
    except sqlite3.IntegrityError:
        ok = False
    conn.close()
    return ok

def get_student_by_reg(reg):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT reg,name,email,phone,password FROM students WHERE reg=?", (reg,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"reg": row[0], "name": row[1], "email": row[2], "phone": row[3], "password": row[4]}
    return None

def add_question(text,a,b,c,d,correct):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO questions (text,a,b,c,d,correct) VALUES (?,?,?,?,?,?)",
              (text,a,b,c,d,correct))
    conn.commit()
    conn.close()

def get_questions():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id,text,a,b,c,d,correct FROM questions")
    rows = c.fetchall()
    conn.close()
    return [{"id":r[0],"text":r[1],"a":r[2],"b":r[3],"c":r[4],"d":r[5],"correct":r[6]} for r in rows]

# Initialize DB on import
init_db()

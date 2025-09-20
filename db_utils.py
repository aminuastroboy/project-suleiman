import sqlite3

DB_FILE = "students.db"

def get_conn():
    return sqlite3.connect(DB_FILE)

def init_all():
    conn = get_conn()
    cur = conn.cursor()
    # students table
    cur.execute("""CREATE TABLE IF NOT EXISTS students (
        student_id TEXT PRIMARY KEY,
        name TEXT,
        email TEXT,
        password TEXT
    )""")
    # results table
    cur.execute("""CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        exam TEXT,
        score INTEGER
    )""")
    conn.commit()
    conn.close()

def add_student(student_id, name, email, password):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO students (student_id, name, email, password) VALUES (?, ?, ?, ?)",
                    (student_id, name, email, password))
        conn.commit()
        conn.close()
        return True, "Student registered successfully."
    except sqlite3.IntegrityError:
        return False, "Student ID already exists."

def get_student(student_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT student_id, name, email, password FROM students WHERE student_id=?", (student_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"student_id": row[0], "name": row[1], "email": row[2], "password": row[3]}
    return None

def add_result(student_id, exam, score):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO results (student_id, exam, score) VALUES (?, ?, ?)", (student_id, exam, score))
    conn.commit()
    conn.close()

def get_results(student_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT exam, score FROM results WHERE student_id=?", (student_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

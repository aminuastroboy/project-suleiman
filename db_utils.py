import sqlite3
import os
import pickle
from sqlite3 import Connection
from PIL import Image
import io

BASE_DIR = os.path.dirname(__file__)
STUD_DB = os.path.join(BASE_DIR, "students.db")
EXAM_DB = os.path.join(BASE_DIR, "exams.db")
RESULT_DB = os.path.join(BASE_DIR, "results.db")

# Biometric helper: optional import
try:
    import face_recognition
except Exception:
    face_recognition = None

def get_conn(path: str) -> Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_students_db():
    conn = get_conn(STUD_DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            password TEXT,
            face_encoding BLOB
        )
    ''')
    conn.commit()
    conn.close()

def init_exams_db():
    conn = get_conn(EXAM_DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            exam_id TEXT PRIMARY KEY,
            title TEXT,
            questions_json TEXT
        )
    ''')
    conn.commit()
    conn.close()

def init_results_db():
    conn = get_conn(RESULT_DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            exam_id TEXT,
            answers_json TEXT,
            score REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def init_all():
    init_students_db()
    init_exams_db()
    init_results_db()

# Students CRUD
def add_student(student_id, name, email, password, face_encoding_bytes=None):
    conn = get_conn(STUD_DB)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO students (student_id, name, email, password, face_encoding) VALUES (?,?,?,?,?)',
                  (student_id, name, email, password, face_encoding_bytes))
        conn.commit()
        return True, "Registered"
    except sqlite3.IntegrityError:
        return False, "Student ID already exists."
    finally:
        conn.close()

def get_student(student_id):
    conn = get_conn(STUD_DB)
    c = conn.cursor()
    c.execute('SELECT * FROM students WHERE student_id = ?', (student_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def biometric_login(image_bytes):
    if face_recognition is None:
        return False, "Biometric not available on this host."
    # load image
    arr = face_recognition.load_image_file(io.BytesIO(image_bytes))
    encodings = face_recognition.face_encodings(arr)
    if len(encodings) == 0:
        return False, "No face detected."
    probe = encodings[0]
    # iterate students
    conn = get_conn(STUD_DB)
    c = conn.cursor()
    c.execute('SELECT student_id, name, face_encoding FROM students WHERE face_encoding IS NOT NULL')
    rows = c.fetchall()
    conn.close()
    for r in rows:
        stored = r['face_encoding']
        if stored is None:
            continue
        stored_vec = pickle.loads(stored)
        matches = face_recognition.compare_faces([stored_vec], probe)
        if matches[0]:
            return True, {'student_id': r['student_id'], 'name': r['name']}
    return False, "No matching student found."

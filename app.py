import streamlit as st
import sqlite3
import hashlib
from PIL import Image
import utils

# ------------------------
# DB Setup
# ------------------------
conn = sqlite3.connect("cbt_full.db")
c = conn.cursor()

# Create tables if not exist
c.execute("""CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT,
    password TEXT,
    face_embedding BLOB
)""")

c.execute("""CREATE TABLE IF NOT EXISTS admins (
    admin_id TEXT PRIMARY KEY,
    password TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    correct TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT,
    question_id INTEGER,
    selected TEXT
)""")

conn.commit()

# Seed admin if not exist
c.execute("SELECT * FROM admins WHERE admin_id=?", ("ADMIN001",))
if not c.fetchone():
    c.execute("INSERT INTO admins VALUES (?,?)", ("ADMIN001", hashlib.sha256("1234".encode()).hexdigest()))
    conn.commit()

# ------------------------
# Helpers
# ------------------------
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def check_password(pw, hashed):
    return hash_password(pw) == hashed

def go_to(page):
    st.session_state.page = page
    st.rerun()

if "page" not in st.session_state:
    st.session_state.page = "home"

if "exam_active" not in st.session_state:
    st.session_state.exam_active = False

# ------------------------
# Pages
# ------------------------
def home():
    st.title("📘 CBT System")
    st.write("Welcome! Please choose an option:")
    if st.button("Student Login"): go_to("student_login")
    if st.button("Student Registration"): go_to("student_register")
    if st.button("Admin Login"): go_to("admin_login")

def student_register():
    st.header("📝 Student Registration")
    student_id = st.text_input("Student ID")
    name = st.text_input("Name")
    password = st.text_input("Password", type="password")

    cam_file = st.camera_input("Take a face photo (optional)")
    face_emb = None
    if cam_file:
        img = Image.open(cam_file)
        st.image(img, caption="Captured Face")
        face_emb = utils.image_to_embedding(img).tobytes()

    if st.button("Register"):
        if student_id and name and password:
            try:
                c.execute("INSERT INTO students VALUES (?,?,?,?)",
                          (student_id, name, hash_password(password), face_emb))
                conn.commit()
                st.success("Registration successful! Please login.")
                go_to("student_login")
            except:
                st.error("Student ID already exists.")
        else:
            st.error("Fill all required fields.")

def student_login():
    st.header("🎓 Student Login")
    student_id = st.text_input("Student ID")
    password = st.text_input("Password", type="password")
    cam_file = st.camera_input("Or login with face")

    if st.button("Login"):
        c.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
        student = c.fetchone()
        if not student:
            st.error("Student not found.")
            return

        _, name, stored_pw, stored_emb = student
        # password login
        if password and check_password(password, stored_pw):
            st.session_state.student_id = student_id
            st.session_state.student_name = name
            go_to("student_dashboard")
            return

        # face login
        if cam_file and stored_emb:
            img = Image.open(cam_file)
            emb = utils.image_to_embedding(img)
            if utils.compare_embeddings(emb, stored_emb):
                st.session_state.student_id = student_id
                st.session_state.student_name = name
                go_to("student_dashboard")
                return

        st.error("Login failed.")

def student_dashboard():
    st.header(f"🎓 Welcome, {st.session_state.student_name}")
    if st.button("Start Exam"):
        go_to("exam_auth")
    if st.button("Logout"):
        st.session_state.clear()
        go_to("home")

def exam_auth():
    st.subheader("Exam Verification")
    student_id = st.session_state.student_id
    c.execute("SELECT face_embedding,password FROM students WHERE student_id=?", (student_id,))
    row = c.fetchone()
    stored_emb, stored_pw = row

    cam_file = st.camera_input("Verify your face to start exam")
    if cam_file and stored_emb:
        img = Image.open(cam_file)
        emb = utils.image_to_embedding(img)
        if utils.compare_embeddings(emb, stored_emb):
            st.success("Face verified ✅")
            st.session_state.exam_active = True
            go_to("exam")
            return
        else:
            st.error("Face mismatch ❌")

    pw = st.text_input("Or re-enter password", type="password")
    if pw and check_password(pw, stored_pw):
        st.success("Password verified ✅")
        st.session_state.exam_active = True
        go_to("exam")

def exam():
    st.header("📝 Exam Started")
    c.execute("SELECT * FROM questions")
    questions = c.fetchall()
    if not questions:
        st.info("No questions yet. Please ask Admin to add some.")
        return

    if "q_index" not in st.session_state:
        st.session_state.q_index = 0

    q = questions[st.session_state.q_index]
    qid, text, a, b, copt, d, correct = q
    st.write(f"**Q{st.session_state.q_index+1}: {text}**")
    choice = st.radio("Options", [a,b,copt,d], key=f"q_{qid}")

    if st.button("Save & Next"):
        c.execute("INSERT INTO attempts (student_id, question_id, selected) VALUES (?,?,?)",
                  (st.session_state.student_id, qid, choice))
        conn.commit()
        st.session_state.q_index += 1
        if st.session_state.q_index >= len(questions):
            st.success("Exam submitted!")
            st.session_state.exam_active = False
            go_to("student_dashboard")
        else:
            st.rerun()

    if st.button("Previous") and st.session_state.q_index > 0:
        st.session_state.q_index -= 1
        st.rerun()

def admin_login():
    st.header("👨‍💼 Admin Login")
    admin_id = st.text_input("Admin ID")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        c.execute("SELECT * FROM admins WHERE admin_id=?", (admin_id,))
        admin = c.fetchone()
        if admin and check_password(password, admin[1]):
            st.session_state.admin_id = admin_id
            go_to("admin_dashboard")
        else:
            st.error("Invalid credentials.")

def admin_dashboard():
    st.header("👨‍💼 Admin Dashboard")
    q = st.text_input("Enter a question")
    a = st.text_input("Option A")
    b = st.text_input("Option B")
    copt = st.text_input("Option C")
    d = st.text_input("Option D")
    correct = st.selectbox("Correct Option", ["A","B","C","D"])

    if st.button("Add Question"):
        c.execute("INSERT INTO questions (question,option_a,option_b,option_c,option_d,correct) VALUES (?,?,?,?,?,?)",
                  (q,a,b,copt,d,correct))
        conn.commit()
        st.success("Question added.")

    if st.button("Logout"):
        st.session_state.clear()
        go_to("home")

# ------------------------
# Router
# ------------------------
if st.session_state.page == "home":
    home()
elif st.session_state.page == "student_register":
    student_register()
elif st.session_state.page == "student_login":
    student_login()
elif st.session_state.page == "student_dashboard":
    student_dashboard()
elif st.session_state.page == "exam_auth":
    exam_auth()
elif st.session_state.page == "exam":
    exam()
elif st.session_state.page == "admin_login":
    admin_login()
elif st.session_state.page == "admin_dashboard":
    admin_dashboard()

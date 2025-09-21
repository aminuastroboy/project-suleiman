
import streamlit as st
import utils
import datetime
from PIL import Image
import numpy as np

st.set_page_config(page_title="CBT WebApp", layout="wide")
utils.init_db()

# --- State ---
if "user" not in st.session_state:
    st.session_state.user = None
if "exam" not in st.session_state:
    st.session_state.exam = {"q_index":0,"score":0,"answers":{},"finished":False}

# --- Helper ---
def login_user(user):
    st.session_state.user = dict(user)

def logout_user():
    st.session_state.user = None
    st.session_state.exam = {"q_index":0,"score":0,"answers":{},"finished":False}

# --- Exam ---
def run_exam():
    conn = utils.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM questions")
    questions = cur.fetchall()
    conn.close()

    if not questions:
        st.warning("No questions found. Contact Admin.")
        return

    q_index = st.session_state.exam["q_index"]
    if q_index >= len(questions):
        st.success(f"Exam Finished! Score: {st.session_state.exam['score']}/{len(questions)}")
        if st.button("Back to Dashboard"):
            st.session_state.exam = {"q_index":0,"score":0,"answers":{},"finished":False}
        return

    q = questions[q_index]
    st.subheader(f"Q{q_index+1}: {q['body']}")
    options = {"A":q["choice_a"],"B":q["choice_b"],"C":q["choice_c"],"D":q["choice_d"]}
    choice = st.radio("Options:", list(options.values()), key=f"q{q['id']}")
    if st.button("Next ➡️"):
        # record
        correct_opt = {"A":q["choice_a"],"B":q["choice_b"],"C":q["choice_c"],"D":q["choice_d"]}[q["correct_choice"]]
        st.session_state.exam["answers"][q["id"]] = choice
        if choice == correct_opt:
            st.session_state.exam["score"] += 1
        st.session_state.exam["q_index"] += 1
        st.experimental_rerun()

# --- Admin Dashboard ---
def admin_dashboard():
    st.subheader("Admin Dashboard")
    tab1, tab2 = st.tabs(["Students","Questions"])
    with tab1:
        st.write("Registered Students:")
        for s in utils.list_students():
            st.write(dict(s))
    with tab2:
        st.write("Questions:")
        for q in utils.list_questions():
            st.write(dict(q))
        with st.expander("Add New Question"):
            title = st.text_input("Title")
            body = st.text_area("Body")
            a = st.text_input("Choice A")
            b = st.text_input("Choice B")
            c = st.text_input("Choice C")
            d = st.text_input("Choice D")
            correct = st.selectbox("Correct Choice",["A","B","C","D"])
            subj = st.text_input("Subject","General")
            diff = st.selectbox("Difficulty",["Easy","Medium","Hard"])
            if st.button("Save Question"):
                utils.add_question(title,body,a,b,c,d,correct,subj,diff)
                st.success("Question added")
                st.experimental_rerun()

# --- Student Dashboard ---
def student_dashboard():
    st.subheader(f"Welcome {st.session_state.user['name']}")
    if st.button("Start Exam"):
        run_exam()
    else:
        run_exam()

# --- Pages ---
menu = ["Home","Login","Register"]
if st.session_state.user:
    if st.session_state.user["role"]=="admin":
        menu=["Admin Dashboard","Logout"]
    else:
        menu=["Student Dashboard","Logout"]
choice = st.sidebar.selectbox("Menu", menu)

if choice=="Home":
    st.title("Computer Based Test System")
    st.info("Please login or register.")
elif choice=="Login":
    st.subheader("Login")
    reg = st.text_input("Reg No")
    pw = st.text_input("Password", type="password")
    face = st.file_uploader("Or upload face image (JPEG/PNG)", type=["jpg","jpeg","png"])
    if st.button("Login"):
        user = utils.get_user_by_reg(reg)
        if user:
            # Password
            if pw and utils.verify_password(pw, user["password_hash"]):
                st.success("Login successful (password)")
                login_user(user)
                st.experimental_rerun()
            # Face
            elif face:
                img = Image.open(face)
                emb = utils.image_to_embedding(img)
                ok, sim = utils.compare_embeddings(emb, user["face_embedding"])
                if ok:
                    st.success(f"Login successful (face match {sim:.2f})")
                    login_user(user)
                    st.experimental_rerun()
                else:
                    st.error("Face did not match")
            else:
                st.error("Invalid credentials")
        else:
            st.error("User not found")
elif choice=="Register":
    st.subheader("Register Student")
    reg = st.text_input("Reg No")
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    pw = st.text_input("Password", type="password")
    face = st.file_uploader("Upload face image", type=["jpg","jpeg","png"])
    if st.button("Register"):
        if not (reg and name and email and pw and face):
            st.error("All fields required")
        else:
            img = Image.open(face)
            emb = utils.image_to_embedding(img)
            fb = utils.embedding_to_bytes(emb)
            ok = utils.add_student(reg,name,email,utils.hash_password(pw),fb)
            if ok:
                st.success("Registration successful. Please login.")
            else:
                st.error("Registration failed (maybe reg no exists)")
elif choice=="Admin Dashboard":
    admin_dashboard()
elif choice=="Student Dashboard":
    student_dashboard()
elif choice=="Logout":
    logout_user()
    st.success("Logged out")
    st.experimental_rerun()

# app.py
import streamlit as st
from PIL import Image
import io, zipfile
import utils

# Initialize DB
utils.init_db()

if "page" not in st.session_state:
    st.session_state["page"] = "home"
if "user" not in st.session_state:
    st.session_state["user"] = None

# ---------- NAVIGATION ----------
def go_to(page):
    st.session_state["page"] = page

# ---------- HOME ----------
if st.session_state["page"] == "home":
    st.title("CBT WebApp with Biometrics")
    if st.button("Login as Admin"):
        go_to("admin_login")
    if st.button("Login as Student"):
        go_to("student_login")
    if st.button("Register as Student"):
        go_to("student_register")

# ---------- ADMIN LOGIN ----------
elif st.session_state["page"] == "admin_login":
    st.title("Admin Login")
    reg = st.text_input("Admin ID")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        user = utils.get_user_by_reg(reg)
        if user and user[6] == pw and user[7] == "admin":
            st.session_state["user"] = user
            go_to("admin_dashboard")
            st.experimental_rerun()
        else:
            st.error("Invalid admin credentials")

# ---------- ADMIN DASHBOARD ----------
elif st.session_state["page"] == "admin_dashboard":
    st.title("Admin Dashboard")

    if st.button("🔄 Reset Database"):
        utils.init_db()
        st.success("Database reset & reseeded!")

    # 📦 Download ZIP
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for fname in ["app.py", "utils.py", "requirements.txt", "cbt_app.db"]:
            try:
                z.write(fname)
            except:
                pass
    st.download_button(
        "📦 Download Full App (ZIP)",
        buf.getvalue(),
        file_name="cbt_app_full.zip",
        mime="application/zip"
    )

    st.subheader("Students")
    students = utils.get_all_students()
    for s in students:
        st.write(f"{s[1]} - {s[2]} ({s[3]})")

    st.subheader("Questions")
    questions = utils.get_all_questions()
    for q in questions:
        st.write(f"Q{q[0]}: {q[1]}")

# ---------- STUDENT REGISTER ----------
elif st.session_state["page"] == "student_register":
    st.title("Student Registration")
    reg = st.text_input("Reg No")
    name = st.text_input("Name")
    email = st.text_input("Email")
    ph = st.text_input("Phone")
    pw = st.text_input("Password", type="password")
    photo = st.camera_input("Capture Face") or st.file_uploader("Upload Face", type=["png","jpg","jpeg"])

    if st.button("Register"):
        if photo:
            img = Image.open(photo)
            emb = utils.image_to_embedding(img)
            face_bytes = utils.embedding_to_bytes(emb)
            ok = utils.add_student(reg, name, email, ph, pw, face_bytes)
            if ok:
                st.success("Registration successful")
                go_to("student_login")
                st.experimental_rerun()
            else:
                st.error("Registration failed (maybe reg no exists?)")
        else:
            st.error("Face required")

# ---------- STUDENT LOGIN ----------
elif st.session_state["page"] == "student_login":
    st.title("Student Login")
    reg = st.text_input("Reg No")
    pw = st.text_input("Password", type="password")
    photo = st.camera_input("Or Face Login")

    if st.button("Login"):
        user = utils.get_user_by_reg(reg)
        if user and user[7] == "student":
            # password
            if pw and pw == user[6]:
                st.session_state["user"] = user
                go_to("student_dashboard")
                st.experimental_rerun()
            # face
            elif photo:
                img = Image.open(photo)
                emb = utils.image_to_embedding(img)
                stored = utils.bytes_to_embedding(user[5])
                if utils.cosine_sim(emb, stored) > 0.8:
                    st.session_state["user"] = user
                    go_to("student_dashboard")
                    st.experimental_rerun()
                else:
                    st.error("Face mismatch")
            else:
                st.error("Invalid login")
        else:
            st.error("Student not found")

# ---------- STUDENT DASHBOARD ----------
elif st.session_state["page"] == "student_dashboard":
    st.title("Student Dashboard")
    st.write(f"Welcome {st.session_state['user'][2]}")

    if st.button("Start Exam"):
        st.session_state["q_index"] = 0
        st.session_state["answers"] = {}
        go_to("exam")
        st.experimental_rerun()

# ---------- EXAM ----------
elif st.session_state["page"] == "exam":
    qs = utils.get_all_questions()
    idx = st.session_state.get("q_index", 0)

    if idx < len(qs):
        q = qs[idx]
        st.subheader(f"Q{idx+1}: {q[1]}")
        choice = st.radio("Options", [("a",q[2]),("b",q[3]),("c",q[4]),("d",q[5])],
                          index=None,key=f"q{idx}")
        if st.button("Next"):
            if choice:
                st.session_state["answers"][q[0]] = choice[0]
                st.session_state["q_index"] = idx+1
                st.experimental_rerun()
            else:
                st.error("Please select an answer")
    else:
        # scoring
        score = 0
        for q in qs:
            qid, correct = q[0], q[6]
            ans = st.session_state["answers"].get(qid)
            if ans == correct: score += 1
        st.success(f"Exam finished! Score: {score}/{len(qs)}")
        go_to("student_dashboard")

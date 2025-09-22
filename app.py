import streamlit as st
import sqlite3, hashlib, json, numpy as np
from PIL import Image, ImageOps
import datetime
from db import init_db, get_conn
import utils

# Initialize DB
init_db()

st.set_page_config(page_title="CBT WebApp (Biometric)", layout="wide")

# Ensure session state slot
if "user" not in st.session_state:
    st.session_state.user = None

def login_user(reg_no, password=None, photo=None):
    row = utils.get_user_by_reg(reg_no)
    if not row:
        return None
    # check password
    if password and row["password_hash"]:
        if utils.verify_password(password, row["password_hash"]):
            return row
    # check photo embedding
    if photo and row["face_embedding"]:
        try:
            pil = Image.open(photo)
            emb_new = utils.image_to_embedding(pil)
            emb_old = np.array(json.loads(row["face_embedding"]))
            if utils.compare_embeddings(emb_new, emb_old):
                return row
        except Exception as e:
            st.error("Error processing photo for login: " + str(e))
    return None

def register_user(reg_no, name, email, password, photo):
    face_json = None
    if photo is not None:
        try:
            pil = Image.open(photo)
            emb = utils.image_to_embedding(pil)
            face_json = json.dumps(emb.tolist())
        except Exception as e:
            st.error("Could not process face image: " + str(e))
            return False
    ok = utils.add_student(reg_no, name, email, password, face_json)
    return ok

# Pages
def admin_dashboard():
    st.title("Admin Dashboard (Biometric)")
    st.write("Welcome, Admin!")
    tab1, tab2, tab3 = st.tabs(["Manage Students", "Question Bank", "Bulk Face Upload"])
    with tab1:
        st.subheader("Register New Student")
        reg = st.text_input("Reg No", key="adm_reg")
        name = st.text_input("Name", key="adm_name")
        email = st.text_input("Email", key="adm_email")
        pw = st.text_input("Password", type="password", key="adm_pw")
        photo = st.file_uploader("Upload Face Photo (optional)", type=["jpg","png"], key="adm_photo")
        if st.button("Register Student", key="adm_register"):
            img = photo if photo else None
            if register_user(reg, name, email, pw, img):
                st.success("Student registered!")
                st.rerun()
            else:
                st.error("Reg No already exists or face processing failed")
        st.subheader("All Students")
        for r in utils.list_students():
            st.write(dict(r))
            # admin can upload face for existing student
            if st.button(f"Upload face for {r['reg_no']}", key=f"upl_{r['reg_no']}"):
                uploaded = st.file_uploader(f"Select face image for {r['reg_no']}", type=["jpg","png"], key=f"file_{r['reg_no']}")
                if uploaded:
                    try:
                        pil = Image.open(uploaded)
                        emb = utils.image_to_embedding(pil)
                        utils.update_user_face(r['reg_no'], json.dumps(emb.tolist()))
                        st.success(f"Face embedding saved for {r['reg_no']}")
                        st.rerun()
                    except Exception as e:
                        st.error("Failed to process image: " + str(e))
    with tab2:
        st.subheader("Add Question")
        title = st.text_input("Title", key="q_title")
        body = st.text_area("Body", key="q_body")
        ca = st.text_input("Choice A", key="q_a")
        cb = st.text_input("Choice B", key="q_b")
        cc = st.text_input("Choice C", key="q_c")
        cd = st.text_input("Choice D", key="q_d")
        correct = st.selectbox("Correct Choice", ["A","B","C","D"], key="q_correct")
        subj = st.text_input("Subject", key="q_subj")
        diff = st.selectbox("Difficulty", ["Easy","Medium","Hard"], key="q_diff")
        if st.button("Save Question", key="q_save"):
            utils.add_question(title, body, ca, cb, cc, cd, correct, subj, diff)
            st.success("Question added")
        st.subheader("All Questions")
        for q in utils.list_questions():
            st.write(dict(q))
    with tab3:
        st.subheader("Bulk Face Upload (ZIP of images named by reg_no)")
        st.write("Upload a ZIP file containing images named like S1001.jpg, S1002.png etc. Admin will map by filename to student reg_no and save embeddings.")
        zip_file = st.file_uploader("Upload ZIP", type=["zip"], key="bulkzip")
        if st.button("Process ZIP"):
            if not zip_file:
                st.error("Please upload a zip file first.")
            else:
                import zipfile, io, os
                z = zipfile.ZipFile(io.BytesIO(zip_file.read()))
                count = 0
                for name in z.namelist():
                    base = os.path.basename(name)
                    reg_no, ext = os.path.splitext(base)
                    if not reg_no:
                        continue
                    try:
                        data = z.read(name)
                        pil = Image.open(io.BytesIO(data))
                        emb = utils.image_to_embedding(pil)
                        utils.update_user_face(reg_no, json.dumps(emb.tolist()))
                        count += 1
                    except Exception as e:
                        continue
                st.success(f"Processed {count} images and updated embeddings where reg_no matched.")

def student_dashboard(user):
    st.title("Student Dashboard (Biometric)")
    st.write(f"Welcome {user['name']} ({user['reg_no']})")
    st.subheader("Take Test")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM questions')
    qs = cur.fetchall()
    conn.close()
    if not qs:
        st.info("No questions in bank yet.")
        return
    score = 0
    total = len(qs)
    answers = []
    with st.form("test_form"):
        for q in qs:
            st.write(f"**{q['title']}** — {q['body']}")
            ans = st.radio(f"Q{q['id']}", ["A","B","C","D"], key=f"q{q['id']}")
            answers.append((q, ans))
        if st.form_submit_button("Submit Test"):
            conn = get_conn()
            cur = conn.cursor()
            for q, ans in answers:
                if ans == q["correct_choice"]:
                    score += 1
            cur.execute("INSERT INTO attempts (user_id,score,total,created_at) VALUES (?,?,?,?)",
                        (user["id"], score, total, str(datetime.datetime.now())))
            conn.commit()
            conn.close()
            st.success(f"Score: {score}/{total}")
            st.rerun()

# Routing
if st.session_state.user:
    if st.session_state.user["role"] == "admin":
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()
        admin_dashboard()
    else:
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()
        student_dashboard(st.session_state.user)
else:
    st.title("CBT Login / Register (Biometric available)")
    choice = st.radio("Role", ["Admin", "Student"])
    if choice == "Admin":
        reg = st.text_input("Admin Reg No", key="login_admin_reg")
        pw = st.text_input("Password", type="password", key="login_admin_pw")
        if st.button("Login as Admin", key="login_admin_btn"):
            row = utils.get_user_by_reg(reg)
            if row and row['role'] == 'admin' and utils.verify_password(pw, row['password_hash']):
                st.session_state.user = row
                st.rerun()
            else:
                st.error("Invalid admin credentials")
    else:
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            reg = st.text_input("Reg No", key="stu_login_reg")
            pw = st.text_input("Password (leave blank to use face)", type="password", key="stu_login_pw")
            st.write("Or use your camera below to login with face (if registered)")
            cam = st.camera_input("Take a photo for login (optional)", key="login_cam")
            img = Image.open(cam) if cam else None
            if st.button("Login as Student", key="login_student_btn"):
                row = None
                if pw:
                    row = utils.get_user_by_reg(reg)
                    if row and row['role']=='student' and utils.verify_password(pw, row['password_hash']):
                        st.session_state.user = row
                        st.success("Student logged in via password")
                        st.rerun()
                    else:
                        st.error('Invalid password')
                else:
                    # try face
                    row = utils.get_user_by_reg(reg)
                    if row and row['role']=='student' and row['face_embedding']:
                        if cam:
                            try:
                                emb_new = utils.image_to_embedding(Image.open(cam))
                                emb_old = np.array(json.loads(row['face_embedding']))
                                if utils.compare_embeddings(emb_new, emb_old):
                                    st.session_state.user = row
                                    st.success("Student logged in via face")
                                    st.rerun()
                                else:
                                    st.error("Face did not match.")
                            except Exception as e:
                                st.error("Error processing face: " + str(e))
                        else:
                            st.error("Take a photo with your camera to login via face.")
                    else:
                        st.error("No face registered for this user or reg_no not found.")
        with tab2:
            reg = st.text_input("Reg No (new)", key="stu_reg")
            name = st.text_input("Name", key="stu_name")
            email = st.text_input("Email", key="stu_email")
            pw = st.text_input("Password (optional)", type="password", key="stu_pw")
            st.write("You can optionally register a face via your camera below (recommended for biometric login)")
            cam = st.camera_input("Take a photo for registration (optional)", key="reg_cam")
            img = Image.open(cam) if cam else None
            if st.button("Register", key="register_student_btn"):
                if not reg or not name:
                    st.error("Reg No and Name are required.")
                else:
                    if register_user(reg, name, email, pw, cam):
                        st.success("Registered!")
                    else:
                        st.error("Reg No already exists or face could not be processed.")

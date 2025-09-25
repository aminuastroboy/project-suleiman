import streamlit as st
import bcrypt, hashlib
from PIL import Image
from db import init_db, get_conn
import utils

st.set_page_config(page_title="CBT — Face++ Ready", layout="wide")

FACEPP_KEY = st.secrets.get("FACEPP_KEY","") if hasattr(st,"secrets") else ""
FACEPP_SECRET = st.secrets.get("FACEPP_SECRET","") if hasattr(st,"secrets") else ""
OUTER_ID = st.secrets.get("FACEPP_OUTER_ID","cbt_students") if hasattr(st,"secrets") else "cbt_students"

init_db()

if "user" not in st.session_state:
    st.session_state.user = None

st.title("CBT System — Face++ (Ready)")
page = st.sidebar.selectbox("Page", ["Home","Admin Login","Admin Dashboard","Student Register","Student Login","Student Dashboard","Question Bank","Exam"])

if page=="Home":
    st.write("CBT system with Face++ integration.")
    st.write("Faceset outer_id:", OUTER_ID)

# Admin Login
if page=="Admin Login":
    st.header("Admin Login")
    reg = st.text_input("Admin Reg No")
    pwd = st.text_input("Password",type="password")
    if st.button("Login as Admin"):
        row = utils.get_user_by_reg(reg)
        if row and row["role"]=="admin" and row["password_hash"] and bcrypt.checkpw(pwd.encode(),row["password_hash"]):
            st.session_state.user = {"id":row["id"],"reg_no":row["reg_no"],"name":row["name"],"role":row["role"]}
            st.success("Admin logged in")
        else:
            st.error("Invalid admin credentials")

# Admin Dashboard
if page=="Admin Dashboard":
    if not st.session_state.user or st.session_state.user.get("role")!="admin":
        st.warning("Please login as admin first.")
    else:
        st.header("Admin Dashboard")
        st.write("Faceset outer_id:",OUTER_ID)
        if st.button("Ensure faceset exists"):
            if not FACEPP_KEY or not FACEPP_SECRET:
                st.error("FACEPP_KEY and FACEPP_SECRET not set.")
            else:
                res = utils.ensure_faceset(FACEPP_KEY,FACEPP_SECRET,OUTER_ID)
                st.write(res)
        st.subheader("Registered students")
        for s in utils.list_students():
            st.write(f"{s['reg_no']} — {s['name']} — face_token: {s['face_token']}")
            cols = st.columns([1,1,1])
            with cols[0]:
                if st.button(f"Delete {s['reg_no']}",key=f"del_{s['reg_no']}"):
                    conn=get_conn();cur=conn.cursor();cur.execute("DELETE FROM users WHERE id=?",(s["id"],));conn.commit();conn.close();st.experimental_rerun()
            with cols[1]:
                if st.button(f"Upload face {s['reg_no']}",key=f"upl_{s['reg_no']}"):
                    uploaded = st.file_uploader(f"Choose image for {s['reg_no']}",type=['jpg','png'],key=f"file_{s['reg_no']}")
                    if uploaded:
                        token=utils.detect_face_bytes(uploaded.getvalue(),FACEPP_KEY,FACEPP_SECRET)
                        if token:
                            utils.add_face_to_faceset(token,FACEPP_KEY,FACEPP_SECRET,OUTER_ID)
                            utils.update_user_face(s["reg_no"],token)
                            st.success(f"Uploaded face for {s['reg_no']}")
            with cols[2]:
                if st.button(f"Reset password {s['reg_no']}",key=f"reset_{s['reg_no']}"):
                    new_pwd = st.text_input(f"New password for {s['reg_no']}",type="password",key=f"np_{s['reg_no']}")
                    if new_pwd:
                        utils.reset_password(s["reg_no"],new_pwd)
                        st.success(f"Password reset for {s['reg_no']}")

# Student Register
if page=="Student Register":
    st.header("Student Register (password and/or face)")
    reg_no = st.text_input("Registration No")
    name = st.text_input("Full name")
    email = st.text_input("Email")
    pwd = st.text_input("Password (optional)",type="password")
    st.write("Optionally capture a photo for biometric login.")
    img = st.camera_input("Take a photo (optional)")
    if st.button("Register Student"):
        if not reg_no or not name:
            st.error("Provide reg no and name.")
        else:
            face_token=None
            if img and FACEPP_KEY and FACEPP_SECRET:
                token=utils.detect_face_bytes(img.getvalue(),FACEPP_KEY,FACEPP_SECRET)
                if token:
                    utils.add_face_to_faceset(token,FACEPP_KEY,FACEPP_SECRET,OUTER_ID)
                    face_token=token
            ok=utils.add_student(reg_no,name,email,pwd,face_token)
            if ok:
                st.success("Registered successfully.")
            else:
                st.error("Registration failed.")

# Student Login
if page=="Student Login":
    st.header("Student Login (password or face)")
    reg = st.text_input("Registration No",key="login_reg")
    pwd = st.text_input("Password (leave blank to use face)",type="password",key="login_pw")
    st.write("Or use camera to login by face (if face was registered)")
    cam = st.camera_input("Take a photo for login (optional)",key="login_cam")
    if st.button("Login"):
        row=utils.get_user_by_reg(reg)
        if not row:
            st.error("User not found.")
        else:
            ok=False
            if pwd and row["password_hash"]:
                if bcrypt.checkpw(pwd.encode(),row["password_hash"]):
                    ok=True
            if not ok and cam and row["face_token"] and FACEPP_KEY and FACEPP_SECRET:
                res=utils.search_face_bytes(cam.getvalue(),FACEPP_KEY,FACEPP_SECRET,OUTER_ID)
                if res and res.get("results"):
                    top=res["results"][0]; confidence=top.get("confidence",0); matched_token=top.get("face_token")
                    if confidence>=80 and matched_token==row["face_token"]:
                        ok=True
            if ok:
                st.session_state.user={"id":row["id"],"reg_no":row["reg_no"],"name":row["name"],"role":row["role"]}
                st.success("Logged in successfully")
            else:
                st.error("Login failed.")

# Student Dashboard
if page=="Student Dashboard":
    if not st.session_state.user:
        st.info("Please login first.")
    else:
        st.header("Student Dashboard")
        st.write(f"Welcome {st.session_state.user['name']}")
        conn=get_conn();cur=conn.cursor();cur.execute("SELECT * FROM attempts WHERE user_id=?",(st.session_state.user["id"],));rows=cur.fetchall();conn.close()
        st.subheader("Past attempts")
        for r in rows: st.write(f"{r['created_at']}: {r['score']}/{r['total']}")

# Question Bank
if page=="Question Bank":
    st.header("Question Bank")
    for q in utils.list_questions(): st.write(f"{q['id']}: {q['title']} - {q['subject']}")

# Exam placeholder
if page=="Exam":
    st.header("Exam")
    st.write("Use Student Dashboard to take the full exam.")

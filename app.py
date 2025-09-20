import streamlit as st
from auth import init_db, register_student, login_student, get_student_by_id
from exams import list_exams, take_exam_interface
from results import show_results
import db_utils

st.set_page_config(page_title="Project-Sadiq CBT", layout="centered")

init_db()  # ensure DBs exist

MENU = ["Home", "Register", "Login", "Dashboard"]
choice = st.sidebar.selectbox("Menu", MENU)

if choice == "Home":
    st.title("Project-Sadiq — CBT Platform")
    st.write("A lightweight CBT system with optional biometric login (face).")
    st.info("Register as a student, capture a face (optional), then login to take exams and view results.")

elif choice == "Register":
    st.header("Student Registration")
    with st.form("reg_form"):
        student_id = st.text_input("Student ID", max_chars=50)
        name = st.text_input("Full name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        st.write("Optional: capture a face image for biometric login")
        face_file = st.camera_input("Capture face photo (optional)")
        submitted = st.form_submit_button("Register")

    if submitted:
        if not student_id or not name or not password:
            st.error("Student ID, name and password are required.")
        else:
            face_bytes = None
            if face_file is not None:
                face_bytes = face_file.getvalue()
            ok, msg = register_student(student_id, name, email, password, face_bytes)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

elif choice == "Login":
    st.header("Login")
    login_mode = st.radio("Login method", ["Password", "Biometric (Face)"], index=0)

    if login_mode == "Password":
        with st.form("login_form"):
            student_id = st.text_input("Student ID")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
        if submitted:
            ok, student = login_student(student_id, password)
            if ok:
                st.session_state['student_id'] = student_id
                st.success(f"Welcome back, {student['name']}")
                st.experimental_rerun()
            else:
                st.error(student)

    else:
        st.write("Point your camera to your face and capture a photo to login.")
        face_file = st.camera_input("Capture for login")
        if st.button("Attempt Biometric Login"):
            if face_file is None:
                st.error("No image captured.")
            else:
                face_bytes = face_file.getvalue()
                ok, student = db_utils.biometric_login(face_bytes)
                if ok:
                    st.session_state['student_id'] = student['student_id']
                    st.success(f"Welcome (biometric), {student['name']}")
                    st.experimental_rerun()
                else:
                    st.error(student)

elif choice == "Dashboard":
    if 'student_id' not in st.session_state:
        st.warning("You must be logged in to access the dashboard.")
    else:
        sid = st.session_state['student_id']
        student = get_student_by_id(sid)
        st.header(f"Dashboard — {student['name']}")
        st.write(f"Student ID: {student['student_id']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Take Exam"):
                take_exam_interface(student['student_id'])
        with col2:
            if st.button("Check Results"):
                show_results(student['student_id'])

        st.markdown("---")
        st.subheader("Account")
        if st.button("Logout"):
            del st.session_state['student_id']
            st.experimental_rerun()

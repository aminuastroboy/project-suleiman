import streamlit as st
from auth import login_user, register_user, get_current_user, logout_user
from db import init_db, get_questions, save_result, get_results

st.set_page_config(page_title="CBT WebAuthn", layout="wide")

init_db()

user = get_current_user()

if not user:
    st.title("Login / Register")
    choice = st.radio("Select option", ["Login", "Register"])

    if choice == "Register":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["student", "admin"])
        if st.button("Register"):
            register_user(username, password, role)
    else:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            login_user(username, password)

else:
    st.sidebar.write(f"👋 Welcome, {user['username']} ({user['role']})")
    if st.sidebar.button("Logout"):
        logout_user()

    if user['role'] == 'admin':
        st.header("Admin Dashboard")
        tab = st.sidebar.radio("Menu", ["Dashboard", "Students", "Question Bank"])
        if tab == "Dashboard":
            st.subheader("Overview")
            st.info("Admin dashboard overview goes here.")
        elif tab == "Students":
            st.subheader("Register Students")
            st.info("Student registration interface.")
        elif tab == "Question Bank":
            st.subheader("Manage Questions")
            st.info("Add/Edit/Delete questions.")
    else:
        st.header("Student Dashboard")
        tab = st.sidebar.radio("Menu", ["Dashboard", "Take Exam", "Results"])
        if tab == "Dashboard":
            st.subheader("Your Dashboard")
            st.info("Student overview here.")
        elif tab == "Take Exam":
            st.subheader("Exam Interface")
            questions = get_questions()
            answers = {}
            for q in questions:
                answers[q['id']] = st.radio(q['question'], q['options'])
            if st.button("Submit Exam"):
                score = sum(1 for q in questions if answers[q['id']] == q['answer'])
                save_result(user['id'], score)
                st.success(f"Exam submitted! Your score: {score}/{len(questions)}")
        elif tab == "Results":
            st.subheader("Past Results")
            results = get_results(user['id'])
            for r in results:
                st.write(f"{r['submitted_at']}: {r['score']} points")

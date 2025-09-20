import streamlit as st
from db_utils import init_all, add_student, get_student
from exams import take_exam_interface
from results import show_results

# Initialize DB
init_all()

def main():
    st.title("Project Suleiman - Student Portal")

    menu = ["Register", "Login"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Register":
        st.subheader("Register")
        student_id = st.text_input("Student ID")
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            if student_id and name and email and password:
                success, msg = add_student(student_id, name, email, password)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.warning("Please fill all fields.")

    elif choice == "Login":
        st.subheader("Login")
        student_id = st.text_input("Student ID")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = get_student(student_id)
            if user and user["password"] == password:
                st.success(f"Welcome {user['name']}!")
                app_mode = st.radio("Select Action", ["Take Exam", "View Results"])
                if app_mode == "Take Exam":
                    take_exam_interface(student_id)
                elif app_mode == "View Results":
                    show_results(student_id)
            else:
                st.error("Invalid Student ID or Password")

if __name__ == "__main__":
    main()

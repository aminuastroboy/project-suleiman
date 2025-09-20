import streamlit as st
import face_recognition
import numpy as np
from PIL import Image
import io
import pickle
import os

# Database file
DB_FILE = "students.pkl"

# Load or initialize database
if os.path.exists(DB_FILE):
    with open(DB_FILE, "rb") as f:
        students_db = pickle.load(f)
else:
    students_db = {"students": {}, "admin": {"username": "admin", "password": "1234"}}

# Save database
def save_db():
    with open(DB_FILE, "wb") as f:
        pickle.dump(students_db, f)

# Encode face
def encode_face(image: Image.Image):
    img = np.array(image)
    encodings = face_recognition.face_encodings(img)
    return encodings[0] if encodings else None

# Registration
def register_student():
    st.subheader("📸 Register Student")
    school_id = st.text_input("Enter School ID")
    name = st.text_input("Enter Full Name")
    uploaded = st.file_uploader("Upload Face Image", type=["jpg", "png", "jpeg"])
    if uploaded and school_id and name:
        img = Image.open(uploaded).convert("RGB")
        encoding = encode_face(img)
        if encoding is not None:
            students_db["students"][school_id] = {"name": name, "encoding": encoding}
            save_db()
            st.success(f"✅ {name} ({school_id}) registered successfully!")
        else:
            st.error("No face detected. Try another image.")

# Login
def student_login():
    st.subheader("🔑 Student Login")
    school_id = st.text_input("Enter School ID")
    uploaded = st.file_uploader("Upload Face Image", type=["jpg", "png", "jpeg"])
    if uploaded and school_id:
        img = Image.open(uploaded).convert("RGB")
        encoding = encode_face(img)
        if encoding is not None:
            if school_id in students_db["students"]:
                known_enc = students_db["students"][school_id]["encoding"]
                match = face_recognition.compare_faces([known_enc], encoding)[0]
                if match:
                    st.success(f"🎉 Welcome, {students_db['students'][school_id]['name']}! You are logged in.")
                else:
                    st.error("Face does not match. Access denied.")
            else:
                st.error("School ID not found.")

# Admin
def admin_panel():
    st.subheader("🛠️ Admin Panel")
    username = st.text_input("Admin Username")
    password = st.text_input("Admin Password", type="password")
    if st.button("Login as Admin"):
        if username == students_db["admin"]["username"] and password == students_db["admin"]["password"]:
            st.success("✅ Admin logged in")
            st.write("### Registered Students")
            for sid, data in students_db["students"].items():
                st.write(f"- {sid}: {data['name']}")
        else:
            st.error("Invalid admin credentials")

# Main UI
st.title("📘 Project Suleiman - CBT App v3")

menu = st.sidebar.radio("Navigation", ["Register", "Login", "Admin"])

if menu == "Register":
    register_student()
elif menu == "Login":
    student_login()
elif menu == "Admin":
    admin_panel()

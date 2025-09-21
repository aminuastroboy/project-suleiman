
import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import os, pickle, math

DB_FILE = "students_simple.pkl"

# Load or initialize DB (keep dummy data)
if os.path.exists(DB_FILE):
    with open(DB_FILE, "rb") as f:
        DB = pickle.load(f)
else:
    DB = {"admin": {"username": "admin", "password": "1234"}, "students": {}}
    # Seed dummy students (no embeddings yet)
    DB["students"]["S1001"] = {"name": "Student One", "embedding": None, "progress": [{"lesson": "Lesson 1", "answer": "Negative: I can't do this → Positive: I'll try step by step"}]}
    DB["students"]["S1002"] = {"name": "Student Two", "embedding": None, "progress": [{"lesson": "Lesson 1", "answer": "Negative: Nobody likes me → Positive: I have people who care"}]}
    with open(DB_FILE, "wb") as f:
        pickle.dump(DB, f)

def save_db():
    with open(DB_FILE, "wb") as f:
        pickle.dump(DB, f)

def image_to_embedding(pil_image, size=(64,64)):
    # Convert to grayscale, resize, normalize and flatten
    img = pil_image.convert("L")  # grayscale
    img = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    emb = arr.flatten()
    # Normalize to unit vector
    norm = np.linalg.norm(emb)
    if norm > 0:
        emb = emb / norm
    return emb

def cosine_similarity(a, b):
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    if a.size == 0 or b.size == 0:
        return -1.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

st.set_page_config(page_title="CBT App v5 (Simple Embeddings, Fixed)", layout="wide")
st.title("🧠 Project Suleiman — CBT App v5 (No OpenCV, Fixed Pillow)")

mode = st.sidebar.radio("Mode", ["Student", "Admin"])

if mode == "Student":
    st.header("Student Portal")
    action = st.sidebar.radio("Action", ["Register", "Login", "Lessons", "Progress"])

    if action == "Register":
        st.subheader("Register with School ID + Face (simple)")
        school_id = st.text_input("School ID")
        name = st.text_input("Full name")
        img_file = st.camera_input("Take a close-up face photo (fill the frame)")
        if st.button("Register"):
            if not school_id or not name or img_file is None:
                st.warning("Provide School ID, name and take a photo.")
            else:
                pil = Image.open(img_file)
                emb = image_to_embedding(pil)
                if emb is None:
                    st.error("Could not process image. Try again.")
                else:
                    DB["students"][school_id] = {"name": name, "embedding": emb.tolist(), "progress": []}
                    save_db()
                    st.success(f"Registered {name} ({school_id}) successfully.")
                    st.info("Note: This is a simple image-based matcher for demo purposes. For production, use a proper biometric model.")

    elif action == "Login":
        st.subheader("Login with School ID + Face (simple)")
        school_id = st.text_input("School ID to login")
        img_file = st.camera_input("Take a close-up face photo for login")
        if st.button("Login"):
            if not school_id or img_file is None:
                st.warning("Provide School ID and take a photo.")
            else:
                if school_id not in DB["students"]:
                    st.error("School ID not found. Please register first.")
                else:
                    pil = Image.open(img_file)
                    emb = image_to_embedding(pil)
                    if emb is None:
                        st.error("Could not process image. Try again.")
                    else:
                        stored = DB["students"][school_id].get("embedding")
                        if stored is None:
                            st.error("No face registered for this School ID. Please register first.")
                        else:
                            sim = cosine_similarity(np.array(stored), emb)
                            # threshold tuned for normalized grayscale embeddings
                            if sim >= 0.90:
                                st.success(f"Welcome back, {DB['students'][school_id]['name']}! (similarity={sim:.3f})")
                                st.session_state["logged_in"] = school_id
                            else:
                                st.error(f"Face did not match (similarity={sim:.3f}). Access denied.")

    elif action == "Lessons":
        if "logged_in" not in st.session_state:
            st.info("Login first to access lessons.")
        else:
            st.subheader("Lesson 1: Challenging Negative Thoughts")
            ans = st.text_area("Write a negative thought and reframe it positively:")
            if st.button("Save Answer"):
                sid = st.session_state["logged_in"]
                DB["students"][sid]["progress"].append({"lesson": "Lesson 1", "answer": ans})
                save_db()
                st.success("Progress saved.")

    elif action == "Progress":
        if "logged_in" not in st.session_state:
            st.info("Login first to view progress.")
        else:
            sid = st.session_state["logged_in"]
            st.subheader(f"Progress for {DB['students'][sid]['name']} ({sid})")
            for p in DB["students"][sid].get("progress", []):
                st.write(f"- {p['lesson']}: {p['answer']}")

elif mode == "Admin":
    st.header("Admin Panel")
    username = st.text_input("Admin username")
    password = st.text_input("Admin password", type="password")
    if st.button("Login as Admin"):
        if username == DB["admin"]["username"] and password == DB["admin"]["password"]:
            st.success("Admin logged in.")
            st.subheader("Registered students")
            for sid, info in DB["students"].items():
                emb_status = "Yes" if info.get("embedding") is not None else "No"
                st.write(f"- {sid}: {info.get('name')} (Embedding registered: {emb_status})")
                st.write("  Progress:")
                for p in info.get("progress", []):
                    st.write(f"    • {p['lesson']}: {p['answer']}")
                if st.button(f"Delete {sid}"):
                    del DB["students"][sid]
                    save_db()
                    st.experimental_rerun()
        else:
            st.error("Invalid admin credentials. Default admin is admin / 1234")

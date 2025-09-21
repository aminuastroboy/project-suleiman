
import streamlit as st
from PIL import Image
import numpy as np
import mediapipe as mp
import pickle, os

DB_FILE = "students_mp.pkl"

# Load or initialize DB
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

mp_face = mp.solutions.face_mesh

def get_embedding_from_image(pil_image):
    # Returns 1D numpy array embedding from mediapipe face landmarks or None
    img = np.asarray(pil_image.convert("RGB"))
    h, w, _ = img.shape
    with mp_face.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=False) as face_mesh:
        results = face_mesh.process(img)
        if not results.multi_face_landmarks:
            return None
        lm = results.multi_face_landmarks[0].landmark
        coords = np.array([[p.x * w, p.y * h, p.z * w] for p in lm], dtype=np.float32)  # shape (468,3)
        # Normalize: subtract center and scale by face size (max dist)
        center = coords.mean(axis=0)
        coords_centered = coords - center
        scale = np.max(np.linalg.norm(coords_centered, axis=1))
        if scale > 0:
            coords_centered /= scale
        embedding = coords_centered.flatten()  # length 468*3 = 1404
        return embedding

def cosine_similarity(a, b):
    if a is None or b is None:
        return -1.0
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    if a.size == 0 or b.size == 0:
        return -1.0
    dot = np.dot(a, b)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return -1.0
    return float(dot / (na * nb))

st.set_page_config(page_title="CBT App v4 (Mediapipe)", layout="wide")
st.title("🧠 Project Suleiman — CBT App v4 (Mediapipe embeddings)")

mode = st.sidebar.radio("Mode", ["Student", "Admin"])

if mode == "Student":
    st.header("Student Portal")
    action = st.sidebar.radio("Action", ["Register", "Login", "Lessons", "Progress"])
    if action == "Register":
        st.subheader("Register with School ID + Face")
        school_id = st.text_input("School ID")
        name = st.text_input("Full name")
        img_file = st.camera_input("Take a photo for registration (allow camera)")
        if st.button("Register"):
            if not school_id or not name or img_file is None:
                st.warning("Provide School ID, name and take a photo.")
            else:
                pil = Image.open(img_file)
                emb = get_embedding_from_image(pil)
                if emb is None:
                    st.error("No face detected. Try again with a clearer photo.")
                else:
                    DB["students"][school_id] = {"name": name, "embedding": emb.tolist(), "progress": []}
                    save_db()
                    st.success(f"Registered {name} ({school_id}) successfully.")
    elif action == "Login":
        st.subheader("Login with School ID + Face")
        school_id = st.text_input("School ID to login")
        img_file = st.camera_input("Take a photo for login (allow camera)")
        if st.button("Login"):
            if not school_id or img_file is None:
                st.warning("Provide School ID and take a photo.")
            else:
                if school_id not in DB["students"]:
                    st.error("School ID not found. Please register first.")
                else:
                    pil = Image.open(img_file)
                    emb = get_embedding_from_image(pil)
                    if emb is None:
                        st.error("No face detected. Try again.")
                    else:
                        stored = DB["students"][school_id].get("embedding")
                        if stored is None:
                            st.error("No face registered for this School ID. Please register first.")
                        else:
                            sim = cosine_similarity(np.array(stored), emb)
                            # similarity near 1.0 => match. threshold can be tuned
                            if sim >= 0.7:
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

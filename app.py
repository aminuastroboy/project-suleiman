import streamlit as st
from db import SessionLocal, User, Progress, Admin, init_db
from deepface import DeepFace
from PIL import Image
import io, json, numpy as np

init_db()
session = SessionLocal()

st.set_page_config(page_title="🧠 CBT Biometric App", page_icon="🧠", layout="wide")

# Helper to capture image using Streamlit's camera_input
def capture_image():
    img_file_buffer = st.camera_input("📷 Take a photo")
    if img_file_buffer is not None:
        # Return a PIL image
        image = Image.open(img_file_buffer)
        image = image.convert("RGB")
        return image
    return None

# Helper to get embedding using DeepFace with mediapipe backend
def get_embedding(pil_image):
    try:
        # DeepFace.represent accepts image path or numpy array; convert PIL to numpy
        img_array = np.asarray(pil_image)
        rep = DeepFace.represent(img_path = img_array, model_name="Facenet", detector_backend="mediapipe", enforce_detection=False)
        if isinstance(rep, list) and len(rep) > 0 and "embedding" in rep[0]:
            return rep[0]["embedding"]
        st.error("Could not extract embedding from image.")
        return None
    except Exception as e:
        st.error(f"Embedding error: {e}")
        return None

# Convert embedding to JSON
def embedding_to_json(embedding):
    return json.dumps(embedding)

def json_to_embedding(s):
    return np.array(json.loads(s))

# Sidebar mode selector
mode = st.sidebar.radio("Choose Mode", ["Student", "Admin"])

if mode == "Student":
    st.title("🧠 CBT Webapp (Student Portal)")
    auth_mode = st.sidebar.radio("🔐 Authentication", ["Register", "Login"])
    user_session = st.session_state.get("user", None)

    if not user_session:
        if auth_mode == "Register":
            st.subheader("📝 Register with Face")
            school_id = st.text_input("School ID")
            img = capture_image()
            if st.button("Register"):
                if school_id and img is not None:
                    emb = get_embedding(img)
                    if emb is not None:
                        user = User(school_id=school_id, face_embedding=embedding_to_json(emb))
                        session.add(user)
                        session.commit()
                        st.success("✅ Registered successfully! Please login.")
                else:
                    st.warning("Provide School ID and face.")

        elif auth_mode == "Login":
            st.subheader("🔓 Login with Face")
            school_id = st.text_input("School ID")
            img = capture_image()
            if st.button("Login"):
                if school_id and img is not None:
                    emb = get_embedding(img)
                    if emb is not None:
                        user = session.query(User).filter_by(school_id=school_id).first()
                        if user:
                            db_emb = json_to_embedding(user.face_embedding)
                            dist = np.linalg.norm(np.array(emb) - db_emb)
                            if dist < 0.7:  # Threshold
                                st.session_state["user"] = user.school_id
                                st.success(f"Welcome back, {user.school_id}! 🎉")
                            else:
                                st.error("Face does not match this School ID.")
                        else:
                            st.error("School ID not found.")
    else:
        st.success(f"✅ Logged in as {st.session_state['user']}")
        menu = ["Home", "Lesson 1", "Progress"]
        choice = st.sidebar.radio("📚 Menu", menu)

        if choice == "Home":
            st.write("Welcome to your CBT companion app.")
        elif choice == "Lesson 1":
            st.header("Lesson 1: Challenging Negative Thoughts")
            ans = st.text_area("Write a negative thought and reframe it positively")
            if st.button("Save Progress"):
                user = session.query(User).filter_by(school_id=st.session_state["user"]).first()
                p = Progress(user_id=user.id, lesson="Lesson 1", answer=ans)
                session.add(p)
                session.commit()
                st.success("Progress saved!")
        elif choice == "Progress":
            user = session.query(User).filter_by(school_id=st.session_state["user"]).first()
            rows = session.query(Progress).filter_by(user_id=user.id).all()
            for r in rows:
                st.write(f"📘 {r.lesson} → {r.answer}")

elif mode == "Admin":
    st.title("👨‍🏫 Admin Dashboard Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login as Admin"):
        admin = session.query(Admin).filter_by(username=username, password=password).first()
        if admin:
            st.session_state["admin"] = admin.username
            st.success(f"✅ Logged in as Admin: {admin.username}")
        else:
            st.error("Invalid admin credentials")

    if "admin" in st.session_state:
        st.subheader("📋 Student Management")
        students = session.query(User).all()
        if students:
            for s in students:
                st.write(f"🎓 School ID: {s.school_id}")
                rows = session.query(Progress).filter_by(user_id=s.id).all()
                for r in rows:
                    st.write(f"📘 {r.lesson} → {r.answer}")
                if st.button(f"Delete {s.school_id}"):
                    session.query(Progress).filter_by(user_id=s.id).delete()
                    session.delete(s)
                    session.commit()
                    st.warning(f"Deleted {s.school_id}")
                    st.experimental_rerun()
        else:
            st.info("No students registered yet.")

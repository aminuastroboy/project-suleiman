from db_utils import init_all, add_student, get_student, biometric_login
import db_utils
import pickle
from PIL import Image
import io

def init_db():
    init_all()

def register_student(student_id, name, email, password, face_bytes=None):
    face_blob = None
    if face_bytes is not None and db_utils.face_recognition is not None:
        try:
            img = db_utils.face_recognition.load_image_file(io.BytesIO(face_bytes))
            enc = db_utils.face_recognition.face_encodings(img)
            if len(enc) > 0:
                face_blob = pickle.dumps(enc[0])
        except Exception as e:
            print("Face encoding failed:", e)
            face_blob = None
    ok, msg = add_student(student_id, name, email, password, face_blob)
    return ok, msg

def login_student(student_id, password):
    student = get_student(student_id)
    if not student:
        return False, "Student not found."
    if student['password'] != password:
        return False, "Wrong password."
    return True, student

def get_student_by_id(student_id):
    return get_student(student_id)

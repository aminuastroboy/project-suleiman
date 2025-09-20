# 🧠 CBT Biometric Webapp (v2)

This patched build uses DeepFace with the mediapipe detector backend (avoids OpenCV),
so it is more compatible with Streamlit Cloud.

## Features
- Student registration & login with School ID + Face Recognition (DeepFace + mediapipe)
- CBT Lesson 1 with progress saving
- Admin login (default: admin / 1234)
- Admin can view all students + their progress, and delete users
- Dummy student data seeded for testing

## Install & Run (local)
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes for Streamlit Cloud
- DeepFace and mediapipe are heavy dependencies; Streamlit Cloud may still have resource limits.
- If you run into memory/timeout issues on Streamlit Cloud, consider running locally or using a VM with more resources.

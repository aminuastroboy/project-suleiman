# CBT App v4 (Mediapipe)

This build uses Mediapipe FaceMesh to extract face landmarks and create a normalized embedding
which is stored in a small pickle database. It avoids dlib/opencv and is much more compatible
with Streamlit Cloud.

## Features
- Student register with School ID + live camera photo (Streamlit camera_input)
- Student login with School ID + live camera photo (compares embeddings with cosine similarity)
- Lesson 1 and progress saving after login
- Admin panel (default admin/admin: admin / 1234) to view and delete students
- Dummy students S1001 and S1002 seeded (without embeddings) and sample progress

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

Notes: Mediapipe and Streamlit can be heavy; if you deploy to Streamlit Cloud and hit resource limits,
consider running locally or using a paid VM.

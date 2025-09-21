# CBT App v5 (No OpenCV, Simple Image Embeddings)

This build removes OpenCV and mediapipe entirely. Instead it uses a simple image-based embedding
(grayscale, resized) as a prototype biometric for demo/testing purposes. This avoids native build
dependencies and should install cleanly on Streamlit Cloud or local Python without extra system libs.

## Features
- Student register with School ID + live camera photo (Streamlit camera_input)
- Student login with School ID + live camera photo (compares simple grayscale embeddings)
- Lesson 1 and progress saving after login
- Admin panel (default admin / 1234) to view and delete students
- Dummy students S1001 and S1002 seeded

## Usage
```bash
pip install -r requirements.txt
streamlit run app.py
```

Notes: This simple matcher is only intended for demo/testing. For production biometric authentication,
use a proper face-recognition model and follow privacy/security best practices.

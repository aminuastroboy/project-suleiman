# CBT App v5 (Fixed Pillow)

This fixes the deprecated Image.ANTIALIAS by using Image.Resampling.LANCZOS.
No OpenCV or mediapipe required. Pure Python + Streamlit + Pillow + NumPy.

## Features
- Student register/login via grayscale embeddings
- Lesson 1 and progress saving
- Admin panel (admin / 1234)
- Dummy students seeded

## Run
pip install -r requirements.txt
streamlit run app.py

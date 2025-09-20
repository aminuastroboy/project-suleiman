# Project-Sadiq — Deploy-ready Streamlit CBT

This repository contains a simple Computer-Based Testing (CBT) Streamlit app with optional biometric features.

## How to run locally

1. Create a Python virtual environment
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```
2. Install requirements
   ```bash
   pip install -r requirements.txt
   ```
3. Run Streamlit
   ```bash
   streamlit run app.py
   ```

## Biometric note
The app optionally integrates `face-recognition` (which depends on `dlib`). On many hosts (including Streamlit Cloud) compiling `dlib` may fail. If that happens, biometric login will be disabled and password login remains available.

## Seeded data
This package includes a seeded sample student and a sample exam so you can test the full flow immediately.

# CBT WebAuthn (Streamlit + Postgres)

## 🚀 Features
- Admin login & dashboard
- Student login & dashboard
- Student registration
- Question bank (MCQs)
- Exam interface
- Results storage
- Password + WebAuthn biometric support (fingerprint/FaceID)

## 📦 Setup

1. Clone repo / upload to Streamlit Cloud
2. Create `.streamlit/secrets.toml` with Postgres credentials:

```toml
[postgres]
host = "your-db-host"
port = 5432
dbname = "your-db-name"
user = "your-username"
password = "your-password"
```

3. Install requirements:
```bash
pip install -r requirements.txt
```

4. Run:
```bash
streamlit run app.py
```

---
For biometric login, browsers will prompt fingerprint/FaceID automatically via WebAuthn API.

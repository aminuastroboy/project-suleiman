CBT WebAuthn App (Streamlit + Postgres) - No npm variant
-------------------------------------------------------

This project is a Streamlit CBT application using WebAuthn (platform authenticator) for biometric login
without requiring any npm or build step. It embeds a small HTML/JS helper into Streamlit via components.html.

Features:
- Admin and Student roles
- Student registration (admin)
- Question bank (add/view)
- Student exam interface and results
- Password + WebAuthn biometric registration & login (fingerprint/FaceID)

Notes:
- WebAuthn requires secure origin: HTTPS (Streamlit Cloud) or localhost for testing.
- Set RP_ID in webauthn_server.py to your app host before deploying.
- Configure Postgres secrets in Streamlit Cloud or in .streamlit/secrets.toml

Quick start:
1. Update .streamlit/secrets.toml with your Postgres credentials or set Streamlit Cloud secrets.
2. Install deps: pip install -r requirements.txt
3. Run locally: streamlit run app.py
4. For production: push repo to GitHub and deploy to Streamlit Cloud.

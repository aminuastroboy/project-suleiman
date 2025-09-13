import streamlit as st
import bcrypt
from db import get_user_by_username, create_user

def register_user(username, password, role):
    if get_user_by_username(username):
        st.error("User already exists.")
        return
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    create_user(username, pw_hash, role)
    st.success("Registered successfully! Please login.")

def login_user(username, password):
    user = get_user_by_username(username)
    if not user:
        st.error("User not found.")
        return
    if bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
        st.session_state['user'] = user
        st.success("Login successful!")
    else:
        st.error("Incorrect password.")

def get_current_user():
    return st.session_state.get("user")

def logout_user():
    if "user" in st.session_state:
        del st.session_state['user']

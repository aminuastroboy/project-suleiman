import streamlit as st
import psycopg2
import psycopg2.extras

def get_conn():
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        dbname=st.secrets["postgres"]["dbname"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"],
    )

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT
    );
    CREATE TABLE IF NOT EXISTS questions (
        id SERIAL PRIMARY KEY,
        question TEXT,
        options TEXT[],
        answer TEXT
    );
    CREATE TABLE IF NOT EXISTS results (
        id SERIAL PRIMARY KEY,
        student_id INT REFERENCES users(id),
        score INT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(username, pw_hash, role):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)", (username, pw_hash, role))
    conn.commit()
    conn.close()

def get_questions():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM questions")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_result(student_id, score):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO results (student_id, score) VALUES (%s, %s)", (student_id, score))
    conn.commit()
    conn.close()

def get_results(student_id):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM results WHERE student_id=%s ORDER BY submitted_at DESC", (student_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

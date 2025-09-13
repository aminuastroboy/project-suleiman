import streamlit as st
import psycopg2
import psycopg2.extras

def get_conn():
    cfg = st.secrets.get('postgres', None)
    if not cfg:
        raise RuntimeError('Postgres credentials not found in st.secrets.postgres')
    return psycopg2.connect(
        host=cfg['host'],
        port=cfg.get('port','5432'),
        dbname=cfg['dbname'],
        user=cfg['user'],
        password=cfg['password']
    )

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('admin','student'))
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS credentials (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        credential_id BYTEA NOT NULL UNIQUE,
        public_key BYTEA NOT NULL,
        sign_count INTEGER DEFAULT 0,
        transports TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id SERIAL PRIMARY KEY,
        question TEXT NOT NULL,
        options_json TEXT NOT NULL,
        answer TEXT NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id SERIAL PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        score INTEGER NOT NULL,
        total INTEGER NOT NULL,
        submitted_at TIMESTAMP DEFAULT NOW()
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def add_user(username, password_hash, role='student'):
    conn = get_conn(); cur = conn.cursor()
    cur.execute('INSERT INTO users (username, password_hash, role) VALUES (%s,%s,%s) RETURNING id', (username, password_hash, role))
    uid = cur.fetchone()[0]; conn.commit(); cur.close(); conn.close(); return uid

def get_user_by_username(username):
    conn = get_conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('SELECT id, username, password_hash, role FROM users WHERE username=%s', (username,))
    row = cur.fetchone(); cur.close(); conn.close()
    return dict(row) if row else None

def get_user_by_id(uid):
    conn = get_conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('SELECT id, username, password_hash, role FROM users WHERE id=%s', (uid,))
    row = cur.fetchone(); cur.close(); conn.close()
    return dict(row) if row else None

def add_credential(user_id, credential_id_bytes, public_key_bytes, sign_count, transports=None):
    conn = get_conn(); cur = conn.cursor()
    cur.execute('INSERT INTO credentials (user_id, credential_id, public_key, sign_count, transports) VALUES (%s,%s,%s,%s,%s)',
                (user_id, psycopg2.Binary(credential_id_bytes), psycopg2.Binary(public_key_bytes), sign_count, transports))
    conn.commit(); cur.close(); conn.close()

def get_credentials_for_user(user_id):
    conn = get_conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('SELECT id, credential_id, public_key, sign_count, transports FROM credentials WHERE user_id=%s', (user_id,))
    rows = cur.fetchall(); cur.close(); conn.close()
    out = []
    for r in rows:
        out.append({'id': r['id'], 'credential_id': bytes(r['credential_id']), 'public_key': bytes(r['public_key']), 'sign_count': r['sign_count'], 'transports': r['transports']})
    return out

def get_credential_by_credential_id(credential_id_bytes):
    conn = get_conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    conn.execute = cur.execute
    cur.execute('SELECT id, user_id, credential_id, public_key, sign_count FROM credentials WHERE credential_id=%s', (psycopg2.Binary(credential_id_bytes),))
    row = cur.fetchone(); cur.close(); conn.close(); return dict(row) if row else None

def update_sign_count(cred_id, sign_count):
    conn = get_conn(); cur = conn.cursor(); cur.execute('UPDATE credentials SET sign_count=%s WHERE id=%s', (sign_count, cred_id)); conn.commit(); cur.close(); conn.close()

def add_question(question, options_json, answer):
    conn = get_conn(); cur = conn.cursor(); cur.execute('INSERT INTO questions (question, options_json, answer) VALUES (%s,%s,%s)', (question, options_json, answer)); conn.commit(); cur.close(); conn.close()

def get_all_questions():
    conn = get_conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor); cur.execute('SELECT id, question, options_json, answer FROM questions ORDER BY id'); rows = cur.fetchall(); cur.close(); conn.close(); return [dict(r) for r in rows]

def add_result(student_id, score, total):
    conn = get_conn(); cur = conn.cursor(); cur.execute('INSERT INTO results (student_id, score, total) VALUES (%s,%s,%s)', (student_id, score, total)); conn.commit(); cur.close(); conn.close()

def get_results_for_student(student_id):
    conn = get_conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor); cur.execute('SELECT id, score, total, submitted_at FROM results WHERE student_id=%s ORDER BY submitted_at DESC', (student_id,)); rows = cur.fetchall(); cur.close(); conn.close(); return [dict(r) for r in rows]

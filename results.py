import streamlit as st
import sqlite3
import json
from db_utils import get_conn, RESULT_DB

def show_results(student_id):
    conn = get_conn(RESULT_DB)
    c = conn.cursor()
    c.execute('SELECT exam_id, score, timestamp, answers_json FROM results WHERE student_id = ? ORDER BY timestamp DESC', (student_id,))
    rows = c.fetchall()
    conn.close()
    if not rows:
        st.info("No results yet.")
        return
    for r in rows:
        st.markdown(f"**Exam:** {r['exam_id']} — Score: {r['score']} — {r['timestamp']}")
        st.write(json.loads(r['answers_json']))
        st.markdown('---')

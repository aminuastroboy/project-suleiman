import streamlit as st
import sqlite3
import json
from db_utils import get_conn, EXAM_DB, RESULT_DB

def list_exams():
    conn = get_conn(EXAM_DB)
    c = conn.cursor()
    c.execute('SELECT exam_id, title FROM exams')
    rows = c.fetchall()
    conn.close()
    return rows

def take_exam_interface(student_id):
    conn = get_conn(EXAM_DB)
    c = conn.cursor()
    c.execute('SELECT exam_id, title, questions_json FROM exams LIMIT 1')
    row = c.fetchone()
    conn.close()
    if not row:
        st.info("No exams available. Admins can add exams by inserting directly into exams.db for now.")
        return
    exam_id = row['exam_id']
    title = row['title']
    questions = json.loads(row['questions_json'])

    st.subheader(f"Exam: {title}")
    answers = {}
    for i, q in enumerate(questions):
        st.markdown(f"**Q{i+1}. {q['question']}**")
        if q['type'] == 'mcq':
            ans = st.radio(f"Choose (Q{i+1})", q['choices'], key=f"q{i}")
            answers[q['id']] = ans
        else:
            ans = st.text_input(f"Answer (Q{i+1})", key=f"q{i}")
            answers[q['id']] = ans

    if st.button("Submit Exam"):
        score = grade_exam(questions, answers)
        save_result(student_id, exam_id, answers, score)
        st.success(f"Submitted. Score: {score}/{len(questions)}")

def grade_exam(questions, answers):
    correct = 0
    for q in questions:
        qid = q['id']
        if q['type'] == 'mcq':
            if q.get('answer') == answers.get(qid):
                correct += 1
        else:
            if q.get('answer', '').strip().lower() == answers.get(qid, '').strip().lower():
                correct += 1
    return correct

def save_result(student_id, exam_id, answers, score):
    conn = sqlite3.connect(RESULT_DB)
    c = conn.cursor()
    import json
    c.execute('INSERT INTO results (student_id, exam_id, answers_json, score) VALUES (?,?,?,?)',
              (student_id, exam_id, json.dumps(answers), score))
    conn.commit()
    conn.close()

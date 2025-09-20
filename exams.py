import streamlit as st
from db_utils import add_result

QUESTIONS = [
    {"q": "What is 2 + 2?", "options": ["3", "4", "5"], "answer": "4"},
    {"q": "What is the capital of France?", "options": ["Paris", "London", "Berlin"], "answer": "Paris"},
    {"q": "Which planet is known as the Red Planet?", "options": ["Earth", "Mars", "Jupiter"], "answer": "Mars"},
]

def take_exam_interface(student_id):
    st.subheader("Take Exam")
    score = 0
    answers = {}
    for idx, q in enumerate(QUESTIONS):
        ans = st.radio(q["q"], q["options"], key=f"q{idx}")
        answers[idx] = ans
    if st.button("Submit Exam"):
        for idx, q in enumerate(QUESTIONS):
            if answers[idx] == q["answer"]:
                score += 1
        add_result(student_id, "General Knowledge", score)
        st.success(f"Exam submitted! Score: {score}/{len(QUESTIONS)}")

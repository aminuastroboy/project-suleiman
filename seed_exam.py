# seed_exam.py - already seeded during packaging but kept for reference
import sqlite3, json, uuid
conn = sqlite3.connect("exams.db")
c = conn.cursor()
questions = [{"id": "q1", "type": "mcq", "question": "What is 2+2?", "choices": ["3", "4", "5"], "answer": "4"}, {"id": "q2", "type": "mcq", "question": "What is the capital of France?", "choices": ["Paris", "Rome", "Berlin"], "answer": "Paris"}, {"id": "q3", "type": "mcq", "question": "Which number is prime?", "choices": ["4", "6", "7"], "answer": "7"}, {"id": "q4", "type": "mcq", "question": "2 * 5 = ?", "choices": ["7", "10", "12"], "answer": "10"}, {"id": "q5", "type": "mcq", "question": "What color do you get by mixing red and white?", "choices": ["Pink", "Purple", "Brown"], "answer": "Pink"}]
exam_id = "exam-" + uuid.uuid4().hex[:6]
c.execute('INSERT OR REPLACE INTO exams (exam_id, title, questions_json) VALUES (?,?,?)',
          (exam_id, 'Sample Exam', json.dumps(questions)))
conn.commit()
conn.close()
print('Seeded exam', exam_id)

\
    import streamlit as st
    from db import init_db, get_conn
    import utils, sqlite3, datetime, json, os
    from PIL import Image, ImageOps
    import numpy as np

    init_db()
    st.set_page_config(page_title='CBT System - Hybrid Biometric', layout='wide')
    st.title('CBT System - Project Suleiman (Hybrid Biometric)')

    def image_to_embedding(pil_image, size=(64,64)):
        img = pil_image.convert("L")
        img = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
        arr = np.asarray(img, dtype=np.float32) / 255.0
        emb = arr.flatten()
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
        return emb.tolist()

    def cosine_similarity(a, b):
        a = np.array(a, dtype=np.float32)
        b = np.array(b, dtype=np.float32)
        if a.size == 0 or b.size == 0:
            return -1.0
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    menu = st.sidebar.selectbox('Go to', ['Home','Admin Login','Admin Dashboard','Student Registration','Student Login','Student Dashboard','Question Bank','Exam (Student)'])

    # Home
    if menu == 'Home':
        st.header('Welcome')
        st.write('This is the CBT system with hybrid login (password OR face). Use the sidebar to navigate.')

    # Admin Login
    if menu == 'Admin Login':
        st.header('Admin Login')
        reg = st.text_input('Admin Reg No (use ADMIN001)')
        pwd = st.text_input('Password', type='password')
        if st.button('Login'):
            row = utils.get_user_by_reg(reg)
            if row and row['role']=='admin' and utils.verify_password(pwd, row['password_hash']):
                st.session_state['admin_logged'] = row['id']
                st.success('Admin logged in')
            else:
                st.error('Invalid credentials')

    # Admin Dashboard
    if menu == 'Admin Dashboard':
        if 'admin_logged' not in st.session_state:
            st.warning('Please login as admin first (Admin Login)')
        else:
            st.header('Admin Dashboard')
            students = utils.list_students()
            questions = utils.list_questions()
            st.subheader('Overview')
            st.write(f'Total students: {len(students)}')
            st.write(f'Total questions: {len(questions)}')
            col1, col2 = st.columns(2)
            with col1:
                st.subheader('Manage Students')
                for s in students:
                    st.write(f\"{s['reg_no']} - {s['name']} - {s['email']} - Face:{'Yes' if s['face_embedding'] else 'No'}\")
                    if st.button('Delete '+s['reg_no']):
                        conn = get_conn()
                        cur = conn.cursor()
                        cur.execute('DELETE FROM users WHERE id=?',(s['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
            with col2:
                st.subheader('Manage Questions')
                for q in questions:
                    st.write(f\"{q['id']}: {q['title']} ({q['subject']})\")
                    if st.button('Delete Q'+str(q['id'])):
                        conn = get_conn()
                        cur = conn.cursor()
                        cur.execute('DELETE FROM questions WHERE id=?',(q['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()

    # Student Registration - hybrid
    if menu == 'Student Registration':
        st.header('Register Student (Password OR Face)')
        reg_no = st.text_input('Registration Number')
        name = st.text_input('Full name')
        email = st.text_input('Email')
        pwd = st.text_input('Password (leave blank to register with face only)', type='password')
        st.write('You may also capture a face image (optional) for biometric login. If you do not provide a password, a face is required.')
        img_file = st.camera_input('Take a close-up face photo (optional)')
        if st.button('Register'):
            if not reg_no or not name:
                st.error('Provide registration number and name.')
            else:
                face_json = None
                if img_file is not None:
                    pil = Image.open(img_file)
                    emb = image_to_embedding(pil)
                    face_json = json.dumps(emb)
                if not pwd and not face_json:
                    st.error('Either a password or a face photo is required.')
                else:
                    ok = utils.add_student(reg_no, name, email, pwd, face_json)
                    if ok:
                        st.success('Student registered.')
                    else:
                        st.error('Registration failed (reg no may exist).')

    # Student Login - hybrid
    if menu == 'Student Login':
        st.header('Student Login (Password OR Face)')
        reg = st.text_input('Registration Number')
        pwd = st.text_input('Password (leave blank to use face)', type='password')
        st.write('Or upload/capture a face photo to login. Photo login will be used if password is blank.')
        img_file = st.camera_input('Take a close-up face photo for login (optional)')
        if st.button('Login'):
            row = utils.get_user_by_reg(reg)
            if not row:
                st.error('User not found.')
            else:
                success = False
                # check password if provided
                if pwd and row['password_hash']:
                    if utils.verify_password(pwd, row['password_hash']):
                        success = True
                # else try face
                if not success and img_file is not None and row['face_embedding']:
                    pil = Image.open(img_file)
                    emb = image_to_embedding(pil)
                    stored = json.loads(row['face_embedding'])
                    sim = cosine_similarity(np.array(stored), np.array(emb))
                    if sim >= 0.90:
                        success = True
                if success:
                    st.session_state['student_logged'] = row['id']
                    st.success('Student logged in')
                else:
                    st.error('Login failed. Provide correct password or a matching face photo.')

    # Student Dashboard
    if menu == 'Student Dashboard':
        if 'student_logged' not in st.session_state:
            st.warning('Please login as student first (Student Login)')
        else:
            st.header('Student Dashboard')
            uid = st.session_state['student_logged']
            user = utils.get_user_by_id(uid)
            st.write(f\"Name: {user['name']}\")
            st.write(f\"Reg No: {user['reg_no']}\")
            conn = get_conn(); cur = conn.cursor()
            cur.execute('SELECT * FROM attempts WHERE user_id=? ORDER BY id DESC',(uid,))
            rows = cur.fetchall()
            st.subheader('Past Attempts')
            for r in rows:
                st.write(f\"{r['created_at']}: {r['score']}/{r['total']}\")
            conn.close()

    # Question Bank
    if menu == 'Question Bank':
        st.header('Question Bank')
        st.subheader('Add Question')
        title = st.text_input('Title')
        body = st.text_area('Question body')
        a = st.text_input('Choice A'); b = st.text_input('Choice B'); c = st.text_input('Choice C'); d = st.text_input('Choice D')
        correct = st.selectbox('Correct choice', ['A','B','C','D'])
        subject = st.text_input('Subject'); difficulty = st.selectbox('Difficulty', ['Easy','Medium','Hard'])
        if st.button('Add Question'):
            utils.add_question(title, body, a,b,c,d,correct,subject,difficulty)
            st.success('Question added')
        st.subheader('Existing Questions')
        qs = utils.list_questions()
        for q in qs:
            st.write(f\"{q['id']}: {q['title']} - {q['subject']} - {q['difficulty']}\")
            st.write(f\"A. {q['choice_a']}  B. {q['choice_b']}  C. {q['choice_c']}  D. {q['choice_d']}\")

    # Exam (Student)
    if menu == 'Exam (Student)':
        st.header('Take Exam')
        if 'student_logged' not in st.session_state:
            st.warning('Please login as student first (Student Login)')
        else:
            uid = st.session_state['student_logged']
            conn = get_conn(); cur = conn.cursor()
            cur.execute('SELECT * FROM questions')
            qs = cur.fetchall()
            if not qs:
                st.info('No questions in bank yet')
            else:
                answers = {}
                for q in qs:
                    st.write(f\"Q{q['id']}: {q['body']}\")
                    ans = st.radio(f\"Select for Q{q['id']}\", ['A','B','C','D'], key=f\"q{q['id']}\")
                    answers[q['id']] = ans
                if st.button('Submit Exam'):
                    score = 0; total = len(qs)
                    cur.execute('INSERT INTO attempts (user_id, score, total, created_at) VALUES (?,?,?,?)', (uid,0,total,str(datetime.datetime.now())))
                    attempt_id = cur.lastrowid
                    for q in qs:
                        sel = answers[q['id']]
                        correct = 1 if sel == q['correct_choice'] else 0
                        if correct: score += 1
                        cur.execute('INSERT INTO answers (attempt_id, question_id, selected_choice, is_correct) VALUES (?,?,?,?)', (attempt_id, q['id'], sel, correct))
                    cur.execute('UPDATE attempts SET score=? WHERE id=?', (score, attempt_id))
                    conn.commit()
                    st.success(f'Exam submitted. Score: {score}/{total}')
            conn.close()

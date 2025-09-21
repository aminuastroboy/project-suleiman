import streamlit as st
from db import init_db, get_conn
import utils, sqlite3, datetime, json
from PIL import Image

init_db()
st.set_page_config(page_title='CBT System - Biometric Live', layout='wide')
st.title('CBT System - Biometric Live (camera_input)')

menu = st.sidebar.selectbox('Go to', ['Home','Admin Login','Admin Dashboard','Student Registration','Student Login','Student Dashboard','Question Bank','Exam (Student)'])

if menu == 'Home':
    st.header('Welcome')
    st.write('Hybrid login: password OR live face (camera). Exams require re-authentication by live face if face is registered.')

if menu == 'Admin Login':
    st.header('Admin Login')
    reg = st.text_input('Admin Reg No (ADMIN001)')
    pwd = st.text_input('Password', type='password')
    if st.button('Login'):
        row = utils.get_user_by_reg(reg)
        if row and row['role']=='admin' and utils.verify_password(pwd,row['password_hash']):
            st.session_state['admin_logged']=row['id']
            st.success('Admin logged in')
        else: st.error('Invalid credentials')

if menu == 'Admin Dashboard':
    if 'admin_logged' not in st.session_state: st.warning('Login as admin first')
    else:
        st.header('Admin Dashboard')
        students=utils.list_students(); qs=utils.list_questions()
        st.write(f'Total students: {len(students)}')
        st.write(f'Total questions: {len(qs)}')
        st.subheader('Students')
        for s in students:
            emb_status = 'Yes' if s['face_embedding'] else 'No'
            st.write(f"{s['reg_no']} - {s['name']} - face registered: {emb_status}")

if menu == 'Student Registration':
    st.header('Register Student (live camera)')
    reg_no=st.text_input('Registration Number')
    name=st.text_input('Full name')
    email=st.text_input('Email')
    pwd=st.text_input('Password (optional)', type='password')
    cam = st.camera_input('Take a face photo (optional) — allow camera access')
    face_emb=None
    if cam is not None:
        img = Image.open(cam)
        st.image(img, caption='Captured face', width=200)
        face_emb = utils.image_to_embedding(img)
    if st.button('Register'):
        if not pwd and face_emb is None:
            st.error('Must provide either password or face')
        else:
            ok=utils.add_student(reg_no,name,email,pwd if pwd else None,face_emb)
            st.success('Student registered' if ok else 'Failed (maybe reg no exists)')

if menu == 'Student Login':
    st.header('Student Login (live camera OR password)')
    reg=st.text_input('Reg No (if using password)')
    pwd=st.text_input('Password', type='password')
    cam = st.camera_input('Or take a live face photo to login (optional)')
    if st.button('Login'):
        # password path
        row=None
        if reg:
            row=utils.get_user_by_reg(reg)
            if row and row['role']=='student' and row['password_hash'] and utils.verify_password(pwd,row['password_hash']):
                st.session_state['student_logged']=row['id']; st.success('Logged in via password'); st.stop()
        # face path
        if cam is not None:
            img = Image.open(cam)
            emb = utils.image_to_embedding(img)
            for stu in utils.list_students():
                if stu['face_embedding']:
                    db_emb=json.loads(stu['face_embedding'])
                    sim=utils.cosine_similarity(emb,db_emb)
                    if sim>0.85:
                        st.session_state['student_logged']=stu['id']; st.success(f'Logged in via face as {stu["name"]}'); st.stop()
        st.error('Login failed')

if menu == 'Student Dashboard':
    if 'student_logged' not in st.session_state: st.warning('Login first')
    else:
        uid=st.session_state['student_logged']; user=utils.get_user_by_id(uid)
        st.header(f'Student Dashboard - {user["name"]}')
        # show past attempts
        conn = get_conn(); cur = conn.cursor()
        cur.execute('SELECT * FROM attempts WHERE user_id=? ORDER BY id DESC',(uid,))
        rows = cur.fetchall()
        st.subheader('Past Attempts')
        for r in rows:
            st.write(f"{r['created_at']}: {r['score']}/{r['total']}")
        conn.close()
        # Start exam button (requires re-auth if face exists)
        if st.button('Start Exam'):
            # check if face registered
            if user['face_embedding']:
                st.info('Face registered for your account. Please re-authenticate with a live face photo to start the exam.')
                cam2 = st.camera_input('Take a live photo to re-authenticate', key='re_auth')
                if cam2 is not None:
                    img = Image.open(cam2)
                    st.image(img, caption='Re-auth photo', width=200)
                    emb = utils.image_to_embedding(img)
                    db_emb = json.loads(user['face_embedding'])
                    sim = utils.cosine_similarity(emb, db_emb)
                    if sim > 0.85:
                        st.success('Re-authentication success. Redirecting to exam...')
                        st.session_state['can_start_exam'] = True
                        st.experimental_rerun()
                    else:
                        st.error(f'Re-authentication failed (similarity={sim:.3f})')
            else:
                # no face; allow password challenge
                pwd_chk = st.text_input('No face on record. Enter your password to start (password required):', type='password')
                if st.button('Verify password to start', key='pwd_start'):
                    if user['password_hash'] and utils.verify_password(pwd_chk, user['password_hash']):
                        st.success('Password verified. You may start the exam.')
                        st.session_state['can_start_exam'] = True
                        st.experimental_rerun()
                    else:
                        st.error('Password incorrect.')

if menu == 'Question Bank':
    st.header('Question Bank (Admin can add via Admin Dashboard)')
    qs=utils.list_questions()
    for q in qs:
        st.write(f"{q['id']}: {q['title']} - {q['subject']}")
        st.write(f"A. {q['choice_a']}  B. {q['choice_b']}  C. {q['choice_c']}  D. {q['choice_d']}")

if menu == 'Exam (Student)':
    st.header('Exam (Student)')
    if 'student_logged' not in st.session_state:
        st.warning('Please login as student first (Student Login)')
    elif not st.session_state.get('can_start_exam', False):
        st.info('Please go to Student Dashboard -> Start Exam and complete re-authentication to begin.')
    else:
        uid = st.session_state['student_logged']
        # load questions
        qs = utils.list_questions()
        if not qs:
            st.info('No questions available.')
        else:
            # init session state for exam
            if 'exam_qs' not in st.session_state:
                st.session_state['exam_qs'] = [dict(q) for q in qs]
                st.session_state['current_q'] = 0
                st.session_state['answers'] = {}
            qidx = st.session_state['current_q']
            q = st.session_state['exam_qs'][qidx]
            st.subheader(f"Question {qidx+1} of {len(st.session_state['exam_qs'])}")
            st.write(q['body'])
            choice = st.radio('Choose', ['A','B','C','D'], index=0, key=f'choice_{qidx}')
            # navigation
            cols = st.columns(3)
            with cols[0]:
                if st.button('Previous') and qidx>0:
                    st.session_state['current_q'] = qidx-1
                    st.experimental_rerun()
            with cols[1]:
                if st.button('Save & Next'):
                    st.session_state['answers'][q['id']] = choice
                    if qidx < len(st.session_state['exam_qs'])-1:
                        st.session_state['current_q'] = qidx+1
                    st.experimental_rerun()
            with cols[2]:
                if st.button('Submit Exam'):
                    # record last answer
                    st.session_state['answers'][q['id']] = choice
                    # grade
                    score = 0; total = len(st.session_state['exam_qs'])
                    conn = get_conn(); cur = conn.cursor()
                    # create attempt with zero score for now
                    cur.execute('INSERT INTO attempts (user_id, score, total, created_at) VALUES (?,?,?,datetime("now"))', (uid, 0, total))
                    attempt_id = cur.lastrowid
                    for qq in st.session_state['exam_qs']:
                        qid = qq['id']
                        sel = st.session_state['answers'].get(qid, None)
                        correct = 1 if sel and sel == qq['correct_choice'] else 0
                        if correct: score += 1
                        cur.execute('INSERT INTO answers (attempt_id, question_id, selected_choice, is_correct) VALUES (?,?,?,?)', (attempt_id, qid, sel if sel else '', correct))
                    cur.execute('UPDATE attempts SET score=? WHERE id=?', (score, attempt_id))
                    conn.commit(); conn.close()
                    # cleanup exam state and deny immediate re-entry until re-auth
                    st.session_state.pop('exam_qs', None)
                    st.session_state.pop('current_q', None)
                    st.session_state.pop('answers', None)
                    st.session_state['can_start_exam'] = False
                    st.success(f'Exam submitted. Score: {score}/{total}')

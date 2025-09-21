import streamlit as st
from db import init_db, get_conn
import utils, sqlite3, datetime, json
from PIL import Image

init_db()
st.set_page_config(page_title='CBT System - Biometric v4', layout='wide')

# ensure page state
if 'page' not in st.session_state:
    st.session_state['page'] = 'home'
if 'student_logged' not in st.session_state:
    st.session_state['student_logged'] = None
if 'admin_logged' not in st.session_state:
    st.session_state['admin_logged'] = None
if 'can_start_exam' not in st.session_state:
    st.session_state['can_start_exam'] = False

def go_to(page):
    st.session_state['page'] = page
    st.experimental_rerun()

def logout_all():
    st.session_state['student_logged'] = None
    st.session_state['admin_logged'] = None
    st.session_state['can_start_exam'] = False
    st.session_state['page'] = 'home'
    st.experimental_rerun()

# Top nav
st.title('CBT System - Biometric v4')
cols = st.columns([1,1,1,1])
with cols[0]:
    if st.button('Home'): go_to('home')
with cols[1]:
    if st.button('Student Login'): go_to('student_login')
with cols[2]:
    if st.button('Student Register'): go_to('student_register')
with cols[3]:
    if st.button('Admin Login'): go_to('admin_login')

# Home
if st.session_state['page'] == 'home':
    st.header('Welcome')
    st.write('Use the top buttons to navigate. Login via password OR live face (camera).')

# Admin Login
if st.session_state['page'] == 'admin_login':
    st.header('Admin Login')
    reg = st.text_input('Admin Reg No', key='admin_reg')
    pwd = st.text_input('Password', type='password', key='admin_pwd')
    if st.button('Login as Admin'):
        row = utils.get_user_by_reg(reg)
        if row and row['role']=='admin' and utils.verify_password(pwd,row['password_hash']):
            st.session_state['admin_logged'] = row['id']
            go_to('admin_dashboard')
        else:
            st.error('Invalid admin credentials')

# Admin Dashboard
if st.session_state['page'] == 'admin_dashboard':
    if not st.session_state['admin_logged']:
        st.warning('Please login as admin')
        if st.button('Go to Admin Login'): go_to('admin_login')
    else:
        st.header('Admin Dashboard')
        st.write('Quick admin tools below.')
        if st.button('Logout Admin'):
            logout_all()
        students = utils.list_students()
        qs = utils.list_questions()
        st.subheader('Overview')
        st.write(f'Total students: {len(students)}')
        st.write(f'Total questions: {len(qs)}')
        st.subheader('Students')
        for s in students:
            emb_status = 'Yes' if s['face_embedding'] else 'No'
            st.write(f"{s['reg_no']} - {s['name']} - face registered: {emb_status}")

# Student Registration
if st.session_state['page'] == 'student_register':
    st.header('Register (live camera)')
    reg_no = st.text_input('Registration Number', key='reg_no')
    name = st.text_input('Full name', key='name')
    email = st.text_input('Email', key='email')
    pwd = st.text_input('Password (optional)', type='password', key='pwd')
    cam = st.camera_input('Take a face photo (optional) — allow camera access', key='reg_cam')
    face_emb = None
    if cam is not None:
        img = Image.open(cam)
        st.image(img, caption='Captured face', width=200)
        face_emb = utils.image_to_embedding(img)
    if st.button('Register Student'):
        if not pwd and face_emb is None:
            st.error('Must provide either password or face')
        else:
            ok = utils.add_student(reg_no, name, email, pwd if pwd else None, face_emb)
            if ok:
                st.success('Registered successfully — please login')
                go_to('student_login')
            else:
                st.error('Registration failed (maybe reg no exists)')

# Student Login
if st.session_state['page'] == 'student_login':
    st.header('Student Login (live camera OR password)')
    reg = st.text_input('Reg No (if using password)', key='login_reg')
    pwd = st.text_input('Password', type='password', key='login_pwd')
    cam = st.camera_input('Or take a live face photo to login (optional)', key='login_cam')
    if st.button('Login Student'):
        # password path
        if reg:
            row = utils.get_user_by_reg(reg)
            if row and row['role']=='student' and row['password_hash'] and utils.verify_password(pwd, row['password_hash']):
                st.session_state['student_logged'] = row['id']
                go_to('student_dashboard')
                st.stop()
        # face path
        if cam is not None:
            img = Image.open(cam)
            emb = utils.image_to_embedding(img)
            for stu in utils.list_students():
                if stu['face_embedding']:
                    db_emb = json.loads(stu['face_embedding'])
                    sim = utils.cosine_similarity(emb, db_emb)
                    if sim > 0.85:
                        st.session_state['student_logged'] = stu['id']
                        go_to('student_dashboard')
                        st.stop()
        st.error('Login failed — check credentials or try face again')

# Student Dashboard
if st.session_state['page'] == 'student_dashboard':
    if not st.session_state['student_logged']:
        st.warning('Please login as student')
        if st.button('Go to Student Login'): go_to('student_login')
    else:
        uid = st.session_state['student_logged']
        user = utils.get_user_by_id(uid)
        st.header(f'Student Dashboard — {user["name"]}')
        if st.button('Logout'):
            logout_all()
        # Past attempts
        conn = get_conn(); cur = conn.cursor()
        cur.execute('SELECT * FROM attempts WHERE user_id=? ORDER BY id DESC',(uid,))
        rows = cur.fetchall()
        st.subheader('Past Attempts')
        for r in rows:
            st.write(f"{r['created_at']}: {r['score']}/{r['total']}")
        conn.close()
        # Start exam flow: re-auth
        if st.button('Start Exam'):
            # require re-auth if face present
            if user['face_embedding']:
                st.session_state['page'] = 're_auth'
                st.experimental_rerun()
            else:
                st.session_state['page'] = 'pwd_auth'
                st.experimental_rerun()

# Re-auth page (face)
if st.session_state['page'] == 're_auth':
    if not st.session_state['student_logged']:
        st.warning('Please login first')
        if st.button('Go to Login'): go_to('student_login')
    else:
        uid = st.session_state['student_logged']; user = utils.get_user_by_id(uid)
        st.header('Re-authenticate (live face) to start exam')
        cam = st.camera_input('Take a live photo to re-authenticate', key='reauth_cam')
        if cam is not None:
            img = Image.open(cam)
            st.image(img, caption='Re-auth photo', width=200)
            emb = utils.image_to_embedding(img)
            db_emb = json.loads(user['face_embedding']) if user['face_embedding'] else None
            if db_emb:
                sim = utils.cosine_similarity(emb, db_emb)
                if sim > 0.85:
                    st.success('Re-auth success — starting exam...')
                    st.session_state['can_start_exam'] = True
                    go_to('exam')
                else:
                    st.error(f'Re-authentication failed (similarity={sim:.3f}) — try again')
            else:
                st.error('No face on record. Use password re-auth instead.')
                if st.button('Use password instead'): go_to('pwd_auth')

# Password auth page (fallback)
if st.session_state['page'] == 'pwd_auth':
    if not st.session_state['student_logged']:
        st.warning('Please login first')
        if st.button('Go to Login'): go_to('student_login')
    else:
        uid = st.session_state['student_logged']; user = utils.get_user_by_id(uid)
        st.header('Password re-auth to start exam')
        pwd_try = st.text_input('Re-enter your password', type='password', key='pwd_reauth')
        if st.button('Verify password'):
            if user['password_hash'] and utils.verify_password(pwd_try, user['password_hash']):
                st.success('Password verified — starting exam...')
                st.session_state['can_start_exam'] = True
                go_to('exam')
            else:
                st.error('Password incorrect')

# Question Bank (simple view/add are under admin dashboard in future)
if st.session_state['page'] == 'question_bank':
    st.header('Question Bank')
    qs = utils.list_questions()
    for q in qs:
        st.write(f"{q['id']}: {q['title']} - {q['subject']}")

# Exam page
if st.session_state['page'] == 'exam':
    if not st.session_state['student_logged']:
        st.warning('Please login first')
        if st.button('Go to Login'): go_to('student_login')
    elif not st.session_state.get('can_start_exam', False):
        st.info('Please complete re-authentication first from your dashboard.')
        if st.button('Go to Dashboard'): go_to('student_dashboard')
    else:
        uid = st.session_state['student_logged']
        # initialize exam state if missing
        if 'exam_qs' not in st.session_state:
            st.session_state['exam_qs'] = [dict(q) for q in utils.list_questions()]
            st.session_state['current_q'] = 0
            st.session_state['answers'] = {}
        qidx = st.session_state['current_q']
        q = st.session_state['exam_qs'][qidx]
        st.subheader(f'Question {qidx+1} of {len(st.session_state["exam_qs"])}')
        st.write(q['body'])
        choice = st.radio('Choose', ['A','B','C','D'], index=0, key=f'choice_{qidx}')
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
                st.session_state['answers'][q['id']] = choice
                # grade and record
                score = 0; total = len(st.session_state['exam_qs'])
                conn = get_conn(); cur = conn.cursor()
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
                # cleanup and require re-auth for next exam
                st.session_state.pop('exam_qs', None)
                st.session_state.pop('current_q', None)
                st.session_state.pop('answers', None)
                st.session_state['can_start_exam'] = False
                st.success(f'Exam submitted. Score: {score}/{total}')
                go_to('student_dashboard')

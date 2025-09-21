import streamlit as st
from PIL import Image
import utils, sqlite3, json
from datetime import datetime

utils.init_db()

st.set_page_config(page_title='CBT Extended', layout='wide')

# session defaults
if 'page' not in st.session_state: st.session_state['page'] = 'home'
if 'user' not in st.session_state: st.session_state['user'] = None

def go(page):
    st.session_state['page'] = page
    st.rerun()

# top nav
col1, col2, col3, col4 = st.columns([1,1,1,1])
with col1:
    if st.button('Home'): go('home')
with col2:
    if st.button('Student Register'): go('register')
with col3:
    if st.button('Student Login'): go('slogin')
with col4:
    if st.button('Admin Login'): go('alogin')

# HOME
if st.session_state['page'] == 'home':
    st.title('CBT — Extended (Admin + Students)')
    st.write('Use the top buttons to navigate.')
    st.write('Seeded admin: ADMIN001 / 1234')

# STUDENT REGISTER
if st.session_state['page'] == 'register':
    st.header('Student Registration (live camera or upload)')
    reg_no = st.text_input('Reg No', key='reg_reg')
    name = st.text_input('Full name', key='reg_name')
    email = st.text_input('Email', key='reg_email')
    pwd = st.text_input('Password (optional)', type='password', key='reg_pwd')
    cam = st.camera_input('Take a face photo (optional)')
    upload = st.file_uploader('Or upload face image (jpg/png)')
    face_bytes = None
    if cam:
        img = Image.open(cam)
        st.image(img, width=200)
        emb = utils.image_to_embedding(img)
        face_bytes = utils.embedding_to_bytes(emb)
    elif upload:
        img = Image.open(upload)
        st.image(img, width=200)
        emb = utils.image_to_embedding(img)
        face_bytes = utils.embedding_to_bytes(emb)

    if st.button('Register Student'):
        if not reg_no or (not pwd and not face_bytes):
            st.error('Provide reg_no and at least password or face.')
        else:
            ph = utils.hash_password(pwd) if pwd else None
            ok = utils.add_student(reg_no, name, email, ph, face_bytes)
            if ok:
                st.success('Student registered successfully. Go to Student Login.')
                go('slogin')
            else:
                st.error('Registration failed (reg_no may exist).')

# STUDENT LOGIN
if st.session_state['page'] == 'slogin':
    st.header('Student Login')
    reg_no = st.text_input('Reg No', key='login_reg')
    pwd = st.text_input('Password', type='password', key='login_pwd')
    cam = st.camera_input('Or take a live face photo (optional)')
    if st.button('Login Student'):
        user = None
        if reg_no and pwd:
            row = utils.get_user_by_reg(reg_no)
            if row and row['role']=='student' and utils.verify_password(pwd, row['password_hash'] or ''):
                user = {'id': row['id'], 'reg_no': row['reg_no'], 'name': row['name']}
        if not user and cam:
            img = Image.open(cam); emb = utils.image_to_embedding(img)
            # check all students
            rows = utils.list_students()
            for r in rows:
                if r['face_embedding']:
                    ok, sim = utils.compare_embeddings(emb, r['face_embedding'])
                    if ok:
                        user = {'id': r['id'], 'reg_no': r['reg_no'], 'name': r['name']}
                        break
        if user:
            st.session_state['user'] = user
            st.success(f"Welcome, {user['name']}")
            go('sdash')
        else:
            st.error('Login failed.')

# STUDENT DASHBOARD
if st.session_state['page'] == 'sdash':
    if not st.session_state['user']:
        st.warning('Please login first.'); st.button('Go to login', on_click=lambda: go('slogin'))
    else:
        user = st.session_state['user']
        st.header(f"Student Dashboard — {user['name']}")
        if st.button('Start Exam'): go('reauth')
        if st.button('Logout'):
            st.session_state['user'] = None; go('home')
        # past attempts
        conn = utils.get_conn(); cur = conn.cursor()
        cur.execute('SELECT * FROM attempts WHERE user_id=? ORDER BY id DESC',(user['id'],))
        atts = cur.fetchall(); conn.close()
        st.subheader('Past Attempts')
        if atts:
            for a in atts:
                st.write(f"{a['created_at']}: {a['score']}/{a['total']}")
        else:
            st.write('No attempts yet.')

# RE-AUTH (face or password) before exam
if st.session_state['page'] == 'reauth':
    if not st.session_state['user']:
        st.warning('Please login first'); st.button('Go to login', on_click=lambda: go('slogin'))
    else:
        st.header('Re-authenticate to start exam')
        user = st.session_state['user']
        cam = st.camera_input('Take a live photo to re-authenticate')
        if cam:
            img = Image.open(cam); emb = utils.image_to_embedding(img)
            conn = utils.get_conn(); cur = conn.cursor()
            cur.execute('SELECT face_embedding FROM users WHERE id=?',(user['id'],))
            row = cur.fetchone(); conn.close()
            stored = row['face_embedding'] if row else None
            ok, sim = utils.compare_embeddings(emb, stored)
            if ok:
                st.success(f'Re-auth success (sim={sim:.3f}). Starting exam...'); go('exam')
            else:
                st.error(f'Re-auth failed (sim={sim:.3f}). Use password fallback below.')
        st.write('---')
        pwd = st.text_input('Or enter your password', type='password', key='reauth_pwd')
        if st.button('Verify password'):
            conn = utils.get_conn(); cur = conn.cursor()
            cur.execute('SELECT password_hash FROM users WHERE id=?',(user['id'],))
            row = cur.fetchone(); conn.close()
            if row and utils.verify_password(pwd, row['password_hash'] or ''):
                st.success('Password verified. Starting exam...'); go('exam')
            else:
                st.error('Password incorrect.')

# EXAM page (per-question navigation)
if st.session_state['page'] == 'exam':
    if not st.session_state['user']:
        st.warning('Please login.'); st.button('Go to login', on_click=lambda: go('slogin'))
    else:
        st.header('Exam — Answer questions and submit')
        # load questions
        qs = utils.list_questions()
        if not qs:
            st.info('No questions in question bank yet.')
        else:
            if 'exam_qs' not in st.session_state:
                st.session_state['exam_qs'] = [dict(q) for q in qs]
                st.session_state['current_q'] = 0
                st.session_state['answers'] = {}
            idx = st.session_state['current_q']
            q = st.session_state['exam_qs'][idx]
            st.subheader(f"Question {idx+1} of {len(st.session_state['exam_qs'])}")
            st.write(q['body'])
            choice = st.radio('Select', ['A','B','C','D'], key=f"choice_{q['id']}")
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button('Previous') and idx>0:
                    st.session_state['current_q'] -= 1; st.experimental_rerun()
            with c2:
                if st.button('Save & Next'):
                    st.session_state['answers'][q['id']] = choice
                    if idx < len(st.session_state['exam_qs'])-1:
                        st.session_state['current_q'] += 1
                    st.experimental_rerun()
            with c3:
                if st.button('Submit Exam'):
                    st.session_state['answers'][q['id']] = choice
                    # grade and persist
                    score = 0; total = len(st.session_state['exam_qs'])
                    conn = utils.get_conn(); cur = conn.cursor()
                    cur.execute('INSERT INTO attempts (user_id, score, total, created_at) VALUES (?,?,?,?)',
                                (st.session_state['user']['id'], 0, total, datetime.utcnow().isoformat()))
                    attempt_id = cur.lastrowid
                    for qq in st.session_state['exam_qs']:
                        qid = qq['id']
                        sel = st.session_state['answers'].get(qid, '') 
                        correct = 1 if sel and sel == qq['correct_choice'] else 0
                        if correct: score += 1
                        cur.execute('INSERT INTO answers (attempt_id, question_id, selected_choice, is_correct) VALUES (?,?,?,?)',
                                    (attempt_id, qid, sel, correct))
                    cur.execute('UPDATE attempts SET score=? WHERE id=?', (score, attempt_id))
                    conn.commit(); conn.close()
                    st.success(f'Exam submitted. Score: {score}/{total}')
                    # cleanup
                    for k in ['exam_qs','current_q','answers']:
                        if k in st.session_state: st.session_state.pop(k)
                    go('sdash')

# ADMIN LOGIN
if st.session_state['page'] == 'alogin':
    st.header('Admin Login')
    reg = st.text_input('Admin reg_no', key='admin_reg')
    pwd = st.text_input('Password', type='password', key='admin_pwd')
    if st.button('Login as admin'):
        row = utils.get_user_by_reg(reg)
        if row and row['role']=='admin' and utils.verify_password(pwd, row['password_hash'] or ''):
            st.session_state['user'] = {'id': row['id'], 'name': row['name'], 'role': 'admin'}
            go('adash')
        else:
            st.error('Invalid admin credentials.')

# ADMIN DASHBOARD
if st.session_state['page'] == 'adash':
    if not st.session_state['user'] or st.session_state['user'].get('role')!='admin':
        st.warning('Please login as admin'); st.button('Go to admin login', on_click=lambda: go('alogin'))
    else:
        st.title('Admin Dashboard')
        if st.button('Logout admin'):
            st.session_state['user'] = None; go('home')
        st.subheader('Students')
        rows = utils.list_students()
        for r in rows:
            emb_status = 'Yes' if r['face_embedding'] else 'No'
            st.write(f"{r['reg_no']} - {r['name']} (face: {emb_status})")
            if st.button('Delete '+r['reg_no']):
                conn = utils.get_conn(); cur = conn.cursor()
                cur.execute('DELETE FROM users WHERE id=?',(r['id'],))
                conn.commit(); conn.close()
                st.experimental_rerun()
        st.subheader('Question Bank')
        qs = utils.list_questions()
        for q in qs:
            st.write(f"{q['id']}: {q['title']} — {q['subject']} ({q['difficulty']})")
            st.write(f"A. {q['choice_a']}  B. {q['choice_b']}  C. {q['choice_c']}  D. {q['choice_d']}")
            if st.button('Delete Q'+str(q['id'])):
                conn = utils.get_conn(); cur = conn.cursor()
                cur.execute('DELETE FROM questions WHERE id=?',(q['id'],))
                conn.commit(); conn.close()
                st.experimental_rerun()
        st.write('---')
        st.subheader('Add New Question')
        title = st.text_input('Title', key='q_title'); body = st.text_area('Body', key='q_body')
        a = st.text_input('Choice A', key='q_a'); b = st.text_input('Choice B', key='q_b')
        c = st.text_input('Choice C', key='q_c'); d = st.text_input('Choice D', key='q_d')
        correct = st.selectbox('Correct choice', ['A','B','C','D'], key='q_correct')
        subject = st.text_input('Subject', key='q_sub', value='General')
        diff = st.selectbox('Difficulty', ['Easy','Medium','Hard'], key='q_diff')
        if st.button('Add Question'):
            mapping = {'A':a,'B':b,'C':c,'D':d}
            correct_text = mapping[correct]
            utils.add_question(title, body, a,b,c,d, correct, subject, diff)
            st.success('Question added.')
            st.experimental_rerun()

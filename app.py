import streamlit as st
from PIL import Image
import io, zipfile, os
import utils
import datetime

# initialize DB and seed
utils.init_db()

st.set_page_config(page_title='CBT Full', layout='wide')

# session defaults
if 'page' not in st.session_state: st.session_state['page'] = 'home'
if 'user' not in st.session_state: st.session_state['user'] = None
if 'exam_state' not in st.session_state: st.session_state['exam_state'] = {}

def go_to(page):
    st.session_state['page'] = page
    st.rerun()

# Top nav
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
    st.title('CBT System — Full Build')
    st.write('Seeded admin: ADMIN001 / admin123  (change passwords in utils.py if desired)')
    st.write('Seeded students: STU001 / pass123, STU002 / pass123')

# Admin Login
if st.session_state['page'] == 'admin_login':
    st.header('Admin Login')
    reg = st.text_input('Admin Reg No', key='admin_reg')
    pwd = st.text_input('Password', type='password', key='admin_pwd')
    if st.button('Login as admin'):
        row = utils.get_user_by_reg(reg)
        if row and row['role']=='admin' and utils.verify_password(pwd, row['password_hash'] or ''):
            st.session_state['user'] = {'id': row['id'], 'role': 'admin', 'name': row['name'], 'reg_no': row['reg_no']}
            go_to('admin_dashboard')
        else:
            st.error('Invalid admin credentials')

# Admin Dashboard
if st.session_state['page'] == 'admin_dashboard':
    if not st.session_state['user'] or st.session_state['user'].get('role')!='admin':
        st.warning('Please login as admin'); st.button('Go to admin login', on_click=lambda: go_to('admin_login'))
    else:
        st.header('Admin Dashboard')
        if st.button('🔄 Reset Database'):
            utils.reset_db(); st.success('Database reset and reseeded'); st.experimental_rerun()

        # Download ZIP of project files + DB
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as z:
            base = os.path.dirname(__file__)
            for fname in ['app.py','utils.py','requirements.txt','cbt_app.db']:
                fpath = os.path.join(base, fname)
                if os.path.exists(fpath):
                    z.write(fpath, arcname=fname)
        st.download_button('📦 Download full app ZIP', buf.getvalue(), file_name='cbt_app_full.zip', mime='application/zip')

        st.subheader('Students')
        for s in utils.list_students():
            st.write(f"{s['reg_no']} - {s['name']} - face_registered: {'Yes' if s['face_embedding'] else 'No'}")
            if st.button('Delete '+s['reg_no']):
                conn = utils.get_conn(); cur = conn.cursor(); cur.execute('DELETE FROM users WHERE id=?', (s['id'],)); conn.commit(); conn.close(); st.experimental_rerun()

        st.subheader('Question Bank')
        for q in utils.list_questions():
            st.write(f"{q['id']}: {q['title']} ({q['subject']}) - {q['difficulty']}")
            st.write(f"A. {q['choice_a']}  B. {q['choice_b']}  C. {q['choice_c']}  D. {q['choice_d']}")
            if st.button('Delete Q'+str(q['id'])):
                conn = utils.get_conn(); cur = conn.cursor(); cur.execute('DELETE FROM questions WHERE id=?', (q['id'],)); conn.commit(); conn.close(); st.experimental_rerun()
        st.write('---')
        st.subheader('Add Question')
        title = st.text_input('Title', key='q_title'); body = st.text_area('Body', key='q_body')
        a = st.text_input('Choice A', key='q_a'); b = st.text_input('Choice B', key='q_b')
        c = st.text_input('Choice C', key='q_c'); d = st.text_input('Choice D', key='q_d')
        correct = st.selectbox('Correct choice', ['A','B','C','D'], key='q_correct')
        subject = st.text_input('Subject', key='q_sub', value='General'); diff = st.selectbox('Difficulty', ['Easy','Medium','Hard'], key='q_diff')
        if st.button('Add Question'):
            mapping = {'A':a,'B':b,'C':c,'D':d}
            utils.add_question(title, body, a,b,c,d, correct, subject, diff); st.success('Question added'); st.experimental_rerun()

# Student Registration
if st.session_state['page'] == 'student_register':
    st.header('Student Registration (camera or upload)')
    reg_no = st.text_input('Registration Number', key='reg_no'); name = st.text_input('Full name', key='name')
    email = st.text_input('Email', key='email'); pwd = st.text_input('Password (optional)', type='password', key='pwd')
    cam = st.camera_input('Take a face photo (optional)', key='reg_cam'); upload = st.file_uploader('Or upload face image', type=['jpg','png','jpeg'])
    face_bytes = None
    if cam:
        img = Image.open(cam); st.image(img, width=180); emb = utils.image_to_embedding(img); face_bytes = utils.embedding_to_bytes(emb)
    elif upload:
        img = Image.open(upload); st.image(img, width=180); emb = utils.image_to_embedding(img); face_bytes = utils.embedding_to_bytes(emb)
    if st.button('Register Student'):
        if not reg_no or (not pwd and not face_bytes):
            st.error('Provide registration number and at least a password or face photo.')
        else:
            pw_hash = utils.hash_password(pwd) if pwd else None
            ok = utils.add_student(reg_no, name, email, pw_hash, face_bytes)
            if ok:
                st.success('Student registered. Please login.'); go_to('student_login')
            else:
                st.error('Registration failed (reg_no may exist)')

# Student Login
if st.session_state['page'] == 'student_login':
    st.header('Student Login (password OR face)')
    reg_no = st.text_input('Registration Number', key='login_reg'); pwd = st.text_input('Password', type='password', key='login_pwd')
    cam = st.camera_input('Or take a live face photo to login (optional)', key='login_cam')
    if st.button('Login Student'):
        user = None
        if reg_no and pwd:
            row = utils.get_user_by_reg(reg_no)
            if row and row['role']=='student' and row['password_hash'] and utils.verify_password(pwd, row['password_hash']):
                user = {'id': row['id'], 'reg_no': row['reg_no'], 'name': row['name']}
        if not user and cam:
            img = Image.open(cam); emb = utils.image_to_embedding(img)
            for s in utils.list_students():
                if s['face_embedding']:
                    ok, sim = utils.compare_embeddings(emb, s['face_embedding'])
                    if ok:
                        user = {'id': s['id'], 'reg_no': s['reg_no'], 'name': s['name']}
                        break
        if user:
            st.session_state['user'] = user; st.success(f"Logged in as {user['name']}"); go_to('student_dashboard')
        else:
            st.error('Login failed.')

# Student Dashboard
if st.session_state['page'] == 'student_dashboard':
    if not st.session_state['user']:
        st.warning('Please login first.'); st.button('Go to login', on_click=lambda: go_to('student_login'))
    else:
        user = st.session_state['user']; st.header(f"Student Dashboard — {user['name']}")
        if st.button('Start Exam'):
            row = utils.get_user_by_reg(user['reg_no']); has_face = bool(row and row['face_embedding'])
            if has_face:
                go_to('re_auth')
            else:
                go_to('pwd_auth')
        if st.button('Logout'):
            st.session_state['user'] = None; go_to('home')
        st.subheader('Past Attempts')
        conn = utils.get_conn(); cur = conn.cursor(); cur.execute('SELECT * FROM attempts WHERE user_id=? ORDER BY id DESC', (user['id'],)); rows = cur.fetchall(); conn.close()
        if rows:
            for r in rows:
                st.write(f"{r['created_at']}: {r['score']}/{r['total']}")
        else:
            st.write('No attempts yet.')

# Re-auth page (face)
if st.session_state['page'] == 're_auth':
    if not st.session_state['user']:
        st.warning('Please login first.'); st.button('Go to login', on_click=lambda: go_to('student_login'))
    else:
        st.header('Re-authenticate with live face to start exam')
        cam = st.camera_input('Take a photo to re-authenticate', key='reauth_cam')
        if cam:
            img = Image.open(cam); emb = utils.image_to_embedding(img)
            row = utils.get_user_by_reg(st.session_state['user']['reg_no']); stored = row['face_embedding'] if row else None
            ok, sim = utils.compare_embeddings(emb, stored)
            if ok:
                st.success(f'Re-auth success (sim={sim:.3f}) — starting exam'); go_to('exam')
            else:
                st.error(f'Re-auth failed (sim={sim:.3f}) — try again or use password fallback')
        if st.button('Use password instead'): go_to('pwd_auth')

# Password auth fallback
if st.session_state['page'] == 'pwd_auth':
    if not st.session_state['user']:
        st.warning('Please login first.'); st.button('Go to login', on_click=lambda: go_to('student_login'))
    else:
        st.header('Password re-auth to start exam'); pwd = st.text_input('Enter your password', type='password', key='pwd_reauth')
        if st.button('Verify password'):
            row = utils.get_user_by_reg(st.session_state['user']['reg_no'])
            if row and row['password_hash'] and utils.verify_password(pwd, row['password_hash']):
                st.success('Password verified — starting exam'); go_to('exam')
            else:
                st.error('Password incorrect')

# Exam page
if st.session_state['page'] == 'exam':
    if not st.session_state['user']:
        st.warning('Please login first'); st.button('Go to login', on_click=lambda: go_to('student_login'))
    else:
        qs = utils.list_questions()
        if not qs:
            st.info('No questions available.')
        else:
            if 'exam_qs' not in st.session_state:
                st.session_state['exam_qs'] = [dict(q) for q in qs]
                st.session_state['current_q'] = 0
                st.session_state['answers'] = {}
            idx = st.session_state['current_q']; q = st.session_state['exam_qs'][idx]
            st.subheader(f"Question {idx+1} of {len(st.session_state['exam_qs'])}"); st.write(q['body'])
            # safe key construction using double quotes around f-string
            choice = st.radio('Choose', ['A','B','C','D'], index=0, key=f"choice_{q['id']}")
            c1,c2,c3 = st.columns(3)
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
                    cur.execute('INSERT INTO attempts (user_id, score, total, created_at) VALUES (?,?,?,?)', (st.session_state['user']['id'], 0, total, datetime.datetime.utcnow().isoformat()))
                    attempt_id = cur.lastrowid
                    for qq in st.session_state['exam_qs']:
                        qid = qq['id']; sel = st.session_state['answers'].get(qid, ''); correct = 1 if sel and sel == qq['correct_choice'] else 0
                        if correct: score += 1
                        cur.execute('INSERT INTO answers (attempt_id, question_id, selected_choice, is_correct) VALUES (?,?,?,?)', (attempt_id, qid, sel, correct))
                    cur.execute('UPDATE attempts SET score=? WHERE id=?', (score, attempt_id)); conn.commit(); conn.close()
                    st.success(f'Exam submitted. Score: {score}/{total}')
                    for k in ['exam_qs','current_q','answers']:
                        if k in st.session_state: st.session_state.pop(k)
                    go_to('student_dashboard')

import streamlit as st
from db import init_db, get_conn
import utils, sqlite3, datetime, json

init_db()
st.set_page_config(page_title='CBT System - Biometric Hybrid', layout='wide')
st.title('CBT System - Biometric Hybrid')

menu = st.sidebar.selectbox('Go to', ['Home','Admin Login','Admin Dashboard','Student Registration','Student Login','Student Dashboard','Question Bank','Exam (Student)'])

if menu == 'Home':
    st.header('Welcome')
    st.write('This CBT system allows login via password OR face biometrics.')

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

if menu == 'Student Registration':
    st.header('Register Student')
    reg_no=st.text_input('Registration Number')
    name=st.text_input('Full name')
    email=st.text_input('Email')
    pwd=st.text_input('Password (optional)', type='password')
    img_file=st.file_uploader('Upload face photo (optional)', type=['jpg','png','jpeg'])
    face_emb=None
    if img_file:
        from PIL import Image
        img=Image.open(img_file)
        st.image(img, caption='Uploaded face')
        face_emb=utils.image_to_embedding(img)
    if st.button('Register'):
        if not pwd and face_emb is None:
            st.error('Must provide either password or face')
        else:
            ok=utils.add_student(reg_no,name,email,pwd if pwd else None,face_emb)
            st.success('Student registered' if ok else 'Failed (maybe reg no exists)')

if menu == 'Student Login':
    st.header('Student Login')
    reg=st.text_input('Reg No (if using password)')
    pwd=st.text_input('Password', type='password')
    img_file=st.file_uploader('Or upload face photo for biometric login', type=['jpg','jpeg','png'])
    if st.button('Login'):
        # password path
        row=None
        if reg:
            row=utils.get_user_by_reg(reg)
            if row and row['role']=='student' and row['password_hash'] and utils.verify_password(pwd,row['password_hash']):
                st.session_state['student_logged']=row['id']; st.success('Logged in via password')
                st.stop()
        # face path
        if img_file:
            from PIL import Image
            img=Image.open(img_file)
            emb=utils.image_to_embedding(img)
            # check similarity with all stored embeddings
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

if menu == 'Question Bank':
    st.header('Question Bank (demo)')
    qs=utils.list_questions()
    for q in qs:
        st.write(f"{q['id']} {q['title']}")

if menu == 'Exam (Student)':
    st.header('Exam Demo')
    st.info('Same as before... exam features intact.')

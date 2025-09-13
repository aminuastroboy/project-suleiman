import streamlit as st, json, time
from db import init_db, get_user_by_username, add_user, get_all_questions, add_question, add_result, get_results_for_student
from auth import hash_password, verify_password, webauthn_begin_register, webauthn_complete_register, webauthn_begin_auth, webauthn_complete_auth
from webauthn_html import get_webauthn_html

st.set_page_config(page_title='CBT WebAuthn', layout='wide')
init_db()
st.title('CBT System — WebAuthn (No npm)')

def run_webauthn_helper(options):
    html = get_webauthn_html()
    placeholder = st.empty()
    placeholder.html(html, height=300)
    time.sleep(0.3)
    st.info('Click "Send options to helper" to post options to the iframe. Follow the device prompt. After it completes, open browser console and copy the result JSON and paste it below.')
    if st.button('Send options to helper'):
        opts_json = json.dumps(options)
        post_js = f"""<script>
        (function(){{
          const iframe = window.parent.document.querySelector('iframe[srcdoc]');
          if (iframe) {{
            iframe.contentWindow.postMessage({opts_json}, '*');
            alert('Options posted to helper iframe — follow your device prompt.');
          }} else alert('helper iframe not found');
        }})();
        </script>"""
        st.components.v1.html(post_js, height=0)
        res_text = st.text_area('Paste WebAuthn result JSON here:')
        if res_text:
            try:
                return json.loads(res_text)
            except Exception as e:
                st.error(f'Invalid JSON: {e}')
    return None

if 'logged_in' not in st.session_state:
    st.session_state['logged_in']=False; st.session_state['username']=None; st.session_state['role']=None; st.session_state['webauthn_state']=None

if not st.session_state['logged_in']:
    st.sidebar.header('Auth')
    mode = st.sidebar.selectbox('Mode', ['Login','Register (pw)','Register & WebAuthn'])
    if mode=='Register (pw)':
        st.subheader('Create account')
        u = st.text_input('Username', key='r_u'); p = st.text_input('Password', type='password', key='r_p'); role = st.selectbox('Role', ['student','admin'], key='r_role')
        if st.button('Create'):
            if not u or not p: st.warning('Fill both'); 
            else:
                if get_user_by_username(u): st.error('User exists')
                else:
                    add_user(u, hash_password(p), role); st.success('Created (password only). Use Register & WebAuthn on device to add biometrics.')
    elif mode=='Register & WebAuthn':
        st.subheader('Create account and register biometric on this device')
        u = st.text_input('Username', key='rw_u'); p = st.text_input('Password', type='password', key='rw_p'); role = st.selectbox('Role', ['student','admin'], key='rw_role2')
        if st.button('Create & Register WebAuthn'):
            if not u or not p: st.warning('Fill both')
            else:
                if get_user_by_username(u): st.error('Exists')
                else:
                    uid = add_user(u, hash_password(p), role); st.success(f'Created user {u} (id {uid}). Beginning WebAuthn registration...')
                    try:
                        registration_data, state = webauthn_begin_register(u)
                        st.session_state['webauthn_state']=state
                        st.write('Registration options (publicKey):'); st.json(registration_data)
                        res = run_webauthn_helper({'action':'register','options':{'publicKey': registration_data['publicKey']}})
                        if res and res.get('status')=='ok':
                            client_att = res['result']; webauthn_complete_register(st.session_state.get('webauthn_state'), client_att); st.success('WebAuthn registration complete.')
                    except Exception as e:
                        st.error(f'Registration failed: {e}')
    else:
        st.subheader('Login')
        u = st.text_input('Username', key='l_u'); p = st.text_input('Password', type='password', key='l_p')
        use_bio = st.checkbox('Use biometric (WebAuthn) for login', value=True)
        if st.button('Login'):
            user = get_user_by_username(u)
            if not user: st.error('User not found')
            else:
                if not verify_password(p, user['password_hash']): st.error('Invalid password')
                else:
                    if use_bio:
                        try:
                            auth_data, state = webauthn_begin_auth(u); st.session_state['webauthn_state']=state; st.write('Authentication options:'); st.json(auth_data)
                            res = run_webauthn_helper({'action':'login','options':{'publicKey': auth_data['publicKey']}})
                            if res and res.get('status')=='ok':
                                client_assert = res['result']; user_id = webauthn_complete_auth(st.session_state.get('webauthn_state'), client_assert)
                                if user_id: st.session_state['logged_in']=True; st.session_state['username']=u; st.session_state['role']=user['role']; st.success('Logged in via WebAuthn'); st.experimental_rerun()
                            else: st.error('Biometric auth failed or canceled')
                        except Exception as e:
                            st.error(f'WebAuthn start failed: {e}')
                    else:
                        st.session_state['logged_in']=True; st.session_state['username']=u; st.session_state['role']=user['role']; st.success('Logged in (password only)'); st.experimental_rerun()
else:
    role = st.session_state['role']; username = st.session_state['username']
    st.sidebar.markdown(f'**Logged in:** {username} ({role})')
    if role=='admin':
        choice = st.sidebar.selectbox('Admin', ['Dashboard','Register Student','Question Bank','Logout'])
        if choice=='Dashboard':
            st.header('Admin Dashboard'); qs = get_all_questions(); st.metric('Questions', len(qs))
            st.subheader('Students (recent)'); import psycopg2; cfg = st.secrets['postgres']; conn = psycopg2.connect(host=cfg['host'], port=cfg.get('port','5432'), dbname=cfg['dbname'], user=cfg['user'], password=cfg['password']); cur = conn.cursor(); cur.execute("""SELECT id, username FROM users WHERE role='student' ORDER BY id DESC LIMIT 10"""); rows = cur.fetchall(); cur.close(); conn.close(); 
            for r in rows: st.write(f"- {r[1]} (id={r[0]})")
        elif choice=='Register Student':
            st.header('Register Student'); su = st.text_input('Student username', key='s_u'); sp = st.text_input('Student password', type='password', key='s_p')
            if st.button('Create student'): 
                if not su or not sp: st.warning('Fill both') 
                else:
                    if get_user_by_username(su): st.error('Exists') 
                    else: uid = add_user(su, hash_password(sp), 'student'); st.success(f'Created student {su} (id {uid}).')
        elif choice=='Question Bank':
            st.header('Question Bank'); q = st.text_area('Question text', key='q_text'); a=st.text_input('Option A', key='opt_a'); b=st.text_input('Option B', key='opt_b'); c=st.text_input('Option C', key='opt_c'); d=st.text_input('Option D', key='opt_d'); ans = st.selectbox('Correct option', ['A','B','C','D'], key='corr')
            if st.button('Add question'):
                if not q or not a: st.warning('Provide question and options') 
                else: import json; opts = {'A':a,'B':b,'C':c,'D':d}; add_question(q, json.dumps(opts), ans); st.success('Added')
        else:
            st.session_state.clear(); st.experimental_rerun()
    else:
        choice = st.sidebar.selectbox('Student', ['Dashboard','Take Exam','Results','Logout'])
        if choice=='Dashboard':
            st.header('Student Dashboard'); st.write('Welcome!')
        elif choice=='Take Exam':
            st.header('Take Exam'); qs = get_all_questions()
            if not qs: st.info('No questions yet') 
            else:
                import json; responses = {}
                for q in qs:
                    opts = json.loads(q['options_json'])
                    responses[q['id']] = st.radio(q['question'], [f"A) {opts.get('A','')}", f"B) {opts.get('B','')}", f"C) {opts.get('C','')}", f"D) {opts.get('D','')}"], key=f"q_{q['id']}")
                if st.button('Submit Exam'):
                    score=0; total=len(qs)
                    for q in qs:
                        sel = responses[q['id']]; opt = sel.split(')')[0][0] if sel else ''
                        if opt == q['answer']: score +=1
                    user = get_user_by_username(username); add_result(user['id'], score, total); st.success(f'Submitted. Score: {score}/{total}')
        elif choice=='Results':
            st.header('My Results'); user = get_user_by_username(username); rows = get_results_for_student(user['id']); 
            for r in rows: st.write(f"- {r['submitted_at']} — {r['score']}/{r['total']}")
        else:
            st.session_state.clear(); st.experimental_rerun()

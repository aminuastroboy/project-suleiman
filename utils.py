import requests, hashlib, bcrypt
from db import get_conn
DETECT_URL='https://api-us.faceplusplus.com/facepp/v3/detect'
FACESET_CREATE_URL='https://api-us.faceplusplus.com/facepp/v3/faceset/create'
FACESET_ADD_URL='https://api-us.faceplusplus.com/facepp/v3/faceset/addface'
SEARCH_URL='https://api-us.faceplusplus.com/facepp/v3/search'

def detect_face_bytes(image_bytes,api_key,api_secret):
    files={'image_file':('img.jpg',image_bytes)}
    data={'api_key':api_key,'api_secret':api_secret}
    res=requests.post(DETECT_URL,data=data,files=files).json()
    if res.get('faces'): return res['faces'][0]['face_token']
    return None

def ensure_faceset(api_key,api_secret,outer_id='cbt_students'):
    data={'api_key':api_key,'api_secret':api_secret,'outer_id':outer_id,'display_name':outer_id}
    res=requests.post(FACESET_CREATE_URL,data=data).json(); return res

def add_face_to_faceset(face_token,api_key,api_secret,outer_id='cbt_students'):
    data={'api_key':api_key,'api_secret':api_secret,'outer_id':outer_id,'face_tokens':face_token}
    res=requests.post(FACESET_ADD_URL,data=data).json(); return res

def search_face_bytes(image_bytes,api_key,api_secret,outer_id='cbt_students'):
    files={'image_file':('img.jpg',image_bytes)}
    data={'api_key':api_key,'api_secret':api_secret,'outer_id':outer_id}
    res=requests.post(SEARCH_URL,data=data,files=files).json(); return res

def add_student(reg_no,name,email,password,face_token=None):
    conn=get_conn();cur=conn.cursor()
    ph=bcrypt.hashpw(password.encode(),bcrypt.gensalt()) if password else None
    try:
        cur.execute("INSERT INTO users (reg_no,name,email,password_hash,role,face_token) VALUES (?,?,?,?,?,?)",(reg_no,name,email,ph,"student",face_token))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def list_students():
    conn=get_conn();cur=conn.cursor();cur.execute("SELECT * FROM users WHERE role='student'");rows=cur.fetchall();conn.close();return rows

def get_user_by_reg(reg_no):
    conn=get_conn();cur=conn.cursor();cur.execute("SELECT * FROM users WHERE reg_no=?",(reg_no,));row=cur.fetchone();conn.close();return row

def update_user_face(reg_no,face_token):
    conn=get_conn();cur=conn.cursor();cur.execute("UPDATE users SET face_token=? WHERE reg_no=?",(face_token,reg_no));conn.commit();conn.close()

def list_questions():
    conn=get_conn();cur=conn.cursor();cur.execute("SELECT * FROM questions");rows=cur.fetchall();conn.close();return rows

def reset_password(reg_no,new_password):
    ph=bcrypt.hashpw(new_password.encode(),bcrypt.gensalt())
    conn=get_conn();cur=conn.cursor();cur.execute("UPDATE users SET password_hash=? WHERE reg_no=?",(ph,reg_no));conn.commit();conn.close()

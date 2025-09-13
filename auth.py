import bcrypt, json
import db, webauthn_server
from db import get_user_by_username, add_user, get_credentials_for_user

def hash_password(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def verify_password(pwd: str, hashed: str) -> bool:
    return bcrypt.checkpw(pwd.encode(), hashed.encode())

def register_user(username: str, password: str, role: str='student'):
    return add_user(username, hash_password(password), role)

def webauthn_begin_register(username: str):
    user = get_user_by_username(username)
    if not user:
        raise Exception('user not found')
    data, state = webauthn_server.begin_registration({'id': user['id'], 'username': user['username']})
    return data, state

def webauthn_complete_register(state, client_attestation):
    return webauthn_server.complete_registration(state, client_attestation)

def webauthn_begin_auth(username: str):
    user = get_user_by_username(username)
    if not user:
        raise Exception('user not found')
    creds = get_credentials_for_user(user['id'])
    allow_ids = [c['credential_id'] for c in creds]
    auth_data, state = webauthn_server.begin_authentication(allow_ids)
    return auth_data, state

def webauthn_complete_auth(state, client_assertion):
    return webauthn_server.complete_authentication(state, client_assertion)

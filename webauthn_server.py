from fido2.server import Fido2Server
from fido2.webauthn import PublicKeyCredentialRpEntity
from fido2.utils import websafe_encode, websafe_decode
import db

# Set this to your domain (no protocol) in production, e.g. 'your-app-name.streamlitapp.com'
RP_ID = "localhost"
RP_NAME = "CBT WebAuthn App"

rp = PublicKeyCredentialRpEntity(id=RP_ID, name=RP_NAME)
server = Fido2Server(rp)

def b64enc(b: bytes) -> str:
    return websafe_encode(b).decode('utf-8')

def b64dec(s: str) -> bytes:
    return websafe_decode(s.encode('utf-8'))

def begin_registration(user):
    user_handle = str(user['id']).encode('utf-8')
    user_entity = {'id': user_handle, 'name': user['username'], 'displayName': user['username']}
    registration_data, state = server.register_begin(user_entity, user_verification='discouraged')
    pd = registration_data
    pd['publicKey']['challenge'] = b64enc(pd['publicKey']['challenge'])
    pd['publicKey']['user']['id'] = b64enc(pd['publicKey']['user']['id'])
    if 'excludeCredentials' in pd['publicKey'] and pd['publicKey']['excludeCredentials']:
        for cred in pd['publicKey']['excludeCredentials']:
            if 'id' in cred:
                cred['id'] = b64enc(cred['id'])
    return pd, state

def complete_registration(state, client_attestation):
    att_obj = {
        'id': client_attestation['id'],
        'rawId': b64dec(client_attestation['rawId']),
        'response': {
            'attestationObject': b64dec(client_attestation['response']['attestationObject']),
            'clientDataJSON': b64dec(client_attestation['response']['clientDataJSON'])
        },
        'type': client_attestation['type']
    }
    auth_data = server.register_complete(state, att_obj)
    cred = auth_data.credential
    db.add_credential(auth_data.user['id'], cred.credential_id, cred.public_key, cred.sign_count)
    return True

def begin_authentication(allow_cred_ids):
    allow_list = [{'type': 'public-key', 'id': cid} for cid in allow_cred_ids]
    auth_data, state = server.authenticate_begin(allow_credentials=allow_list, user_verification='discouraged')
    ad = auth_data
    ad['publicKey']['challenge'] = b64enc(ad['publicKey']['challenge'])
    if 'allowCredentials' in ad['publicKey'] and ad['publicKey']['allowCredentials']:
        for cred in ad['publicKey']['allowCredentials']:
            cred['id'] = b64enc(cred['id'])
    return ad, state

def complete_authentication(state, client_assertion):
    assert_obj = {
        'id': client_assertion['id'],
        'rawId': b64dec(client_assertion['rawId']),
        'response': {
            'authenticatorData': b64dec(client_assertion['response']['authenticatorData']),
            'clientDataJSON': b64dec(client_assertion['response']['clientDataJSON']),
            'signature': b64dec(client_assertion['response']['signature']),
            'userHandle': b64dec(client_assertion['response']['userHandle']) if client_assertion['response'].get('userHandle') else None
        },
        'type': client_assertion['type']
    }
    authn = server.authenticate_complete(state, assert_obj)
    credential = authn.credential
    cred_row = db.get_credential_by_credential_id(credential.credential_id)
    if not cred_row:
        raise Exception('Unknown credential')
    db.update_sign_count(cred_row['id'], credential.sign_count)
    return cred_row['user_id']

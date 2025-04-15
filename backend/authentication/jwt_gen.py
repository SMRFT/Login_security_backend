import jwt
import os
import base64
import time
import datetime
import uuid
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

PRIVATE_KEY_NAMES =  ['GLOBAL_PRIVATE_KEY', 'GLOBAL_PRIVATE_KEY_PART1', 'GLOBAL_PRIVATE_KEY_PART2', 'GLOBAL_PRIVATE_KEY_PART3']
PRIVATE_KEY_PASS_NAME =  'GLOBAL_PRIVATE_KEY_PASS'
REQUIRED_KEYS =  ['aud', 'email', 'name', 'allowed-actions', 'allowed-data']
REQUIRED_KEYS_TYPES =  ['str', 'str', 'str', 'list', 'list']
ISSUER_KEY =  'iss'
ISSUER_VALUE =  'https://lab.shinova.in/'
ISSUED_AT_KEY = "iat"
EXPIRES_AT_KEY = "exp"
EXPIRY_DURATION_MINS = 1440 #24 Hours
TOKEN_ID_KEY = "jti"

_pk_B64 = ''
for n in PRIVATE_KEY_NAMES:
    try:
        _pk_B64 += os.environ[n]
        print(f"Private key part {n} is SET... appending")
    except KeyError:
        print(f"Private key part {n} is not set... skipping")
    except:
        raise ValueError(f'Unable to read private key part {n} of ({PRIVATE_KEY_NAMES})')
    

if not _pk_B64:
    raise ValueError(f'Private key ({PRIVATE_KEY_NAMES}) not set')

_pk = base64.b64decode(_pk_B64) 
_pk_pass_B64 = os.environ[PRIVATE_KEY_PASS_NAME]
_pk_pass = base64.b64decode(_pk_pass_B64) 

PRIVATE_KEY = serialization.load_pem_private_key(
    _pk, password=_pk_pass, backend=default_backend())

def createJwt(values:dict):
    for i, k in enumerate(REQUIRED_KEYS):
        if k not in values:
            raise ValueError(f'Values does not contain {k}', k)
        if type(values[k]).__name__ !=  REQUIRED_KEYS_TYPES[i]:
            raise ValueError(f'Values does not contain {k} in the correct format', k)

    payload = values.copy()
    payload[ISSUER_KEY] = ISSUER_VALUE

    ct = round(time.time()-1)
    payload[ISSUED_AT_KEY] = ct
    payload[EXPIRES_AT_KEY] = ct + (EXPIRY_DURATION_MINS * 60) 

    payload[TOKEN_ID_KEY] = str(uuid.uuid4())

    return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")


import os
from dotenv import load_dotenv
load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()

from authentication import jwt_gen
from authentication import jwt_crypter

# Mock a user profile with HMS-R-V permissions
token_vals = {
    'aud': 'test_user',
    'email': 'test@example.com',
    'name': 'Velavan',
    'allowed-actions': [
        "HMS-P-VI-RW",
        "HMS-P-VV-RW",
        "HMS-P-VINR-RW",
        "HMS-P-HMS"
    ],
    'allowed-data': [],
    'hospital_code': 'SH001'
}

token = jwt_gen.createJwt(token_vals)
print("\nGenerated Token:", token)

import jwt
decoded = jwt.decode(token, options={"verify_signature": False})
print("\nDecoded Payload:", decoded)

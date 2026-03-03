import os
import jwt
from django.http import JsonResponse
from pymongo import MongoClient

class SingleDeviceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.client = MongoClient(os.getenv('GLOBAL_DB_HOST'))
        self.db = self.client[os.getenv('GLOBAL_DB_NAME')]
        self.user_collection = self.db['backend_diagnostics_user']

    def __call__(self, request):
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith(''):
            token = auth_header.split(' ')[1]
            try:
                # Decode purely to check the JTI (pyauth handles signature verification elsewhere)
                unverified_payload = jwt.decode(token, options={"verify_signature": False})
                jti = unverified_payload.get('jti')
                aud = unverified_payload.get('aud') # Employee ID
                
                if jti and aud:
                    user_doc = self.user_collection.find_one({"employeeId": aud})
                    
                    if user_doc:
                        active_jti = user_doc.get("active_jti")
                        if active_jti and active_jti != jti:
                            return JsonResponse(
                                {'error': 'Session invalidated: Logged in from another device'}, 
                                status=401
                            )
            except jwt.DecodeError:
                pass # Let pyauth handle invalid tokens
            except Exception as e:
                print(f"SingleDeviceMiddleware error: {e}")

        response = self.get_response(request)
        return response

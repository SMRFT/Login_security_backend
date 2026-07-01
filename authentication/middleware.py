import jwt
from django.http import JsonResponse

class SingleDeviceLoginMiddleware:
    """
    Middleware to enforce single-device login.
    Checks incoming request's JWT token against the stored 'active_token' in the database.
    If the token does not match the active session, a 401 response is returned to invalidate the session.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Public endpoints that do not require session verification
        public_paths = [
            '/login/',
            '/forgot-password/',
            '/verify-reset-token/',
            '/reset-password/',
            '/get_permissions/',
        ]
        if any(request.path.endswith(path) or path in request.path for path in public_paths):
            return self.get_response(request)

        auth_header = request.META.get('HTTP_AUTHORIZATION') or request.headers.get('Authorization') or request.GET.get('token')
        if auth_header:
            token = auth_header.replace('Bearer ', '').replace('bearer ', '').strip()
            if token:
                try:
                    # Decode token without verification just to extract aud (employeeId)
                    payload = jwt.decode(token, options={"verify_signature": False})
                    employee_id = payload.get('aud')
                    if employee_id:
                        # Query database using shared auth_collection from views
                        from authentication.views import auth_collection
                        user = auth_collection.find_one({"employeeId": employee_id, "is_active": True}, {"active_token": 1})
                        if user and user.get("active_token"):
                            if user.get("active_token") != token:
                                return JsonResponse({
                                    'error': 'Session invalidated: Logged in from another device',
                                    'message': 'Your account was logged in from another device.'
                                }, status=401)
                except Exception:
                    # If token decoding fails, let the downstream view/DRF handle or ignore
                    pass
        return self.get_response(request)

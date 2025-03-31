from django.shortcuts import render

# Create your views here.
import os
from django.contrib.auth.hashers import check_password
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import RefreshToken
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient(os.getenv('GLOBAL_DB_HOST'))
db = client[os.getenv('GLOBAL_DB_NAME')]
collection = db['backend_diagnostics_user']

@api_view(['POST'])
def login_view(request):
    employee_id = request.data.get('employeeId')
    password = request.data.get('password')

    if not employee_id or not password:
        return Response({'error': 'Employee ID and password are required'}, status=400)

    # Fetch user from MongoDB
    user_data = collection.find_one({"employeeId": employee_id})

    if not user_data:
        return Response({'error': 'Invalid Employee ID'}, status=400)

    stored_password = user_data.get("password")

    # Debugging output
    print(f"Stored Hashed Password: {stored_password}")
    print(f"User Entered Password: {password}")

    # Check if the stored password is hashed in Django format
    if stored_password and stored_password.startswith("pbkdf2_sha256$"):
        password_valid = check_password(password, stored_password)
    else:
        password_valid = False  # If the password isn't hashed properly, reject login

    if not password_valid:
        return Response({'error': 'Invalid Password'}, status=400)

    # Generate JWT tokens (custom payload for MongoDB users)
    refresh = RefreshToken()
    refresh.payload['employeeId'] = employee_id  # Custom claim
    refresh.payload['is_active'] = user_data.get('is_active', True)

    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    })


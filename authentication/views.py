from django.shortcuts import render
import os, json
from django.contrib.auth.hashers import check_password
from rest_framework.response import Response
from rest_framework.decorators import api_view
from pymongo import MongoClient
from bson import ObjectId
from . import jwt_gen


# Connect to MongoDB
client = MongoClient(os.getenv('GLOBAL_DB_HOST'))
db = client[os.getenv('GLOBAL_DB_NAME')]
auth_collection = db['backend_diagnostics_user']
profile_collection = db['backend_diagnostics_profile']
role_mapping_collection = db['backend_diagnostics_RoleMapping']

@api_view(['POST'])
def login_view(request):
    employee_id = request.data.get('employeeId')
    password = request.data.get('password')

    if not employee_id or not password:
        return Response({'error': 'Employee ID and password are required'}, status=400)

    # Fetch user from MongoDB authentication collection
    user_data = auth_collection.find_one({"employeeId": employee_id})

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

    # Fetch user profile data from profile collection
    profile_data = profile_collection.find_one({"employeeId": employee_id})
    
    if not profile_data:
        return Response({'error': 'User profile not found'}, status=400)
    
    # Extract required fields from profile
    user_profile = {
        'employeeId': profile_data.get('employeeId'),
        'name': profile_data.get('employeeName'),
        'emailId': profile_data.get('email'),
        'primaryRole': profile_data.get('primaryRole'),
    }
    
    # Handle additionalRoles and dataEntitlements which are stored as JSON strings
    try:
        if profile_data.get('additionalRoles'):
            user_profile['additionalRoles'] = json.loads(profile_data.get('additionalRoles', '[]'))
        else:
            user_profile['additionalRoles'] = []
            
        if profile_data.get('dataEntitlements'):
            user_profile['dataEntitlements'] = json.loads(profile_data.get('dataEntitlements', '[]'))
        else:
            user_profile['dataEntitlements'] = []
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        user_profile['additionalRoles'] = []
        user_profile['dataEntitlements'] = []

    # Combine primaryRole and additionalRoles to get all user roles
    all_roles = [user_profile['primaryRole']] + user_profile['additionalRoles']
    
    # Get permissions for all roles from the RoleMapping collection
    all_permissions = []
    role_details = []
    
    for role_code in all_roles:
        role_data = role_mapping_collection.find_one({"role_code": role_code})
        print("role_data:",all_roles)
      
        if role_data and role_data.get('is_active', True):
            # Extract permissions
            if 'permissions' in role_data and 'allowed' in role_data['permissions']:
                role_permissions = role_data['permissions']['allowed']
                all_permissions.extend(role_permissions)
                
                # Add role details
                role_details.append({
                    'role_code': role_data.get('role_code'),
                    'role_name': role_data.get('role_name'),
                    'role_description': role_data.get('role_description')
                })
    
    # Remove duplicate permissions
    unique_permissions = list(set(all_permissions))
    
    # Add permissions to user profile
    user_profile['permissions'] = unique_permissions
    user_profile['roleDetails'] = role_details
    
    token_vals = {
        'aud': employee_id, 
        'email': user_profile['emailId'], 
        'name': user_profile['name'], 
        'allowed-actions': unique_permissions, 
        'allowed-data': user_profile['dataEntitlements']
    }
    print(token_vals)
    token = jwt_gen.createJwt(token_vals)


    return Response({
        'access_token': token
    })

from django.http import JsonResponse
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

def getmodules(request):
    try:
        client = MongoClient(os.getenv('GLOBAL_DB_HOST'))
        db = client[os.getenv('GLOBAL_DB_NAME')]
        collection = db['backend_diagnostics_Modules']

        modules_cursor = collection.find({"is_active": True}, {'_id': 0})
        modules = list(modules_cursor)

        return JsonResponse({'modules': modules}, status=200)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

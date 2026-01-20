from django.shortcuts import render
import os, json
from django.contrib.auth.hashers import check_password
from rest_framework.response import Response
from rest_framework.decorators import api_view
from pymongo import MongoClient
from bson import ObjectId
from . import jwt_gen
from dotenv import load_dotenv

load_dotenv()

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

    # ---------------- AUTH COLLECTION CHECK ----------------
    user_data = auth_collection.find_one({
        "employeeId": employee_id,
        "is_active": True   # ✅ only active users
    })

    if not user_data:
        return Response({'error': 'Invalid or inactive Employee ID'}, status=400)

    stored_password = user_data.get("password")

    print("Stored Hashed Password:", stored_password)
    print("User Entered Password:", password)

    if stored_password and stored_password.startswith("pbkdf2_sha256$"):
        password_valid = check_password(password, stored_password)
    else:
        password_valid = False

    if not password_valid:
        return Response({'error': 'Invalid Password'}, status=400)

    # ---------------- PROFILE COLLECTION CHECK ----------------
    profile_data = profile_collection.find_one({
        "employeeId": employee_id,
    
    })

    if not profile_data:
        return Response({'error': 'User profile not found or inactive'}, status=400)

    # ---------------- BUILD USER PROFILE ----------------
    user_profile = {
        'employeeId': profile_data.get('employeeId'),
        'name': profile_data.get('employeeName'),
        'emailId': profile_data.get('email'),
        'primaryRole': profile_data.get('primaryRole'),
    }

    # additionalRoles
    if isinstance(profile_data.get('additionalRoles'), list):
        user_profile['additionalRoles'] = profile_data.get('additionalRoles')
    else:
        user_profile['additionalRoles'] = []

    # dataEntitlements
    if isinstance(profile_data.get('dataEntitlements'), list):
        user_profile['dataEntitlements'] = profile_data.get('dataEntitlements')
    else:
        user_profile['dataEntitlements'] = []

    # ---------------- ROLES & PERMISSIONS ----------------
    all_roles = [user_profile['primaryRole']] + user_profile['additionalRoles']

    all_permissions = []
    role_details = []

    for role_code in all_roles:
        role_data = role_mapping_collection.find_one({
            "role_code": role_code,
          
        })

        if role_data:
            if role_data.get('permissions') and role_data['permissions'].get('allowed'):
                all_permissions.extend(role_data['permissions']['allowed'])

            role_details.append({
                'role_code': role_data.get('role_code'),
                'role_name': role_data.get('role_name'),
                'role_description': role_data.get('role_description')
            })

    # remove duplicate permissions
    unique_permissions = list(set(all_permissions))

    user_profile['permissions'] = unique_permissions
    user_profile['roleDetails'] = role_details

    # ---------------- JWT TOKEN ----------------
    token_vals = {
        'aud': employee_id,
        'email': user_profile['emailId'],
        'name': user_profile['name'],
        'allowed-actions': unique_permissions,
        'allowed-data': user_profile['dataEntitlements']
    }

    print("JWT Payload:", token_vals)

    token = jwt_gen.createJwt(token_vals)

    return Response({
        'success': True,
        'access_token': token,
        'user': user_profile
    }, status=200)

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

from django.http import JsonResponse
from pymongo import MongoClient
import os
def get_data_entitlements(request):
    client = MongoClient(os.getenv('GLOBAL_DB_HOST'))
    db = client[os.getenv('GLOBAL_DB_NAME')]
    collection = db['backend_diagnostics_DataEntitlements']
    # Get allowed branch codes from request parameters (e.g., ?branchCodes=SHB001,ABC123)
    branch_codes = request.GET.get('branchCodes', '')
    branch_code_list = branch_codes.split(',') if branch_codes else []
    # Filter by DataEntitlementsCode if provided
    query = {'DataEntitlementsCode': {'$in': branch_code_list}} if branch_code_list else {}
    # Fetch matched entries excluding _id
    data_entitlements = collection.find(query, {'_id': 0, 'DataEntitlementsCode': 1, 'DataEntitlements': 1})
    # Convert cursor to list
    entitlements_list = list(data_entitlements)

    return JsonResponse({'dataEntitlements': entitlements_list})


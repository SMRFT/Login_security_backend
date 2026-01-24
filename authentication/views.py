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

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
import logging
import pytz
from datetime import date, datetime
from pymongo import MongoClient
import os

logger = logging.getLogger(__name__)
IST = pytz.timezone("Asia/Kolkata")

@api_view(['GET'])
def get_todays_birthdays(request):
    try:
        # Re-establish connection or use global if preferred (sticking to local for safety in this mixed file)
        client = MongoClient(os.getenv('GLOBAL_DB_HOST'))
        db = client[os.getenv('GLOBAL_DB_NAME')]
        profile_col = db['backend_diagnostics_profile']
        dept_col = db["backend_diagnostics_Departments"]
        desig_col = db["backend_diagnostics_Designation"]

        today = timezone.now().astimezone(IST).date()
        
        # Fetch all profiles
        # Note: Adapted from Profile.objects.all() to PyMongo
        profiles_cursor = profile_col.find({})
        
        filtered_profiles = []
        
        for profile in profiles_cursor:
            dob = profile.get('dateOfBirth')
            dob_date = None
            
            # Parse Date of Birth
            if dob:
                if isinstance(dob, str):
                    try:
                        # Attempt to parse common format YYYY-MM-DD
                        dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
                    except ValueError:
                        # Try parsing ISO format if needed or ignore
                        continue
                elif isinstance(dob, datetime):
                    dob_date = dob.date()
                elif isinstance(dob, date):
                    dob_date = dob
            
            if dob_date and dob_date.month == today.month and dob_date.day == today.day:
                # calculate age
                age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
                
                # Update age in DB
                profile_col.update_one(
                    {'_id': profile['_id']},
                    {'$set': {'age': age}}
                )
                
                profile['age'] = age
                # Convert ObjectId to string for JSON serialization
                profile['id'] = str(profile['_id'])
                if '_id' in profile:
                    del profile['_id']
                    
                filtered_profiles.append(profile)

        if not filtered_profiles:
            return Response({"success": False, "message": "No birthdays found today."}, status=200)

        # Use filtered_profiles directly (instead of EmployeeBirthdaySerializer)
        birthday_data = filtered_profiles

        # Enrich department & designation from Mongo
        for profile in birthday_data:
            dept_code = profile.get("department")
            desig_code = profile.get("designation")

            # Department
            if dept_code:
                dept = dept_col.find_one({"department_code": dept_code})
                if dept:
                    profile["department"] = dept.get("department_name")
                else:
                    logger.warning(f"No department found for code {dept_code}")

            # Designation
            if desig_code:
                desig = desig_col.find_one({"Designation_code": desig_code})
                if desig:
                    profile["designation"] = desig.get("designation")
                else:
                    logger.warning(f"No designation found for code {desig_code}")

        return Response({
            "success": True,
            "count": len(filtered_profiles),
            "birthdays": birthday_data
        }, status=200)

    except Exception as e:
        logger.error(f"Error fetching today's birthdays: {str(e)}")

        return Response({"success": False, "message": "Error retrieving data.", "error": str(e)}, status=500)



import gridfs
from django.http import HttpResponse

def get_file(request, file_id):
    try:
        client = MongoClient(os.getenv('GLOBAL_DB_HOST'))
        db = client[os.getenv('GLOBAL_DB_NAME')]
        fs = gridfs.GridFS(db)
        
        try:
            # Convert string ID to ObjectId
            oid = ObjectId(file_id)
            
            # Retrieve file from GridFS
            grid_out = fs.get(oid)
            
            # Create response with file content
            # Note: For large files, StreamingHttpResponse is better, but this suffices for typical use cases
            response = HttpResponse(grid_out.read(), content_type=grid_out.content_type)
            
            # Set filename header (inline enables preview in browser)
            response['Content-Disposition'] = f'inline; filename="{grid_out.filename}"'
            
            return response
            
        except gridfs.errors.NoFile:
            return JsonResponse({'error': 'File not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f"Invalid ID or other error: {str(e)}"}, status=400)
            
    except Exception as e:
        logger.error(f"Error serving file: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)






from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt

from django.db.models import Sum
from pymongo import MongoClient
import os
import json
from datetime import datetime, timedelta
from django.utils import timezone
import logging
from bson.decimal128 import Decimal128
import traceback

logger = logging.getLogger(__name__)

def to_float(value):
    """ Safely convert various number formats (BSON Decimal128, string, dict) to float """
    if value is None:
        return 0.0
    
    try:
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            clean_val = value.strip()
            if not clean_val:
                return 0.0
            return float(clean_val)
            
        # Handle Decimal128 (PyMongo)
        if isinstance(value, Decimal128):
            return float(value.to_decimal())
            
        # Handle decimal128-like object (sometimes imported differently)
        if hasattr(value, 'to_decimal'):
            return float(value.to_decimal())

        # Handle Extended JSON dict format i.e. {"$numberDecimal": "123.45"}
        if isinstance(value, dict):
            if '$numberDecimal' in value:
                return float(value['$numberDecimal'])
            # Fallback for other dict structures if any
            return 0.0
            
        return float(value)
    except Exception as e:
        # logger.warning(f"Failed to convert value {value} to float: {e}")
        return 0.0

@api_view(['POST'])
@csrf_exempt
# @permission_classes([HasRoleAndDataPermission])
def m_dashboard_stats(request):
    try:
        # Date Filtering
        date_str = request.data.get('date')
        from_date_str = request.data.get('from_date')
        to_date_str = request.data.get('to_date')
        
        start_date = None
        end_date = None

        if from_date_str and to_date_str:
            try:
                start_date = datetime.strptime(from_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(to_date_str, '%Y-%m-%d') + timedelta(days=1)
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
        elif date_str:
            try:
                start_date = datetime.strptime(date_str, '%Y-%m-%d')
                end_date = start_date + timedelta(days=1)
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
        
        # If no date provided, default to today
        if not start_date:
            today = timezone.localtime(timezone.now()).date()
            start_date = datetime.combine(today, datetime.min.time())
            end_date = start_date + timedelta(days=1)
            
        # Ensure UTC/Offset-naive handling matches DB expectations
        # MongoDB usually stores naive datetime as UTC.
        # If start_date is timezon-aware, converting to naive might be needed depending on how PyMongo is configured or how data was inserted.
        # Assuming standard usage:
        
        # Initialize Stats
        stats = {
            "samples": {
                "total": 0,
                "segments": {
                    "home_collection": 0,
                    "b2b": 0,
                    "franchise": 0,
                    "company_health_check": 0,
                    "other": 0,
                    "insurance": 0,
                    "milestone": 0
                }
            },
            "tests": {
                "total": 0
            },
            "financials": {
                "gross": {
                    "b2b": 0,
                    "home_collection": 0,
                    "company_health_check": 0,
                    "franchise_share": 0,
                    "insurance": 0,
                    "milestone": 0
                },
                "credit_amount": 0,
                "net_amount": 0,
                "refund_amount": 0
            }
        }

        # --- MongoDB Connection ---
        client = MongoClient(os.getenv('GLOBAL_DB_HOST'))

        # --- 1. Core Billing (MongoDB) ---
        try:
            db_core = client.Diagnostics
            col_core = db_core.core_billing

            core_query = {
                "date": {"$gte": start_date, "$lt": end_date}
            }
            core_bills = list(col_core.find(core_query))

            for bill in core_bills:
                # Segment
                segment = bill.get("segment", "") or ""
                b2b_val = bill.get("B2B", "") or ""
                
                if "Home" in segment and "Collection" in segment:
                    stats["samples"]["segments"]["home_collection"] += 1
                    stats["financials"]["gross"]["home_collection"] += to_float(bill.get("totalAmount"))
                elif "B2B" in segment or b2b_val.strip(): 
                    stats["samples"]["segments"]["b2b"] += 1
                    stats["financials"]["gross"]["b2b"] += to_float(bill.get("totalAmount"))
                elif "Company" in segment and "Health" in segment:
                    stats["samples"]["segments"]["company_health_check"] += 1
                    stats["financials"]["gross"]["company_health_check"] += to_float(bill.get("totalAmount"))
                else:
                    stats["samples"]["segments"]["other"] += 1

                # Total Samples
                stats["samples"]["total"] += 1

                # Tests Count
                try:
                    td = bill.get("testdetails")
                    if isinstance(td, str):
                        td = json.loads(td)
                    if isinstance(td, list):
                        stats["tests"]["total"] += len(td)
                except:
                    pass
                
                # Financials
                stats["financials"]["credit_amount"] += to_float(bill.get("credit_amount"))
                stats["financials"]["net_amount"] += to_float(bill.get("netAmount"))

        except Exception as e:
            logger.error(f"Error fetching core billing data: {e}")
            logger.error(traceback.format_exc())
        
        # --- 2. Franchise (MongoDB) ---
        try:
            db_franchise = client.franchise
            col_franchise = db_franchise.franchise_billing
            
            franchise_query = {
                "created_date": {"$gte": start_date, "$lt": end_date}
            }
            
            franchise_bills = list(col_franchise.find(franchise_query))
            
            for bill in franchise_bills:
                stats["samples"]["segments"]["franchise"] += 1
                stats["samples"]["total"] += 1
                
                try:
                    # Credit Amount
                    credit_val = to_float(bill.get("credit_amount"))
                    stats["financials"]["credit_amount"] += credit_val
                    
                    # Franchisor Share (billed_amount is priority, else netAmount)
                    billed_amt = to_float(bill.get("billed_amount"))
                    net_amt_val = to_float(bill.get("netAmount"))

                    if billed_amt == 0 and net_amt_val > 0:
                        billed_amt = net_amt_val

                    stats["financials"]["gross"]["franchise_share"] += billed_amt
                    
                    # Net Amount
                    stats["financials"]["net_amount"] += net_amt_val
                    
                except Exception as e:
                    logger.error(f"Error processing franchise bill financial: {e}")

                # Tests
                try:
                    td = bill.get("testdetails")
                    if isinstance(td, str):
                        td = json.loads(td)
                    if isinstance(td, list):
                        stats["tests"]["total"] += len(td)
                except:
                    pass

        except Exception as e:
            logger.error(f"Error fetching franchise data: {e}")
            logger.error(traceback.format_exc())


        # --- 3. Company Health Checkup (MongoDB) ---
        try:
            db_corporate = client.Corporatehealthcheckup
            col_corporate = db_corporate.core_billing 
            
            corp_query = {
                "created_date": {"$gte": start_date, "$lt": end_date}
            }
            
            corp_bills = list(col_corporate.find(corp_query))
            
            for bill in corp_bills:
                stats["samples"]["segments"]["company_health_check"] += 1
                stats["samples"]["total"] += 1
                
                try:
                    # Amounts
                    # Try 'total', then 'totalAmount', then 'netAmount'
                    total_amt = to_float(bill.get("total"))
                    if total_amt == 0:
                        total_amt = to_float(bill.get("totalAmount"))
                    if total_amt == 0:
                        total_amt = to_float(bill.get("netAmount"))
                        
                    stats["financials"]["gross"]["company_health_check"] += total_amt
                    
                    # Net
                    net_amt = to_float(bill.get("netAmount"))
                    stats["financials"]["net_amount"] += net_amt
                    
                    # Credit
                    credit_val = to_float(bill.get("credit_amount"))
                    # If credit_amount is 0/missing, check paymentMode
                    if credit_val == 0:
                        pm = bill.get("paymentMode", "")
                        if isinstance(pm, str) and pm.lower() in ["credit", "due"]:
                            credit_val = net_amt
                            
                    stats["financials"]["credit_amount"] += credit_val
                    
                except:
                    pass

                # Tests
                try:
                    td = bill.get("testdetails")
                    if isinstance(td, str):
                        td = json.loads(td)
                    if isinstance(td, list):
                        stats["tests"]["total"] += len(td)
                except:
                    pass

        except Exception as e:
            logger.error(f"Error fetching corporate data: {e}")
            logger.error(traceback.format_exc())

        # --- 4. Insurance (MongoDB) ---
        try:
            db_insurance = client.Insurance
            col_insurance = db_insurance.insurance_otherrecord
            
            # Use 'date' string field for filtering as 'created_date' format varies
            # Convert start_date and end_date (exclusive) to string range (inclusive for date string)
            s_str = start_date.strftime('%Y-%m-%d')
            # end_date is exclusive (next day 00:00), so subtract 1 day to get the inclusive 'to_date'
            e_str = (end_date - timedelta(days=1)).strftime('%Y-%m-%d')

            ins_query = {
                "date": {"$gte": s_str, "$lte": e_str}
            }
            
            ins_records = list(col_insurance.find(ins_query))
            
            for record in ins_records:
                # Add to Insurance segment (will need to add key to stats init)
                if "insurance" not in stats["samples"]["segments"]:
                    stats["samples"]["segments"]["insurance"] = 0
                stats["samples"]["segments"]["insurance"] += 1
                
                stats["samples"]["total"] += 1
                
                try:
                    # Amount Calculation
                    # Prioritize root-level 'amount' as it represents Total Bill
                    amt = to_float(record.get("amount"))
                    
                    # Fallback to payment_details only if root amount is 0/missing
                    if amt == 0:
                        payment_details = record.get("payment_details")
                        if isinstance(payment_details, list) and payment_details:
                            # Sum up amounts from payment_details
                            for pay_item in payment_details:
                                if isinstance(pay_item, dict):
                                    amt += to_float(pay_item.get("amount"))

                    refund = to_float(record.get("refund"))
                    if "refund_amount" not in stats["financials"]:
                         stats["financials"]["refund_amount"] = 0
                    stats["financials"]["refund_amount"] += refund
                    
                    # Add to gross (create key if missing)
                    if "insurance" not in stats["financials"]["gross"]:
                        stats["financials"]["gross"]["insurance"] = 0
                    stats["financials"]["gross"]["insurance"] += amt
                    
                    # Net Amount (Amount - Refund)
                    stats["financials"]["net_amount"] += (amt - refund)
                    
                except Exception as e:
                    logger.error(f"Error processing insurance record financial: {e}")

        except Exception as e:
            logger.error(f"Error fetching insurance data: {e}")
            logger.error(traceback.format_exc())

        # --- 5. Milestone (MongoDB) ---
        try:
            db_milestone = client.Milestone
            col_therapy = db_milestone.milestone_backend_therapybilling
            col_others = db_milestone.milestone_backend_othersbilling
            col_assessment = db_milestone.milestone_backend_patientassessment
            
            # Query Objects
            # Therapy uses 'bill_date' (ISODate)
            therapy_query = {
                "bill_date": {"$gte": start_date, "$lt": end_date}
            }
            # Others uses 'date' (ISODate)
            others_query = {
                "date": {"$gte": start_date, "$lt": end_date}
            }
            # Assessment uses 'date' (ISODate)
            assessment_query = {
                "date": {"$gte": start_date, "$lt": end_date}
            }
            
            therapy_recs = list(col_therapy.find(therapy_query))
            others_recs = list(col_others.find(others_query))
            assessment_recs = list(col_assessment.find(assessment_query))
            
            # Combine all records
            all_milestone = therapy_recs + others_recs + assessment_recs
            
            for record in all_milestone:
                if "milestone" not in stats["samples"]["segments"]:
                    stats["samples"]["segments"]["milestone"] = 0
                stats["samples"]["segments"]["milestone"] += 1
                stats["samples"]["total"] += 1
                
                # Financials
                gross = 0.0
                net = 0.0
                
                # Logic based on collection type / fields
                if "assessments" in record: # Assessment
                     gross = to_float(record.get("total_price"))
                     # Use finalAmount if available, else gross
                     # User snippet: "finalAmount": {"$numberDecimal": "1400.00"}
                     net_val = record.get("finalAmount")
                     if net_val is not None:
                         net = to_float(net_val)
                     else:
                         net = gross

                elif "others_items" in record: # Others
                     gross = to_float(record.get("total_amount"))
                     # User snippet: "amount_paid": {"$numberDecimal": "150.00"}, "total_amount": 150.00
                     # Use total_amount as gross. Net is collected? 
                     # Let's align with others: Net is Revenue Booked. 
                     net = to_float(record.get("total_amount"))
                     
                else: # Therapy (fallback or check specific fields)
                     # User snippet: "total_amount": 10675.00, "amount_paid": 1000.00
                     gross = to_float(record.get("total_amount"))
                     net = gross

                # Update Stats
                if "milestone" not in stats["financials"]["gross"]:
                    stats["financials"]["gross"]["milestone"] = 0
                stats["financials"]["gross"]["milestone"] += gross
                
                stats["financials"]["net_amount"] += net

        except Exception as e:
            logger.error(f"Error fetching milestone data: {e}")
            logger.error(traceback.format_exc())

        finally:
            client.close()

        return Response({"success": True, "data": stats})

    except Exception as e:
        logger.error(f"Error in m_dashboard_stats: {str(e)}")
        logger.error(traceback.format_exc())
        return Response({"success": False, "error": str(e)}, status=500)

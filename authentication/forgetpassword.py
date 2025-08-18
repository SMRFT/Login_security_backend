import os
import secrets
import string
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from pymongo import MongoClient
import json

# MongoDB connection
client = MongoClient(os.getenv('GLOBAL_DB_HOST'))
db = client[os.getenv('GLOBAL_DB_NAME', "Global")]
users_collection = db['backend_diagnostics_profile']
reset_tokens_collection = db['password_reset_tokens']

def generate_reset_token():
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

@csrf_exempt
@require_http_methods(["POST"])
def forgot_password(request):
    try:
        data = json.loads(request.body)
        employee_id = data.get('employeeId', '').strip()

        if not employee_id:
            return JsonResponse({'success': False, 'message': 'Employee ID is required'}, status=400)

        user = users_collection.find_one({'employeeId': employee_id})
        if not user:
            return JsonResponse({'success': False, 'message': 'Employee ID not found'}, status=404)

        user_email = user.get('email')
        if not user_email:
            return JsonResponse({'success': False, 'message': 'No email associated with this Employee ID'}, status=400)

        reset_token = generate_reset_token()

        # Ensure expires_at is timezone-aware
        token_data = {
            'employeeId': employee_id,
            'email': user_email,
            'token': reset_token,
            'created_at': timezone.now(),
            'expires_at': timezone.now() + timedelta(hours=24),
            'used': False
        }

        reset_tokens_collection.delete_many({'employeeId': employee_id})
        reset_tokens_collection.insert_one(token_data)

        frontend_url = os.getenv('FRONTEND_URL', 'http://127.0.0.1:2102/')
        reset_link = f"{frontend_url}/reset-password?token={reset_token}&employeeId={employee_id}"

        send_password_reset_email(user_email, user.get('name', employee_id), reset_link)

        return JsonResponse({
            'success': True,
            'message': f'Password reset link has been sent to {user_email}'
        })

    except Exception as e:
        print(f"Forgot password error: {e}")
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again later.'}, status=500)

def send_password_reset_email(email, name, reset_link):
    """Send password reset email to user"""
    subject = 'Password Reset - Shanmuga Hospital'
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                font-family: Arial, sans-serif;
            }}
            .header {{
                background: linear-gradient(135deg, #845EC2, #D65DB1);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background: #f9f9f9;
                padding: 30px;
                border-radius: 0 0 10px 10px;
                border: 1px solid #ddd;
            }}
            .button {{
                display: inline-block;
                background: linear-gradient(90deg, #845EC2, #D65DB1);
                color: white;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 8px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .warning {{
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏥 Shanmuga Hospital</h1>
                <h2>Password Reset Request</h2>
            </div>
            <div class="content">
                <p>Hello {name},</p>
                
                <p>We received a request to reset your password for your Shanmuga Hospital employee account.</p>
                
                <p>Click the button below to reset your password:</p>
                
                <a href="{reset_link}" class="button">Reset Password</a>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #845EC2;">{reset_link}</p>
                
                <div class="warning">
                    <strong>Important:</strong>
                    <ul>
                        <li>This link will expire in 24 hours</li>
                        <li>If you didn't request this reset, please ignore this email</li>
                        <li>For security, don't share this link with anyone</li>
                    </ul>
                </div>
                
                <p>If you have any questions, please contact the IT department.</p>
                
                <p>Best regards,<br>
                Shanmuga Hospital IT Team</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    plain_message = f"""
    Hello {name},
    
    We received a request to reset your password for your Shanmuga Hospital employee account.
    
    Please click the following link to reset your password:
    {reset_link}
    
    This link will expire in 24 hours.
    
    If you didn't request this reset, please ignore this email.
    
    Best regards,
    Shanmuga Hospital IT Team
    """
    
    send_mail(
        subject=subject,
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

@csrf_exempt
@require_http_methods(["POST"])
def verify_reset_token(request):
    """Verify if reset token is valid and not expired"""
    try:
        data = json.loads(request.body)
        token = data.get('token', '').strip()
        employee_id = data.get('employeeId', '').strip()
        
        if not token or not employee_id:
            return JsonResponse({
                'success': False,
                'message': 'Token and Employee ID are required'
            }, status=400)
        
        # Find token in database
        token_data = reset_tokens_collection.find_one({
            'token': token,
            'employeeId': employee_id,
            'used': False
        })
        
        if not token_data:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired reset token'
            }, status=400)
        
        # Check if token is expired
        if datetime.utcnow() > token_data['expires_at']:
            return JsonResponse({
                'success': False,
                'message': 'Reset token has expired'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'message': 'Token is valid'
        })
        
    except Exception as e:
        print(f"Token verification error: {e}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred during verification'
        }, status=500)

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import utc
from django.contrib.auth.hashers import make_password
import json
from datetime import datetime
from django.utils import timezone

empusers_collection = db['backend_diagnostics_user']
from django.utils import timezone
import pytz

from datetime import datetime, timedelta, timezone as dt_timezone

@csrf_exempt
def reset_password(request):
    """Handle both GET (display form) and POST (process form) for password reset"""

    if request.method == "GET":
        token = request.GET.get('token', '')
        employee_id = request.GET.get('employeeId', '')

        if not token or not employee_id:
            return render(request, 'reset_password.html', {
                'valid_token': False,
                'error': 'Invalid reset link. Please request a new password reset.'
            })

        token_data = reset_tokens_collection.find_one({
            'token': token,
            'employeeId': employee_id,
            'used': False
        })

        if not token_data:
            return render(request, 'reset_password.html', {
                'valid_token': False,
                'error': 'Invalid or expired reset token. Please request a new password reset.'
            })

        expires_at = token_data.get('expires_at')
        if expires_at and timezone.is_naive(expires_at):
            expires_at = expires_at.replace(tzinfo=dt_timezone.utc)

        is_valid = expires_at and timezone.now() < expires_at

        return render(request, 'reset_password.html', {
            'token': token,
            'employeeId': employee_id,
            'valid_token': is_valid,
            'employee_name': users_collection.find_one(
                {'employeeId': employee_id}, {'name': 1}
            ).get('name', employee_id) if is_valid else None
        })

    elif request.method == "POST":
        password_reset_successful = False
        user_details = {}
        token_email = None
        
        try:
            token = request.POST.get('token', '').strip()
            employee_id = request.POST.get('employeeId', '').strip()
            new_password = request.POST.get('newPassword', '').strip()
            confirm_password = request.POST.get('confirmPassword', '').strip()

            # === Validations ===
            if not token or not employee_id or not new_password or not confirm_password:
                return render(request, 'reset_password.html', {
                    'error': 'All fields are required.',
                    'token': token, 'employeeId': employee_id, 'valid_token': True
                })

            if new_password != confirm_password:
                return render(request, 'reset_password.html', {
                    'error': 'Passwords do not match.',
                    'token': token, 'employeeId': employee_id, 'valid_token': True
                })

            if len(new_password) < 8:
                return render(request, 'reset_password.html', {
                    'error': 'Password must be at least 8 characters long.',
                    'token': token, 'employeeId': employee_id, 'valid_token': True
                })

            if not any(c.isalpha() for c in new_password):
                return render(request, 'reset_password.html', {
                    'error': 'Password must contain at least one letter.',
                    'token': token, 'employeeId': employee_id, 'valid_token': True
                })

            if not any(c.isdigit() for c in new_password):
                return render(request, 'reset_password.html', {
                    'error': 'Password must contain at least one number.',
                    'token': token, 'employeeId': employee_id, 'valid_token': True
                })

            # === Validate Token ===
            token_data = reset_tokens_collection.find_one({
                'token': token,
                'employeeId': employee_id,
                'used': False
            })
            if not token_data:
                return render(request, 'reset_password.html', {
                    'error': 'Invalid or expired reset token.',
                    'valid_token': False
                })

            expires_at = token_data.get('expires_at')
            if expires_at and timezone.is_naive(expires_at):
                expires_at = expires_at.replace(tzinfo=dt_timezone.utc)

            if timezone.now() > expires_at:
                return render(request, 'reset_password.html', {
                    'error': 'Reset token has expired.',
                    'valid_token': False
                })

            # Store email for confirmation email
            token_email = token_data.get('email')

            # === Update Password ===
            hashed_password = make_password(new_password)

            update_result = empusers_collection.update_one(
                {'employeeId': employee_id},
                {'$set': {
                    'password': hashed_password,
                    'is_password_set': True,
                    'password_updated_at': datetime.now(dt_timezone.utc),
                    'updated_at': datetime.now(dt_timezone.utc)
                }}
            )

            if update_result.modified_count == 0:
                profile_update = users_collection.update_one(
                    {'employeeId': employee_id},
                    {'$set': {
                        'password': hashed_password,
                        'is_password_set': True,
                        'password_updated_at': datetime.now(dt_timezone.utc),
                        'updated_at': datetime.now(dt_timezone.utc)
                    }}
                )
                if profile_update.modified_count == 0:
                    return render(request, 'reset_password.html', {
                        'error': 'Failed to update password. Please contact IT support.',
                        'valid_token': True
                    })

            # === Mark token as used ===
            reset_tokens_collection.update_one(
                {'token': token},
                {'$set': {'used': True, 'used_at': datetime.now(dt_timezone.utc)}}
            )

            password_reset_successful = True
            
            # Get user details for success page
            user_details = users_collection.find_one(
                {'employeeId': employee_id}, {'name': 1, 'email': 1}
            ) or {}

        except Exception as e:
            print(f"Password reset error: {e}")
            if not password_reset_successful:
                return render(request, 'reset_password.html', {
                    'error': 'An unexpected error occurred. Please try again later or contact IT support.',
                    'token': request.POST.get('token', ''),
                    'employeeId': request.POST.get('employeeId', ''),
                    'valid_token': True
                })

        if password_reset_successful:
            # Try to send confirmation email, but don't fail if it doesn't work
            try:
                if token_email:
                    send_password_reset_confirmation_email(
                        token_email,
                        user_details.get('name', employee_id)
                    )
            except Exception as email_error:
                print(f"Confirmation email failed (but password was reset successfully): {email_error}")
                # Continue to success page even if email fails

            return render(request, 'reset_success.html', {
                'employee_name': user_details.get('name', employee_id),
                'employee_id': employee_id,
                'success': True,
                'message': 'Your password has been successfully reset.'
            })

        return render(request, 'reset_password.html', {
            'error': 'An unexpected error occurred. Please try again later or contact IT support.',
            'token': request.POST.get('token', ''),
            'employeeId': request.POST.get('employeeId', ''),
            'valid_token': True
        })

def send_password_reset_confirmation_email(email, name):
    """Send confirmation email after successful password reset"""
    subject = 'Password Successfully Reset - Shanmuga Hospital'
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 20px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #27AE60, #2ECC71); color: white; padding: 30px; text-align: center; }}
            .content {{ padding: 30px; color: #333; }}
            .success-icon {{ font-size: 48px; text-align: center; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏥 Shanmuga Hospital</h1>
                <h2>Password Reset Confirmation</h2>
            </div>
            <div class="content">
                <div class="success-icon">✅</div>
                <p>Hello <strong>{name}</strong>,</p>
                <p>This email confirms that your password has been successfully reset for your Shanmuga Hospital employee account.</p>
                <p><strong>Reset completed:</strong> {timezone.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                <p>If you did not make this change, please contact IT support immediately.</p>
                <p>Best regards,<br>Shanmuga Hospital IT Team</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    plain_message = f"""
    Hello {name},
    
    This email confirms that your password has been successfully reset for your Shanmuga Hospital employee account.
    
    Reset completed: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}
    
    If you did not make this change, please contact IT support immediately.
    
    Best regards,
    Shanmuga Hospital IT Team
    """
    
    send_mail(
        subject=subject,
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=True,  # Don't fail if confirmation email fails
    )

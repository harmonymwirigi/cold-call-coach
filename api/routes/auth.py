# ===== IMPROVED API/ROUTES/AUTH.PY =====
from flask import Blueprint, request, jsonify, session
from services.supabase_client import SupabaseService
from services.resend_service import ResendService
from utils.constants import JOB_TITLES, INDUSTRIES
import logging
import json
import re

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

supabase_service = SupabaseService()
resend_service = ResendService()

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password requirements"""
    return password and len(password) >= 6

@auth_bp.route('/send-verification', methods=['POST'])
def send_verification():
    """Send verification code and store user data for later registration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Extract and validate data
        email = data.get('email', '').strip().lower()
        first_name = data.get('first_name', '').strip()
        password = data.get('password', '')
        prospect_job_title = data.get('prospect_job_title', '')
        prospect_industry = data.get('prospect_industry', '')
        custom_ai_notes = data.get('custom_ai_notes', '').strip()
        
        # Validate required fields
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        if not first_name:
            return jsonify({'error': 'First name is required'}), 400
        if not validate_password(password):
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        if not prospect_job_title:
            return jsonify({'error': 'Job title is required'}), 400
        if not prospect_industry:
            return jsonify({'error': 'Industry is required'}), 400
        
        # Validate job title and industry against allowed values
        if prospect_job_title not in JOB_TITLES:
            return jsonify({'error': 'Invalid job title selected'}), 400
        
        if prospect_industry not in INDUSTRIES:
            return jsonify({'error': 'Invalid industry selected'}), 400
        
        # Check if user already exists in a better way
        client = supabase_service.get_client()
        try:
            # Check if email is already registered by looking at existing profiles
            existing_profile = client.table('user_profiles').select('id').eq('id', 
                client.table('user_profiles').select('id').execute().data
            ).execute()
            
            # Alternative: check auth users via API (this is safer)
            # For now, we'll proceed and let Supabase handle duplicate email errors
            
        except Exception as e:
            logger.warning(f"Could not check existing user: {e}")
            # Continue with registration process
        
        # Generate verification code
        code = resend_service.generate_verification_code()
        
        # Store user data temporarily with the verification code
        user_data = {
            'email': email,
            'password': password,
            'first_name': first_name,
            'prospect_job_title': prospect_job_title,
            'prospect_industry': prospect_industry,
            'custom_ai_notes': custom_ai_notes
        }
        
        # Store verification code with user data
        if not supabase_service.create_verification_code_with_data(email, code, user_data):
            return jsonify({'error': 'Failed to create verification code. Please try again.'}), 500
        
        # Send email
        if not resend_service.send_verification_email(email, code, first_name):
            return jsonify({'error': 'Failed to send verification email. Please check your email address.'}), 500
        
        logger.info(f"Verification code sent successfully to {email}")
        return jsonify({'message': 'Verification code sent successfully'})
        
    except Exception as e:
        logger.error(f"Error sending verification: {e}")
        return jsonify({'error': 'Internal server error. Please try again.'}), 500

@auth_bp.route('/verify-and-register', methods=['POST'])
def verify_and_register():
    """Verify email code and automatically create user account"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        if not code:
            return jsonify({'error': 'Verification code is required'}), 400
        if len(code) != 6 or not code.isdigit():
            return jsonify({'error': 'Verification code must be 6 digits'}), 400
        
        # Verify code and get stored user data
        user_data = supabase_service.verify_code_and_get_data(email, code)
        if not user_data:
            return jsonify({'error': 'Invalid or expired verification code'}), 400
        
        # Extract user data
        password = user_data.get('password')
        first_name = user_data.get('first_name')
        prospect_job_title = user_data.get('prospect_job_title')
        prospect_industry = user_data.get('prospect_industry')
        custom_ai_notes = user_data.get('custom_ai_notes', '')
        
        # Double-check we have all required data
        if not all([password, first_name, prospect_job_title, prospect_industry]):
            return jsonify({'error': 'Registration data incomplete. Please start over.'}), 400
        
        # Create user in Supabase Auth
        client = supabase_service.get_client()
        try:
            auth_response = client.auth.sign_up({
                "email": email,
                "password": password
            })
        except Exception as auth_error:
            logger.error(f"Supabase auth error during signup: {auth_error}")
            error_msg = str(auth_error).lower()
            if "already registered" in error_msg or "already exists" in error_msg:
                return jsonify({'error': 'An account with this email already exists. Please log in instead.'}), 409
            else:
                return jsonify({'error': 'Failed to create account. Please try again.'}), 500
        
        if not auth_response.user:
            return jsonify({'error': 'Failed to create user account'}), 500
        
        user_id = auth_response.user.id
        
        # Create user profile with limited_trial access level (controlled by admin)
        profile_data = {
            'id': user_id,
            'first_name': first_name,
            'prospect_job_title': prospect_job_title,
            'prospect_industry': prospect_industry,
            'custom_ai_notes': custom_ai_notes,
            'access_level': 'limited_trial'  # Default access level - admin can upgrade
        }
        # Initialize progress for the starting roleplays (1.1 and 1.2)
        # This ensures a record always exists for access checks.
        initial_progress_data = [
            {'user_id': user_id, 'roleplay_id': '1.1', 'is_unlocked': True},
            {'user_id': user_id, 'roleplay_id': '1.2', 'is_unlocked': True},
        ]
        
        # Use the service client to upsert these initial records
        try:
            supabase_service.get_service_client().table('user_roleplay_stats').upsert(initial_progress_data).execute()
            logger.info(f"Initialized starting progress for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to initialize progress for user {user_id}: {e}")
        if not supabase_service.create_user_profile(profile_data):
            # If profile creation fails, we should clean up the auth user
            try:
                client.auth.admin.delete_user(user_id)
            except:
                logger.error(f"Failed to cleanup auth user {user_id} after profile creation failure")
            return jsonify({'error': 'Failed to create user profile'}), 500
        
        # Initialize progress for Roleplay 1 (always unlocked)
        supabase_service.update_user_progress(user_id, 1, {
            'unlocked_at': 'NOW()'
        })
        
        # Send welcome email
        try:
            resend_service.send_welcome_email(email, first_name)
        except Exception as e:
            logger.warning(f"Failed to send welcome email: {e}")
            # Don't fail registration if welcome email fails
        
        logger.info(f"User {email} registered successfully with limited_trial access")
        return jsonify({
            'message': 'Account created successfully! You can now log in.',
            'user': {
                'id': user_id,
                'email': email,
                'first_name': first_name,
                'access_level': 'limited_trial'
            }
        })
        
    except Exception as e:
        logger.error(f"Error in verify-and-register: {e}")
        return jsonify({'error': 'Internal server error. Please try again.'}), 500

# Keep the old routes for backward compatibility
@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Legacy verify email endpoint - redirects to new flow"""
    return verify_and_register()

@auth_bp.route('/register', methods=['POST'])
def register():
    """Legacy register endpoint - redirects to new flow"""
    return send_verification()

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user with enhanced error handling"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Authenticate with Supabase
        client = supabase_service.get_client()
        
        try:
            auth_response = client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
        except Exception as auth_error:
            logger.error(f"Supabase auth error: {auth_error}")
            
            # Parse specific error messages
            error_msg = str(auth_error).lower()
            if "invalid login credentials" in error_msg or "invalid" in error_msg:
                return jsonify({'error': 'Invalid email or password'}), 401
            elif "email not confirmed" in error_msg:
                return jsonify({'error': 'Please verify your email first'}), 401
            else:
                return jsonify({'error': 'Login failed. Please try again.'}), 401
        
        if not auth_response.user or not auth_response.session:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        user = auth_response.user
        session_token = auth_response.session.access_token
        
        # Get user profile with better error handling
        profile = supabase_service.get_user_profile_by_service(user.id)
        if not profile:
            logger.error(f"User profile not found for user_id: {user.id}")
            return jsonify({
                'error': 'Account setup incomplete. Please register again.',
                'code': 'profile_not_found'
            }), 404
        
        # Store session
        session['user_id'] = user.id
        session['access_token'] = session_token
        
        logger.info(f"User {email} logged in successfully")
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': profile['first_name'],
                'access_level': profile['access_level'],
                'trial_signup_date': profile.get('trial_signup_date'),
                'lifetime_usage_minutes': profile.get('lifetime_usage_minutes', 0)
            },
            'access_token': session_token
        })
        
    except Exception as e:
        logger.error(f"Error logging in: {e}")
        return jsonify({'error': 'Internal server error. Please try again.'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    try:
        # Clear session
        session.clear()
        
        return jsonify({'message': 'Logout successful'})
        
    except Exception as e:
        logger.error(f"Error logging out: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user info"""
    try:
        access_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not access_token:
            access_token = session.get('access_token')
        
        if not access_token:
            return jsonify({'error': 'No access token provided'}), 401
        
        # Verify token and get user
        user = supabase_service.authenticate_user(access_token)
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Handle both dict and object types for user
        try:
            if hasattr(user, 'id'):
                user_id = user.id
                user_email = user.email
            elif isinstance(user, dict):
                user_id = user['id']
                user_email = user['email']
            else:
                return jsonify({'error': 'Invalid user object format'}), 401
        except (AttributeError, KeyError) as e:
            logger.error(f"Error extracting user data: {e}")
            return jsonify({'error': 'Invalid user object format'}), 401
        
        # Get user profile
        profile = supabase_service.get_user_profile_by_service(user_id)
        if not profile:
            return jsonify({'error': 'User profile not found'}), 404
        
        # Get user progress
        progress = supabase_service.get_user_progress(user_id)
        
        return jsonify({
            'user': {
                'id': user_id,
                'email': user_email,
                'first_name': profile['first_name'],
                'prospect_job_title': profile['prospect_job_title'],
                'prospect_industry': profile['prospect_industry'],
                'access_level': profile['access_level'],
                'monthly_usage_minutes': profile['monthly_usage_minutes'],
                'lifetime_usage_minutes': profile['lifetime_usage_minutes'],
                'trial_signup_date': profile.get('trial_signup_date')
            },
            'progress': progress
        })
        
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    
# ===== API/ROUTES/DASHBOARD.PY =====
from flask import Blueprint, render_template, session, redirect, url_for
from utils.decorators import require_auth
import logging

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@require_auth
def dashboard():
    """Dashboard page"""
    try:
        return render_template('dashboard.html')
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        return redirect(url_for('home'))

@dashboard_bp.route('/roleplay/<int:roleplay_id>')
@require_auth
def roleplay(roleplay_id):
    """Roleplay page"""
    try:
        # Validate roleplay ID
        if roleplay_id not in [1, 2, 3, 4, 5]:
            return redirect(url_for('dashboard'))
        
        # Here you would check if user has access to this roleplay
        # For now, just render a placeholder
        return render_template('roleplay.html', roleplay_id=roleplay_id)
    except Exception as e:
        logger.error(f"Error rendering roleplay {roleplay_id}: {e}")
        return redirect(url_for('dashboard'))
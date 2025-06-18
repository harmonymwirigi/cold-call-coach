# ===== API/UTILS/DECORATORS.PY =====
from functools import wraps
from flask import session, request, jsonify, redirect, url_for
import logging
from typing import List

logger = logging.getLogger(__name__)

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if 'user_id' not in session:
            # For API requests, return JSON error
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            # For page requests, redirect to login
            return redirect(url_for('login_page'))
        
        return f(*args, **kwargs)
    return decorated_function

def check_usage_limits(f):
    """Decorator to check user usage limits"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            from services.supabase_client import SupabaseService
            from utils.helpers import calculate_usage_limits
            
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            supabase_service = SupabaseService()
            profile = supabase_service.get_user_profile_by_service(user_id)
            
            if not profile:
                return jsonify({'error': 'User profile not found'}), 404
            
            # Calculate usage limits
            usage_info = calculate_usage_limits(profile)
            
            # Check if user has exceeded limits
            if usage_info['remaining_minutes'] <= 0:
                return jsonify({
                    'error': 'Usage limit exceeded',
                    'limit_type': usage_info['limit_type'],
                    'upgrade_required': True
                }), 403
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error checking usage limits: {e}")
            return f(*args, **kwargs)  # Continue if check fails
    
    return decorated_function

def validate_json_input(required_fields: List[str] = None):
    """Decorator to validate JSON input"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': f'Missing required fields: {", ".join(missing_fields)}'
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_api_call(f):
    """Decorator to log API calls"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id', 'anonymous')
        logger.info(f"API call: {request.method} {request.path} - User: {user_id}")
        
        try:
            result = f(*args, **kwargs)
            logger.info(f"API call completed: {request.method} {request.path} - User: {user_id}")
            return result
        except Exception as e:
            logger.error(f"API call failed: {request.method} {request.path} - User: {user_id} - Error: {e}")
            raise
    
    return decorated_function
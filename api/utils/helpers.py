
# ===== API/UTILS/HELPERS.PY =====
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union
import hashlib
import secrets
import json

logger = logging.getLogger(__name__)

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password: str) -> Dict[str, Any]:
    """
    Validate password strength
    Returns dict with 'valid' boolean and 'errors' list
    """
    errors = []
    
    if not password:
        errors.append("Password is required")
        return {'valid': False, 'errors': errors}
    
    if len(password) < 6:
        errors.append("Password must be at least 6 characters long")
    
    if len(password) > 128:
        errors.append("Password must be less than 128 characters")
    
    # Check for common weak passwords
    weak_passwords = ['password', '123456', 'qwerty', 'abc123', 'password123']
    if password.lower() in weak_passwords:
        errors.append("Password is too common")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input text"""
    if not text:
        return ""
    
    # Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Strip whitespace
    return text.strip()

def generate_session_id(user_id: str, roleplay_id: int) -> str:
    """Generate unique session ID"""
    timestamp = datetime.now().timestamp()
    data = f"{user_id}_{roleplay_id}_{timestamp}_{secrets.token_hex(8)}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]

def calculate_usage_limits(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate user's usage limits and remaining time"""
    access_level = profile.get('access_level', 'limited_trial')
    monthly_usage = profile.get('monthly_usage_minutes', 0) or 0
    lifetime_usage = profile.get('lifetime_usage_minutes', 0) or 0
    
    result = {
        'access_level': access_level,
        'monthly_usage_minutes': monthly_usage,
        'lifetime_usage_minutes': lifetime_usage
    }
    
    if access_level == 'limited_trial':
        # 3 hours lifetime limit or 7 days from signup
        trial_limit_minutes = 180  # 3 hours
        remaining_minutes = max(0, trial_limit_minutes - lifetime_usage)
        
        # Check days remaining
        signup_date_str = profile.get('trial_signup_date') or profile.get('created_at')
        if signup_date_str:
            try:
                signup_date = parse_iso_datetime(signup_date_str)
                current_time = datetime.now(timezone.utc)
                days_since_signup = (current_time - signup_date).days
                days_remaining = max(0, 7 - days_since_signup)
            except:
                days_remaining = 7  # Default if can't parse
        else:
            days_remaining = 7
        
        result.update({
            'trial_minutes_remaining': remaining_minutes,
            'trial_days_remaining': days_remaining,
            'usage_percentage': round((lifetime_usage / trial_limit_minutes) * 100, 1) if trial_limit_minutes > 0 else 0,
            'is_expired': remaining_minutes == 0 or days_remaining == 0,
            'limit_type': 'trial'
        })
    
    else:  # Basic or Pro
        # 50 hours monthly limit
        monthly_limit_minutes = 3000  # 50 hours
        remaining_minutes = max(0, monthly_limit_minutes - monthly_usage)
        
        result.update({
            'monthly_minutes_remaining': remaining_minutes,
            'monthly_limit_minutes': monthly_limit_minutes,
            'usage_percentage': round((monthly_usage / monthly_limit_minutes) * 100, 1) if monthly_limit_minutes > 0 else 0,
            'is_expired': remaining_minutes == 0,
            'limit_type': 'monthly'
        })
    
    return result

def parse_iso_datetime(date_string: str) -> datetime:
    """Parse ISO datetime string with timezone handling"""
    if not date_string:
        return datetime.now(timezone.utc)
    
    try:
        # Handle various datetime formats
        if 'T' in date_string:
            if date_string.endswith('Z'):
                return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            elif '+' in date_string or date_string.endswith('00'):
                return datetime.fromisoformat(date_string)
            else:
                return datetime.fromisoformat(date_string + '+00:00')
        else:
            # Legacy format
            return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse datetime {date_string}: {e}")
        return datetime.now(timezone.utc)

def format_duration(minutes: int) -> str:
    """Format duration in minutes to human readable string"""
    if minutes < 60:
        return f"{minutes}m"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours}h"
    else:
        return f"{hours}h {remaining_minutes}m"

def calculate_success_rate(sessions: List[Dict]) -> float:
    """Calculate success rate from sessions list"""
    if not sessions:
        return 0.0
    
    successful = sum(1 for s in sessions if s.get('success') is True)
    return round((successful / len(sessions)) * 100, 1)

def get_time_periods() -> Dict[str, datetime]:
    """Get common time periods for analytics"""
    now = datetime.now(timezone.utc)
    return {
        'now': now,
        'hour_ago': now - timedelta(hours=1),
        'day_ago': now - timedelta(days=1),
        'week_ago': now - timedelta(days=7),
        'month_ago': now - timedelta(days=30),
        'year_ago': now - timedelta(days=365)
    }

def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """Safely parse JSON string with fallback"""
    try:
        return json.loads(json_string) if json_string else default
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """Safely convert data to JSON string"""
    try:
        return json.dumps(data) if data is not None else default
    except (TypeError, ValueError):
        return default

def mask_email(email: str) -> str:
    """Mask email for privacy (e.g., user@domain.com -> u***@domain.com)"""
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    if len(local) <= 1:
        return email
    
    masked_local = local[0] + '*' * (len(local) - 1)
    return f"{masked_local}@{domain}"

def generate_prospect_name(job_title: str, industry: str) -> str:
    """Generate realistic prospect name based on role"""
    first_names = {
        'executive': ['Alex', 'Jordan', 'Taylor', 'Casey', 'Morgan', 'Riley'],
        'technical': ['Sam', 'Blake', 'Quinn', 'Avery', 'Sage', 'Cameron'],
        'manager': ['Jamie', 'Drew', 'Peyton', 'Skyler', 'Emery', 'Parker'],
        'sales': ['Dakota', 'Reese', 'Phoenix', 'River', 'Scout', 'Finley']
    }
    
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 
                  'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez']
    
    # Determine name category based on job title
    title_lower = job_title.lower()
    if any(word in title_lower for word in ['ceo', 'cto', 'cfo', 'president', 'founder']):
        category = 'executive'
    elif any(word in title_lower for word in ['engineer', 'technical', 'developer', 'architect']):
        category = 'technical'
    elif any(word in title_lower for word in ['sales', 'business', 'account']):
        category = 'sales'
    else:
        category = 'manager'
    
    first_name = secrets.choice(first_names[category])
    last_name = secrets.choice(last_names)
    
    return f"{first_name} {last_name}"

def get_avatar_path(job_title: str, gender_preference: str = 'neutral') -> str:
    """Get appropriate avatar image path"""
    title_lower = job_title.lower()
    
    if any(word in title_lower for word in ['ceo', 'president', 'founder']):
        return '/static/images/prospect-avatars/executive.jpg'
    elif any(word in title_lower for word in ['engineer', 'technical', 'developer']):
        return '/static/images/prospect-avatars/technical.jpg'
    elif any(word in title_lower for word in ['manager', 'director']):
        return '/static/images/prospect-avatars/manager.jpg'
    else:
        return '/static/images/prospect-avatars/default.jpg'

def log_user_action(user_id: str, action: str, details: Dict = None):
    """Log user action for analytics"""
    try:
        log_entry = {
            'user_id': user_id,
            'action': action,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'details': details or {}
        }
        logger.info(f"User action: {json.dumps(log_entry)}")
    except Exception as e:
        logger.error(f"Failed to log user action: {e}")

# ===== API/UTILS/DECORATORS.PY (ENHANCED) =====
from functools import wraps
from flask import session, request, jsonify, redirect, url_for
from services.supabase_client import SupabaseService
import os

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check session
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            else:
                return redirect(url_for('login_page'))
        
        # Verify token if provided
        access_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not access_token:
            access_token = session.get('access_token')
        
        if access_token:
            supabase_service = SupabaseService()
            user = supabase_service.authenticate_user(access_token)
            if not user:
                session.clear()
                if request.is_json:
                    return jsonify({'error': 'Invalid or expired token'}), 401
                else:
                    return redirect(url_for('login_page'))
        
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check authentication
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            else:
                return redirect(url_for('login_page'))
        
        # Get user profile to check admin status
        try:
            supabase_service = SupabaseService()
            profile = supabase_service.get_user_profile_by_service(session['user_id'])
            
            if not profile:
                return jsonify({'error': 'User profile not found'}), 404
            
            # Check if user is admin (you can define admin logic here)
            admin_email = os.getenv('REACT_APP_ADMIN_EMAIL')
            user_email = profile.get('email')  # Would need to get email from auth
            
            # For now, simple admin check - you can enhance this
            if admin_email and user_email and user_email.lower() == admin_email.lower():
                return f(*args, **kwargs)
            
            # Alternative: check access_level
            if profile.get('access_level') == 'admin':
                return f(*args, **kwargs)
            
            return jsonify({'error': 'Admin privileges required'}), 403
            
        except Exception as e:
            logger.error(f"Error checking admin privileges: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return decorated_function

def require_access_level(min_level: str):
    """Decorator to require minimum access level"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                else:
                    return redirect(url_for('login_page'))
            
            try:
                supabase_service = SupabaseService()
                profile = supabase_service.get_user_profile_by_service(session['user_id'])
                
                if not profile:
                    return jsonify({'error': 'User profile not found'}), 404
                
                user_level = profile.get('access_level', 'limited_trial')
                
                # Define access level hierarchy
                level_hierarchy = {
                    'limited_trial': 1,
                    'unlimited_basic': 2,
                    'unlimited_pro': 3,
                    'admin': 4
                }
                
                user_level_num = level_hierarchy.get(user_level, 0)
                required_level_num = level_hierarchy.get(min_level, 0)
                
                if user_level_num >= required_level_num:
                    return f(*args, **kwargs)
                else:
                    return jsonify({'error': f'Access level {min_level} required'}), 403
                    
            except Exception as e:
                logger.error(f"Error checking access level: {e}")
                return jsonify({'error': 'Internal server error'}), 500
        
        return decorated_function
    return decorator

def check_usage_limits(f):
    """Decorator to check if user has exceeded usage limits"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        try:
            supabase_service = SupabaseService()
            profile = supabase_service.get_user_profile_by_service(session['user_id'])
            
            if not profile:
                return jsonify({'error': 'User profile not found'}), 404
            
            # Calculate usage limits
            usage_info = calculate_usage_limits(profile)
            
            if usage_info.get('is_expired'):
                return jsonify({
                    'error': 'Usage limit exceeded',
                    'usage_info': usage_info
                }), 403
            
            # Add usage info to request context for the view
            request.usage_info = usage_info
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error checking usage limits: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return decorated_function

def log_api_call(f):
    """Decorator to log API calls for analytics"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = datetime.now()
        user_id = session.get('user_id', 'anonymous')
        
        try:
            result = f(*args, **kwargs)
            
            # Log successful call
            duration = (datetime.now() - start_time).total_seconds()
            log_user_action(user_id, f'api_call_{f.__name__}', {
                'endpoint': request.endpoint,
                'method': request.method,
                'duration_seconds': duration,
                'status': 'success'
            })
            
            return result
            
        except Exception as e:
            # Log failed call
            duration = (datetime.now() - start_time).total_seconds()
            log_user_action(user_id, f'api_call_{f.__name__}', {
                'endpoint': request.endpoint,
                'method': request.method,
                'duration_seconds': duration,
                'status': 'error',
                'error': str(e)
            })
            
            raise e  # Re-raise the exception
    
    return decorated_function

def validate_json_input(required_fields: List[str] = None, optional_fields: List[str] = None):
    """Decorator to validate JSON input"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid JSON data'}), 400
            
            # Check required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': f'Missing required fields: {", ".join(missing_fields)}'
                    }), 400
            
            # Sanitize inputs
            all_fields = (required_fields or []) + (optional_fields or [])
            for field in all_fields:
                if field in data and isinstance(data[field], str):
                    data[field] = sanitize_input(data[field])
            
            # Store sanitized data back to request
            request._json = data
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def rate_limit(max_requests: int = 100, window_minutes: int = 60):
    """Simple rate limiting decorator (in-memory, not persistent)"""
    from collections import defaultdict, deque
    
    # Simple in-memory store (would use Redis in production)
    rate_limit_store = defaultdict(deque)
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client identifier
            client_id = request.remote_addr
            if 'user_id' in session:
                client_id = f"user_{session['user_id']}"
            
            now = datetime.now()
            window_start = now - timedelta(minutes=window_minutes)
            
            # Clean old requests
            requests = rate_limit_store[client_id]
            while requests and requests[0] < window_start:
                requests.popleft()
            
            # Check rate limit
            if len(requests) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': window_minutes * 60
                }), 429
            
            # Add current request
            requests.append(now)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
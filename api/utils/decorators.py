# ===== API/UTILS/DECORATORS.PY (SIMPLIFIED) =====
from functools import wraps
from flask import session, request, jsonify, redirect, url_for
import logging

logger = logging.getLogger(__name__)

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if 'user_id' not in session:
            logger.warning(f"Unauthenticated access attempt to {request.endpoint}")
            
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            else:
                return redirect(url_for('login_page'))
        
        logger.debug(f"Authenticated access by user {session['user_id']} to {request.endpoint}")
        return f(*args, **kwargs)
    
    return decorated_function
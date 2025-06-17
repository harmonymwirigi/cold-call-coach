# ===== API/ROUTES/DEBUG.PY (FOR TESTING ONLY) =====
from flask import Blueprint, request, jsonify
from services.supabase_client import SupabaseService
import logging
import os

logger = logging.getLogger(__name__)
debug_bp = Blueprint('debug', __name__)

supabase_service = SupabaseService()

# Only enable debug routes in development
DEBUG_ENABLED = os.getenv('FLASK_ENV') == 'development' or os.getenv('DEBUG') == 'true'

@debug_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Cold Calling Coach API is running'
    })

@debug_bp.route('/test-db', methods=['GET'])
def test_database():
    """Test database connection"""
    if not DEBUG_ENABLED:
        return jsonify({'error': 'Debug routes disabled'}), 403
    
    try:
        client = supabase_service.get_client()
        
        # Test basic query
        response = client.table('user_profiles').select('count').execute()
        
        return jsonify({
            'status': 'success',
            'message': 'Database connection successful',
            'user_count': len(response.data) if response.data else 0
        })
        
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Database connection failed: {str(e)}'
        }), 500

@debug_bp.route('/check-verification/<email>', methods=['GET'])
def check_verification_codes(email):
    """Check verification codes for an email (development only)"""
    if not DEBUG_ENABLED:
        return jsonify({'error': 'Debug routes disabled'}), 403
    
    try:
        client = supabase_service.get_client()
        
        # Get all verification codes for this email
        response = client.table('verification_codes')\
            .select('*')\
            .eq('email', email.lower())\
            .order('created_at', desc=True)\
            .execute()
        
        codes = []
        for record in response.data:
            codes.append({
                'code': record['code'],
                'used': record['used'],
                'expires_at': record['expires_at'],
                'created_at': record['created_at'],
                'has_user_data': bool(record.get('user_data', '{}') != '{}')
            })
        
        return jsonify({
            'email': email,
            'codes': codes,
            'total_codes': len(codes)
        })
        
    except Exception as e:
        logger.error(f"Error checking verification codes: {e}")
        return jsonify({'error': str(e)}), 500

@debug_bp.route('/cleanup-verification', methods=['POST'])
def cleanup_verification_codes():
    """Clean up expired verification codes (development only)"""
    if not DEBUG_ENABLED:
        return jsonify({'error': 'Debug routes disabled'}), 403
    
    try:
        client = supabase_service.get_client()
        
        # Delete expired codes
        response = client.table('verification_codes')\
            .delete()\
            .lt('expires_at', 'NOW()')\
            .execute()
        
        return jsonify({
            'status': 'success',
            'message': 'Expired verification codes cleaned up'
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up verification codes: {e}")
        return jsonify({'error': str(e)}), 500

@debug_bp.route('/validate-constants', methods=['GET'])
def validate_constants():
    """Validate job titles and industries constants"""
    from utils.constants import JOB_TITLES, INDUSTRIES
    
    return jsonify({
        'job_titles': {
            'count': len(JOB_TITLES),
            'first_5': JOB_TITLES[:5],
            'last_5': JOB_TITLES[-5:]
        },
        'industries': {
            'count': len(INDUSTRIES),
            'first_5': INDUSTRIES[:5],
            'last_5': INDUSTRIES[-5:]
        }
    })

@debug_bp.route('/test-email-service', methods=['POST'])
def test_email_service():
    """Test email service (development only)"""
    if not DEBUG_ENABLED:
        return jsonify({'error': 'Debug routes disabled'}), 403
    
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        from services.resend_service import ResendService
        resend_service = ResendService()
        
        # Generate test code
        code = resend_service.generate_verification_code()
        
        # Try to send email
        success = resend_service.send_verification_email(email, code, 'Test User')
        
        return jsonify({
            'status': 'success' if success else 'failed',
            'code': code,  # Only in debug mode
            'message': 'Test email sent' if success else 'Failed to send email'
        })
        
    except Exception as e:
        logger.error(f"Error testing email service: {e}")
        return jsonify({'error': str(e)}), 500


# ===== API/ROUTES/ADMIN.PY =====
from flask import Blueprint, request, jsonify, session
from services.supabase_client import SupabaseService
import logging
from utils.helpers import require_admin
from datetime import datetime, timezone, timedelta
logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)

supabase_service = SupabaseService()

@admin_bp.route('/users', methods=['GET'])
@require_admin
def get_all_users():
    """Get all users for admin panel"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        search = request.args.get('search', '').strip()
        
        offset = (page - 1) * limit
        
        # Use service client to bypass RLS for admin operations
        service_client = supabase_service.get_service_client()
        
        logger.info(f"Admin users request: page={page}, limit={limit}, search='{search}'")
        
        # Use the view that includes emails
        query = service_client.table('admin_users_view').select('*')
        
        # Apply search filter (can now search email too!)
        if search:
            query = query.or_(f'first_name.ilike.%{search}%,email.ilike.%{search}%')
        
        # Execute query with pagination
        response = query.order('created_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        users = response.data or []
        logger.info(f"Query returned {len(users)} users with emails")
        
        # Emails are now included in the response from the view!
        for user in users:
            if not user.get('email'):
                user['email'] = 'N/A'
        
        # Get total count using the view
        count_query = service_client.table('admin_users_view').select('id', count='exact')
        if search:
            count_query = count_query.or_(f'first_name.ilike.%{search}%,email.ilike.%{search}%')
        
        count_response = count_query.execute()
        total_count = count_response.count or 0
        
        logger.info(f"Total count: {total_count}")
        
        return jsonify({
            'users': users,
            'total_count': total_count,
            'page': page,
            'limit': limit,
            'total_pages': (total_count + limit - 1) // limit if total_count > 0 else 1
        })
        
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
@admin_bp.route('/users/<user_id>/access-level', methods=['PUT'])
@require_admin
def update_user_access_level(user_id):  # ADD user_id parameter here
    """Update user's access level"""
    try:
        # Remove this line since user_id is now a parameter
        # user_id = request.view_args['user_id']  # DELETE THIS LINE
        
        data = request.get_json()
        new_access_level = data.get('access_level')
        
        if new_access_level not in ['limited_trial', 'unlimited_basic', 'unlimited_pro', 'admin']:
            return jsonify({'error': 'Invalid access level'}), 400
        
        # Use service client to update admin users
        if supabase_service.update_user_profile_by_service(user_id, {'access_level': new_access_level}):
            logger.info(f"Updated access level for user {user_id} to {new_access_level}")
            return jsonify({'message': 'Access level updated successfully'})
        else:
            return jsonify({'error': 'Failed to update access level'}), 500
            
    except Exception as e:
        logger.error(f"Error updating access level: {e}")
        return jsonify({'error': 'Internal server error'}), 500
@admin_bp.route('/stats', methods=['GET'])
@require_admin
def get_admin_stats():
    """Get overall platform statistics"""
    try:
        # Use service client to bypass RLS
        service_client = supabase_service.get_service_client()
        
        # Get user stats
        users_response = service_client.table('user_profiles')\
            .select('access_level,created_at')\
            .execute()
        
        users = users_response.data or []
        
        # Get session stats
        sessions_response = service_client.table('voice_sessions')\
            .select('duration_minutes,success,created_at')\
            .execute()
        
        sessions = sessions_response.data or []
        
        # Calculate stats - USE TIMEZONE-AWARE DATETIME
        now = datetime.now(timezone.utc)  # This is timezone-aware
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        stats = {
            'total_users': len(users),
            'trial_users': sum(1 for u in users if u['access_level'] == 'limited_trial'),
            'basic_users': sum(1 for u in users if u['access_level'] == 'unlimited_basic'),
            'pro_users': sum(1 for u in users if u['access_level'] == 'unlimited_pro'),
            'admin_users': sum(1 for u in users if u['access_level'] == 'admin'),
            'new_users_this_week': 0,
            'new_users_this_month': 0,
            'total_sessions': len(sessions),
            'successful_sessions': sum(1 for s in sessions if s.get('success')),
            'total_minutes': sum(s.get('duration_minutes', 0) for s in sessions if s.get('duration_minutes')),
            'sessions_this_week': 0,
            'sessions_this_month': 0
        }
        
        # Helper function to parse datetime strings consistently
        def parse_datetime_string(date_string):
            """Parse datetime string to timezone-aware datetime"""
            if not date_string:
                return None
            try:
                # Handle different datetime formats from Supabase
                if date_string.endswith('Z'):
                    # Convert 'Z' to '+00:00'
                    return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
                elif '+' in date_string and date_string.count('+') == 1:
                    # Already has timezone info
                    return datetime.fromisoformat(date_string)
                elif 'T' in date_string:
                    # No timezone info, assume UTC
                    return datetime.fromisoformat(date_string + '+00:00')
                else:
                    # Legacy format without timezone
                    dt = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
                    return dt.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse datetime '{date_string}': {e}")
                return None
        
        # Calculate time-based stats for users
        for user in users:
            user_date = parse_datetime_string(user.get('created_at'))
            if user_date:
                if user_date >= week_ago:
                    stats['new_users_this_week'] += 1
                if user_date >= month_ago:
                    stats['new_users_this_month'] += 1
        
        # Calculate time-based stats for sessions
        for session in sessions:
            session_date = parse_datetime_string(session.get('created_at'))
            if session_date:
                if session_date >= week_ago:
                    stats['sessions_this_week'] += 1
                if session_date >= month_ago:
                    stats['sessions_this_month'] += 1
        
        # Calculate success rate
        if stats['total_sessions'] > 0:
            stats['success_rate'] = round((stats['successful_sessions'] / stats['total_sessions']) * 100, 1)
        else:
            stats['success_rate'] = 0
        
        logger.info(f"Admin stats calculated successfully: {stats}")
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


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
        
        # Build query
        query = supabase_service.get_client().table('user_profiles').select('*')
        
        if search:
            query = query.ilike('first_name', f'%{search}%').or_('email.ilike.%{}%'.format(search))
        
        response = query.order('created_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        users = response.data or []
        
        # Get total count
        count_query = supabase_service.get_client().table('user_profiles').select('id', count='exact')
        if search:
            count_query = count_query.ilike('first_name', f'%{search}%')
        
        count_response = count_query.execute()
        total_count = count_response.count or 0
        
        return jsonify({
            'users': users,
            'total_count': total_count,
            'page': page,
            'limit': limit,
            'total_pages': (total_count + limit - 1) // limit
        })
        
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/users/<user_id>/access-level', methods=['PUT'])
@require_admin
def update_user_access_level():
    """Update user's access level"""
    try:
        user_id = request.view_args['user_id']
        data = request.get_json()
        new_access_level = data.get('access_level')
        
        if new_access_level not in ['limited_trial', 'unlimited_basic', 'unlimited_pro']:
            return jsonify({'error': 'Invalid access level'}), 400
        
        if supabase_service.update_user_profile(user_id, {'access_level': new_access_level}):
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
        # Get user stats
        users_response = supabase_service.get_client().table('user_profiles')\
            .select('access_level,created_at')\
            .execute()
        
        users = users_response.data or []
        
        # Get session stats
        sessions_response = supabase_service.get_client().table('voice_sessions')\
            .select('duration_minutes,success,created_at')\
            .execute()
        
        sessions = sessions_response.data or []
        
        # Calculate stats
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        stats = {
            'total_users': len(users),
            'trial_users': sum(1 for u in users if u['access_level'] == 'limited_trial'),
            'basic_users': sum(1 for u in users if u['access_level'] == 'unlimited_basic'),
            'pro_users': sum(1 for u in users if u['access_level'] == 'unlimited_pro'),
            'new_users_this_week': 0,
            'new_users_this_month': 0,
            'total_sessions': len(sessions),
            'successful_sessions': sum(1 for s in sessions if s.get('success')),
            'total_minutes': sum(s.get('duration_minutes', 0) for s in sessions),
            'sessions_this_week': 0,
            'sessions_this_month': 0
        }
        
        # Calculate time-based stats
        for user in users:
            user_date = datetime.fromisoformat(user['created_at'].replace('Z', '+00:00'))
            if user_date >= week_ago:
                stats['new_users_this_week'] += 1
            if user_date >= month_ago:
                stats['new_users_this_month'] += 1
        
        for session in sessions:
            session_date = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00'))
            if session_date >= week_ago:
                stats['sessions_this_week'] += 1
            if session_date >= month_ago:
                stats['sessions_this_month'] += 1
        
        # Calculate success rate
        if stats['total_sessions'] > 0:
            stats['success_rate'] = round((stats['successful_sessions'] / stats['total_sessions']) * 100, 1)
        else:
            stats['success_rate'] = 0
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500





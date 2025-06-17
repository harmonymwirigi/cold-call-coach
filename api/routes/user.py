# ===== API/ROUTES/USER.PY (COMPLETELY FIXED) =====
from flask import Blueprint, request, jsonify, session
from services.supabase_client import SupabaseService
from utils.decorators import require_auth
from utils.constants import ROLEPLAY_CONFIG
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)
user_bp = Blueprint('user', __name__)

supabase_service = SupabaseService()

@user_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get user profile and progress"""
    try:
        user_id = session['user_id']
        logger.info(f"Getting profile for user {user_id}")
        
        # Get user profile using service client to bypass RLS
        profile = supabase_service.get_user_profile_by_service(user_id)
        if not profile:
            logger.error(f"Profile not found for user {user_id}")
            return jsonify({'error': 'Profile not found'}), 404
        
        # Get user progress
        progress = supabase_service.get_user_progress(user_id)
        
        # Calculate usage limits and access
        access_info = _calculate_access_info(profile)
        
        # Get roleplay unlock status
        roleplay_access = _get_roleplay_access(progress, profile['access_level'])
        
        logger.info(f"Successfully retrieved profile for user {user_id}")
        return jsonify({
            'profile': profile,
            'progress': progress,
            'access_info': access_info,
            'roleplay_access': roleplay_access
        })
        
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/stats', methods=['GET'])
@require_auth
def get_user_stats():
    """Get user statistics"""
    try:
        user_id = session['user_id']
        logger.info(f"Getting stats for user {user_id}")
        
        # Get profile for usage info using service client
        profile = supabase_service.get_user_profile_by_service(user_id)
        if not profile:
            logger.error(f"Profile not found for user {user_id}")
            return jsonify({'error': 'Profile not found'}), 404
        
        # Get session statistics using service client
        user_sessions = supabase_service.get_user_sessions(user_id, limit=1000)  # Get all sessions for stats
        
        # Calculate stats with better null handling
        stats = {
            'total_sessions': len(user_sessions),
            'total_minutes': sum(s.get('duration_minutes', 0) or 0 for s in user_sessions),
            'successful_sessions': sum(1 for s in user_sessions if s.get('success') is True),
            'success_rate': 0,
            'favorite_roleplay': None,
            'sessions_this_week': 0,
            'sessions_this_month': 0,
            'monthly_usage_minutes': profile.get('monthly_usage_minutes', 0) or 0,
            'lifetime_usage_minutes': profile.get('lifetime_usage_minutes', 0) or 0
        }
        
        if stats['total_sessions'] > 0:
            stats['success_rate'] = round((stats['successful_sessions'] / stats['total_sessions']) * 100, 1)
        
        # Calculate sessions this week/month with proper timezone handling
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        for user_session in user_sessions:
            try:
                session_date_str = user_session.get('created_at') or user_session.get('started_at')
                if not session_date_str:
                    continue
                    
                # Handle timezone-aware datetime strings
                if 'T' in session_date_str:
                    if session_date_str.endswith('Z'):
                        session_date = datetime.fromisoformat(session_date_str.replace('Z', '+00:00'))
                    elif '+' in session_date_str or session_date_str.endswith('00'):
                        session_date = datetime.fromisoformat(session_date_str)
                    else:
                        session_date = datetime.fromisoformat(session_date_str + '+00:00')
                else:
                    session_date = datetime.strptime(session_date_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                
                if session_date >= week_ago:
                    stats['sessions_this_week'] += 1
                if session_date >= month_ago:
                    stats['sessions_this_month'] += 1
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse session date {session_date_str}: {e}")
                continue
        
        # Find favorite roleplay
        roleplay_counts = {}
        for user_session in user_sessions:
            rp_id = user_session.get('roleplay_id')
            if rp_id:
                roleplay_counts[rp_id] = roleplay_counts.get(rp_id, 0) + 1
        
        if roleplay_counts:
            favorite_id = max(roleplay_counts, key=roleplay_counts.get)
            stats['favorite_roleplay'] = ROLEPLAY_CONFIG.get(favorite_id, {}).get('name', f'Roleplay {favorite_id}')
        
        logger.info(f"Successfully retrieved stats for user {user_id}")
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/sessions', methods=['GET'])
@require_auth
def get_user_sessions():
    """Get user's roleplay sessions"""
    try:
        user_id = session['user_id']
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        logger.info(f"Getting sessions for user {user_id}, page {page}, limit {limit}")
        
        # Get sessions from database using service client
        offset = (page - 1) * limit
        user_sessions = supabase_service.get_user_sessions(user_id, limit=limit, offset=offset)
        
        # Get total count
        total_count = supabase_service.get_session_count(user_id)
        
        logger.info(f"Successfully retrieved {len(user_sessions)} sessions for user {user_id}")
        return jsonify({
            'sessions': user_sessions,
            'total_count': total_count,
            'page': page,
            'limit': limit,
            'total_pages': (total_count + limit - 1) // limit if total_count > 0 else 1
        })
        
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update user profile"""
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Allow updating specific fields
        allowed_fields = ['first_name', 'prospect_job_title', 'prospect_industry', 'custom_ai_notes']
        updates = {k: v for k, v in data.items() if k in allowed_fields and v is not None}
        
        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        logger.info(f"Updating profile for user {user_id} with fields: {list(updates.keys())}")
        
        if supabase_service.update_user_profile_by_service(user_id, updates):
            logger.info(f"Successfully updated profile for user {user_id}")
            return jsonify({'message': 'Profile updated successfully'})
        else:
            logger.error(f"Failed to update profile for user {user_id}")
            return jsonify({'error': 'Failed to update profile'}), 500
            
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def _calculate_access_info(profile):
    """Calculate user's access limits and usage"""
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
                signup_date = _parse_iso_datetime(signup_date_str)
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

def _get_roleplay_access(progress, access_level):
    """Get roleplay unlock status"""
    access = {}
    
    for roleplay_id in range(1, 6):
        config = ROLEPLAY_CONFIG.get(roleplay_id, {})
        progress_item = next((p for p in progress if p.get('roleplay_id') == roleplay_id), None)
        
        if roleplay_id == 1:
            # Roleplay 1 always unlocked
            access[roleplay_id] = {
                'unlocked': True,
                'unlock_condition': 'Always available',
                'expires_at': None
            }
        elif access_level == 'unlimited_pro':
            # Pro users have everything unlocked
            access[roleplay_id] = {
                'unlocked': True,
                'unlock_condition': 'Pro access',
                'expires_at': None
            }
        elif progress_item and progress_item.get('unlocked_at'):
            # Check if unlock has expired (for Basic users)
            is_unlocked = True
            expires_at = progress_item.get('expires_at')
            
            if expires_at and access_level == 'unlimited_basic':
                try:
                    expire_time = _parse_iso_datetime(expires_at)
                    current_time = datetime.now(timezone.utc)
                    is_unlocked = current_time < expire_time
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse expiry date {expires_at}: {e}")
                    is_unlocked = True  # Default to unlocked if can't parse
            
            access[roleplay_id] = {
                'unlocked': is_unlocked,
                'unlock_condition': config.get('unlock_condition', 'Unknown'),
                'expires_at': expires_at
            }
        else:
            # Not unlocked
            access[roleplay_id] = {
                'unlocked': False,
                'unlock_condition': config.get('unlock_condition', 'Unknown'),
                'expires_at': None
            }
    
    return access

def _parse_iso_datetime(date_string: str) -> datetime:
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
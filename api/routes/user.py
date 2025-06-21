# ===== API/ROUTES/USER.PY (COMPLETELY FIXED) =====
from flask import Blueprint, request, jsonify, session
from services.supabase_client import SupabaseService
from services.user_progress_service import UserProgressService
from utils.decorators import require_auth
from utils.constants import ROLEPLAY_CONFIG
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)
user_bp = Blueprint('user', __name__)

supabase_service = SupabaseService()
progress_service = UserProgressService()

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

# ===== COMPLETE FIX: Replace these functions in routes/user.py =====

@user_bp.route('/roleplay-progress', methods=['GET'])
@require_auth
def get_user_roleplay_progress():
    """Get comprehensive user roleplay progress - FIXED"""
    try:
        user_id = session.get('user_id')
        
        # Get progress data
        progress = progress_service.get_user_roleplay_progress(user_id)
        available_roleplays = progress_service.get_available_roleplays(user_id)
        completion_stats = progress_service.get_completion_stats(user_id)
        recommendations = progress_service.get_next_recommendations(user_id)
        
        # Get recent activity
        recent_completions = get_recent_completions(user_id, limit=5)
        
        # Get achievements - FIXED: Call helper function
        achievements = get_user_achievements_helper(user_id)
        
        response_data = {
            'user_id': user_id,
            'progress': progress,
            'available_roleplays': available_roleplays,
            'completion_stats': completion_stats,
            'recommendations': recommendations,
            'recent_activity': recent_completions,
            'achievements': achievements,
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting user progress: {e}")
        return jsonify({'error': 'Failed to load progress data'}), 500

# ADD this new helper function:
def get_user_achievements_helper(user_id: str):
    """Helper function to get user achievements (not a route)"""
    try:
        result = supabase_service.get_service_client().table('user_achievements').select(
            '*'
        ).eq('user_id', user_id).order('earned_at', desc=True).execute()
        
        achievements = result.data if result.data else []
        
        return {
            'achievements': achievements,
            'total_points': sum(a.get('points', 0) for a in achievements),
            'total_count': len(achievements)
        }
        
    except Exception as e:
        logger.error(f"Error getting achievements for user {user_id}: {e}")
        return {'achievements': [], 'total_points': 0, 'total_count': 0}

# UPDATE the existing route function:
@user_bp.route('/achievements', methods=['GET'])
@require_auth  
def get_user_achievements():
    """Get user's achievements (route function) - UPDATED"""
    try:
        user_id = session.get('user_id')
        
        # Call the helper function
        return jsonify(get_user_achievements_helper(user_id))
        
    except Exception as e:
        logger.error(f"Error getting achievements: {e}")
        return jsonify({'achievements': [], 'total_points': 0, 'total_count': 0})

@user_bp.route('/leaderboard/<roleplay_id>', methods=['GET'])
@require_auth
def get_roleplay_leaderboard(roleplay_id):
    """Get leaderboard for specific roleplay"""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)
        user_id = session.get('user_id')
        
        leaderboard = progress_service.get_leaderboard(roleplay_id, limit)
        
        # Find user's rank
        user_rank = None
        user_score = None
        for entry in leaderboard:
            if entry['user_id'] == user_id:
                user_rank = entry['rank']
                user_score = entry['score']
                break
        
        # If user not in top, find their rank
        if user_rank is None:
            user_stats = supabase_service.get_service_client().table('user_roleplay_stats').select(
                'best_score'
            ).eq('user_id', user_id).eq('roleplay_id', roleplay_id).execute()
            
            if user_stats.data and user_stats.data[0]['best_score']:
                user_score = user_stats.data[0]['best_score']
                
                # Count how many users have higher scores
                higher_scores = supabase_service.get_service_client().table('user_roleplay_stats').select(
                    'user_id', count='exact'
                ).eq('roleplay_id', roleplay_id).gt('best_score', user_score).execute()
                
                user_rank = (higher_scores.count or 0) + 1
        
        return jsonify({
            'roleplay_id': roleplay_id,
            'leaderboard': leaderboard,
            'user_rank': user_rank,
            'user_score': user_score,
            'total_participants': len(leaderboard)
        })
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return jsonify({'error': 'Failed to load leaderboard'}), 500
    
@user_bp.route('/export-progress', methods=['GET'])
@require_auth
def export_user_progress():
    """Export user's complete progress data"""
    try:
        user_id = session.get('user_id')
        format_type = request.args.get('format', 'json')  # json, csv
        
        # Get all user data
        progress = progress_service.get_user_roleplay_progress(user_id)
        completions = get_all_completions(user_id)
        achievements = get_user_achievements(user_id)
        
        export_data = {
            'user_id': user_id,
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'progress_summary': progress,
            'all_completions': completions,
            'achievements': achievements['achievements'],
            'statistics': progress_service.get_completion_stats(user_id)
        }
        
        if format_type == 'csv':
            # Convert to CSV format
            return export_to_csv(export_data)
        else:
            # Return JSON
            return jsonify(export_data)
        
    except Exception as e:
        logger.error(f"Error exporting progress: {e}")
        return jsonify({'error': 'Failed to export data'}), 500

# ===== Helper Functions =====

def get_recent_completions(user_id: str, limit: int = 5):
    """Get recent roleplay completions"""
    try:
        result = supabase_service.get_service_client().table('roleplay_completions').select(
            'roleplay_id, score, completed_at, duration_minutes, success'
        ).eq('user_id', user_id).order('completed_at', desc=True).limit(limit).execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        logger.error(f"Error getting recent completions: {e}")
        return []

def get_all_completions(user_id: str):
    """Get all user completions for export"""
    try:
        result = supabase_service.get_service_client().table('roleplay_completions').select(
            '*'
        ).eq('user_id', user_id).order('completed_at', desc=True).execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        logger.error(f"Error getting all completions: {e}")
        return []

def calculate_improvement_trend(user_id: str):
    """Calculate if user is improving over time"""
    try:
        # Get recent scores vs older scores
        recent_completions = supabase_service.get_service_client().table('roleplay_completions').select(
            'score, completed_at'
        ).eq('user_id', user_id).order('completed_at', desc=True).limit(10).execute()
        
        if not recent_completions.data or len(recent_completions.data) < 3:
            return 'insufficient_data'
        
        scores = [c['score'] for c in recent_completions.data]
        recent_avg = sum(scores[:3]) / 3  # Last 3
        older_avg = sum(scores[3:]) / len(scores[3:])  # Earlier ones
        
        if recent_avg > older_avg + 5:
            return 'improving'
        elif recent_avg < older_avg - 5:
            return 'declining'
        else:
            return 'stable'
            
    except Exception as e:
        logger.error(f"Error calculating improvement trend: {e}")
        return 'unknown'

def calculate_consistency_score(scores):
    """Calculate how consistent user's performance is"""
    if not scores or len(scores) < 2:
        return 0
    
    # Calculate standard deviation
    mean = sum(scores) / len(scores)
    variance = sum((x - mean) ** 2 for x in scores) / len(scores)
    std_dev = variance ** 0.5
    
    # Convert to consistency score (lower std_dev = higher consistency)
    # Scale from 0-100 where 100 is perfect consistency
    max_possible_std = 50  # Assume max std dev of 50 points
    consistency = max(0, 100 - (std_dev / max_possible_std * 100))
    
    return round(consistency, 1)

def export_to_csv(data):
    """Convert export data to CSV format"""
    import csv
    import io
    from flask import Response
    
    output = io.StringIO()
    
    # Write completions data
    if data['all_completions']:
        writer = csv.DictWriter(output, fieldnames=[
            'roleplay_id', 'score', 'completed_at', 'duration_minutes', 'success'
        ])
        writer.writeheader()
        for completion in data['all_completions']:
            writer.writerow({
                'roleplay_id': completion['roleplay_id'],
                'score': completion['score'],
                'completed_at': completion['completed_at'],
                'duration_minutes': completion['duration_minutes'],
                'success': completion['success']
            })
    
    csv_data = output.getvalue()
    output.close()
    
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=roleplay_progress.csv'}
    )

# ===== Achievement Tracking =====

@user_bp.route('/award-achievement', methods=['POST'])
@require_auth
def award_achievement():
    """Award achievement to user (internal use)"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        # Verify this is an internal request or admin
        # Add proper authorization logic here
        
        achievement_data = {
            'user_id': user_id,
            'achievement_type': data['type'],
            'roleplay_id': data.get('roleplay_id'),
            'title': data['title'],
            'description': data['description'],
            'badge_icon': data.get('badge_icon', 'fas fa-trophy'),
            'points': data.get('points', 0)
        }
        
        result = supabase_service.get_service_client().table('user_achievements').insert(
            achievement_data
        ).execute()
        
        if result.data:
            return jsonify({'success': True, 'achievement': result.data[0]})
        else:
            return jsonify({'success': False, 'error': 'Failed to award achievement'}), 500
            
    except Exception as e:
        logger.error(f"Error awarding achievement: {e}")
        return jsonify({'error': 'Failed to award achievement'}), 500

logger.info("User progress routes initialized")
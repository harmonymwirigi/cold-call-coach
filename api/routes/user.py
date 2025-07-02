# ===== FIXED api/routes/user.py =====
from flask import Blueprint, request, jsonify, session
from services.supabase_client import SupabaseService
from services.user_progress_service import UserProgressService
from utils.decorators import require_auth
from utils.constants import ROLEPLAY_CONFIG
from datetime import datetime, timedelta, timezone
import logging
from typing import Dict, List, Any, Optional
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
        
        # FIXED: Get user progress from the correct service
        progress = progress_service.get_user_roleplay_progress(user_id)
        
        # Calculate usage limits and access
        access_info = _calculate_access_info(profile)
        
        # FIXED: Get roleplay unlock status using the progress service
        roleplay_access = _get_roleplay_access_fixed(user_id, progress, profile['access_level'])
        
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
    """FIXED: Get user statistics with correct data"""
    try:
        user_id = session['user_id']
        logger.info(f"Getting stats for user {user_id}")
        
        profile = supabase_service.get_user_profile_by_service(user_id)
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        # FIXED: Get completions from the correct table with proper stats
        user_completions = supabase_service.get_user_completions(user_id, limit=1000)
        
        # FIXED: Calculate stats properly
        stats = {
            'total_sessions': len(user_completions),
            'total_minutes': sum(c.get('duration_minutes', 0) or 0 for c in user_completions),
            'successful_sessions': sum(1 for c in user_completions if c.get('success') is True),
            'success_rate': 0,
            'favorite_roleplay': None,
            'sessions_this_week': 0,
            'sessions_this_month': 0,
            'monthly_usage_minutes': profile.get('monthly_usage_minutes', 0) or 0,
            'lifetime_usage_minutes': profile.get('lifetime_usage_minutes', 0) or 0,
            'average_score': 0,
            'best_score': 0
        }
        
        # Calculate rates and averages
        if stats['total_sessions'] > 0:
            stats['success_rate'] = round((stats['successful_sessions'] / stats['total_sessions']) * 100, 1)
            
            # Calculate average and best scores
            scores = [c.get('score', 0) for c in user_completions if c.get('score', 0) > 0]
            if scores:
                stats['average_score'] = round(sum(scores) / len(scores), 1)
                stats['best_score'] = max(scores)
        
        # FIXED: Date calculations for recent activity
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        for completion in user_completions:
            try:
                completed_at = completion.get('completed_at')
                if not completed_at:
                    continue
                    
                session_date = _parse_iso_datetime(completed_at)
                
                if session_date >= week_ago:
                    stats['sessions_this_week'] += 1
                if session_date >= month_ago:
                    stats['sessions_this_month'] += 1
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse completion date {completed_at}: {e}")
                continue
        
        # FIXED: Calculate favorite roleplay
        roleplay_counts = {}
        for completion in user_completions:
            rp_id = completion.get('roleplay_id')
            if rp_id:
                # Extract main ID for counting (e.g., '1' from '1.1')
                try:
                    main_rp_id = rp_id.split('.')[0] if '.' in str(rp_id) else str(rp_id)
                    roleplay_counts[main_rp_id] = roleplay_counts.get(main_rp_id, 0) + 1
                except:
                    roleplay_counts[str(rp_id)] = roleplay_counts.get(str(rp_id), 0) + 1

        if roleplay_counts:
            favorite_id = max(roleplay_counts, key=roleplay_counts.get)
            roleplay_names = {
                '1': 'Opener & Early Objections',
                '2': 'Pitch & Close',
                '3': 'Warm-up Challenge',
                '4': 'Full Cold Call',
                '5': 'Power Hour'
            }
            stats['favorite_roleplay'] = roleplay_names.get(favorite_id, f'Roleplay {favorite_id}')
        
        logger.info(f"Successfully retrieved stats for user {user_id}: {stats['total_sessions']} sessions")
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/sessions', methods=['GET'])
@require_auth
def get_user_sessions():
    """FIXED: Get user's roleplay sessions with enhanced data"""
    try:
        user_id = session['user_id']
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        logger.info(f"Getting sessions for user {user_id}, page {page}, limit {limit}")
        
        offset = (page - 1) * limit
        user_completions = supabase_service.get_user_completions(user_id, limit=limit, offset=offset)
        total_count = supabase_service.get_completion_count(user_id)
        
        # FIXED: Enhance session data with proper formatting
        enhanced_sessions = []
        for session in user_completions:
            try:
                enhanced_session = {
                    'id': session.get('id'),
                    'roleplay_id': session.get('roleplay_id'),
                    'mode': session.get('mode', 'practice'),
                    'score': session.get('score', 0),
                    'success': session.get('success', False),
                    'duration_minutes': session.get('duration_minutes', 0),
                    'completed_at': session.get('completed_at'),
                    'started_at': session.get('started_at'),
                    'created_at': session.get('created_at'),
                    
                    # FIXED: Add formatted fields for display
                    'roleplay_name': _get_roleplay_display_name(session.get('roleplay_id')),
                    'duration_display': _format_duration(session.get('duration_minutes', 0)),
                    'score_display': f"{session.get('score', 0)}/100",
                    'result_display': 'Success' if session.get('success', False) else 'Practice',
                    'date_display': _format_date(session.get('completed_at')),
                    
                    # Additional helpful info
                    'coaching_feedback': session.get('coaching_feedback'),
                    'forced_end': session.get('forced_end', False)
                }
                enhanced_sessions.append(enhanced_session)
            except Exception as session_error:
                logger.warning(f"Error enhancing session data: {session_error}")
                enhanced_sessions.append(session)  # Fallback to original
        
        logger.info(f"Successfully retrieved {len(enhanced_sessions)} sessions for user {user_id}")
        return jsonify({
            'sessions': enhanced_sessions,
            'total_count': total_count,
            'page': page,
            'limit': limit,
            'total_pages': (total_count + limit - 1) // limit if total_count > 0 else 1
        })
        
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/roleplay-progress', methods=['GET'])
@require_auth
def get_user_roleplay_progress():
    """FIXED: Get comprehensive user roleplay progress"""
    try:
        user_id = session.get('user_id')
        
        # Get progress data from the service
        progress = progress_service.get_user_roleplay_progress(user_id)
        available_roleplays = _get_available_roleplays(user_id)
        completion_stats = progress_service.get_completion_stats(user_id)
        recommendations = _get_next_recommendations(user_id, progress)
        
        # Get recent activity
        recent_completions = get_recent_completions(user_id, limit=5)
        
        # Get achievements
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

@user_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
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

# ===== FIXED HELPER FUNCTIONS =====

def _get_roleplay_access_fixed(user_id: str, progress: Dict[str, Any], access_level: str) -> Dict[str, Any]:
    """FIXED: Get roleplay unlock status using progress service"""
    access = {}
    
    roleplay_ids = ['1.1', '1.2', '1.3', '2.1', '2.2', '3', '4', '5']
    
    for roleplay_id in roleplay_ids:
        try:
            # Use the progress service for access checking
            access_check = progress_service.check_roleplay_access(user_id, roleplay_id)
            progress_data = progress.get(roleplay_id, {})
            
            access[roleplay_id] = {
                'unlocked': access_check['allowed'],
                'unlock_condition': access_check.get('reason', 'Unknown'),
                'expires_at': None,  # Not used for now
                'required_roleplay': access_check.get('required_roleplay'),
                'current_progress': access_check.get('current_progress'),
                'best_score': progress_data.get('best_score', 0),
                'total_attempts': progress_data.get('total_attempts', 0),
                'marathon_passed': progress_data.get('marathon_passed', False),
                'completed': progress_data.get('completed', False)
            }
        except Exception as e:
            logger.warning(f"Error checking access for {roleplay_id}: {e}")
            access[roleplay_id] = {
                'unlocked': roleplay_id in ['1.1', '1.2', '3'],  # Fallback
                'unlock_condition': 'Error checking access',
                'expires_at': None
            }
    
    return access

def _get_available_roleplays(user_id: str) -> List[str]:
    """Get list of roleplays available to the user"""
    try:
        available = []
        
        # Always available
        always_available = ['1.1', '1.2', '3']
        available.extend(always_available)
        
        # Check unlocked roleplays using progress service
        for roleplay_id in ['1.3', '2.1', '2.2', '4', '5']:
            try:
                access_check = progress_service.check_roleplay_access(user_id, roleplay_id)
                if access_check['allowed']:
                    available.append(roleplay_id)
            except Exception as e:
                logger.warning(f"Error checking access for {roleplay_id}: {e}")
        
        logger.info(f"Available roleplays for user {user_id}: {available}")
        return available
        
    except Exception as e:
        logger.error(f"Error getting available roleplays: {e}")
        return ['1.1', '1.2', '3']  # Safe fallback

def _get_next_recommendations(user_id: str, progress: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get next recommended actions for the user"""
    try:
        recommendations = []
        
        # Check Marathon progression
        marathon_progress = progress.get('1.2', {})
        if marathon_progress.get('marathon_passed', False):
            # User has passed marathon - recommend advanced content
            rp21_progress = progress.get('2.1', {})
            if not rp21_progress.get('best_score', 0) >= 70:
                recommendations.append({
                    'roleplay_id': '2.1',
                    'name': 'Post-Pitch Practice',
                    'priority': 'high',
                    'reason': 'Newly unlocked! Practice advanced conversation skills.',
                    'best_score': rp21_progress.get('best_score', 0),
                    'attempts': rp21_progress.get('total_attempts', 0)
                })
        else:
            # User hasn't passed marathon yet
            if marathon_progress.get('total_attempts', 0) == 0:
                recommendations.append({
                    'roleplay_id': '1.2',
                    'name': 'Marathon Mode',
                    'priority': 'high',
                    'reason': 'Complete this to unlock advanced content!',
                    'best_score': marathon_progress.get('marathon_best_run', 0),
                    'attempts': marathon_progress.get('total_attempts', 0)
                })
        
        # Always recommend practice if struggling
        practice_progress = progress.get('1.1', {})
        if practice_progress.get('best_score', 0) < 80:
            recommendations.append({
                'roleplay_id': '1.1',
                'name': 'Practice Mode',
                'priority': 'medium',
                'reason': 'Strengthen fundamentals before advancing',
                'best_score': practice_progress.get('best_score', 0),
                'attempts': practice_progress.get('total_attempts', 0)
            })
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: (priority_order.get(x['priority'], 3), x['attempts']))
        
        return recommendations[:3]
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return []

def _get_roleplay_display_name(roleplay_id: str) -> str:
    """Get display name for roleplay ID"""
    names = {
        '1.1': 'Practice Mode',
        '1.2': 'Marathon Mode', 
        '1.3': 'Legend Mode',
        '2.1': 'Post-Pitch Practice',
        '2.2': 'Advanced Marathon',
        '3': 'Warm-up Challenge',
        '4': 'Full Cold Call',
        '5': 'Power Hour'
    }
    return names.get(str(roleplay_id), f'Roleplay {roleplay_id}')

def _format_duration(minutes: int) -> str:
    """Format duration in minutes to readable string"""
    if minutes < 1:
        return "< 1 min"
    elif minutes < 60:
        return f"{minutes} min"
    else:
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes == 0:
            return f"{hours}h"
        else:
            return f"{hours}h {remaining_minutes}m"

def _format_date(date_string: str) -> str:
    """Format date string for display"""
    try:
        if not date_string:
            return "Unknown"
        
        date_obj = _parse_iso_datetime(date_string)
        now = datetime.now(timezone.utc)
        diff = now - date_obj
        
        if diff.days == 0:
            return "Today"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        else:
            return date_obj.strftime("%b %d, %Y")
    except:
        return "Unknown"

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

def get_user_achievements_helper(user_id: str):
    """Helper function to get user achievements"""
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

@user_bp.route('/achievements', methods=['GET'])
@require_auth  
def get_user_achievements():
    """Get user's achievements"""
    try:
        user_id = session.get('user_id')
        return jsonify(get_user_achievements_helper(user_id))
        
    except Exception as e:
        logger.error(f"Error getting achievements: {e}")
        return jsonify({'achievements': [], 'total_points': 0, 'total_count': 0})

def get_recent_completions(user_id: str, limit: int = 5):
    """Get recent roleplay completions"""
    try:
        result = supabase_service.get_service_client().table('roleplay_completions').select(
            'roleplay_id, score, completed_at, duration_minutes, success, mode'
        ).eq('user_id', user_id).order('completed_at', desc=True).limit(limit).execute()
        
        # Enhance the data for display
        enhanced_completions = []
        for completion in (result.data or []):
            enhanced_completions.append({
                **completion,
                'roleplay_name': _get_roleplay_display_name(completion.get('roleplay_id')),
                'duration_display': _format_duration(completion.get('duration_minutes', 0)),
                'date_display': _format_date(completion.get('completed_at'))
            })
        
        return enhanced_completions
        
    except Exception as e:
        logger.error(f"Error getting recent completions: {e}")
        return []

logger.info("User progress routes initialized with fixes")

# ===== Add this to your routes/debug.py or routes/user.py =====

@user_bp.route('/debug/progress/<user_id>', methods=['GET'])
def debug_user_progress(user_id):
    """Debug endpoint to check user progress data flow"""
    try:
        debug_info = {
            'user_id': user_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data_sources': {}
        }
        
        # 1. Check user_roleplay_progress table
        try:
            client = supabase_service.get_service_client()
            progress_records = client.table('user_roleplay_progress').select('*').eq('user_id', user_id).execute()
            debug_info['data_sources']['user_roleplay_progress'] = {
                'count': len(progress_records.data or []),
                'records': progress_records.data or []
            }
        except Exception as e:
            debug_info['data_sources']['user_roleplay_progress'] = {'error': str(e)}
        
        # 2. Check roleplay_completions table
        try:
            completions = client.table('roleplay_completions').select('*').eq('user_id', user_id).order('completed_at', desc=True).execute()
            debug_info['data_sources']['roleplay_completions'] = {
                'count': len(completions.data or []),
                'recent_records': (completions.data or [])[:5]  # Last 5 for brevity
            }
        except Exception as e:
            debug_info['data_sources']['roleplay_completions'] = {'error': str(e)}
        
        # 3. Check what the progress service returns
        try:
            progress_service_data = progress_service.get_user_roleplay_progress(user_id)
            debug_info['data_sources']['progress_service'] = {
                'roleplay_ids': list(progress_service_data.keys()),
                'data': progress_service_data
            }
        except Exception as e:
            debug_info['data_sources']['progress_service'] = {'error': str(e)}
        
        # 4. Check access checks
        try:
            access_checks = {}
            for rp_id in ['1.1', '1.2', '1.3', '2.1']:
                access_checks[rp_id] = progress_service.check_roleplay_access(user_id, rp_id)
            debug_info['data_sources']['access_checks'] = access_checks
        except Exception as e:
            debug_info['data_sources']['access_checks'] = {'error': str(e)}
        
        # 5. Check what gets returned by the profile endpoint
        try:
            # Simulate what the frontend gets
            profile = supabase_service.get_user_profile_by_service(user_id)
            progress = progress_service.get_user_roleplay_progress(user_id)
            
            debug_info['frontend_simulation'] = {
                'profile_exists': profile is not None,
                'progress_keys': list(progress.keys()) if progress else [],
                'marathon_data': progress.get('1.2', {}),
                'practice_data': progress.get('1.1', {})
            }
        except Exception as e:
            debug_info['frontend_simulation'] = {'error': str(e)}
        
        # 6. Raw SQL check for Marathon data
        try:
            # Direct query to see what's actually in the database
            marathon_query = """
                SELECT * FROM user_roleplay_progress 
                WHERE user_id = %s AND roleplay_id = '1.2'
            """
            # Note: This would need to be adapted based on your actual DB access method
            debug_info['raw_marathon_check'] = "SQL query would go here - check manually"
        except Exception as e:
            debug_info['raw_marathon_check'] = {'error': str(e)}
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': f'Debug endpoint failed: {str(e)}'}), 500

@user_bp.route('/debug/simulate-marathon/<user_id>', methods=['POST'])
def debug_simulate_marathon(user_id):
    """Debug endpoint to simulate a marathon completion"""
    try:
        # Simulate marathon completion data
        completion_data = {
            'user_id': user_id,
            'session_id': f'debug_session_{int(datetime.now().timestamp())}',
            'roleplay_id': '1.2',
            'mode': 'marathon',
            'score': 75,
            'success': True,
            'duration_minutes': 25,
            'started_at': (datetime.now(timezone.utc) - timedelta(minutes=25)).isoformat(),
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'marathon_results': {
                'calls_passed': 6,
                'calls_total': 10,
                'marathon_passed': True,
                'marathon_completed': True
            }
        }
        
        # Save completion
        completion_id = progress_service.save_roleplay_completion(completion_data)
        
        # Update progress
        progress_updated = progress_service.update_user_progress_after_completion(completion_data)
        
        # Check what was actually saved
        updated_progress = progress_service.get_user_roleplay_progress(user_id, ['1.2'])
        
        return jsonify({
            'success': True,
            'completion_id': completion_id,
            'progress_updated': progress_updated,
            'final_progress': updated_progress.get('1.2', {}),
            'completion_data': completion_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Simulation failed: {str(e)}'}), 500

@user_bp.route('/debug/fix-marathon/<user_id>', methods=['POST'])
def debug_fix_marathon(user_id):
    """Debug endpoint to manually fix marathon data"""
    try:
        client = supabase_service.get_service_client()
        
        # Get current record
        existing = client.table('user_roleplay_progress').select('*').eq(
            'user_id', user_id
        ).eq('roleplay_id', '1.2').execute()
        
        if not existing.data:
            return jsonify({'error': 'No 1.2 progress record found'}), 404
        
        current = existing.data[0]
        
        # Manually set marathon as passed based on request data
        request_data = request.get_json() or {}
        calls_passed = request_data.get('calls_passed', 6)
        
        updates = {
            'marathon_best_run': calls_passed,
            'marathon_completed': calls_passed >= 6,
            'marathon_passed': calls_passed >= 6,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Update the record
        result = client.table('user_roleplay_progress').update(updates).eq('id', current['id']).execute()
        
        # Verify the update
        updated_record = client.table('user_roleplay_progress').select('*').eq('id', current['id']).execute()
        
        return jsonify({
            'success': True,
            'before': current,
            'updates_applied': updates,
            'after': updated_record.data[0] if updated_record.data else None
        })
        
    except Exception as e:
        return jsonify({'error': f'Fix failed: {str(e)}'}), 500
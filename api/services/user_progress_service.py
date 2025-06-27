# ===== services/user_progress_service.py =====

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)

class UserProgressService:
    """Service for managing user roleplay progress and achievements"""
    
    def __init__(self, supabase_service=None):
        if supabase_service:
            self.supabase = supabase_service
        else:
            # Import here to avoid circular imports
            try:
                from .supabase_client import SupabaseService
                self.supabase = SupabaseService()
            except ImportError as e:
                logger.error(f"Failed to import SupabaseService: {e}")
                self.supabase = None
        
        # Roleplay progression rules
        self.progression_rules = {
            '1.1': {
                'name': 'Practice Mode',
                'unlocks': [],
                'required_for': ['1.2'],
                'always_available': True
            },
            '1.2': {
                'name': 'Marathon Mode', 
                'unlocks': ['1.3'],
                'required_for': ['2.1'],
                'requires_completion': False,
                'requires_pass': False
            },
            '1.3': {
                'name': 'Legend Mode',
                'unlocks': ['2.1', '2.2'],
                'required_for': [],
                'requires_completion': '1.2',
                'requires_pass': True
            },
            '2.1': {
                'name': 'Advanced Practice',
                'unlocks': ['2.2'],
                'required_for': [],
                'requires_completion': '1.3',
                'requires_pass': True
            },
            '2.2': {
                'name': 'Advanced Marathon',
                'unlocks': [],
                'required_for': [],
                'requires_completion': '2.1',
                'requires_pass': True
            }
        }
        
        logger.info("UserProgressService initialized")
    
    def check_roleplay_access(self, user_id: str, roleplay_id: str) -> Dict[str, Any]:
        """Check if user has access to a specific roleplay"""
        try:
            if not self.supabase:
                return {'allowed': True, 'reason': 'Service unavailable'}
            
            # Always allow Practice Mode (1.1)
            if roleplay_id == '1.1':
                return {'allowed': True, 'reason': 'Always available'}
            
            rules = self.progression_rules.get(roleplay_id)
            if not rules:
                return {'allowed': False, 'reason': f'Unknown roleplay: {roleplay_id}'}
            
            # Check if requires completion of another roleplay
            if 'requires_completion' in rules:
                required_roleplay = rules['requires_completion']
                requires_pass = rules.get('requires_pass', False)
                
                progress = self.get_user_roleplay_progress(user_id, [required_roleplay])
                required_progress = progress.get(required_roleplay)
                
                if not required_progress:
                    return {
                        'allowed': False,
                        'reason': f'Must complete {self.progression_rules[required_roleplay]["name"]} first',
                        'requirements': [required_roleplay]
                    }
                
                if requires_pass and not required_progress.get('completed'):
                    return {
                        'allowed': False,
                        'reason': f'Must pass {self.progression_rules[required_roleplay]["name"]} first',
                        'requirements': [required_roleplay]
                    }
            
            return {'allowed': True, 'reason': 'Access granted'}
            
        except Exception as e:
            logger.error(f"Error checking roleplay access: {e}")
            return {'allowed': True, 'reason': 'Error checking access'}
    
    def get_user_roleplay_progress(self, user_id: str, roleplay_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get user's progress for specific roleplays or all roleplays"""
        try:
            if not self.supabase:
                return {}
            
            # Get progress records
            if roleplay_ids:
                progress_records = []
                for roleplay_id in roleplay_ids:
                    records = self.supabase.get_data_with_filter(
                        'user_roleplay_progress',
                        'user_id',
                        user_id,
                        additional_filters={'roleplay_id': roleplay_id}
                    )
                    progress_records.extend(records)
            else:
                progress_records = self.supabase.get_data_with_filter(
                    'user_roleplay_progress',
                    'user_id',
                    user_id
                )
            
            # Get recent completions for additional context
            completions = self.supabase.get_data_with_filter(
                'roleplay_completions',
                'user_id',
                user_id,
                limit=50,
                order_by='created_at',
                ascending=False
            )
            
            # Build progress dictionary
            progress = {}
            
            for record in progress_records:
                roleplay_id = record['roleplay_id']
                
                # Get recent completions for this roleplay
                roleplay_completions = [c for c in completions if c['roleplay_id'] == roleplay_id]
                
                progress[roleplay_id] = {
                    'best_score': record.get('best_score', 0),
                    'total_attempts': record.get('total_attempts', 0),
                    'successful_attempts': record.get('successful_attempts', 0),
                    'marathon_best_run': record.get('marathon_best_run', 0),
                    'marathon_completed': record.get('marathon_completed', False),
                    'marathon_passed': record.get('marathon_passed', False),
                    'legend_streak': record.get('legend_streak', 0),
                    'legend_completed': record.get('legend_completed', False),
                    'is_unlocked': record.get('is_unlocked', True),
                    'first_attempt_at': record.get('first_attempt_at'),
                    'last_attempt_at': record.get('last_attempt_at'),
                    'recent_completions': roleplay_completions[:5],  # Last 5 attempts
                    'completed': self._determine_completion_status(roleplay_id, record, roleplay_completions),
                    'passed': self._determine_pass_status(roleplay_id, record, roleplay_completions)
                }
            
            return progress
            
        except Exception as e:
            logger.error(f"Error getting user roleplay progress: {e}")
            return {}
    
    def _determine_completion_status(self, roleplay_id: str, progress_record: Dict, completions: List[Dict]) -> bool:
        """Determine if user has completed a roleplay based on type"""
        if roleplay_id.endswith('.1'):  # Practice modes
            return progress_record.get('best_score', 0) >= 70
        elif roleplay_id.endswith('.2'):  # Marathon modes
            return progress_record.get('marathon_completed', False) and progress_record.get('marathon_passed', False)
        elif roleplay_id.endswith('.3'):  # Legend modes
            return progress_record.get('legend_completed', False)
        else:
            return len(completions) > 0 and any(c.get('success', False) for c in completions)
    
    def _determine_pass_status(self, roleplay_id: str, progress_record: Dict, completions: List[Dict]) -> bool:
        """Determine if user has passed a roleplay"""
        if roleplay_id.endswith('.1'):  # Practice modes
            return progress_record.get('best_score', 0) >= 70
        elif roleplay_id.endswith('.2'):  # Marathon modes
            return progress_record.get('marathon_passed', False)
        elif roleplay_id.endswith('.3'):  # Legend modes
            return progress_record.get('legend_completed', False)
        else:
            return progress_record.get('best_score', 0) >= 70
    
    def log_roleplay_attempt(self, user_id: str, roleplay_id: str, session_id: str) -> bool:
        """Log that a user started a roleplay attempt"""
        try:
            if not self.supabase:
                return False
            
            # Create or update progress record
            now = datetime.now(timezone.utc).isoformat()
            
            existing_progress = self.supabase.get_data_with_filter(
                'user_roleplay_progress',
                'user_id',
                user_id,
                additional_filters={'roleplay_id': roleplay_id}
            )
            
            if existing_progress:
                # Update existing record
                progress_id = existing_progress[0]['id']
                updates = {
                    'total_attempts': (existing_progress[0].get('total_attempts', 0) + 1),
                    'last_attempt_at': now,
                    'updated_at': now
                }
                
                if not existing_progress[0].get('first_attempt_at'):
                    updates['first_attempt_at'] = now
                
                self.supabase.update_data_by_id('user_roleplay_progress', {'id': progress_id}, updates)
            else:
                # Create new progress record
                self.supabase.insert_data('user_roleplay_progress', {
                    'user_id': user_id,
                    'roleplay_id': roleplay_id,
                    'total_attempts': 1,
                    'first_attempt_at': now,
                    'last_attempt_at': now,
                    'is_unlocked': True,
                    'created_at': now
                })
            
            logger.info(f"Logged roleplay attempt: {user_id} -> {roleplay_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging roleplay attempt: {e}")
            return False
    
    def save_roleplay_completion(self, completion_data: Dict[str, Any]) -> Optional[str]:
        # ... this method is fine, no changes needed, but ensure it's here ...
        try:
            if not self.supabase:
                return None
            for key in ['ai_evaluation', 'coaching_feedback', 'conversation_data', 'rubric_scores', 'marathon_results']:
                if key in completion_data and not isinstance(completion_data[key], (str, type(None))):
                    completion_data[key] = json.dumps(completion_data[key])
            result = self.supabase.insert_data('roleplay_completions', completion_data)
            if result:
                completion_id = result.get('id')
                logger.info(f"Saved roleplay completion: {completion_id}")
                return completion_id
            return None
        except Exception as e:
            logger.error(f"Error saving roleplay completion: {e}", exc_info=True)
            return None
        
    def update_user_progress_after_completion(self, completion_data: Dict[str, Any]) -> bool:
        """
        Updates aggregate stats in user_roleplay_stats and usage in user_profiles.
        This is the core function for tracking user progress after a call.
        """
        try:
            if not self.supabase:
                return False

            user_id = completion_data.get('user_id')
            roleplay_id = completion_data.get('roleplay_id')
            score = completion_data.get('score', 0)
            duration = completion_data.get('duration_minutes', 1)
            now = datetime.now(timezone.utc).isoformat()

            if not all([user_id, roleplay_id, score is not None, duration is not None]):
                logger.error(f"Missing data for progress update: {completion_data}")
                return False

            # --- 1. Update user_roleplay_stats ---
            client = self.supabase.get_service_client()
            stats_query = client.table('user_roleplay_stats').select('*').eq('user_id', user_id).eq('roleplay_id', roleplay_id).maybe_single().execute()
            
            if stats_query.data:
                current_stats = stats_query.data
                updates = {
                    'total_attempts': current_stats.get('total_attempts', 0) + 1,
                    'last_score': score,
                    'last_attempt_at': now,
                    'best_score': max(current_stats.get('best_score', 0), score),
                    'completed': current_stats.get('completed') or (score >= 70)
                }
                client.table('user_roleplay_stats').update(updates).eq('id', current_stats['id']).execute()
            else:
                new_stats = {
                    'user_id': user_id,
                    'roleplay_id': roleplay_id,
                    'total_attempts': 1,
                    'best_score': score,
                    'last_score': score,
                    'completed': score >= 70,
                    'last_attempt_at': now
                }
                client.table('user_roleplay_stats').insert(new_stats).execute()
            logger.info(f"Updated user_roleplay_stats for {user_id} on {roleplay_id}")

            # --- 2. Update user_profiles for usage time ---
            profile_query = client.table('user_profiles').select('lifetime_usage_minutes, monthly_usage_minutes').eq('id', user_id).single().execute()
            
            if profile_query.data:
                profile = profile_query.data
                new_lifetime_usage = (profile.get('lifetime_usage_minutes') or 0) + duration
                new_monthly_usage = (profile.get('monthly_usage_minutes') or 0) + duration
                
                profile_updates = {
                    'lifetime_usage_minutes': new_lifetime_usage,
                    'monthly_usage_minutes': new_monthly_usage,
                    'last_active_at': now
                }
                client.table('user_profiles').update(profile_updates).eq('id', user_id).execute()
                logger.info(f"Updated usage for user {user_id}: +{duration} minutes")

            return True

        except Exception as e:
            logger.error(f"Error updating user progress after completion: {e}", exc_info=True)
            return False
        
    def update_user_progress(self, user_id: str, roleplay_id: str, completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user's overall progress based on a completion"""
        try:
            if not self.supabase:
                return {'updated': False, 'error': 'Service unavailable'}
            
            score = completion_data.get('score', 0)
            success = completion_data.get('success', False)
            marathon_results = completion_data.get('marathon_results')
            
            # Get existing progress
            existing_progress = self.supabase.get_data_with_filter(
                'user_roleplay_progress',
                'user_id',
                user_id,
                additional_filters={'roleplay_id': roleplay_id}
            )
            
            if not existing_progress:
                # Create initial progress record
                progress_data = {
                    'user_id': user_id,
                    'roleplay_id': roleplay_id,
                    'best_score': score,
                    'total_attempts': 1,
                    'successful_attempts': 1 if success else 0,
                    'is_unlocked': True,
                    'first_attempt_at': completion_data.get('started_at'),
                    'last_attempt_at': completion_data.get('ended_at'),
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                
                # Handle mode-specific data
                if roleplay_id.endswith('.2') and marathon_results:  # Marathon mode
                    progress_data.update({
                        'marathon_best_run': marathon_results.get('calls_passed', 0),
                        'marathon_completed': marathon_results.get('marathon_complete', False),
                        'marathon_passed': marathon_results.get('marathon_passed', False)
                    })
                elif roleplay_id.endswith('.3'):  # Legend mode
                    progress_data.update({
                        'legend_streak': score // 10,  # Simplified calculation
                        'legend_completed': success
                    })
                
                self.supabase.insert_data('user_roleplay_progress', progress_data)
                
            else:
                # Update existing progress
                current_progress = existing_progress[0]
                progress_id = current_progress['id']
                
                updates = {
                    'last_attempt_at': completion_data.get('ended_at'),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
                
                # Update best score if this is better
                if score > current_progress.get('best_score', 0):
                    updates['best_score'] = score
                
                # Update successful attempts
                if success:
                    updates['successful_attempts'] = current_progress.get('successful_attempts', 0) + 1
                
                # Handle mode-specific updates
                if roleplay_id.endswith('.2') and marathon_results:  # Marathon mode
                    calls_passed = marathon_results.get('calls_passed', 0)
                    if calls_passed > current_progress.get('marathon_best_run', 0):
                        updates['marathon_best_run'] = calls_passed
                    
                    if marathon_results.get('marathon_complete', False):
                        updates['marathon_completed'] = True
                        
                    if marathon_results.get('marathon_passed', False):
                        updates['marathon_passed'] = True
                        
                elif roleplay_id.endswith('.3') and success:  # Legend mode
                    updates['legend_completed'] = True
                    updates['legend_streak'] = max(current_progress.get('legend_streak', 0), score // 10)
                
                self.supabase.update_data_by_id('user_roleplay_progress', {'id': progress_id}, updates)
            
            logger.info(f"Updated user progress: {user_id} -> {roleplay_id} (score: {score})")
            
            return {
                'updated': True,
                'best_score': score,
                'completion_recorded': True
            }
            
        except Exception as e:
            logger.error(f"Error updating user progress: {e}")
            return {'updated': False, 'error': str(e)}
    
    def check_new_unlocks(self, user_id: str) -> List[str]:
        """Check for new roleplay unlocks based on current progress"""
        try:
            if not self.supabase:
                return []
            
            unlocked_roleplays = []
            progress = self.get_user_roleplay_progress(user_id)
            
            for roleplay_id, rules in self.progression_rules.items():
                if 'unlocks' not in rules or not rules['unlocks']:
                    continue
                
                # Check if this roleplay was just completed
                roleplay_progress = progress.get(roleplay_id)
                if not roleplay_progress or not roleplay_progress.get('completed'):
                    continue
                
                # Check what this roleplay unlocks
                for unlock_id in rules['unlocks']:
                    unlock_progress = progress.get(unlock_id)
                    
                    # If not yet unlocked, add to unlocks list
                    if not unlock_progress or not unlock_progress.get('is_unlocked'):
                        unlocked_roleplays.append(unlock_id)
                        
                        # Update database to mark as unlocked
                        try:
                            existing = self.supabase.get_data_with_filter(
                                'user_roleplay_progress',
                                'user_id',
                                user_id,
                                additional_filters={'roleplay_id': unlock_id}
                            )
                            
                            now = datetime.now(timezone.utc).isoformat()
                            
                            if existing:
                                self.supabase.update_data_by_id(
                                    'user_roleplay_progress',
                                    {'id': existing[0]['id']},
                                    {'is_unlocked': True, 'unlocked_at': now, 'updated_at': now}
                                )
                            else:
                                self.supabase.insert_data('user_roleplay_progress', {
                                    'user_id': user_id,
                                    'roleplay_id': unlock_id,
                                    'is_unlocked': True,
                                    'unlocked_at': now,
                                    'created_at': now
                                })
                                
                        except Exception as unlock_error:
                            logger.error(f"Error updating unlock status: {unlock_error}")
            
            if unlocked_roleplays:
                logger.info(f"New unlocks for {user_id}: {unlocked_roleplays}")
            
            return unlocked_roleplays
            
        except Exception as e:
            logger.error(f"Error checking new unlocks: {e}")
            return []
    
    def get_available_roleplays(self, user_id: str) -> List[str]:
        """Get list of roleplays available to the user"""
        try:
            progress = self.get_user_roleplay_progress(user_id)
            available = []
            
            for roleplay_id, rules in self.progression_rules.items():
                access_check = self.check_roleplay_access(user_id, roleplay_id)
                if access_check['allowed']:
                    available.append(roleplay_id)
            
            return available
            
        except Exception as e:
            logger.error(f"Error getting available roleplays: {e}")
            return ['1.1']  # Always return at least Practice Mode
    
    def get_completion_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user's overall completion statistics"""
        try:
            if not self.supabase:
                return {}
            
            completions = self.supabase.get_data_with_filter(
                'roleplay_completions',
                'user_id',
                user_id
            )
            
            if not completions:
                return {
                    'total_sessions': 0,
                    'successful_sessions': 0,
                    'average_score': 0,
                    'total_time_minutes': 0,
                    'completion_rate': 0
                }
            
            total_sessions = len(completions)
            successful_sessions = len([c for c in completions if c.get('success', False)])
            scores = [c.get('score', 0) for c in completions if c.get('score', 0) > 0]
            total_time = sum(c.get('duration_minutes', 0) for c in completions)
            
            return {
                'total_sessions': total_sessions,
                'successful_sessions': successful_sessions,
                'average_score': sum(scores) / len(scores) if scores else 0,
                'best_score': max(scores) if scores else 0,
                'total_time_minutes': total_time,
                'completion_rate': (successful_sessions / total_sessions * 100) if total_sessions > 0 else 0,
                'roleplays_completed': len(set(c['roleplay_id'] for c in completions if c.get('success', False)))
            }
            
        except Exception as e:
            logger.error(f"Error getting completion stats: {e}")
            return {}
    
    def get_leaderboard(self, roleplay_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard for a specific roleplay"""
        try:
            if not self.supabase:
                return []
            
            # Get top scores for this roleplay
            progress_records = self.supabase.get_data_with_filter(
                'user_roleplay_progress',
                'roleplay_id',
                roleplay_id,
                limit=limit,
                order_by='best_score',
                ascending=False
            )
            
            leaderboard = []
            
            for i, record in enumerate(progress_records):
                if record.get('best_score', 0) > 0:
                    # Get user info (anonymized for privacy)
                    user_id = record['user_id']
                    
                    leaderboard.append({
                        'rank': i + 1,
                        'user_id': user_id[:8] + '...',  # Anonymized
                        'score': record.get('best_score', 0),
                        'total_attempts': record.get('total_attempts', 0),
                        'successful_attempts': record.get('successful_attempts', 0),
                        'completion_rate': (record.get('successful_attempts', 0) / max(record.get('total_attempts', 1), 1)) * 100,
                        'last_attempt': record.get('last_attempt_at')
                    })
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
    
    def get_next_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recommended next steps for the user"""
        try:
            progress = self.get_user_roleplay_progress(user_id)
            recommendations = []
            
            # Check what's available and not completed
            for roleplay_id, rules in self.progression_rules.items():
                access_check = self.check_roleplay_access(user_id, roleplay_id)
                
                if access_check['allowed']:
                    user_progress = progress.get(roleplay_id, {})
                    
                    if not user_progress.get('completed'):
                        priority = 'high' if roleplay_id == '1.1' else 'medium'
                        
                        recommendations.append({
                            'roleplay_id': roleplay_id,
                            'name': rules['name'],
                            'priority': priority,
                            'reason': self._get_recommendation_reason(roleplay_id, user_progress),
                            'best_score': user_progress.get('best_score', 0),
                            'attempts': user_progress.get('total_attempts', 0)
                        })
            
            # Sort by priority and attempts
            recommendations.sort(key=lambda x: (
                0 if x['priority'] == 'high' else 1,
                x['attempts']
            ))
            
            return recommendations[:3]  # Return top 3 recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    def _get_recommendation_reason(self, roleplay_id: str, progress: Dict[str, Any]) -> str:
        """Get reason for recommending a specific roleplay"""
        attempts = progress.get('total_attempts', 0)
        best_score = progress.get('best_score', 0)
        
        if attempts == 0:
            return "Not yet attempted"
        elif best_score < 70:
            return f"Best score: {best_score}% - keep practicing!"
        elif roleplay_id.endswith('.2'):
            return "Ready for marathon challenge"
        elif roleplay_id.endswith('.3'):
            return "Ready for legend challenge"
        else:
            return "Continue improving"

# Global instance
_user_progress_service = None

def get_user_progress_service():
    """Get global user progress service instance"""
    global _user_progress_service
    if _user_progress_service is None:
        _user_progress_service = UserProgressService()
    return _user_progress_service
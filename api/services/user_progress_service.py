# ===== services/user_progress_service.py =====

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta, timezone
logger = logging.getLogger(__name__)

class UserProgressService:
    """Service for managing user roleplay progress and achievements"""
    
    def __init__(self, supabase_service=None):
        if supabase_service:
            self.supabase = supabase_service
        else:
            try:
                from .supabase_client import SupabaseService
                self.supabase = SupabaseService()
            except ImportError as e:
                logger.error(f"Failed to import SupabaseService: {e}")
                self.supabase = None
        
        self.progression_rules = {
        '1.3': {
            'requires_completion': '1.2', 
            'pass_needed': True,
            'name': 'Legend Mode',
            'description': 'Requires Marathon Mode completion'
        },
        '2.1': {
            'requires_completion': '1.2',
            'pass_needed': True,  # Must pass Marathon Mode
            'name': 'Post-Pitch Practice', 
            'description': 'Advanced practice unlocked by Marathon completion',
            'unlock_benefits': [
                'Access to advanced objection handling',
                'Qualification training',
                'Meeting ask practice',
                'Module 2 content preview'
            ]
        },
        '2.2': {
            'requires_completion': '2.1',
            'pass_needed': True,
            'name': 'Advanced Marathon',
            'description': 'Requires Post-Pitch Practice completion'
        },
        '3': {
            'always_available': True,
            'name': 'Warm-up Challenge',
            'description': 'Always available for skill sharpening'
        },
        '4': {
            'requires_completion': '2.1',
            'pass_needed': True,
            'name': 'Full Cold Call Simulation',
            'description': 'Complete simulation requires advanced training'
        },
        '5': {
            'requires_completion': '2.2',
            'pass_needed': True,
            'name': 'Power Hour Challenge',
            'description': 'Ultimate endurance test'
        }
    }
    logger.info("UserProgressService initialized with enhanced progression rules")

    def get_user_roleplay_stats(self, user_id: str, roleplay_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Gets all roleplay stats for a user from the CORRECT `user_roleplay_progress` table.
        """
        try:
            if not self.supabase: return {}
            
            client = self.supabase.get_service_client()
            # TARGET THE CORRECT TABLE
            query = client.table('user_roleplay_progress').select('*').eq('user_id', user_id)
            
            if roleplay_id:
                query = query.eq('roleplay_id', roleplay_id)
                
            response = query.execute()
            
            stats_dict = {stat['roleplay_id']: stat for stat in response.data} if response.data else {}
            return stats_dict
        except Exception as e:
            logger.error(f"Error getting user roleplay stats from user_roleplay_progress: {e}", exc_info=True)
            return {}
        
    def check_roleplay_access(self, user_id: str, roleplay_id: str) -> Dict[str, Any]:
        """Enhanced access check with detailed reasoning"""
        try:
            # Always available roleplays
            always_available = ['1.1', '1.2', '3']
            if roleplay_id in always_available:
                return {'allowed': True, 'reason': 'Always available'}
            
            # Check progression rules
            rule = self.progression_rules.get(roleplay_id)
            if not rule:
                return {'allowed': True, 'reason': 'No specific unlock requirement'}

            required_rp_id = rule.get('requires_completion')
            if not required_rp_id:
                return {'allowed': True, 'reason': 'No prerequisite required'}
                
            # Get user's progress on required roleplay
            user_stats = self.get_user_roleplay_stats(user_id, required_rp_id)
            required_stats = user_stats.get(required_rp_id)
            
            if not required_stats:
                return {
                    'allowed': False, 
                    'reason': f'Complete {rule.get("description", required_rp_id)} first',
                    'required_roleplay': required_rp_id,
                    'required_name': rule.get('name', f'Roleplay {required_rp_id}')
                }
            
            # ENHANCED: Check specific pass conditions for each roleplay type
            if required_rp_id == '1.2':  # Marathon Mode
                # For 2.1 and 1.3, check marathon_passed flag
                if not required_stats.get('marathon_passed', False):
                    return {
                        'allowed': False,
                        'reason': f'Pass Marathon Mode (6/10 calls) to unlock {roleplay_id}',
                        'required_roleplay': required_rp_id,
                        'required_name': 'Marathon Mode',
                        'current_progress': f"{required_stats.get('marathon_best_run', 0)}/10 calls passed"
                    }
            elif required_rp_id == '1.3':  # Legend Mode
                if not required_stats.get('legend_completed', False):
                    return {
                        'allowed': False,
                        'reason': f'Complete Legend Mode to unlock {roleplay_id}',
                        'required_roleplay': required_rp_id,
                        'required_name': 'Legend Mode'
                    }
            elif required_rp_id == '2.1':  # Post-Pitch Practice
                # Check if user has passed 2.1 (score >= 70)
                if not required_stats.get('best_score', 0) >= 70:
                    return {
                        'allowed': False,
                        'reason': f'Pass Post-Pitch Practice (70+ score) to unlock {roleplay_id}',
                        'required_roleplay': required_rp_id,
                        'required_name': 'Post-Pitch Practice',
                        'current_progress': f"Best score: {required_stats.get('best_score', 0)}/100"
                    }
            else:
                # Generic completion check
                if not required_stats.get('completed', False):
                    return {
                        'allowed': False,
                        'reason': f'Complete {required_rp_id} to unlock {roleplay_id}',
                        'required_roleplay': required_rp_id
                    }

            return {
                'allowed': True, 
                'reason': 'Requirement met',
                'unlocked_by': required_rp_id
            }
            
        except Exception as e:
            logger.error(f"Error in check_roleplay_access for {roleplay_id}: {e}", exc_info=True)
            return {'allowed': False, 'reason': 'Error checking access'}

    def get_user_roleplay_progress(self, user_id: str, roleplay_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get user's progress for specific roleplays or all roleplays"""
        try:
            if not self.supabase:
                return {}
            
            # This part is correct, it queries the right table.
            client = self.supabase.get_service_client()
            query = client.table('user_roleplay_progress').select('*').eq('user_id', user_id)
            if roleplay_ids:
                query = query.in_('roleplay_id', roleplay_ids)
            
            progress_records = query.execute().data or []
            
            # Build the progress dictionary
            progress = {}
            for record in progress_records:
                roleplay_id = record['roleplay_id']
                
                # THIS IS THE CRITICAL FIX:
                # We determine the 'passed' status based on the specific rules for each mode.
                is_passed = False
                if roleplay_id.endswith('.1'):  # Practice Mode (e.g., '1.1')
                    is_passed = record.get('best_score', 0) >= 70
                elif roleplay_id.endswith('.2'):  # Marathon Mode (e.g., '1.2')
                    is_passed = record.get('marathon_passed', False)
                elif roleplay_id.endswith('.3'):  # Legend Mode (e.g., '1.3')
                    is_passed = record.get('legend_completed', False)

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
                    # The 'passed' key is now correctly determined by our logic above.
                    'passed': is_passed,
                    # We can remove the 'completed' key as 'passed' is more specific and useful.
                }
            
            return progress
            
        except Exception as e:
            logger.error(f"Error getting user roleplay progress: {e}", exc_info=True)
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
            
            now = datetime.now(timezone.utc).isoformat()
            
            table_to_query = 'user_roleplay_stats' # <--- CORRECT TABLE NAME

            existing_progress = self.supabase.get_data_with_filter(
                table_to_query, # <--- USE THE VARIABLE
                'user_id',
                user_id,
                additional_filters={'roleplay_id': roleplay_id}
            )
            
            if existing_progress:
                progress_id = existing_progress[0]['id']
                updates = {
                    'total_attempts': (existing_progress[0].get('total_attempts', 0) + 1),
                    'last_attempt_at': now,
                    'updated_at': now
                }
                if not existing_progress[0].get('first_attempt_at'):
                    updates['first_attempt_at'] = now
                self.supabase.update_data_by_id(table_to_query, {'id': progress_id}, updates) # <--- USE THE VARIABLE
            else:
                # Create new progress record
                self.supabase.insert_data(table_to_query, { # <--- USE THE VARIABLE
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
            logger.error(f"Error logging roleplay attempt: {e}", exc_info=True)
            return False
    def save_roleplay_completion(self, completion_data: Dict[str, Any]) -> Optional[str]:
        """Save a completed roleplay session to the completions table."""
        try:
            if not self.supabase: 
                return None
            
            # The Supabase client library automatically handles converting Python dicts
            # to jsonb. Manually calling json.dumps() causes an error.
            # We are REMOVING the loop that did this.
            
            # Create a copy to ensure we don't modify the original dict
            data_to_insert = completion_data.copy()

            response = self.supabase.insert_data('roleplay_completions', data_to_insert)
            
            if response:
                logger.info(f"✅ Successfully saved roleplay completion ID: {response.get('id')}")
                return response.get('id')
            else:
                logger.error(f"❌ Failed to save roleplay completion. insert_data returned None.")
                return None

        except Exception as e:
            logger.error(f"❌ Exception in save_roleplay_completion: {e}", exc_info=True)
            return None
        
    def update_user_progress_after_completion(self, completion_data: Dict[str, Any]) -> bool:
        """Enhanced progress update with Roleplay 2.1 unlocking"""
        try:
            if not self.supabase: return False

            user_id = completion_data.get('user_id')
            roleplay_id = completion_data.get('roleplay_id')
            score = completion_data.get('score', 0)
            duration = completion_data.get('duration_minutes', 1)
            marathon_results = completion_data.get('marathon_results', {})
            advanced_results = completion_data.get('advanced_results', {})

            if not all([user_id, roleplay_id, score is not None]):
                logger.warning(f"Insufficient data to update progress: {completion_data}")
                return False

            client = self.supabase.get_service_client()
            
            # --- ENHANCED: Marathon Mode completion unlocks 2.1 ---
            if roleplay_id == '1.2' and marathon_results.get('marathon_passed', False):
                logger.info(f"Marathon passed for user {user_id}. Unlocking Roleplay 2.1 and advanced content.")
                
                unlock_timestamp = datetime.now(timezone.utc)
                twenty_four_hours_from_now = (unlock_timestamp + timedelta(hours=24)).isoformat()
                
                # Unlock advanced features
                profile_updates = {
                    'legend_attempt_used': False,  # Grant Legend try
                    'module_2_unlocked_until': twenty_four_hours_from_now,  # Unlock Module 2
                    'roleplay_2_1_unlocked': True,  # NEW: Unlock 2.1
                    'updated_at': unlock_timestamp.isoformat()
                }
                self.supabase.update_data_by_id('user_profiles', {'id': user_id}, profile_updates)
                
                # Create initial progress record for 2.1
                try:
                    client.table('user_roleplay_progress').insert({
                        'user_id': user_id,
                        'roleplay_id': '2.1',
                        'is_unlocked': True,
                        'unlocked_at': unlock_timestamp.isoformat(),
                        'unlocked_by': '1.2',
                        'created_at': unlock_timestamp.isoformat()
                    }).execute()
                    logger.info(f"Created initial progress record for Roleplay 2.1 for user {user_id}")
                except Exception as insert_error:
                    logger.warning(f"Could not create 2.1 progress record: {insert_error}")
                
                logger.info(f"User {user_id} profile updated with Marathon Pass rewards and 2.1 access.")

            # --- ENHANCED: Roleplay 2.1 completion unlocks further content ---
            if roleplay_id == '2.1' and score >= 70:
                logger.info(f"Post-Pitch Practice passed for user {user_id}. Unlocking advanced roleplays.")
                
                unlock_timestamp = datetime.now(timezone.utc)
                
                # Unlock 2.2 and 4
                for unlock_id in ['2.2', '4']:
                    try:
                        client.table('user_roleplay_progress').insert({
                            'user_id': user_id,
                            'roleplay_id': unlock_id,
                            'is_unlocked': True,
                            'unlocked_at': unlock_timestamp.isoformat(),
                            'unlocked_by': '2.1',
                            'created_at': unlock_timestamp.isoformat()
                        }).execute()
                        logger.info(f"Unlocked Roleplay {unlock_id} for user {user_id}")
                    except Exception as unlock_error:
                        logger.warning(f"Could not unlock {unlock_id}: {unlock_error}")

            # Update user_roleplay_progress (main stats)
            current_stats_dict = self.get_user_roleplay_stats(user_id, roleplay_id)
            current_stats = current_stats_dict.get(roleplay_id)
            
            updates = {
                'last_score': score,
                'last_attempt_at': datetime.now(timezone.utc).isoformat(),
            }
            
            if current_stats:
                updates.update({
                    'total_attempts': current_stats.get('total_attempts', 0) + 1,
                    'best_score': max(current_stats.get('best_score', 0), score),
                    'completed': current_stats.get('completed') or (score >= 70)
                })
                
                # Add type-specific updates
                if marathon_results:
                    updates['marathon_passed'] = current_stats.get('marathon_passed') or marathon_results.get('marathon_passed')
                    updates['marathon_best_run'] = max(
                        current_stats.get('marathon_best_run', 0),
                        marathon_results.get('calls_passed', 0)
                    )
                
                if advanced_results:
                    updates['advanced_completed'] = advanced_results.get('company_fit_qualified', False) and advanced_results.get('meeting_asked', False)
                    updates['stages_completed'] = advanced_results.get('stages_completed', 0)

                client.table('user_roleplay_progress').update(updates).eq('id', current_stats['id']).execute()
            else:
                updates.update({
                    'user_id': user_id, 
                    'roleplay_id': roleplay_id, 
                    'total_attempts': 1, 
                    'best_score': score,
                    'completed': score >= 70
                })
                
                if marathon_results:
                    updates['marathon_passed'] = marathon_results.get('marathon_passed')
                    updates['marathon_best_run'] = marathon_results.get('calls_passed', 0)
                
                if advanced_results:
                    updates['advanced_completed'] = advanced_results.get('company_fit_qualified', False) and advanced_results.get('meeting_asked', False)
                    updates['stages_completed'] = advanced_results.get('stages_completed', 0)
                    
                client.table('user_roleplay_progress').insert(updates).execute()
            
            logger.info(f"Updated stats for user {user_id} on roleplay {roleplay_id}")

            # Update user_profiles for usage time
            client.rpc('increment_usage_minutes', { 'p_user_id': user_id, 'p_duration': duration }).execute()
            logger.info(f"Updated usage for user {user_id}: +{duration} minutes via RPC.")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in update_user_progress_after_completion: {e}", exc_info=True)
            return False

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
            available = []
            
            # Always available
            always_available = ['1.1', '1.2', '3']
            available.extend(always_available)
            
            # Check unlocked roleplays
            for roleplay_id in ['1.3', '2.1', '2.2', '4', '5']:
                access_check = self.check_roleplay_access(user_id, roleplay_id)
                if access_check['allowed']:
                    available.append(roleplay_id)
            
            logger.info(f"Available roleplays for user {user_id}: {available}")
            return available
            
        except Exception as e:
            logger.error(f"Error getting available roleplays: {e}")
            return ['1.1', '1.2', '3']  # Safe fallback

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
        """Enhanced recommendations including 2.1 pathway"""
        try:
            progress = self.get_user_roleplay_progress(user_id)
            recommendations = []
            
            # Check progression pathway
            marathon_progress = progress.get('1.2', {})
            if marathon_progress.get('marathon_passed', False):
                # User has passed marathon - recommend 2.1
                rp21_progress = progress.get('2.1', {})
                if not rp21_progress.get('best_score', 0) >= 70:
                    recommendations.append({
                        'roleplay_id': '2.1',
                        'name': 'Post-Pitch Practice',
                        'priority': 'high',
                        'reason': 'Newly unlocked! Practice advanced conversation skills.',
                        'best_score': rp21_progress.get('best_score', 0),
                        'attempts': rp21_progress.get('total_attempts', 0),
                        'unlock_benefit': 'Unlocks Advanced Marathon and Full Cold Call'
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
                        'attempts': marathon_progress.get('total_attempts', 0),
                        'unlock_benefit': 'Unlocks Legend Mode and Post-Pitch Practice'
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
    
    
    
    def save_roleplay_completion(self, completion_data: Dict[str, Any]) -> Optional[str]:
        """Save a completed roleplay session to the completions table."""
        try:
            if not self.supabase: 
                return None
            
            # The Supabase client library automatically handles converting Python dicts
            # to jsonb. Manually calling json.dumps() causes an error.
            # We are REMOVING the loop that did this.
            
            # Create a copy to ensure we don't modify the original dict
            data_to_insert = completion_data.copy()

            response = self.supabase.insert_data('roleplay_completions', data_to_insert)
            
            if response:
                logger.info(f"✅ Successfully saved roleplay completion ID: {response.get('id')}")
                return response.get('id')
            else:
                logger.error(f"❌ Failed to save roleplay completion. insert_data returned None.")
                return None

        except Exception as e:
            logger.error(f"❌ Exception in save_roleplay_completion: {e}", exc_info=True)
            return None
        
    
    
    
    
    
    

# Global instance
_user_progress_service = None

def get_user_progress_service():
    """Get global user progress service instance"""
    global _user_progress_service
    if _user_progress_service is None:
        _user_progress_service = UserProgressService()
    return _user_progress_service
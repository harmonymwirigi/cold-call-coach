# ===== FIXED: services/user_progress_service.py =====

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)

class UserProgressService:
    """FIXED Service for managing user roleplay progress and achievements"""
    
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
                'description': 'Advanced practice unlocked by Marathon completion'
            },
            '2.2': {
                'requires_completion': '2.1',
                'pass_needed': True,
                'name': 'Advanced Marathon',
                'description': 'Requires Post-Pitch Practice completion'
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

    def save_roleplay_completion(self, completion_data: Dict[str, Any]) -> Optional[str]:
        """Save a completed roleplay session to the completions table"""
        try:
            if not self.supabase: 
                return None
            
            # Create a copy to ensure we don't modify the original dict
            data_to_insert = completion_data.copy()
            
            # Ensure required fields have default values
            data_to_insert.setdefault('completed_at', datetime.now(timezone.utc).isoformat())
            data_to_insert.setdefault('success', False)
            data_to_insert.setdefault('score', 0)
            data_to_insert.setdefault('duration_minutes', 1)

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
        """FIXED: Enhanced progress update with proper data synchronization"""
        try:
            if not self.supabase: 
                return False

            user_id = completion_data.get('user_id')
            roleplay_id = completion_data.get('roleplay_id')
            score = completion_data.get('score', 0)
            duration = completion_data.get('duration_minutes', 1)
            success = completion_data.get('success', False)
            marathon_results = completion_data.get('marathon_results', {})
            advanced_results = completion_data.get('advanced_results', {})

            if not all([user_id, roleplay_id]):
                logger.warning(f"Insufficient data to update progress: {completion_data}")
                return False

            client = self.supabase.get_service_client()
            now = datetime.now(timezone.utc).isoformat()
            
            # Get current progress record
            existing_progress = client.table('user_roleplay_progress').select('*').eq(
                'user_id', user_id
            ).eq('roleplay_id', roleplay_id).execute()
            
            # Prepare update data
            updates = {
                'last_attempt_at': now,
                'updated_at': now,
            }
            
            if existing_progress.data:
                # Update existing record
                current = existing_progress.data[0]
                
                # FIXED: Properly increment attempt count
                updates.update({
                    'total_attempts': (current.get('total_attempts', 0) + 1),
                    'best_score': max(current.get('best_score', 0), score),
                    'last_score': score,
                })
                
                # FIXED: Count successful attempts correctly
                if success:
                    updates['successful_attempts'] = (current.get('successful_attempts', 0) + 1)
                
                # FIXED: Handle marathon-specific updates
                if roleplay_id == '1.2' and marathon_results:
                    calls_passed = marathon_results.get('calls_passed', 0)
                    marathon_passed = marathon_results.get('marathon_passed', False)
                    
                    updates.update({
                        'marathon_best_run': max(current.get('marathon_best_run', 0), calls_passed),
                        'marathon_completed': current.get('marathon_completed', False) or (calls_passed >= 6),
                        'marathon_passed': current.get('marathon_passed', False) or marathon_passed
                    })
                    
                    logger.info(f"Marathon progress for {user_id}: best_run={updates['marathon_best_run']}, passed={updates['marathon_passed']}")
                
                # FIXED: Handle practice mode completion
                if roleplay_id.endswith('.1'):  # Practice modes
                    updates['completed'] = score >= 70
                
                # FIXED: Handle legend mode
                if roleplay_id == '1.3' and advanced_results:
                    if advanced_results.get('legend_streak', 0) >= 6:
                        updates['legend_completed'] = True
                        updates['legend_streak'] = advanced_results.get('legend_streak', 0)
                
                # Update the record
                client.table('user_roleplay_progress').update(updates).eq('id', current['id']).execute()
                logger.info(f"✅ Updated existing progress for {user_id}/{roleplay_id}")
                
            else:
                # Create new record
                new_record = {
                    'user_id': user_id,
                    'roleplay_id': roleplay_id,
                    'total_attempts': 1,
                    'successful_attempts': 1 if success else 0,
                    'best_score': score,
                    'last_score': score,
                    'first_attempt_at': now,
                    'is_unlocked': True,
                    'created_at': now,
                    **updates
                }
                
                # FIXED: Handle marathon data for new records
                if roleplay_id == '1.2' and marathon_results:
                    calls_passed = marathon_results.get('calls_passed', 0)
                    marathon_passed = marathon_results.get('marathon_passed', False)
                    
                    new_record.update({
                        'marathon_best_run': calls_passed,
                        'marathon_completed': calls_passed >= 6,
                        'marathon_passed': marathon_passed
                    })
                
                # FIXED: Handle practice mode for new records
                if roleplay_id.endswith('.1'):
                    new_record['completed'] = score >= 70
                
                client.table('user_roleplay_progress').insert(new_record).execute()
                logger.info(f"✅ Created new progress record for {user_id}/{roleplay_id}")

            # FIXED: Handle unlocking logic for Marathon completion
            if roleplay_id == '1.2' and marathon_results.get('marathon_passed', False):
                logger.info(f"🔓 Marathon passed for user {user_id}. Unlocking advanced content...")
                
                # Unlock Legend Mode (1.3)
                self._ensure_roleplay_unlocked(user_id, '1.3', '1.2')
                
                # Unlock Post-Pitch Practice (2.1)
                self._ensure_roleplay_unlocked(user_id, '2.1', '1.2')
                
                # Update profile with unlock benefits
                unlock_timestamp = datetime.now(timezone.utc)
                profile_updates = {
                    'legend_attempt_used': False,
                    'module_2_unlocked_until': (unlock_timestamp + timedelta(hours=24)).isoformat(),
                    'updated_at': unlock_timestamp.isoformat()
                }
                self.supabase.update_data_by_id('user_profiles', {'id': user_id}, profile_updates)
                logger.info(f"✅ Updated profile unlocks for user {user_id}")

            # FIXED: Handle Post-Pitch Practice completion unlocking
            if roleplay_id == '2.1' and score >= 70:
                logger.info(f"🔓 Post-Pitch Practice passed for user {user_id}. Unlocking advanced content...")
                
                # Unlock Advanced Marathon (2.2) and Full Simulation (4)
                for unlock_id in ['2.2', '4']:
                    self._ensure_roleplay_unlocked(user_id, unlock_id, '2.1')

            # Update user profile usage
            try:
                client.rpc('increment_usage_minutes', {
                    'p_user_id': user_id, 
                    'p_duration': duration
                }).execute()
                logger.info(f"✅ Updated usage for user {user_id}: +{duration} minutes")
            except Exception as usage_error:
                logger.warning(f"⚠️ Could not update usage: {usage_error}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in update_user_progress_after_completion: {e}", exc_info=True)
            return False

    def _ensure_roleplay_unlocked(self, user_id: str, roleplay_id: str, unlocked_by: str):
        """Ensure a roleplay is unlocked for a user"""
        try:
            client = self.supabase.get_service_client()
            
            # Check if already exists
            existing = client.table('user_roleplay_progress').select('*').eq(
                'user_id', user_id
            ).eq('roleplay_id', roleplay_id).execute()
            
            now = datetime.now(timezone.utc).isoformat()
            
            if existing.data:
                # Update existing to ensure it's unlocked
                client.table('user_roleplay_progress').update({
                    'is_unlocked': True,
                    'unlocked_at': now,
                    'unlocked_by': unlocked_by,
                    'updated_at': now
                }).eq('id', existing.data[0]['id']).execute()
            else:
                # Create new unlocked record
                client.table('user_roleplay_progress').insert({
                    'user_id': user_id,
                    'roleplay_id': roleplay_id,
                    'is_unlocked': True,
                    'unlocked_at': now,
                    'unlocked_by': unlocked_by,
                    'created_at': now
                }).execute()
            
            logger.info(f"✅ Ensured {roleplay_id} is unlocked for user {user_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not ensure unlock for {roleplay_id}: {e}")

    def get_user_roleplay_progress(self, user_id: str, roleplay_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """FIXED: Get user's progress with correct data structure"""
        try:
            if not self.supabase:
                return {}
            
            client = self.supabase.get_service_client()
            query = client.table('user_roleplay_progress').select('*').eq('user_id', user_id)
            
            if roleplay_ids:
                query = query.in_('roleplay_id', roleplay_ids)
            
            progress_records = query.execute().data or []
            
            # FIXED: Build progress dictionary with correct field mappings
            progress = {}
            for record in progress_records:
                roleplay_id = record['roleplay_id']
                
                # FIXED: Determine passed status correctly
                is_passed = False
                if roleplay_id.endswith('.1'):  # Practice Mode
                    is_passed = record.get('best_score', 0) >= 70
                elif roleplay_id.endswith('.2'):  # Marathon Mode
                    is_passed = record.get('marathon_passed', False)
                elif roleplay_id.endswith('.3'):  # Legend Mode
                    is_passed = record.get('legend_completed', False)
                else:
                    is_passed = record.get('best_score', 0) >= 70
                
                progress[roleplay_id] = {
                    'best_score': record.get('best_score', 0),
                    'last_score': record.get('last_score', 0),
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
                    'unlocked_at': record.get('unlocked_at'),
                    'unlocked_by': record.get('unlocked_by'),
                    'completed': record.get('completed', False),
                    'passed': is_passed  # FIXED: Correct passed determination
                }
            
            logger.info(f"✅ Retrieved progress for user {user_id}: {list(progress.keys())}")
            return progress
            
        except Exception as e:
            logger.error(f"❌ Error getting user roleplay progress: {e}", exc_info=True)
            return {}

    def check_roleplay_access(self, user_id: str, roleplay_id: str) -> Dict[str, Any]:
        """FIXED: Enhanced access check with detailed reasoning"""
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
            user_progress = self.get_user_roleplay_progress(user_id, [required_rp_id])
            required_stats = user_progress.get(required_rp_id)
            
            if not required_stats:
                return {
                    'allowed': False, 
                    'reason': f'Complete {rule.get("description", required_rp_id)} first',
                    'required_roleplay': required_rp_id,
                    'required_name': rule.get('name', f'Roleplay {required_rp_id}')
                }
            
            # FIXED: Check specific pass conditions
            if required_rp_id == '1.2':  # Marathon Mode requirement
                if not required_stats.get('marathon_passed', False):
                    return {
                        'allowed': False,
                        'reason': f'Pass Marathon Mode (6/10 calls) to unlock {roleplay_id}',
                        'required_roleplay': required_rp_id,
                        'required_name': 'Marathon Mode',
                        'current_progress': f"{required_stats.get('marathon_best_run', 0)}/10 calls passed"
                    }
            elif required_rp_id == '2.1':  # Post-Pitch Practice requirement
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
                if not required_stats.get('completed', False) and not required_stats.get('passed', False):
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
            logger.error(f"❌ Error in check_roleplay_access for {roleplay_id}: {e}", exc_info=True)
            return {'allowed': False, 'reason': 'Error checking access'}

    def log_roleplay_attempt(self, user_id: str, roleplay_id: str, session_id: str) -> bool:
        """Log that a user started a roleplay attempt"""
        try:
            if not self.supabase:
                return False
            
            now = datetime.now(timezone.utc).isoformat()
            client = self.supabase.get_service_client()
            
            # Check for existing progress record
            existing = client.table('user_roleplay_progress').select('*').eq(
                'user_id', user_id
            ).eq('roleplay_id', roleplay_id).execute()
            
            if existing.data:
                # Update existing record
                current = existing.data[0]
                updates = {
                    'total_attempts': (current.get('total_attempts', 0) + 1),
                    'last_attempt_at': now,
                    'updated_at': now
                }
                if not current.get('first_attempt_at'):
                    updates['first_attempt_at'] = now
                    
                client.table('user_roleplay_progress').update(updates).eq(
                    'id', current['id']
                ).execute()
            else:
                # Create new progress record
                client.table('user_roleplay_progress').insert({
                    'user_id': user_id,
                    'roleplay_id': roleplay_id,
                    'total_attempts': 1,
                    'first_attempt_at': now,
                    'last_attempt_at': now,
                    'is_unlocked': True,
                    'created_at': now
                }).execute()
            
            logger.info(f"✅ Logged roleplay attempt: {user_id} -> {roleplay_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error logging roleplay attempt: {e}", exc_info=True)
            return False

    def get_completion_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user's overall completion statistics"""
        try:
            if not self.supabase:
                return {}
            
            # Get completions from the correct table
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
                'average_score': round(sum(scores) / len(scores), 1) if scores else 0,
                'best_score': max(scores) if scores else 0,
                'total_time_minutes': total_time,
                'completion_rate': round((successful_sessions / total_sessions * 100), 1) if total_sessions > 0 else 0,
                'roleplays_completed': len(set(c['roleplay_id'] for c in completions if c.get('success', False)))
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting completion stats: {e}")
            return {}


# Global instance
_user_progress_service = None

def get_user_progress_service():
    """Get global user progress service instance"""
    global _user_progress_service
    if _user_progress_service is None:
        _user_progress_service = UserProgressService()
    return _user_progress_service
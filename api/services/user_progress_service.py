# ===== FIXED: services/user_progress_service.py - Supabase Compatible =====

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from services.supabase_client import SupabaseService

logger = logging.getLogger(__name__)

class UserProgressService:
    """Service for tracking user progress across roleplays - Supabase Compatible"""
    
    def __init__(self):
        self.supabase = SupabaseService()
        
        # Roleplay unlock requirements
        self.unlock_requirements = {
            '1.1': [],  # Always available
            '1.2': [],  # Always available
            '1.3': ['1.2'],  # Requires Marathon completion
            '2.1': ['1.3'],  # Requires Legend completion
            '2.2': ['2.1'],  # Requires 2.1 completion
            '2.3': ['2.2'],  # Requires 2.2 completion
        }
        
        # Completion criteria for each roleplay
        self.completion_criteria = {
            '1.1': {'min_score': 70},  # Practice mode
            '1.2': {'min_calls_passed': 6, 'total_calls': 10},  # Marathon mode
            '1.3': {'perfect_calls': 6, 'consecutive': True},  # Legend mode
            '2.1': {'min_score': 75},  # Advanced practice
            '2.2': {'min_calls_passed': 7, 'total_calls': 10},  # Advanced marathon
            '2.3': {'perfect_calls': 8, 'consecutive': True},  # Advanced legend
        }
    
    def get_user_roleplay_progress(self, user_id: str, roleplay_ids: List[str] = None) -> Dict[str, Any]:
        """Get user's progress across all or specific roleplays"""
        try:
            # Get all completions for user
            query = self.supabase.get_service_client().table('roleplay_completions').select('*').eq('user_id', user_id)
            
            if roleplay_ids:
                query = query.in_('roleplay_id', roleplay_ids)
            
            result = query.order('completed_at', desc=True).execute()
            completions = result.data if result.data else []
            
            # Process completions into progress structure
            progress = {}
            for completion in completions:
                roleplay_id = completion['roleplay_id']
                
                if roleplay_id not in progress:
                    progress[roleplay_id] = {
                        'attempts': 0,
                        'best_score': 0,
                        'completed': False,
                        'passed': False,
                        'last_attempt': None,
                        'completion_date': None,
                        'statistics': {
                            'total_attempts': 0,
                            'average_score': 0,
                            'best_performance': None
                        }
                    }
                
                # Update statistics
                progress[roleplay_id]['attempts'] += 1
                progress[roleplay_id]['statistics']['total_attempts'] += 1
                
                # Track best score
                if completion['score'] > progress[roleplay_id]['best_score']:
                    progress[roleplay_id]['best_score'] = completion['score']
                    progress[roleplay_id]['statistics']['best_performance'] = completion
                
                # Check if this completion meets criteria
                if self._meets_completion_criteria(roleplay_id, completion):
                    progress[roleplay_id]['completed'] = True
                    progress[roleplay_id]['passed'] = True
                    if not progress[roleplay_id]['completion_date']:
                        progress[roleplay_id]['completion_date'] = completion['completed_at']
                
                # Track latest attempt
                if not progress[roleplay_id]['last_attempt'] or completion['completed_at'] > progress[roleplay_id]['last_attempt']:
                    progress[roleplay_id]['last_attempt'] = completion['completed_at']
                
                # Marathon-specific data
                if roleplay_id in ['1.2', '2.2'] and completion.get('marathon_results'):
                    marathon = completion['marathon_results']
                    progress[roleplay_id]['calls_passed'] = marathon.get('calls_passed', 0)
                    progress[roleplay_id]['total_calls'] = marathon.get('total_calls', 10)
                    progress[roleplay_id]['marathon_results'] = marathon
            
            # Calculate average scores
            for roleplay_id in progress:
                scores = [c['score'] for c in completions if c['roleplay_id'] == roleplay_id]
                if scores:
                    progress[roleplay_id]['statistics']['average_score'] = sum(scores) / len(scores)
            
            return progress
            
        except Exception as e:
            logger.error(f"Error getting user progress: {e}")
            return {}
    
    def _meets_completion_criteria(self, roleplay_id: str, completion: Dict) -> bool:
        """Check if a completion meets the criteria for the roleplay"""
        criteria = self.completion_criteria.get(roleplay_id, {})
        
        # Score-based completion (Practice modes)
        if 'min_score' in criteria:
            return completion['score'] >= criteria['min_score']
        
        # Marathon-based completion
        if 'min_calls_passed' in criteria:
            marathon_results = completion.get('marathon_results', {})
            calls_passed = marathon_results.get('calls_passed', 0)
            return calls_passed >= criteria['min_calls_passed']
        
        # Legend-based completion (consecutive perfect calls)
        if 'perfect_calls' in criteria:
            marathon_results = completion.get('marathon_results', {})
            if criteria.get('consecutive'):
                # For legend mode, need consecutive perfect calls
                return marathon_results.get('consecutive_perfects', 0) >= criteria['perfect_calls']
            else:
                return marathon_results.get('perfect_calls', 0) >= criteria['perfect_calls']
        
        return False
    
    def check_roleplay_access(self, user_id: str, roleplay_id: str) -> Dict[str, Any]:
        """Check if user has access to a specific roleplay"""
        try:
            # Always allow 1.1 and 1.2
            if roleplay_id in ['1.1', '1.2']:
                return {'allowed': True}
            
            # Check requirements
            requirements = self.unlock_requirements.get(roleplay_id, [])
            if not requirements:
                return {'allowed': True}
            
            # Get user progress
            progress = self.get_user_roleplay_progress(user_id, requirements)
            
            # Check each requirement
            missing_requirements = []
            for req_roleplay in requirements:
                if req_roleplay not in progress or not progress[req_roleplay]['completed']:
                    missing_requirements.append(req_roleplay)
            
            if missing_requirements:
                return {
                    'allowed': False,
                    'reason': f'Must complete {", ".join(missing_requirements)} first',
                    'requirements': missing_requirements
                }
            
            return {'allowed': True}
            
        except Exception as e:
            logger.error(f"Error checking roleplay access: {e}")
            return {'allowed': False, 'reason': 'Error checking access'}
    
    def save_roleplay_completion(self, completion_data: Dict) -> str:
        """Save roleplay completion to database"""
        try:
            # Prepare data for database
            db_data = {
                'user_id': completion_data['user_id'],
                'roleplay_id': completion_data['roleplay_id'],
                'session_id': completion_data['session_id'],
                'mode': completion_data['mode'],
                'score': completion_data['score'],
                'success': completion_data['success'],
                'duration_minutes': completion_data['duration_minutes'],
                'started_at': completion_data['started_at'],
                'completed_at': completion_data.get('ended_at', datetime.now(timezone.utc).isoformat()),
                'conversation_data': completion_data.get('conversation_data', {}),
                'coaching_feedback': completion_data.get('coaching_feedback', {}),
                'ai_evaluation': completion_data.get('ai_evaluation'),
                'marathon_results': completion_data.get('marathon_results'),
                'rubric_scores': completion_data.get('rubric_scores', {}),
                'forced_end': completion_data.get('forced_end', False)
            }
            
            # Insert into database
            result = self.supabase.get_service_client().table('roleplay_completions').insert(db_data).execute()
            
            if result.data:
                completion_id = result.data[0]['id']
                logger.info(f"Roleplay completion saved: {completion_id}")
                return completion_id
            else:
                raise Exception("No data returned from insert")
                
        except Exception as e:
            logger.error(f"Error saving roleplay completion: {e}")
            raise
    
    def log_roleplay_attempt(self, user_id: str, roleplay_id: str, session_id: str):
        """Log when user starts a roleplay attempt"""
        try:
            attempt_data = {
                'user_id': user_id,
                'roleplay_id': roleplay_id,
                'session_id': session_id,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'status': 'started'
            }
            
            self.supabase.get_service_client().table('roleplay_attempts').insert(attempt_data).execute()
            logger.info(f"Roleplay attempt logged: {session_id}")
            
        except Exception as e:
            logger.error(f"Error logging roleplay attempt: {e}")
    
    def update_user_progress(self, user_id: str, roleplay_id: str, completion_data: Dict) -> Dict[str, Any]:
        """Update user's overall progress and check for achievements"""
        try:
            # Get current progress
            progress = self.get_user_roleplay_progress(user_id, [roleplay_id])
            current = progress.get(roleplay_id, {})
            
            # Determine if this is a new best or completion
            is_new_best = completion_data['score'] > current.get('best_score', 0)
            is_completion = self._meets_completion_criteria(roleplay_id, completion_data)
            is_first_completion = is_completion and not current.get('completed', False)
            
            # Update user stats table
            self._update_user_stats(user_id, roleplay_id, completion_data, is_new_best, is_first_completion)
            
            return {
                'is_new_best': is_new_best,
                'is_completion': is_completion,
                'is_first_completion': is_first_completion,
                'score': completion_data['score'],
                'previous_best': current.get('best_score', 0)
            }
            
        except Exception as e:
            logger.error(f"Error updating user progress: {e}")
            return {}
    
    def _update_user_stats(self, user_id: str, roleplay_id: str, completion_data: Dict, is_new_best: bool, is_first_completion: bool):
        """Update user_roleplay_stats table"""
        try:
            # Check if record exists
            existing = self.supabase.get_service_client().table('user_roleplay_stats').select('*').eq('user_id', user_id).eq('roleplay_id', roleplay_id).execute()
            
            now = datetime.now(timezone.utc).isoformat()
            
            if existing.data:
                # Update existing record
                stats = existing.data[0]
                update_data = {
                    'total_attempts': stats['total_attempts'] + 1,
                    'last_attempt_at': now,
                    'last_score': completion_data['score']
                }
                
                if is_new_best:
                    update_data['best_score'] = completion_data['score']
                    update_data['best_score_at'] = now
                
                if is_first_completion:
                    update_data['completed'] = True
                    update_data['completed_at'] = now
                
                self.supabase.get_service_client().table('user_roleplay_stats').update(update_data).eq('user_id', user_id).eq('roleplay_id', roleplay_id).execute()
                
            else:
                # Create new record
                stats_data = {
                    'user_id': user_id,
                    'roleplay_id': roleplay_id,
                    'total_attempts': 1,
                    'best_score': completion_data['score'],
                    'last_score': completion_data['score'],
                    'completed': is_first_completion,
                    'last_attempt_at': now,
                    'best_score_at': now,
                    'completed_at': now if is_first_completion else None
                }
                
                self.supabase.get_service_client().table('user_roleplay_stats').insert(stats_data).execute()
                
        except Exception as e:
            logger.error(f"Error updating user stats: {e}")
    
    def check_new_unlocks(self, user_id: str) -> List[str]:
        """Check for newly unlocked roleplays"""
        try:
            # Get user's current progress
            progress = self.get_user_roleplay_progress(user_id)
            
            # Check each roleplay for unlock status
            newly_unlocked = []
            
            for roleplay_id, requirements in self.unlock_requirements.items():
                if not requirements:  # Always available
                    continue
                
                # Check if all requirements are met
                all_requirements_met = True
                for req_roleplay in requirements:
                    if req_roleplay not in progress or not progress[req_roleplay]['completed']:
                        all_requirements_met = False
                        break
                
                if all_requirements_met:
                    # Check if this is newly unlocked (not previously attempted)
                    if roleplay_id not in progress:
                        newly_unlocked.append(roleplay_id)
            
            return newly_unlocked
            
        except Exception as e:
            logger.error(f"Error checking new unlocks: {e}")
            return []
    
    def get_available_roleplays(self, user_id: str) -> List[str]:
        """Get list of all available roleplays for user"""
        available = []
        
        for roleplay_id in self.unlock_requirements.keys():
            access = self.check_roleplay_access(user_id, roleplay_id)
            if access['allowed']:
                available.append(roleplay_id)
        
        return available
    
    def get_completion_stats(self, user_id: str) -> Dict[str, Any]:
        """Get overall completion statistics for user"""
        try:
            progress = self.get_user_roleplay_progress(user_id)
            
            total_roleplays = len(self.unlock_requirements)
            completed_roleplays = len([rp for rp in progress.values() if rp['completed']])
            total_attempts = sum(rp['attempts'] for rp in progress.values())
            average_score = sum(rp['best_score'] for rp in progress.values()) / len(progress) if progress else 0
            
            return {
                'total_roleplays_available': total_roleplays,
                'completed_roleplays': completed_roleplays,
                'completion_percentage': (completed_roleplays / total_roleplays) * 100,
                'total_attempts': total_attempts,
                'average_best_score': round(average_score, 1),
                'current_level': self._calculate_user_level(progress),
                'next_unlock': self._get_next_unlock(user_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting completion stats: {e}")
            return {}
    
    def _calculate_user_level(self, progress: Dict) -> str:
        """Calculate user's current level based on completions"""
        if not progress:
            return "Beginner"
        
        completed = [rp for rp in progress.values() if rp['completed']]
        
        if len(completed) >= 6:
            return "Master"
        elif len(completed) >= 4:
            return "Advanced"
        elif len(completed) >= 2:
            return "Intermediate"
        else:
            return "Beginner"
    
    def _get_next_unlock(self, user_id: str) -> Optional[str]:
        """Get the next roleplay that could be unlocked"""
        progress = self.get_user_roleplay_progress(user_id)
        
        for roleplay_id, requirements in self.unlock_requirements.items():
            if roleplay_id in progress and progress[roleplay_id]['completed']:
                continue  # Already completed
            
            access = self.check_roleplay_access(user_id, roleplay_id)
            if not access['allowed'] and requirements:
                # This is the next one that needs requirements
                return roleplay_id
        
        return None
    
    def get_next_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get personalized recommendations for user's next steps"""
        try:
            progress = self.get_user_roleplay_progress(user_id)
            recommendations = []
            
            # Check current status and recommend next steps
            if '1.1' not in progress:
                recommendations.append({
                    'type': 'start',
                    'roleplay_id': '1.1',
                    'message': 'Start with Practice Mode to learn the basics',
                    'priority': 'high'
                })
            elif not progress['1.1']['completed']:
                recommendations.append({
                    'type': 'improve',
                    'roleplay_id': '1.1',
                    'message': f"Keep practicing! Your best score is {progress['1.1']['best_score']}/100. Need 70+ to master.",
                    'priority': 'high'
                })
            elif '1.2' not in progress:
                recommendations.append({
                    'type': 'advance',
                    'roleplay_id': '1.2',
                    'message': 'Ready for Marathon Mode! Test your consistency across 10 calls.',
                    'priority': 'medium'
                })
            elif not progress['1.2']['completed']:
                calls_passed = progress['1.2'].get('calls_passed', 0)
                recommendations.append({
                    'type': 'complete',
                    'roleplay_id': '1.2',
                    'message': f"You've passed {calls_passed}/10 calls. Need 6+ to unlock Legend Mode.",
                    'priority': 'medium'
                })
            else:
                # User has completed Marathon, suggest Legend
                if '1.3' not in progress:
                    recommendations.append({
                        'type': 'master',
                        'roleplay_id': '1.3',
                        'message': 'Unlock Legend Mode! 6 perfect calls in a row to master Roleplay 1.',
                        'priority': 'high'
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    def get_leaderboard(self, roleplay_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard for a specific roleplay - Fixed for Supabase"""
        try:
            # Modified to work with your existing user_profiles table
            result = self.supabase.get_service_client().table('user_roleplay_stats').select(
                'user_id, best_score, completed_at'
            ).eq('roleplay_id', roleplay_id).eq('completed', True).order(
                'best_score', desc=True
            ).limit(limit).execute()
            
            leaderboard = []
            for i, record in enumerate(result.data if result.data else []):
                # Get user profile for display name
                try:
                    profile_result = self.supabase.get_service_client().table('user_profiles').select(
                        'first_name'
                    ).eq('id', record['user_id']).execute()
                    
                    if profile_result.data:
                        first_name = profile_result.data[0].get('first_name', 'Anonymous')
                        display_name = first_name[:10] + "..." if len(first_name) > 10 else first_name
                    else:
                        display_name = 'Anonymous'
                except:
                    display_name = 'Anonymous'
                
                leaderboard.append({
                    'rank': i + 1,
                    'user_id': record['user_id'],
                    'name': display_name,
                    'score': record['best_score'],
                    'completed_at': record['completed_at']
                })
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
# ===== UPDATED: services/roleplay_engine.py =====

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import uuid

from .supabase_client import SupabaseService
from .user_progress_service import UserProgressService

logger = logging.getLogger(__name__)

class RoleplayEngine:
    """Enhanced Roleplay Engine with Roleplay 2.1 support"""
    
    def __init__(self, openai_service=None, supabase_service=None):
        self.active_sessions = {}
        if not openai_service:
            from .openai_service import OpenAIService
            self.openai_service = OpenAIService()
        else:
            self.openai_service = openai_service

        if not supabase_service:
            self.supabase_service = SupabaseService()
        else:
            self.supabase_service = supabase_service

        self.progress_service = UserProgressService(self.supabase_service)

        self.roleplay_implementations = {}
        self._load_roleplay_implementations()
        logger.info(f"✅ RoleplayEngine initialized with {len(self.roleplay_implementations)} roleplay types")
    
    def _load_roleplay_implementations(self):
        """Load all available roleplay implementations"""
        try:
            # Import existing roleplays
            from .roleplay.roleplay_1_1 import Roleplay11
            from .roleplay.roleplay_1_2 import Roleplay12
            
            # Import new Roleplay 2.1
            from .roleplay.roleplay_2_1 import Roleplay21
            
            self.roleplay_implementations = {
                '1.1': Roleplay11(self.openai_service),
                '1.2': Roleplay12(self.openai_service),
                '2.1': Roleplay21(self.openai_service),  # NEW: Advanced Post-Pitch Practice
            }
            
            # Try to load other roleplays if they exist
            try:
                from .roleplay.roleplay_1_3 import Roleplay13
                self.roleplay_implementations['1.3'] = Roleplay13(self.openai_service)
                logger.info("✅ Loaded Roleplay 1.3 (Legend Mode)")
            except ImportError:
                logger.info("⏳ Roleplay 1.3 not yet implemented")
            
            try:
                from .roleplay.roleplay_2_2 import Roleplay22
                self.roleplay_implementations['2.2'] = Roleplay22(self.openai_service)
                logger.info("✅ Loaded Roleplay 2.2 (Advanced Marathon)")
            except ImportError:
                logger.info("⏳ Roleplay 2.2 not yet implemented")
            
            # Try to load direct roleplays (3, 4, 5)
            for roleplay_id in ['3', '4', '5']:
                try:
                    module_name = f'.roleplay.roleplay_{roleplay_id}'
                    class_name = f'Roleplay{roleplay_id}'
                    module = __import__(f'services.roleplay.roleplay_{roleplay_id}', fromlist=[class_name])
                    roleplay_class = getattr(module, class_name)
                    self.roleplay_implementations[roleplay_id] = roleplay_class(self.openai_service)
                    logger.info(f"✅ Loaded Roleplay {roleplay_id}")
                except ImportError:
                    logger.info(f"⏳ Roleplay {roleplay_id} not yet implemented")
            
            logger.info(f"🎮 Loaded roleplay implementations: {list(self.roleplay_implementations.keys())}")
            
        except Exception as e:
            logger.error(f"❌ Error loading roleplay implementations: {e}")
            # Create fallback implementations
            self._create_fallback_implementations()

    def _create_fallback_implementations(self):
        """Create fallback implementations for missing roleplays"""
        from .base_roleplay import BaseRoleplay
        
        essential_roleplays = ['1.1', '1.2', '2.1']
        for roleplay_id in essential_roleplays:
            if roleplay_id not in self.roleplay_implementations:
                logger.warning(f"⚠️ Creating fallback for {roleplay_id}")
                fallback = BaseRoleplay(self.openai_service)
                fallback.roleplay_id = roleplay_id
                self.roleplay_implementations[roleplay_id] = fallback

    def get_available_roleplays(self) -> List[str]:
        """Get list of available roleplay IDs"""
        return list(self.roleplay_implementations.keys())
    
    def get_roleplay_info(self, roleplay_id: str) -> Dict[str, Any]:
        """Get information about a specific roleplay"""
        try:
            if roleplay_id not in self.roleplay_implementations:
                return {'error': f'Roleplay {roleplay_id} not found'}
            
            implementation = self.roleplay_implementations[roleplay_id]
            return implementation.get_roleplay_info()
            
        except Exception as e:
            logger.error(f"❌ Error getting roleplay info for {roleplay_id}: {e}")
            return self._get_fallback_info(roleplay_id)

    def _get_fallback_info(self, roleplay_id: str) -> Dict[str, Any]:
        """Get fallback info for roleplays"""
        fallback_info = {
            '1.1': {
                'id': '1.1',
                'name': 'Practice Mode',
                'description': 'Single call with detailed coaching',
                'type': 'practice'
            },
            '1.2': {
                'id': '1.2', 
                'name': 'Marathon Mode',
                'description': '10 calls, need 6 to pass',
                'type': 'marathon'
            },
            '1.3': {
                'id': '1.3',
                'name': 'Legend Mode', 
                'description': '6 perfect calls in a row',
                'type': 'legend'
            },
            '2.1': {
                'id': '2.1',
                'name': 'Post-Pitch Practice',
                'description': 'Advanced pitch, objections, qualification, and meeting ask',
                'type': 'advanced_practice'
            },
            '2.2': {
                'id': '2.2',
                'name': 'Advanced Marathon',
                'description': '10 advanced calls with complex scenarios', 
                'type': 'advanced_marathon'
            },
            '3': {
                'id': '3',
                'name': 'Warm-up Challenge',
                'description': '25 rapid-fire questions',
                'type': 'challenge'
            },
            '4': {
                'id': '4',
                'name': 'Full Cold Call Simulation',
                'description': 'Complete end-to-end call practice',
                'type': 'simulation'
            },
            '5': {
                'id': '5',
                'name': 'Power Hour Challenge', 
                'description': '10 consecutive calls for endurance',
                'type': 'endurance'
            }
        }
        
        return fallback_info.get(roleplay_id, {
            'id': roleplay_id,
            'name': f'Roleplay {roleplay_id}',
            'description': 'Roleplay training',
            'type': 'unknown'
        })
    
    def create_session(self, user_id: str, roleplay_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create a roleplay session with enhanced validation"""
        try:
            if not user_id or not roleplay_id:
                return {'success': False, 'error': 'Missing required parameters'}
            
            # Enhanced access check for advanced roleplays
            if roleplay_id in ['2.1', '2.2', '4', '5']:
                access_check = self.progress_service.check_roleplay_access(user_id, roleplay_id)
                if not access_check['allowed']:
                    return {
                        'success': False, 
                        'error': 'Access denied',
                        'reason': access_check['reason'],
                        'required_roleplay': access_check.get('required_roleplay'),
                        'access_denied': True
                    }
            
            if roleplay_id not in self.roleplay_implementations:
                return {'success': False, 'error': f'Roleplay {roleplay_id} not available'}
            
            logger.info(f"🚀 Creating session: {roleplay_id} for user {user_id} (mode: {mode})")
            
            self._cleanup_user_sessions(user_id)
            
            implementation = self.roleplay_implementations[roleplay_id]
            session_result = implementation.create_session(user_id, mode, user_context)
            
            if not session_result.get('success'):
                logger.error(f"❌ Implementation failed to create session: {session_result}")
                return session_result
            
            session_id = session_result['session_id']
            session_data = implementation.active_sessions.get(session_id)
            
            if session_data:
                # Store the session in the engine's active memory
                self.active_sessions[session_id] = {
                    'implementation_id': roleplay_id,
                    'session_data': session_data,
                    'user_id': user_id,
                }
                logger.info(f"✅ Session {session_id} created and stored in active memory.")
            
            # Log the attempt for progress tracking
            self.progress_service.log_roleplay_attempt(user_id, roleplay_id, session_id)
            
            return session_result
            
        except Exception as e:
            logger.error(f"❌ Error creating roleplay session: {e}", exc_info=True)
            return {'success': False, 'error': f'Failed to create session: {str(e)}'}

    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input by delegating to the correct implementation"""
        try:
            if not session_id or not user_input:
                return {'success': False, 'error': 'Missing required parameters'}
            
            logger.info(f"💬 Processing input for session {session_id}: '{user_input[:50]}...'")
            
            session_info = self._get_session_with_recovery(session_id)
            if not session_info:
                logger.error(f"❌ Session {session_id} not found")
                return {'success': False, 'error': 'Session not found or expired'}
            
            implementation_id = session_info['implementation_id']
            implementation = self.roleplay_implementations[implementation_id]
            
            session_data = session_info['session_data']
            if not session_data.get('session_active', True):
                logger.error(f"❌ Session {session_id} is no longer active")
                return {'success': False, 'error': 'Session has ended'}
            
            result = implementation.process_user_input(session_id, user_input)
            
            if result.get('success'):
                updated_session_data = implementation.active_sessions.get(session_id)
                if updated_session_data and session_id in self.active_sessions:
                    self.active_sessions[session_id]['session_data'] = updated_session_data
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing user input: {e}", exc_info=True)
            return {'success': False, 'error': f"Processing failed: {str(e)}"}
    
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End session with enhanced results processing"""
        try:
            logger.info(f"📞 Ending session {session_id} (forced: {forced_end})")
            
            session_info = self.active_sessions.get(session_id)
            if not session_info:
                logger.warning(f"⚠️ Session {session_id} not found in active memory for ending.")
                for impl in self.roleplay_implementations.values():
                    if session_id in impl.active_sessions:
                        session_info = {'session_data': impl.active_sessions.get(session_id)}
                        break
            
            if not session_info:
                 return {'success': True, 'message': 'Session not found or already ended.'}

            implementation_id = session_info.get('implementation_id', '1.1')
            implementation = self.roleplay_implementations.get(implementation_id)
            
            if not implementation:
                raise ValueError(f"Implementation for {implementation_id} not found")

            # Get the final result from the specific roleplay logic
            result = implementation.end_session(session_id, forced_end)
            
            if result.get('success'):
                session_data = result.get('session_data', {})
                user_id = session_data.get('user_id')
                
                if user_id:
                    completion_data = {
                        'user_id': user_id,
                        'session_id': session_id,
                        'roleplay_id': session_data.get('roleplay_id'),
                        'mode': session_data.get('mode', 'practice'),
                        'score': result.get('overall_score'),
                        'success': result.get('session_success'),
                        'duration_minutes': result.get('duration_minutes'),
                        'started_at': session_data.get('started_at'),
                        'completed_at': session_data.get('ended_at'),
                        'conversation_data': session_data.get('conversation_history'),
                        'coaching_feedback': result.get('coaching'),
                        'rubric_scores': session_data.get('rubric_scores'),
                        'forced_end': forced_end
                    }
                    
                    # Add type-specific results
                    if result.get('marathon_results'):
                        completion_data['marathon_results'] = result.get('marathon_results')
                    
                    if result.get('advanced_results'):
                        completion_data['advanced_results'] = result.get('advanced_results')
                    
                    # Save completion and update progress
                    self.progress_service.save_roleplay_completion(completion_data)
                    self.progress_service.update_user_progress_after_completion(completion_data)

                    logger.info(f"✅ Session {session_id} results have been saved to the database.")
                else:
                    logger.warning("No user_id found in session data, cannot save progress.")

            # Cleanup in-memory session
            self.active_sessions.pop(session_id, None)
            
            logger.info(f"✅ Session {session_id} ended and cleaned from memory.")
            return result
                        
        except Exception as e:
            logger.error(f"❌ Error ending session: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a session"""
        try:
            session_info = self._get_session_with_recovery(session_id)
            
            if not session_info:
                return None
            
            session_data = session_info['session_data']
            
            return {
                'session_active': session_data.get('session_active', False),
                'current_stage': session_data.get('current_stage', 'unknown'),
                'rubric_scores': session_data.get('rubric_scores', {}),
                'conversation_length': len(session_data.get('conversation_history', [])),
                'openai_available': self.is_openai_available(),
                'user_id': session_data.get('user_id'),
                'roleplay_id': session_data.get('roleplay_id'),
                'mode': session_data.get('mode'),
                'last_activity': session_info.get('last_activity')
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting session status: {e}")
            return None
    
    def is_openai_available(self) -> bool:
        """Check if OpenAI service is available"""
        try:
            return (
                self.openai_service is not None and 
                hasattr(self.openai_service, 'is_available') and 
                self.openai_service.is_available()
            )
        except Exception:
            return False
    
    def _get_session_with_recovery(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.active_sessions.get(session_id)
    
    def _cleanup_user_sessions(self, user_id: str):
        sessions_to_remove = [sid for sid, s_info in self.active_sessions.items() if s_info.get('user_id') == user_id]
        for session_id in sessions_to_remove:
            logger.info(f"🧹 Cleaning up stale active session {session_id} for user {user_id}")
            self.active_sessions.pop(session_id, None)
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old/abandoned sessions"""
        try:
            cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
            sessions_to_remove = []
            
            for session_id, session_info in self.active_sessions.items():
                last_activity_str = session_info.get('last_activity')
                if last_activity_str:
                    try:
                        last_activity = datetime.fromisoformat(last_activity_str.replace('Z', '+00:00'))
                        if last_activity.timestamp() < cutoff_time:
                            sessions_to_remove.append(session_id)
                    except Exception as parse_error:
                        logger.warning(f"⚠️ Error parsing last_activity for session {session_id}: {parse_error}")
                        sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                try:
                    self.end_session(session_id, forced_end=True)
                    logger.info(f"✅ Cleaned up old session: {session_id}")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ Error cleaning up old session {session_id}: {cleanup_error}")
            
            if sessions_to_remove:
                logger.info(f"✅ Cleaned up {len(sessions_to_remove)} old sessions")
            
            return len(sessions_to_remove)
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up old sessions: {e}")
            return 0

    def get_user_available_roleplays(self, user_id: str) -> Dict[str, Any]:
        """Get available roleplays for a specific user with access info"""
        try:
            available_roleplays = {}
            
            for roleplay_id in self.get_available_roleplays():
                try:
                    # Get roleplay info
                    roleplay_info = self.get_roleplay_info(roleplay_id)
                    
                    # Check access
                    access_check = self.progress_service.check_roleplay_access(user_id, roleplay_id)
                    
                    available_roleplays[roleplay_id] = {
                        **roleplay_info,
                        'access_allowed': access_check['allowed'],
                        'access_reason': access_check['reason'],
                        'required_roleplay': access_check.get('required_roleplay'),
                        'unlock_benefit': access_check.get('unlock_benefit')
                    }
                    
                except Exception as roleplay_error:
                    logger.warning(f"Error checking roleplay {roleplay_id}: {roleplay_error}")
            
            return available_roleplays
            
        except Exception as e:
            logger.error(f"Error getting user available roleplays: {e}")
            return {}

# Global instance for singleton pattern
_roleplay_engine = None

def get_roleplay_engine():
    """Get global roleplay engine instance"""
    global _roleplay_engine
    if _roleplay_engine is None:
        _roleplay_engine = RoleplayEngine()
    return _roleplay_engine
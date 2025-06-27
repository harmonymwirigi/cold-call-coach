# ===== FIXED: services/roleplay_engine.py =====
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import uuid

# Re-import just in case
from .supabase_client import SupabaseService
from .user_progress_service import UserProgressService

logger = logging.getLogger(__name__)

class RoleplayEngine:
    """FIXED Roleplay Engine with robust session management and recovery"""
    
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
        from .roleplay.roleplay_1_1 import Roleplay11
        from .roleplay.roleplay_1_2 import Roleplay12
        from .roleplay.roleplay_1_3 import Roleplay13
        self.roleplay_implementations = {
            '1.1': Roleplay11(self.openai_service),
            '1.2': Roleplay12(self.openai_service),
            '1.3': Roleplay13(self.openai_service),
        }

    def _create_fallback_roleplay(self, roleplay_id: str):
        """Create a minimal fallback roleplay implementation"""
        class FallbackRoleplay:
            def __init__(self, roleplay_id):
                self.roleplay_id = roleplay_id
                self.active_sessions = {}
                logger.warning(f"⚠️ Using fallback implementation for {roleplay_id}")
            
            def get_roleplay_info(self):
                return {
                    'id': roleplay_id,
                    'name': f'Roleplay {roleplay_id}',
                    'description': 'Basic roleplay training (fallback mode)',
                    'type': 'practice',
                    'features': {'ai_evaluation': False, 'basic_coaching': True}
                }
            
            def create_session(self, user_id, mode, user_context):
                session_id = f"{user_id}_{roleplay_id}_{int(datetime.now().timestamp())}"
                session_data = {
                    'session_id': session_id,
                    'user_id': user_id,
                    'roleplay_id': roleplay_id,
                    'mode': mode,
                    'started_at': datetime.now(timezone.utc).isoformat(),
                    'conversation_history': [],
                    'current_stage': 'phone_pickup',
                    'session_active': True,
                    'turn_count': 0,
                    'user_context': user_context
                }
                self.active_sessions[session_id] = session_data
                return { 'success': True, 'session_id': session_id, 'initial_response': 'Hello?'}
            
            def process_user_input(self, session_id, user_input):
                if session_id not in self.active_sessions:
                    return {'success': False, 'error': 'Session not found'}
                
                session = self.active_sessions[session_id]
                session['turn_count'] += 1
                
                # Very basic logic - continue for a few turns then end
                if session['turn_count'] < 5:
                    return {
                        'success': True,
                        'ai_response': 'I see. Please continue.',
                        'call_continues': True,
                        'evaluation': {'score': 2, 'passed': True}
                    }
                else:
                    return {
                        'success': True,
                        'ai_response': 'Thank you for calling.',
                        'call_continues': False,
                        'evaluation': {'score': 2, 'passed': True}
                    }
            
            def end_session(self, session_id, forced_end=False):
                session_data = self.active_sessions.pop(session_id, {})
                return {
                    'success': True,
                    'duration_minutes': 2,
                    'session_success': True,
                    'coaching': {'overall': 'Good practice session! (Fallback mode)'},
                    'overall_score': 75,
                    'session_data': session_data
                }
        
        return FallbackRoleplay(roleplay_id)
    
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
            return {'error': str(e)}
    
    def create_session(self, user_id: str, roleplay_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create a roleplay session and store it in active memory."""
        try:
            if not user_id or not roleplay_id:
                return {'success': False, 'error': 'Missing required parameters'}
            
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
                # We no longer persist to the active_sessions table here.
                # It's better managed in memory or a cache like Redis if needed.
            
            return session_result
            
        except Exception as e:
            logger.error(f"❌ Error creating roleplay session: {e}", exc_info=True)
            return {'success': False, 'error': f'Failed to create session: {str(e)}'}

    
    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input by delegating to the correct implementation."""
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
            
            # THE FIX: This function was removed, so we must remove the call to it.
            # self._update_session_activity(session_id) 
            
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
            logger.error(f"❌ Error processing user input: {e}", exc_info=True) # Added exc_info for better logging
            return {'success': False, 'error': f"Processing failed: {str(e)}"}
    
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End session, calculate results, and save the permanent record to the database."""
        try:
            logger.info(f"📞 Ending session {session_id} (forced: {forced_end})")
            
            session_info = self.active_sessions.get(session_id)
            if not session_info:
                logger.warning(f"⚠️ Session {session_id} not found in active memory for ending.")
                # Attempt to recover from implementation state if it exists
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
                    
                    # 1. Save the final record to the correct 'roleplay_completions' table.
                    self.progress_service.save_roleplay_completion(completion_data)
                    
                    # 2. Update the user's aggregate stats and usage.
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
    
        
    def _cleanup_session_from_database(self, session_id: str):
        # ...
        pass
    
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
                        sessions_to_remove.append(session_id)  # Remove sessions with bad timestamps
            
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

# Global instance for singleton pattern
_roleplay_engine = None

def get_roleplay_engine():
    """Get global roleplay engine instance"""
    global _roleplay_engine
    if _roleplay_engine is None:
        _roleplay_engine = RoleplayEngine()
    return _roleplay_engine
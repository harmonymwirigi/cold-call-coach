# ===== FIXED: services/roleplay/base_roleplay.py =====

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)

class BaseRoleplay:
    """Enhanced base class for all roleplay implementations"""
    
    def __init__(self, openai_service=None):
        self.openai_service = openai_service
        self.active_sessions = {}
        self.roleplay_id = "base"
        
        logger.info(f"BaseRoleplay initialized with OpenAI: {self.is_openai_available()}")
    
    def is_openai_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.openai_service and hasattr(self.openai_service, 'is_available') and self.openai_service.is_available()
    
    def get_roleplay_info(self) -> Dict[str, Any]:
        """Base roleplay info - should be overridden by subclasses"""
        return {
            'id': self.roleplay_id,
            'name': f'Roleplay {self.roleplay_id}',
            'description': 'Cold calling training',
            'type': 'base',
            'features': {
                'ai_evaluation': self.is_openai_available(),
                'basic_coaching': True
            }
        }
    
    def create_session(self, user_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create a basic roleplay session"""
        try:
            session_id = f"{user_id}_{self.roleplay_id}_{mode}_{int(datetime.now().timestamp())}"
            
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'roleplay_id': self.roleplay_id,
                'mode': mode,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'user_context': user_context,
                'conversation_history': [],
                'current_stage': 'initial',
                'session_active': True,
                'turn_count': 0,
                'overall_quality': 0
            }
            
            # Store session
            self.active_sessions[session_id] = session_data
            
            # Generate initial response
            initial_response = self._get_basic_initial_response(user_context)
            
            # Add to conversation
            session_data['conversation_history'].append({
                'role': 'assistant',
                'content': initial_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': 'initial'
            })
            
            logger.info(f"Created base session {session_id}")
            
            return {
                'success': True,
                'session_id': session_id,
                'initial_response': initial_response,
                'roleplay_info': self.get_roleplay_info()
            }
            
        except Exception as e:
            logger.error(f"Error creating base session: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input - basic implementation"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            
            if not session.get('session_active'):
                raise ValueError("Session not active")
            
            # Increment turn count
            session['turn_count'] += 1
            
            # Add user input to conversation
            session['conversation_history'].append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session.get('current_stage', 'conversation')
            })
            
            # Generate AI response
            ai_response = self._generate_basic_response(session, user_input)
            
            # Add AI response to conversation
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session.get('current_stage', 'conversation')
            })
            
            # Determine if call should continue
            call_continues = session['turn_count'] < 10  # Simple limit
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': call_continues,
                'session_state': session.get('current_stage', 'conversation'),
                'turn_count': session['turn_count']
            }
            
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return {'success': False, 'error': str(e), 'call_continues': False}
    
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End session - basic implementation"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            session['session_active'] = False
            session['ended_at'] = datetime.now(timezone.utc).isoformat()
            
            # Calculate duration
            started_at = datetime.fromisoformat(session['started_at'].replace('Z', '+00:00'))
            ended_at = datetime.now(timezone.utc)
            duration_minutes = max(1, int((ended_at - started_at).total_seconds() / 60))
            
            # Basic scoring
            basic_score = min(100, max(30, session['turn_count'] * 10))
            
            # Basic coaching
            basic_coaching = {
                'opening': 'Good effort on your call opening.',
                'communication': 'Your communication was clear.',
                'overall': 'Keep practicing to improve your skills!'
            }
            
            result = {
                'success': True,
                'duration_minutes': duration_minutes,
                'session_success': session['turn_count'] >= 3,
                'coaching': basic_coaching,
                'overall_score': basic_score,
                'session_data': session,
                'roleplay_type': 'basic'
            }
            
            # Clean up session
            del self.active_sessions[session_id]
            
            return result
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session status"""
        session = self.active_sessions.get(session_id)
        if session:
            return {
                'session_active': session.get('session_active', False),
                'current_stage': session.get('current_stage', 'unknown'),
                'conversation_length': len(session.get('conversation_history', [])),
                'turn_count': session.get('turn_count', 0),
                'roleplay_type': 'base',
                'openai_available': self.is_openai_available()
            }
        return None
    
    def cleanup_expired_sessions(self):
        """Clean up old sessions"""
        try:
            current_time = datetime.now(timezone.utc)
            expired_sessions = []
            
            for session_id, session_data in self.active_sessions.items():
                try:
                    started_at = datetime.fromisoformat(session_data['started_at'].replace('Z', '+00:00'))
                    if (current_time - started_at).total_seconds() > 3600:  # 1 hour
                        expired_sessions.append(session_id)
                except:
                    expired_sessions.append(session_id)  # Clean up malformed sessions
            
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
                logger.info(f"Cleaned up expired session: {session_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
    
    # ===== HELPER METHODS =====
    
    def _get_basic_initial_response(self, user_context: Dict) -> str:
        """Generate basic initial response"""
        responses = [
            "Hello?",
            "Good morning.",
            f"{user_context.get('first_name', 'Alex')} speaking.",
            "Yes, this is Alex.",
            "Hi there."
        ]
        
        import random
        return random.choice(responses)
    
    def _generate_basic_response(self, session: Dict, user_input: str) -> str:
        """Generate basic AI response"""
        try:
            # Try using OpenAI if available
            if self.is_openai_available():
                response_result = self.openai_service.generate_roleplay_response(
                    user_input,
                    session['conversation_history'],
                    session['user_context'],
                    session.get('current_stage', 'conversation')
                )
                
                if response_result.get('success'):
                    return response_result['response']
            
            # Fallback to basic responses
            return self._get_fallback_response(user_input, session['turn_count'])
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._get_fallback_response(user_input, session['turn_count'])
    
    def _get_fallback_response(self, user_input: str, turn_count: int) -> str:
        """Get fallback response when AI is unavailable"""
        import random
        
        user_input_lower = user_input.lower()
        
        # Early turn responses
        if turn_count <= 2:
            if any(word in user_input_lower for word in ['calling from', 'my name', 'hi']):
                return random.choice([
                    "What's this about?",
                    "I'm listening.",
                    "Go ahead."
                ])
            else:
                return random.choice([
                    "I'm not interested.",
                    "What do you want?"
                ])
        
        # Mid-conversation responses
        elif turn_count <= 5:
            if any(word in user_input_lower for word in ['help', 'save', 'improve']):
                return random.choice([
                    "That sounds interesting. Tell me more.",
                    "How does that work?",
                    "What kind of results do you see?"
                ])
            else:
                return random.choice([
                    "I'm not sure I understand.",
                    "Can you be more specific?",
                    "That's pretty vague."
                ])
        
        # Later conversation responses
        else:
            return random.choice([
                "I'll have to think about it.",
                "Send me some information.",
                "I need to discuss this with my team.",
                "This isn't a priority right now.",
                "Thanks for calling."
            ])
    
    def _calculate_basic_quality(self, session: Dict) -> float:
        """Calculate basic conversation quality"""
        try:
            turn_count = session.get('turn_count', 0)
            conversation_length = len(session.get('conversation_history', []))
            
            # Basic quality based on engagement
            if turn_count >= 6 and conversation_length >= 10:
                return 75.0
            elif turn_count >= 4:
                return 60.0
            elif turn_count >= 2:
                return 45.0
            else:
                return 30.0
                
        except:
            return 50.0
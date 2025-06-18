# ===== API/SERVICES/ELEVENLABS_SERVICE.PY (SIMPLE VERSION) =====
import os
import logging
from typing import Dict, Any, Optional
from io import BytesIO

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        self.api_key = os.getenv('REACT_APP_ELEVENLABS_API_KEY')
        self.voice_id = os.getenv('REACT_APP_ELEVENLABS_VOICE_ID')
        
        if not self.api_key:
            logger.warning("ElevenLabs API key not provided")
    
    def text_to_speech(self, text: str, voice_settings: Dict = None) -> Optional[BytesIO]:
        """Convert text to speech (placeholder implementation)"""
        try:
            logger.info(f"TTS request for text: {text[:50]}...")
            
            # For now, return None - this will be handled gracefully by the caller
            # In a real implementation, this would call the ElevenLabs API
            logger.warning("TTS not implemented - returning None")
            return None
            
        except Exception as e:
            logger.error(f"Error in text_to_speech: {e}")
            return None
    
    def get_voice_settings_for_prospect(self, prospect_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get voice settings based on prospect information"""
        job_title = prospect_info.get('prospect_job_title', '')
        
        # Default voice settings
        settings = {
            "stability": 0.75,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
        
        # Adjust based on job title
        if 'CEO' in job_title or 'President' in job_title:
            settings["stability"] = 0.85
            settings["style"] = 0.2
        elif 'Manager' in job_title:
            settings["similarity_boost"] = 0.8
        
        return settings

# ===== API/SERVICES/ROLEPLAY_ENGINE.PY (SIMPLE VERSION) =====
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

class RoleplayEngine:
    def __init__(self):
        self.active_sessions = {}
        logger.info("RoleplayEngine initialized")
    
    def create_session(self, user_id: str, roleplay_id: int, mode: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new roleplay session"""
        try:
            session_id = str(uuid.uuid4())
            
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'roleplay_id': roleplay_id,
                'mode': mode,
                'user_context': user_context,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'conversation_history': [],
                'current_stage': 'opening'
            }
            
            self.active_sessions[session_id] = session_data
            
            # Generate initial AI response based on roleplay
            initial_responses = {
                1: "Hello, this is Alex from TechCorp. Do you have a moment to chat?",
                2: "Hi there, I'm calling about your sales process. Is now a good time?",
                3: "Quick question - are you the person who handles business development?",
                4: "Good morning! I'm reaching out about improving your team's productivity.",
                5: "Hi, I have something that could help your business. Do you have 2 minutes?"
            }
            
            initial_response = initial_responses.get(roleplay_id, "Hello, thanks for taking my call. How are you today?")
            
            return {
                'success': True,
                'session_id': session_id,
                'initial_response': initial_response
            }
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return {
                'success': False,
                'error': 'Failed to create session'
            }
    
    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input and generate AI response"""
        try:
            if session_id not in self.active_sessions:
                return {
                    'success': False,
                    'error': 'Session not found'
                }
            
            session = self.active_sessions[session_id]
            
            # Add user input to conversation history
            session['conversation_history'].append({
                'speaker': 'user',
                'message': user_input,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            # Generate simple AI response (in real implementation, this would use OpenAI)
            ai_responses = [
                "That's interesting. Can you tell me more about your current process?",
                "I understand. Many of our clients had similar concerns initially.",
                "That makes sense. Let me ask you this...",
                "Absolutely. Here's how we've helped companies like yours...",
                "Great point. What if I told you we could solve that specific challenge?"
            ]
            
            import random
            ai_response = random.choice(ai_responses)
            
            # Add AI response to conversation history
            session['conversation_history'].append({
                'speaker': 'ai',
                'message': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            # Determine if call should continue (simple logic)
            call_continues = len(session['conversation_history']) < 8  # End after 4 exchanges
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': call_continues,
                'session_state': 'in_progress' if call_continues else 'ending'
            }
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            return {
                'success': False,
                'error': 'Failed to process input'
            }
    
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End a roleplay session and provide coaching"""
        try:
            if session_id not in self.active_sessions:
                return {
                    'success': False,
                    'error': 'Session not found'
                }
            
            session = self.active_sessions[session_id]
            session['ended_at'] = datetime.now(timezone.utc).isoformat()
            
            # Calculate duration
            started_at = datetime.fromisoformat(session['started_at'].replace('Z', '+00:00'))
            ended_at = datetime.now(timezone.utc)
            duration_minutes = int((ended_at - started_at).total_seconds() / 60)
            
            # Generate simple coaching feedback
            coaching = {
                'coaching': {
                    'sales': 'Good job building rapport at the beginning of the call.',
                    'grammar': 'Your grammar was clear and professional throughout.',
                    'vocabulary': 'Consider using more industry-specific terms.',
                    'pronunciation': 'Speak slightly slower for better clarity.',
                    'rapport': 'Great job showing genuine interest in their business.'
                },
                'overall_score': 75,
                'next_steps': 'Practice handling objections more confidently and work on your closing technique.'
            }
            
            # Clean up session
            del self.active_sessions[session_id]
            
            return {
                'success': True,
                'session_data': session,
                'duration_minutes': duration_minutes,
                'session_success': True,
                'overall_score': coaching['overall_score'],
                'coaching': coaching,
                'completion_message': 'Great job! Keep practicing to improve even more.'
            }
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return {
                'success': False,
                'error': 'Failed to end session'
            }
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session status"""
        return self.active_sessions.get(session_id)
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            current_time = datetime.now(timezone.utc)
            expired_sessions = []
            
            for session_id, session in self.active_sessions.items():
                started_at = datetime.fromisoformat(session['started_at'].replace('Z', '+00:00'))
                if (current_time - started_at).total_seconds() > 3600:  # 1 hour timeout
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
                
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
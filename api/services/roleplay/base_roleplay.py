# ===== Quick Fix for services/roleplay/base_roleplay.py =====

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class BaseRoleplay:
    """Fixed base class for all roleplay implementations"""
    
    def __init__(self, openai_service=None):
        self.openai_service = openai_service
        self.active_sessions = {}
        self.roleplay_id = "1.1"
        
        logger.info(f"BaseRoleplay initialized with OpenAI: {bool(openai_service)}")
    
    def create_session(self, user_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create a new roleplay session - FIXED VERSION"""
        try:
            session_id = f"{user_id}_{self.roleplay_id}_{mode}_{int(datetime.now().timestamp())}"
            
            # Generate initial AI response immediately
            initial_response = self.generate_initial_response(user_context)
            
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'roleplay_id': self.roleplay_id,
                'mode': mode,
                'user_context': user_context,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'conversation_history': [
                    {
                        'speaker': 'ai',
                        'text': initial_response,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                ],
                'current_stage': 'greeting',
                'turn_count': 0,
                'session_active': True
            }
            
            self.active_sessions[session_id] = session_data
            
            logger.info(f"✅ Session created successfully: {session_id}")
            
            return {
                'success': True,
                'session_id': session_id,
                'initial_response': initial_response,
                'roleplay_info': self.get_roleplay_info(),
                'session_data': session_data
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating session: {e}")
            return {
                'success': False, 
                'error': str(e),
                'session_id': None,
                'initial_response': 'Hello? This is Alex from TechCorp.'
            }
    
    def generate_initial_response(self, user_context: Dict) -> str:
        """Generate initial AI response - FIXED VERSION"""
        try:
            if self.openai_service and self.openai_service.is_available():
                # Try to get OpenAI response
                user_name = user_context.get('first_name', 'there')
                prospect_title = user_context.get('prospect_job_title', 'CTO')
                prospect_industry = user_context.get('prospect_industry', 'Technology')
                
                prompt = f"""You are a {prospect_title} at a {prospect_industry} company. You just answered your phone during work hours. A cold caller is about to speak. Respond naturally as a busy professional would - be realistic, maybe slightly resistant but professional. Keep it short (1-2 sentences max).

Examples:
- "Hello, this is Alex."
- "Hi, Alex speaking."
- "Yeah, this is Sarah, what's this about?"
- "Hello? I've only got a minute."

Respond now as the prospect:"""

                try:
                    response = self.openai_service.chat_completion(
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=50,
                        temperature=0.8
                    )
                    
                    if response and response.strip():
                        logger.info(f"✅ Generated AI initial response: {response[:50]}...")
                        return response.strip()
                    else:
                        logger.warning("⚠️ Empty AI response, using fallback")
                        
                except Exception as ai_error:
                    logger.warning(f"⚠️ OpenAI generation failed: {ai_error}")
            
            # Fallback responses
            fallback_responses = [
                "Hello, this is Alex speaking.",
                "Hi, Alex here. What's this about?",
                "Yeah, this is Sarah. I've got a minute.",
                "Hello? This is Mike.",
                "Hi there, Emma speaking."
            ]
            
            import random
            response = random.choice(fallback_responses)
            logger.info(f"📞 Using fallback initial response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error generating initial response: {e}")
            return "Hello, this is Alex speaking."
    
    def get_roleplay_info(self) -> Dict[str, Any]:
        """Get roleplay information"""
        return {
            'id': self.roleplay_id,
            'name': 'Practice Mode',
            'description': 'Single call with detailed coaching',
            'type': 'practice'
        }
    
    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input - FIXED VERSION"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return {
                    'success': False, 
                    'error': 'Session not found', 
                    'call_continues': False,
                    'ai_response': 'Sorry, the call was disconnected.'
                }
            
            session['turn_count'] += 1
            session['conversation_history'].append({
                'speaker': 'user',
                'text': user_input,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            # Generate AI response
            ai_response = self.generate_ai_response(session, user_input)
            
            session['conversation_history'].append({
                'speaker': 'ai',
                'text': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            # Determine if call should continue (simple logic for now)
            call_continues = session['turn_count'] < 8  # End after 8 exchanges
            
            if not call_continues:
                session['session_active'] = False
                session['ended_at'] = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"✅ Processed input, turn {session['turn_count']}, continues: {call_continues}")
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': call_continues,
                'session_state': 'in_progress' if call_continues else 'completed',
                'turn_count': session['turn_count']
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing user input: {e}")
            return {
                'success': False, 
                'error': str(e), 
                'call_continues': False,
                'ai_response': 'Sorry, I need to go.'
            }
    
    def generate_ai_response(self, session: Dict, user_input: str) -> str:
        """Generate AI response to user input"""
        try:
            if self.openai_service and self.openai_service.is_available():
                # Build conversation context
                conversation = []
                for exchange in session['conversation_history'][-6:]:  # Last 6 exchanges
                    role = "user" if exchange['speaker'] == 'user' else "assistant"
                    conversation.append({"role": role, "content": exchange['text']})
                
                # Add current user input
                conversation.append({"role": "user", "content": user_input})
                
                # Generate response
                try:
                    response = self.openai_service.chat_completion(
                        messages=conversation,
                        max_tokens=100,
                        temperature=0.7
                    )
                    
                    if response and response.strip():
                        return response.strip()
                        
                except Exception as ai_error:
                    logger.warning(f"⚠️ AI response generation failed: {ai_error}")
            
            # Fallback responses based on common cold call scenarios
            fallback_responses = [
                "I see. Can you tell me more about that?",
                "That's interesting. How does that work exactly?",
                "I'm not sure I follow. What are you proposing?",
                "Look, I'm pretty busy right now. What exactly are you selling?",
                "Okay, but how much time is this going to take?",
                "I'll need to think about it. Can you send me some information?",
                "Thanks, but I'm not interested right now.",
                "Sorry, I need to get back to work. Have a good day."
            ]
            
            import random
            response = random.choice(fallback_responses)
            logger.info(f"📞 Using fallback AI response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error generating AI response: {e}")
            return "Sorry, I need to go now."
    
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End roleplay session - FIXED VERSION"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return {'success': False, 'error': 'Session not found'}
            
            session['session_active'] = False
            session['ended_at'] = datetime.now(timezone.utc).isoformat()
            session['forced_end'] = forced_end
            
            # Calculate duration
            started_at = datetime.fromisoformat(session['started_at'].replace('Z', '+00:00'))
            ended_at = datetime.now(timezone.utc)
            duration_minutes = max(1, int((ended_at - started_at).total_seconds() / 60))
            
            # Simple evaluation
            score = min(90, max(60, 80 - (session['turn_count'] * 2)))
            
            coaching = {
                'opening': 'Good job starting the conversation!',
                'communication': 'Your communication was clear.',
                'overall': f'You completed {session["turn_count"]} exchanges. Keep practicing!'
            }
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            logger.info(f"✅ Session ended: {session_id}, Duration: {duration_minutes}min, Score: {score}")
            
            return {
                'success': True,
                'session_data': session,
                'duration_minutes': duration_minutes,
                'session_success': score >= 70,
                'overall_score': score,
                'coaching': coaching,
                'roleplay_type': session.get('mode', 'practice')
            }
            
        except Exception as e:
            logger.error(f"❌ Error ending session: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session status"""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        return {
            'session_active': session.get('session_active', False),
            'current_stage': session.get('current_stage', 'unknown'),
            'conversation_length': len(session.get('conversation_history', [])),
            'turn_count': session.get('turn_count', 0),
            'openai_available': bool(self.openai_service and self.openai_service.is_available())
        }
# ===== FIXED: services/roleplay/base_roleplay.py =====

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
    
    def is_openai_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.openai_service and hasattr(self.openai_service, 'is_available') and self.openai_service.is_available()
    
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
                        'role': 'assistant',
                        'content': initial_response,
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'stage': 'phone_pickup'
                    }
                ],
                'current_stage': 'phone_pickup',
                'turn_count': 0,
                'user_turn_count': 0,  # NEW: Track only user turns
                'session_active': True,
                'minimum_turns_required': 3,  # NEW: Minimum user interactions required
                'last_activity': datetime.now(timezone.utc).isoformat()  # NEW: Track activity
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
            if self.is_openai_available():
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
                    # Use the OpenAI service properly
                    response = self.openai_service.client.chat.completions.create(
                        model=self.openai_service.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=50,
                        temperature=0.8
                    )
                    
                    ai_response = response.choices[0].message.content.strip()
                    
                    if ai_response and ai_response.strip():
                        logger.info(f"✅ Generated AI initial response: {ai_response[:50]}...")
                        return ai_response.strip()
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
            
            # Check if session is still active
            if not session.get('session_active', False):
                return {
                    'success': False, 
                    'error': 'Session is no longer active', 
                    'call_continues': False,
                    'ai_response': 'The call has ended.'
                }
            
            # Update activity timestamp
            session['last_activity'] = datetime.now(timezone.utc).isoformat()
            
            # Increment counters
            session['turn_count'] += 1
            session['user_turn_count'] += 1  # NEW: Track user turns specifically
            
            # Add user input to conversation
            session['conversation_history'].append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session.get('current_stage', 'unknown')
            })
            
            logger.info(f"🎤 User input processed: Turn {session['user_turn_count']}, Input: '{user_input[:50]}...'")
            
            # Generate AI response
            ai_response = self.generate_ai_response(session, user_input)
            
            # Add AI response to conversation
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session.get('current_stage', 'unknown')
            })
            
            # Update stage progression
            self.update_session_stage(session, user_input)
            
            # Determine if call should continue - FIXED LOGIC
            call_continues = self.should_call_continue(session, user_input)
            
            if not call_continues:
                session['session_active'] = False
                session['ended_at'] = datetime.now(timezone.utc).isoformat()
                logger.info(f"📞 Call ending naturally after {session['user_turn_count']} user turns")
            
            logger.info(f"✅ Processed input, user turn {session['user_turn_count']}, continues: {call_continues}")
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': call_continues,
                'session_state': 'in_progress' if call_continues else 'completed',
                'turn_count': session['turn_count'],
                'user_turn_count': session['user_turn_count']
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing user input: {e}")
            return {
                'success': False, 
                'error': str(e), 
                'call_continues': False,
                'ai_response': 'Sorry, I need to go.'
            }
    
    def update_session_stage(self, session: Dict, user_input: str):
        """Update session stage based on conversation progress"""
        user_turns = session['user_turn_count']
        current_stage = session.get('current_stage', 'phone_pickup')
        
        # Simple stage progression based on user turns
        if user_turns == 1 and current_stage == 'phone_pickup':
            session['current_stage'] = 'opener_evaluation'
        elif user_turns == 2 and current_stage == 'opener_evaluation':
            session['current_stage'] = 'objection_handling'
        elif user_turns >= 3 and current_stage == 'objection_handling':
            session['current_stage'] = 'pitch_stage'
        elif user_turns >= 5:
            session['current_stage'] = 'discovery_stage'
    
    def should_call_continue(self, session: Dict, user_input: str) -> bool:
        """Determine if call should continue - IMPROVED LOGIC"""
        user_turns = session['user_turn_count']
        minimum_required = session.get('minimum_turns_required', 3)
        
        # Never end call before minimum turns
        if user_turns < minimum_required:
            logger.info(f"📞 Call continues: {user_turns}/{minimum_required} minimum turns")
            return True
        
        # End call after reasonable conversation (6-8 turns)
        if user_turns >= 8:
            logger.info(f"📞 Call ending: Reached {user_turns} turns")
            return False
        
        # Random chance to end after minimum turns (simulate natural end)
        if user_turns >= minimum_required:
            import random
            # 20% chance to end after turn 5, 40% after turn 6, etc.
            end_probability = max(0, (user_turns - minimum_required) * 0.2)
            if random.random() < end_probability:
                logger.info(f"📞 Call ending: Natural conclusion after {user_turns} turns")
                return False
        
        return True
    
    def generate_ai_response(self, session: Dict, user_input: str) -> str:
        """Generate AI response to user input"""
        try:
            if self.is_openai_available():
                # Build conversation context
                conversation = []
                for exchange in session['conversation_history'][-6:]:  # Last 6 exchanges
                    role = "user" if exchange['role'] == 'user' else "assistant"
                    conversation.append({"role": role, "content": exchange['content']})
                
                # Add current user input
                conversation.append({"role": "user", "content": user_input})
                
                # Generate response using OpenAI
                try:
                    response = self.openai_service.client.chat.completions.create(
                        model=self.openai_service.model,
                        messages=conversation,
                        max_tokens=100,
                        temperature=0.7
                    )
                    
                    ai_response = response.choices[0].message.content.strip()
                    
                    if ai_response and ai_response.strip():
                        logger.info(f"🤖 AI response generated: '{ai_response[:50]}...'")
                        return ai_response.strip()
                        
                except Exception as ai_error:
                    logger.warning(f"⚠️ AI response generation failed: {ai_error}")
            
            # Fallback responses based on conversation stage and user input
            fallback_response = self.get_fallback_response(session, user_input)
            logger.info(f"📞 Using fallback AI response: {fallback_response}")
            return fallback_response
            
        except Exception as e:
            logger.error(f"❌ Error generating AI response: {e}")
            return "I see. Can you tell me more about that?"
    
    def get_fallback_response(self, session: Dict, user_input: str) -> str:
        """Get appropriate fallback response based on conversation context"""
        user_turns = session['user_turn_count']
        stage = session.get('current_stage', 'unknown')
        
        # Response patterns based on stage
        if stage == 'opener_evaluation':
            responses = [
                "Okay, what's this about?",
                "Alright, I'm listening.",
                "You have 30 seconds.",
                "What are you calling about?"
            ]
        elif stage == 'objection_handling':
            responses = [
                "I'm not really interested in cold calls.",
                "We already have something in place.",
                "I don't have time for this.",
                "Send me an email instead."
            ]
        elif stage == 'pitch_stage':
            responses = [
                "That sounds interesting. Tell me more.",
                "How exactly does that work?",
                "What makes you different from others?",
                "I'd need to see some numbers."
            ]
        elif stage == 'discovery_stage':
            responses = [
                "Let me think about it.",
                "I'd need to discuss this with my team.",
                "Send me some information.",
                "When can we schedule a proper meeting?"
            ]
        else:
            responses = [
                "I see.",
                "Go on.",
                "What do you mean?",
                "Can you be more specific?"
            ]
        
        # Add some variation based on user input keywords
        user_lower = user_input.lower()
        if 'help' in user_lower or 'assist' in user_lower:
            responses.extend(["How can you help us?", "What kind of assistance?"])
        elif 'save' in user_lower or 'money' in user_lower:
            responses.extend(["How much can we save?", "What's the ROI?"])
        elif 'time' in user_lower:
            responses.extend(["How much time would this take?", "I don't have much time."])
        
        import random
        return random.choice(responses)
    
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
            
            # FIXED: Only calculate score if user had meaningful interaction
            user_turns = session.get('user_turn_count', 0)
            minimum_required = session.get('minimum_turns_required', 3)
            
            if user_turns < minimum_required and not forced_end:
                # Session ended too early - lower score
                score = 40
                session_success = False
                coaching_message = f"Practice session was too short ({user_turns} interactions). Try to have a longer conversation."
            elif user_turns == 0:
                # No user input at all - very low score
                score = 20
                session_success = False
                coaching_message = "No conversation detected. Make sure your microphone is working and speak clearly."
            else:
                # Calculate score based on conversation quality
                score = self.calculate_conversation_score(session)
                session_success = score >= 70
                coaching_message = f"Good practice! You had {user_turns} interactions."
            
            coaching = {
                'opening': 'Practice your opening with confidence and empathy.',
                'communication': coaching_message,
                'overall': f'You completed {user_turns} interactions. {"Great job!" if session_success else "Keep practicing to improve!"}'
            }
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            logger.info(f"✅ Session ended: {session_id}, Duration: {duration_minutes}min, Score: {score}, User turns: {user_turns}")
            
            return {
                'success': True,
                'session_data': session,
                'duration_minutes': duration_minutes,
                'session_success': session_success,
                'overall_score': score,
                'coaching': coaching,
                'roleplay_type': session.get('mode', 'practice'),
                'user_interactions': user_turns,
                'forced_end': forced_end
            }
            
        except Exception as e:
            logger.error(f"❌ Error ending session: {e}")
            return {'success': False, 'error': str(e)}
    
    def calculate_conversation_score(self, session: Dict) -> int:
        """Calculate conversation score based on various factors"""
        user_turns = session.get('user_turn_count', 0)
        total_conversation = len(session.get('conversation_history', []))
        
        # Base score from number of user interactions
        base_score = min(80, user_turns * 15)  # 15 points per user turn, max 80
        
        # Bonus for conversation length
        length_bonus = min(20, total_conversation * 2)  # 2 points per total exchange, max 20
        
        # Stage progression bonus
        stage = session.get('current_stage', 'phone_pickup')
        stage_bonus = {
            'phone_pickup': 0,
            'opener_evaluation': 5,
            'objection_handling': 10,
            'pitch_stage': 15,
            'discovery_stage': 20
        }.get(stage, 0)
        
        total_score = min(100, max(20, base_score + length_bonus + stage_bonus))
        
        logger.info(f"📊 Score calculation: Base({base_score}) + Length({length_bonus}) + Stage({stage_bonus}) = {total_score}")
        
        return total_score
    
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
            'user_turn_count': session.get('user_turn_count', 0),
            'openai_available': self.is_openai_available(),
            'last_activity': session.get('last_activity')
        }
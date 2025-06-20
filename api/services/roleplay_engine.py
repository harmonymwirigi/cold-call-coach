# ===== FIXED API/SERVICES/ROLEPLAY_ENGINE.PY - SIMPLE & WORKING =====

import random
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class RoleplayEngine:
    def __init__(self):
        # Import here to avoid circular imports
        try:
            from services.openai_service import OpenAIService
            self.openai_service = OpenAIService()
        except Exception as e:
            logger.error(f"Failed to import OpenAI service: {e}")
            self.openai_service = None
        
        # Session storage
        self.active_sessions = {}
        
        # Roleplay 1.1 stage flow
        self.stage_flow = {
            'phone_pickup': 'opener_evaluation',
            'opener_evaluation': 'early_objection',
            'early_objection': 'objection_handling', 
            'objection_handling': 'mini_pitch',
            'mini_pitch': 'soft_discovery',
            'soft_discovery': 'call_ended'
        }
        
        logger.info(f"RoleplayEngine initialized. OpenAI available: {bool(self.openai_service and self.openai_service.is_available())}")

    def create_session(self, user_id: str, roleplay_id: int, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create new Roleplay 1.1 session"""
        try:
            session_id = f"{user_id}_{roleplay_id}_{mode}_{datetime.now().timestamp()}"
            
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'roleplay_id': roleplay_id,
                'mode': mode,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'user_context': user_context,
                'conversation_history': [],
                'current_stage': 'phone_pickup',
                'session_active': True,
                'hang_up_triggered': False,
                
                # Roleplay 1.1 tracking
                'rubric_scores': {},
                'stage_progression': ['phone_pickup'],
                'overall_call_result': 'in_progress'
            }
            
            # Store session
            self.active_sessions[session_id] = session_data
            
            # Generate initial phone pickup
            initial_response = random.choice(["Hello?", "Hi there.", "Good morning.", "Yes?"])
            
            # Add to conversation
            session_data['conversation_history'].append({
                'role': 'assistant',
                'content': initial_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': 'phone_pickup'
            })
            
            logger.info(f"Created Roleplay 1.1 session {session_id}")
            
            return {
                'success': True,
                'session_id': session_id,
                'initial_response': initial_response
            }
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return {'success': False, 'error': str(e)}

    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input for Roleplay 1.1"""
        try:
            logger.info(f"Processing input for session {session_id}: {user_input[:50]}...")
            
            if session_id not in self.active_sessions:
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            
            if not session.get('session_active'):
                raise ValueError("Session not active")
            
            # Handle silence triggers
            if user_input in ['[SILENCE_IMPATIENCE]', '[SILENCE_HANGUP]']:
                return self._handle_silence_trigger(session, user_input)
            
            # Add user input to conversation
            session['conversation_history'].append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage']
            })
            
            # Determine what to evaluate based on current stage
            evaluation_stage = self._get_evaluation_stage(session['current_stage'])
            
            # Evaluate user input using AI
            evaluation = self._evaluate_user_input(session, user_input, evaluation_stage)
            
            # Generate AI response based on evaluation
            ai_response = self._generate_ai_response(session, user_input, evaluation)
            
            # Add AI response to conversation
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage'],
                'evaluation': evaluation
            })
            
            # Update session state
            self._update_session_state(session, evaluation)
            
            # Check if call should continue
            call_continues = self._should_call_continue(session, evaluation)
            
            logger.info(f"Response: {ai_response[:50]}... | Call continues: {call_continues}")
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': call_continues,
                'evaluation': evaluation,
                'session_state': session['current_stage']
            }
            
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return {
                'success': False,
                'error': str(e),
                'call_continues': False
            }

    def _get_evaluation_stage(self, current_stage: str) -> str:
        """Map current stage to evaluation stage"""
        mapping = {
            'phone_pickup': 'opener',
            'opener_evaluation': 'opener',
            'early_objection': 'objection_handling',
            'objection_handling': 'objection_handling',
            'mini_pitch': 'mini_pitch',
            'soft_discovery': 'soft_discovery'
        }
        return mapping.get(current_stage, 'opener')

    def _evaluate_user_input(self, session: Dict, user_input: str, evaluation_stage: str) -> Dict[str, Any]:
        """Evaluate user input using OpenAI"""
        try:
            if self.openai_service and self.openai_service.is_available():
                logger.info(f"Evaluating with OpenAI: stage={evaluation_stage}")
                evaluation = self.openai_service.evaluate_user_input(
                    user_input,
                    session['conversation_history'],
                    evaluation_stage
                )
                
                # Store in session rubric scores
                session['rubric_scores'][evaluation_stage] = {
                    'score': evaluation.get('score', 0),
                    'passed': evaluation.get('passed', False),
                    'criteria_met': evaluation.get('criteria_met', [])
                }
                
                logger.info(f"AI Evaluation: {evaluation}")
                return evaluation
            else:
                logger.warning("OpenAI not available, using basic evaluation")
                return self._basic_evaluation(user_input, evaluation_stage)
                
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return self._basic_evaluation(user_input, evaluation_stage)

    def _basic_evaluation(self, user_input: str, evaluation_stage: str) -> Dict[str, Any]:
        """Basic evaluation fallback"""
        # Simple scoring based on input quality
        score = 2  # Base score
        criteria_met = []
        user_input_lower = user_input.lower()
        
        # Basic checks
        if len(user_input.strip()) > 10:  # Substantial input
            score += 1
            criteria_met.append('substantial_input')
        
        if any(word in user_input_lower for word in ["i'm", "don't", "can't"]):
            score += 1
            criteria_met.append('contractions')
        
        if user_input.strip().endswith('?'):
            score += 1
            criteria_met.append('question')
        
        passed = score >= 3
        
        return {
            'score': score,
            'passed': passed,
            'criteria_met': criteria_met,
            'feedback': 'Basic evaluation',
            'should_continue': True,
            'next_action': 'continue',
            'source': 'basic'
        }

    def _generate_ai_response(self, session: Dict, user_input: str, evaluation: Dict) -> str:
        """Generate AI prospect response"""
        try:
            current_stage = session['current_stage']
            
            # Check if should hang up based on evaluation
            if self._should_hang_up(evaluation, current_stage):
                session['hang_up_triggered'] = True
                return self._get_hangup_response(current_stage, evaluation)
            
            # Use OpenAI if available
            if self.openai_service and self.openai_service.is_available():
                logger.info("Generating AI response with OpenAI")
                response_result = self.openai_service.generate_roleplay_response(
                    user_input,
                    session['conversation_history'],
                    session['user_context'],
                    current_stage
                )
                
                if response_result.get('success'):
                    return response_result['response']
                else:
                    logger.warning("OpenAI response failed, using fallback")
            
            # Fallback response
            return self._get_fallback_response(current_stage, evaluation)
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._get_fallback_response(current_stage, evaluation)

    def _should_hang_up(self, evaluation: Dict, current_stage: str) -> bool:
        """Determine if prospect should hang up"""
        # Hang up based on evaluation quality
        if current_stage == 'opener_evaluation':
            score = evaluation.get('score', 0)
            if score <= 1:
                return random.random() < 0.8  # 80% chance
            elif score == 2:
                return random.random() < 0.3  # 30% chance
            elif score >= 3:
                return random.random() < 0.1  # 10% chance
        
        # Hang up if evaluation says so
        if evaluation.get('next_action') == 'hangup':
            return True
        
        # Hang up if poor objection handling
        if current_stage == 'objection_handling' and not evaluation.get('passed', True):
            return random.random() < 0.5  # 50% chance
        
        return False

    def _get_hangup_response(self, current_stage: str, evaluation: Dict) -> str:
        """Get appropriate hangup response"""
        hangup_responses = {
            'opener_evaluation': [
                "Not interested.", "Please don't call here again.", 
                "I'm hanging up now.", "Take me off your list."
            ],
            'objection_handling': [
                "I already told you I'm not interested.", 
                "You're not listening. Goodbye.",
                "This is exactly why I hate cold calls."
            ],
            'default': [
                "I have to go. Goodbye.", "Not interested. Thanks."
            ]
        }
        
        responses = hangup_responses.get(current_stage, hangup_responses['default'])
        return random.choice(responses)

    def _get_fallback_response(self, current_stage: str, evaluation: Dict) -> str:
        """Get fallback response when OpenAI fails"""
        fallback_responses = {
            'phone_pickup': ["Hello?", "Hi there.", "Good morning."],
            'opener_evaluation': [
                "What's this about?", "I'm not interested", "Now is not a good time",
                "I have a meeting", "Send me an email", "Is this a sales call?"
            ],
            'early_objection': [
                "What's this about?", "I'm not interested", "Now is not a good time"
            ],
            'objection_handling': [
                "Alright, I'm listening.", "Go ahead, what is it?", 
                "You have 30 seconds.", "This better be good."
            ],
            'mini_pitch': [
                "That's interesting. Tell me more.", "How exactly do you do that?",
                "What does that look like?", "I don't understand."
            ],
            'soft_discovery': [
                "That's a good question. Send me information. Goodbye.",
                "Interesting. Email me the details.",
                "Not relevant to us. Goodbye."
            ]
        }
        
        responses = fallback_responses.get(current_stage, ["I see. Continue."])
        return random.choice(responses)

    def _update_session_state(self, session: Dict, evaluation: Dict):
        """Update session state based on evaluation"""
        current_stage = session['current_stage']
        
        # Move to next stage if appropriate
        if evaluation.get('passed', False) or evaluation.get('should_continue', True):
            next_stage = self.stage_flow.get(current_stage)
            if next_stage and next_stage != current_stage:
                session['current_stage'] = next_stage
                session['stage_progression'].append(next_stage)
                logger.info(f"Stage progression: {current_stage} → {next_stage}")

    def _should_call_continue(self, session: Dict, evaluation: Dict) -> bool:
        """Determine if call should continue"""
        # End if hung up
        if session.get('hang_up_triggered'):
            return False
        
        # End if reached final stage
        if session['current_stage'] == 'call_ended':
            return False
        
        # End if at discovery stage (natural ending point)
        if session['current_stage'] == 'soft_discovery':
            return False
        
        return True

    def _handle_silence_trigger(self, session: Dict, trigger: str) -> Dict[str, Any]:
        """Handle silence triggers"""
        if trigger == '[SILENCE_IMPATIENCE]':
            impatience_phrases = [
                "Hello? Are you still with me?", "Can you hear me?",
                "Just checking you're there…", "Still on the line?",
                "I don't have much time for this."
            ]
            response = random.choice(impatience_phrases)
            
            session['conversation_history'].append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'trigger': 'silence_impatience'
            })
            
            return {
                'success': True,
                'ai_response': response,
                'call_continues': True,
                'evaluation': {'trigger': 'impatience'}
            }
        
        elif trigger == '[SILENCE_HANGUP]':
            response = "I don't have time for this. Goodbye."
            session['hang_up_triggered'] = True
            
            session['conversation_history'].append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'trigger': 'silence_hangup'
            })
            
            return {
                'success': True,
                'ai_response': response,
                'call_continues': False,
                'evaluation': {'trigger': 'hangup'}
            }

    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End session and generate coaching"""
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
            
            # Generate coaching
            coaching_result = self._generate_coaching(session)
            
            # Calculate success
            rubric_scores = session.get('rubric_scores', {})
            session_success = self._calculate_session_success(rubric_scores)
            
            # Clean up
            del self.active_sessions[session_id]
            
            logger.info(f"Session {session_id} ended. Success: {session_success}")
            
            return {
                'success': True,
                'duration_minutes': duration_minutes,
                'session_success': session_success,
                'coaching': coaching_result['coaching'],
                'overall_score': coaching_result['score'],
                'session_data': session
            }
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return {'success': False, 'error': str(e)}

    def _generate_coaching(self, session: Dict) -> Dict[str, Any]:
        """Generate coaching feedback"""
        try:
            if self.openai_service and self.openai_service.is_available():
                logger.info("Generating coaching with OpenAI")
                return self.openai_service.generate_coaching_feedback(
                    session['conversation_history'],
                    session.get('rubric_scores', {}),
                    session['user_context']
                )
            else:
                logger.warning("OpenAI not available, using basic coaching")
                return self._basic_coaching(session.get('rubric_scores', {}))
                
        except Exception as e:
            logger.error(f"Coaching generation error: {e}")
            return self._basic_coaching(session.get('rubric_scores', {}))

    def _basic_coaching(self, rubric_scores: Dict) -> Dict[str, Any]:
        """Basic coaching fallback"""
        score = 40  # Base score
        
        # Add points for passed rubrics
        for stage_scores in rubric_scores.values():
            if stage_scores.get('passed', False):
                score += 15
        
        score = min(100, max(0, score))
        
        coaching = {
            'sales_coaching': 'Practice your opening with empathy and use contractions.',
            'grammar_coaching': 'Use "I\'m" instead of "I am" to sound natural.',
            'vocabulary_coaching': 'Use simple business words like "book a meeting".',
            'pronunciation_coaching': 'Speak clearly and not too fast.',
            'rapport_assertiveness': 'Be confident but polite. Show empathy first.'
        }
        
        return {
            'success': True,
            'coaching': coaching,
            'score': score,
            'source': 'basic'
        }

    def _calculate_session_success(self, rubric_scores: Dict) -> bool:
        """Calculate if session was successful"""
        # Session succeeds if most rubrics passed
        total_rubrics = len(rubric_scores)
        if total_rubrics == 0:
            return False
        
        passed_rubrics = sum(1 for scores in rubric_scores.values() if scores.get('passed', False))
        return passed_rubrics >= (total_rubrics * 0.6)  # 60% pass rate

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session status"""
        session = self.active_sessions.get(session_id)
        if session:
            return {
                'session_active': session.get('session_active', False),
                'current_stage': session.get('current_stage', 'unknown'),
                'rubric_scores': session.get('rubric_scores', {}),
                'conversation_length': len(session.get('conversation_history', [])),
                'openai_available': bool(self.openai_service and self.openai_service.is_available())
            }
        return None

    def cleanup_expired_sessions(self):
        """Clean up old sessions"""
        try:
            current_time = datetime.now(timezone.utc)
            expired_sessions = []
            
            for session_id, session in self.active_sessions.items():
                started_at = datetime.fromisoformat(session['started_at'].replace('Z', '+00:00'))
                if current_time - started_at > timedelta(hours=2):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
                logger.info(f"Cleaned up expired session: {session_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")

    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'active_sessions': len(self.active_sessions),
            'openai_available': bool(self.openai_service and self.openai_service.is_available()),
            'engine_status': 'running'
        }
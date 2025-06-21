# ===== services/roleplay/roleplay_1_1.py =====

import random
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from .base_roleplay import BaseRoleplay
from .configs.roleplay_1_1_config import Roleplay11Config

logger = logging.getLogger(__name__)

class Roleplay11(BaseRoleplay):
    """Roleplay 1.1 - Practice Mode: Single call with detailed coaching"""
    
    def __init__(self, openai_service=None):
        super().__init__(openai_service)
        self.config = Roleplay11Config()
        
    def get_roleplay_info(self) -> Dict[str, Any]:
        """Return Roleplay 1.1 configuration"""
        return {
            'id': self.config.ROLEPLAY_ID,
            'name': self.config.NAME,
            'description': self.config.DESCRIPTION,
            'type': 'practice',
            'features': {
                'ai_evaluation': True,
                'dynamic_scoring': True,
                'extended_conversation': True,
                'detailed_coaching': True,
                'natural_conversation': True
            },
            'stages': list(self.config.STAGE_FLOW.keys()),
            'max_turns': self.config.MAX_TOTAL_TURNS
        }
    
    def create_session(self, user_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create new Roleplay 1.1 session"""
        try:
            session_id = f"{user_id}_{self.config.ROLEPLAY_ID}_{mode}_{int(datetime.now().timestamp())}"
            
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'roleplay_id': self.config.ROLEPLAY_ID,
                'mode': mode,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'user_context': user_context,
                'conversation_history': [],
                'current_stage': 'phone_pickup',
                'session_active': True,
                'hang_up_triggered': False,
                'turn_count': 0,
                'stage_turn_count': 0,
                'stages_completed': [],
                'conversation_quality': 0,
                'rubric_scores': {},
                'stage_progression': ['phone_pickup'],
                'overall_call_result': 'in_progress'
            }
            
            # Store session
            self.active_sessions[session_id] = session_data
            
            # Generate initial response
            initial_response = self._get_initial_response(user_context)
            
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
                'initial_response': initial_response,
                'roleplay_info': self.get_roleplay_info()
            }
            
        except Exception as e:
            logger.error(f"Error creating Roleplay 1.1 session: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input for Roleplay 1.1"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            
            if not session.get('session_active'):
                raise ValueError("Session not active")
            
            # Handle silence triggers
            if user_input in ['[SILENCE_IMPATIENCE]', '[SILENCE_HANGUP]']:
                return self._handle_silence_trigger(session, user_input)
            
            # Increment counters
            session['turn_count'] += 1
            session['stage_turn_count'] += 1
            
            # Add user input to conversation
            session['conversation_history'].append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage']
            })
            
            # Evaluate user input
            evaluation_stage = self._get_evaluation_stage(session['current_stage'])
            evaluation = self._evaluate_user_input(session, user_input, evaluation_stage)
            
            # Update conversation quality
            self._update_conversation_quality(session, evaluation)
            
            # Check if should hang up
            should_hang_up = self._should_hang_up_now(session, evaluation, user_input)
            
            if should_hang_up:
                ai_response = self._get_hangup_response(session['current_stage'], evaluation)
                session['hang_up_triggered'] = True
                call_continues = False
            else:
                # Generate AI response
                ai_response = self._generate_ai_response(session, user_input, evaluation)
                
                # Update session state
                self._update_session_state(session, evaluation)
                
                # Check if call should continue
                call_continues = self._should_call_continue(session, evaluation)
            
            # Add AI response to conversation
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage'],
                'evaluation': evaluation
            })
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': call_continues,
                'evaluation': evaluation,
                'session_state': session['current_stage'],
                'turn_count': session['turn_count'],
                'conversation_quality': session['conversation_quality']
            }
            
        except Exception as e:
            logger.error(f"Error processing Roleplay 1.1 input: {e}")
            return {'success': False, 'error': str(e), 'call_continues': False}
    
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End Roleplay 1.1 session and generate coaching"""
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
            session_success = self._calculate_session_success(session)
            
            result = {
                'success': True,
                'duration_minutes': duration_minutes,
                'session_success': session_success,
                'coaching': coaching_result.get('coaching', {}),
                'overall_score': coaching_result.get('score', 50),
                'session_data': session,
                'roleplay_type': 'practice'
            }
            
            # Clean up session
            del self.active_sessions[session_id]
            
            return result
            
        except Exception as e:
            logger.error(f"Error ending Roleplay 1.1 session: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current Roleplay 1.1 session status"""
        session = self.active_sessions.get(session_id)
        if session:
            return {
                'session_active': session.get('session_active', False),
                'current_stage': session.get('current_stage', 'unknown'),
                'rubric_scores': session.get('rubric_scores', {}),
                'conversation_length': len(session.get('conversation_history', [])),
                'conversation_quality': session.get('conversation_quality', 0),
                'stages_completed': session.get('stages_completed', []),
                'turn_count': session.get('turn_count', 0),
                'roleplay_type': 'practice',
                'openai_available': self.is_openai_available()
            }
        return None
    
    # ===== PRIVATE METHODS =====
    
    def _get_initial_response(self, user_context: Dict) -> str:
        """Generate initial phone pickup response"""
        responses = [
            "Hello?", 
            "Hi there.", 
            "Good morning.", 
            "Yes?",
            f"{user_context.get('first_name', 'Alex')} speaking."
        ]
        return random.choice(responses)
    
    def _get_evaluation_stage(self, current_stage: str) -> str:
        """Map current stage to evaluation stage"""
        mapping = {
            'phone_pickup': 'opener',
            'opener_evaluation': 'opener',
            'early_objection': 'objection_handling',
            'objection_handling': 'objection_handling',
            'mini_pitch': 'mini_pitch',
            'soft_discovery': 'soft_discovery',
            'extended_conversation': 'soft_discovery'
        }
        return mapping.get(current_stage, 'opener')
    
    def _evaluate_user_input(self, session: Dict, user_input: str, evaluation_stage: str) -> Dict[str, Any]:
        """Evaluate user input using OpenAI or fallback"""
        try:
            if self.is_openai_available():
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
                
                return evaluation
            else:
                return self._basic_evaluation(user_input, evaluation_stage)
                
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return self._basic_evaluation(user_input, evaluation_stage)
    
    def _basic_evaluation(self, user_input: str, evaluation_stage: str) -> Dict[str, Any]:
        """Basic evaluation fallback"""
        score = 0
        criteria_met = []
        user_input_lower = user_input.lower().strip()
        
        # Basic scoring logic based on stage
        if evaluation_stage == "opener":
            if len(user_input.strip()) > 15:
                score += 1
                criteria_met.append('substantial_opener')
            
            if any(phrase in user_input_lower for phrase in ["i'm calling", "calling from", "calling about"]):
                score += 1
                criteria_met.append('clear_opener')
            
            if any(contraction in user_input_lower for contraction in ["i'm", "don't", "can't"]):
                score += 1
                criteria_met.append('casual_tone')
            
            if any(empathy in user_input_lower for empathy in ["know this is", "out of the blue"]):
                score += 1
                criteria_met.append('shows_empathy')
        
        # Similar logic for other stages...
        
        threshold = self.config.PASS_THRESHOLDS.get(evaluation_stage, 2)
        passed = score >= threshold
        
        return {
            'score': score,
            'passed': passed,
            'criteria_met': criteria_met,
            'feedback': f'Basic evaluation: {score} criteria met for {evaluation_stage}',
            'should_continue': True,
            'next_action': 'continue',
            'hang_up_probability': 0.3 if score <= 1 else 0.1,
            'source': 'basic',
            'stage': evaluation_stage
        }
    
    def _update_conversation_quality(self, session: Dict, evaluation: Dict):
        """Track overall conversation quality"""
        score = evaluation.get('score', 0)
        max_score = 4
        
        turn_quality = (score / max_score) * 100
        total_turns = session['turn_count']
        current_quality = session.get('conversation_quality', 0)
        
        session['conversation_quality'] = ((current_quality * (total_turns - 1)) + turn_quality) / total_turns
    
    def _should_hang_up_now(self, session: Dict, evaluation: Dict, user_input: str) -> bool:
        """Determine if prospect should hang up"""
        current_stage = session['current_stage']
        
        # Never hang up on first interaction
        if session['turn_count'] <= 1:
            return False
        
        # Good conversation quality reduces hang-up chance
        conversation_quality = session.get('conversation_quality', 0)
        if conversation_quality >= 60:
            return False
        
        # Get hang up probability from evaluation
        hang_up_prob = evaluation.get('hang_up_probability', 0.1)
        
        # Adjust based on stage and performance
        score = evaluation.get('score', 0)
        if current_stage == 'opener_evaluation':
            if score <= 1:
                hang_up_prob = 0.4
            elif score == 2:
                hang_up_prob = 0.15
            else:
                hang_up_prob = 0.02
        
        # Reduce hang-up chance as conversation progresses
        if session['turn_count'] >= 3:
            hang_up_prob *= 0.5
        
        return random.random() < hang_up_prob
    
    def _generate_ai_response(self, session: Dict, user_input: str, evaluation: Dict) -> str:
        """Generate AI prospect response"""
        try:
            if self.is_openai_available():
                response_result = self.openai_service.generate_roleplay_response(
                    user_input,
                    session['conversation_history'],
                    session['user_context'],
                    session['current_stage']
                )
                
                if response_result.get('success'):
                    return response_result['response']
            
            # Fallback response
            return self._get_fallback_response(session['current_stage'], evaluation)
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._get_fallback_response(session['current_stage'], evaluation)
    
    def _get_fallback_response(self, current_stage: str, evaluation: Dict) -> str:
        """Get fallback response based on stage and evaluation"""
        passed = evaluation.get('passed', False)
        
        responses_map = {
            'opener_evaluation': {
                True: ["Alright, what's this about?", "I'm listening. Go ahead."],
                False: ["What's this about?", "I'm not interested."]
            },
            'early_objection': ["I'm not interested.", "We don't take cold calls.", "Now is not a good time."],
            'objection_handling': {
                True: ["Alright, I'm listening. What do you do?", "Okay, you have 30 seconds."],
                False: ["I already told you I'm not interested.", "You're not listening."]
            },
            'mini_pitch': {
                True: ["That sounds interesting. Tell me more.", "How exactly does that work?"],
                False: ["I don't understand what you're saying.", "That's too vague."]
            },
            'soft_discovery': ["That's a good question.", "Send me some information.", "I'd need to discuss this with my team."],
            'extended_conversation': ["Interesting. How does that work?", "That makes sense.", "I'll think about it."]
        }
        
        stage_responses = responses_map.get(current_stage, ["I see."])
        
        if isinstance(stage_responses, dict):
            responses = stage_responses.get(passed, stage_responses.get(True, ["I see."]))
        else:
            responses = stage_responses
        
        return random.choice(responses)
    
    def _update_session_state(self, session: Dict, evaluation: Dict):
        """Update session state based on evaluation"""
        current_stage = session['current_stage']
        should_progress = False
        
        # Stage progression logic
        if current_stage == 'phone_pickup':
            should_progress = True
        elif current_stage == 'opener_evaluation':
            if evaluation.get('passed', False) or session['stage_turn_count'] >= 2:
                should_progress = True
        elif current_stage == 'early_objection':
            should_progress = True
        elif current_stage == 'objection_handling':
            if evaluation.get('passed', False) or session['stage_turn_count'] >= 3:
                should_progress = True
        elif current_stage == 'mini_pitch':
            if evaluation.get('score', 0) >= 2 or session['stage_turn_count'] >= 2:
                should_progress = True
        elif current_stage == 'soft_discovery':
            if session['stage_turn_count'] >= 2:
                should_progress = True
        
        if should_progress:
            next_stage = self.config.STAGE_FLOW.get(current_stage)
            if next_stage and next_stage != current_stage:
                # Mark current stage as completed
                if current_stage not in session.get('stages_completed', []):
                    session.setdefault('stages_completed', []).append(current_stage)
                
                session['current_stage'] = next_stage
                session['stage_progression'].append(next_stage)
                session['stage_turn_count'] = 0
    
    def _should_call_continue(self, session: Dict, evaluation: Dict) -> bool:
        """Determine if call should continue"""
        if session.get('hang_up_triggered'):
            return False
        
        if session['current_stage'] == 'call_ended':
            return False
        
        # Extended conversation logic
        if session['current_stage'] == 'extended_conversation':
            conversation_quality = session.get('conversation_quality', 50)
            if session['stage_turn_count'] >= 4 and session['turn_count'] >= 10:
                if conversation_quality < 40:
                    return False
                elif session['turn_count'] >= self.config.MAX_TOTAL_TURNS:
                    return False
        
        if session['turn_count'] >= self.config.MAX_TOTAL_TURNS:
            return False
        
        return True
    
    def _get_hangup_response(self, current_stage: str, evaluation: Dict) -> str:
        """Get appropriate hangup response"""
        hangup_responses = {
            'opener_evaluation': ["Not interested. Don't call here again.", "Please remove this number from your list."],
            'objection_handling': ["I already told you I'm not interested.", "You're not listening. Goodbye."],
            'early_objection': ["Not interested. Goodbye.", "Don't call here again."],
            'default': ["I have to go. Goodbye.", "Not interested. Thanks."]
        }
        
        responses = hangup_responses.get(current_stage, hangup_responses['default'])
        return random.choice(responses)
    
    def _handle_silence_trigger(self, session: Dict, trigger: str) -> Dict[str, Any]:
        """Handle silence triggers"""
        if trigger == '[SILENCE_IMPATIENCE]':
            impatience_phrases = [
                "Hello? Are you still with me?", 
                "Can you hear me?",
                "Just checking you're there…", 
                "Still on the line?",
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
    
    def _generate_coaching(self, session: Dict) -> Dict[str, Any]:
        """Generate coaching feedback"""
        try:
            if self.is_openai_available():
                return self.openai_service.generate_coaching_feedback(
                    session['conversation_history'],
                    session.get('rubric_scores', {}),
                    session['user_context']
                )
            else:
                return self._basic_coaching(session)
                
        except Exception as e:
            logger.error(f"Coaching generation error: {e}")
            return self._basic_coaching(session)
    
    def _basic_coaching(self, session: Dict) -> Dict[str, Any]:
        """Basic coaching fallback"""
        conversation_quality = session.get('conversation_quality', 50)
        stages_completed = len(session.get('stages_completed', []))
        
        base_score = int(conversation_quality)
        stage_bonus = stages_completed * 10
        turns = session.get('turn_count', 0)
        length_bonus = min(20, turns * 2)
        
        total_score = min(100, max(30, base_score + stage_bonus + length_bonus))
        
        coaching = {
            'sales_coaching': 'Practice your opener with empathy and confidence.',
            'grammar_coaching': 'Use contractions to sound more natural.',
            'vocabulary_coaching': 'Use simple, outcome-focused language.',
            'pronunciation_coaching': 'Speak clearly and at a moderate pace.',
            'rapport_assertiveness': 'Show empathy first, then be confident.'
        }
        
        return {
            'success': True,
            'coaching': coaching,
            'score': total_score,
            'source': 'basic'
        }
    
    def _calculate_session_success(self, session: Dict) -> bool:
        """Calculate if session was successful"""
        conversation_quality = session.get('conversation_quality', 0)
        stages_completed = session.get('stages_completed', [])
        total_turns = session.get('turn_count', 0)
        
        reached_pitch = 'mini_pitch' in stages_completed or session.get('current_stage') in ['mini_pitch', 'soft_discovery', 'extended_conversation']
        sufficient_length = total_turns >= 4
        decent_quality = conversation_quality >= 40
        completed_most_stages = len(stages_completed) >= 3
        
        return reached_pitch and sufficient_length and (decent_quality or completed_most_stages)
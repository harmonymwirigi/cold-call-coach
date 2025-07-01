# ===== FIXED: services/roleplay/roleplay_1_2.py =====
# Marathon Mode with proper conversation flow adapted from successful Roleplay 1.1

import random
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from .base_roleplay import BaseRoleplay
from .configs.roleplay_1_2_config import Roleplay12Config
from utils.constants import EARLY_OBJECTIONS, SUCCESS_MESSAGES, IMPATIENCE_PHRASES

logger = logging.getLogger(__name__)

class Roleplay12(BaseRoleplay):
    """
    Roleplay 1.2 - Marathon Mode
    10 calls, need 6 to pass. Uses enhanced conversation flow from Roleplay 1.1
    """
    
    def __init__(self, openai_service=None):
        super().__init__(openai_service)
        self.config = Roleplay12Config()
        self.roleplay_id = self.config.ROLEPLAY_ID

    def get_roleplay_info(self) -> Dict[str, Any]:
        return {
            'id': self.config.ROLEPLAY_ID,
            'name': self.config.NAME,
            'description': self.config.DESCRIPTION,
            'type': 'marathon',
            'total_calls': self.config.TOTAL_CALLS,
            'calls_to_pass': self.config.CALLS_TO_PASS,
            'features': {
                'ai_evaluation': self.is_openai_available(),
                'marathon_mode': True,
                'natural_conversation': True,
                'detailed_coaching': True
            }
        }

    def create_session(self, user_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Creates a Marathon session with enhanced conversation tracking"""
        session_id = f"{user_id}_{self.config.ROLEPLAY_ID}_{mode}_{int(datetime.now().timestamp())}"
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'roleplay_id': self.config.ROLEPLAY_ID,
            'mode': 'marathon',
            'started_at': datetime.now(timezone.utc).isoformat(),
            'user_context': user_context,
            'session_active': True,
            
            # Marathon state
            'marathon_state': {
                'current_call_number': 1,
                'calls_passed': 0,
                'calls_failed': 0
            },
            'all_calls_data': [],
            'used_objections': set(),
            
            # Current call state (adapted from Roleplay 1.1)
            'conversation_history': [],
            'current_stage': 'phone_pickup',
            'hang_up_triggered': False,
            'turn_count': 0,
            'stage_turn_count': 0,
            'stages_completed': [],
            'conversation_quality': 0,
            'rubric_scores': {},
            'stage_progression': ['phone_pickup'],
            'overall_call_result': 'in_progress',
            
            # Enhanced conversation tracking
            'prospect_warmth': 0,
            'empathy_shown': False,
            'specific_benefits_mentioned': False,
            'conversation_flow_score': 0,
            'last_evaluation': None,
            'cumulative_score': 0,
            'minimum_turns_completed': False,
            'valid_opener_received': False,
            'conversation_started': False,
            'attempts_count': 0
        }
        
        self.active_sessions[session_id] = session_data
        
        initial_response = self._get_contextual_initial_response(user_context)
        session_data['conversation_history'].append({
            'role': 'assistant',
            'content': initial_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'phone_pickup',
            'call_number': 1
        })
        
        logger.info(f"Marathon session {session_id} created for user {user_id}")
        return {
            'success': True,
            'session_id': session_id,
            'initial_response': initial_response,
            'roleplay_info': self.get_roleplay_info(),
            'marathon_status': session_data['marathon_state']
        }

    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Enhanced user input processing adapted from Roleplay 1.1"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            
            if not session.get('session_active'):
                raise ValueError("Session not active")
            
            # Handle special silence triggers
            if user_input in ['[SILENCE_IMPATIENCE]', '[SILENCE_HANGUP]']:
                return self._handle_silence_trigger(session, user_input)
            
            # Increment counters
            session['turn_count'] += 1
            session['stage_turn_count'] += 1
            session['attempts_count'] += 1
            
            # Add user input to conversation
            session['conversation_history'].append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage'],
                'call_number': session['marathon_state']['current_call_number']
            })
            
            logger.info(f"Marathon Call #{session['marathon_state']['current_call_number']} Turn #{session['turn_count']}: Processing '{user_input[:50]}...'")
            
            # FIXED: Enhanced evaluation
            evaluation_stage = self._get_evaluation_stage(session['current_stage'])
            evaluation = self._evaluate_user_input_enhanced(session, user_input, evaluation_stage)
            
            # Store evaluation
            session['last_evaluation'] = evaluation
            
            # Update conversation metrics
            self._update_conversation_metrics(session, evaluation)
            
            # Validate conversation progress
            self._validate_conversation_progress(session, user_input, evaluation)
            
            # Check if should hang up (very lenient for marathon)
            should_hang_up = self._should_hang_up_marathon(session, evaluation, user_input)
            
            if should_hang_up:
                ai_response = self._get_contextual_hangup_response(session, evaluation)
                return self._handle_call_failure(session, "Call ended by prospect")
            
            # Generate AI response
            ai_response = self._generate_contextual_ai_response(session, user_input, evaluation)
            
            # Update session state
            self._update_session_state_marathon(session, evaluation)
            
            # Check if call should continue
            call_continues = self._should_call_continue_marathon(session, evaluation)
            
            # Add AI response to conversation
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage'],
                'call_number': session['marathon_state']['current_call_number'],
                'evaluation': evaluation,
                'prospect_warmth': session.get('prospect_warmth', 0)
            })
            
            if not call_continues:
                # Check if this call passed or failed
                if self._did_call_pass(session):
                    return self._handle_call_success(session)
                else:
                    return self._handle_call_failure(session, "Call did not meet pass criteria")
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': call_continues,
                'evaluation': evaluation,
                'session_state': session['current_stage'],
                'turn_count': session['turn_count'],
                'marathon_status': session['marathon_state'],
                'conversation_quality': session['conversation_quality'],
                'prospect_warmth': session.get('prospect_warmth', 0)
            }
            
        except Exception as e:
            logger.error(f"Error processing Marathon input: {e}")
            return {'success': False, 'error': str(e), 'call_continues': False}

    def _evaluate_user_input_enhanced(self, session: Dict, user_input: str, evaluation_stage: str) -> Dict[str, Any]:
        """Enhanced evaluation adapted from Roleplay 1.1"""
        try:
            if self.is_openai_available():
                evaluation = self.openai_service.evaluate_user_input(
                    user_input,
                    session['conversation_history'],
                    evaluation_stage
                )
                
                # Apply weighted scoring
                evaluation = self._apply_weighted_scoring(evaluation, evaluation_stage)
                
                # Store in session rubric scores
                session['rubric_scores'][evaluation_stage] = {
                    'score': evaluation.get('score', 0),
                    'weighted_score': evaluation.get('weighted_score', 0),
                    'passed': evaluation.get('passed', False),
                    'criteria_met': evaluation.get('criteria_met', [])
                }
                
                return evaluation
            else:
                return self._enhanced_basic_evaluation(user_input, evaluation_stage, session)
                
        except Exception as e:
            logger.error(f"Enhanced evaluation error: {e}")
            return self._enhanced_basic_evaluation(user_input, evaluation_stage, session)

    def _enhanced_basic_evaluation(self, user_input: str, evaluation_stage: str, session: Dict) -> Dict[str, Any]:
        """Enhanced basic evaluation for Marathon mode"""
        score = 0
        weighted_score = 0
        criteria_met = []
        user_input_lower = user_input.lower().strip()
        turn_count = session.get('turn_count', 1)
        
        # Marathon mode is more forgiving to encourage completion
        word_count = len(user_input.split())
        
        # Give credit for effort
        if word_count >= 1:
            score += 1.0  # Base effort bonus
        if word_count >= 3:
            score += 1.0  # Meaningful attempt bonus
        if word_count >= 5:
            score += 1.0  # Good length bonus
        
        # Marathon-specific generous scoring
        if turn_count <= 3:
            score = max(score, 2.0)  # Minimum score for early attempts
            weighted_score = max(score, 2.0)
        
        # Check for basic communication patterns
        if any(word in user_input_lower for word in ['hello', 'hi', 'good', 'morning', 'calling', 'help']):
            score += 1.0
            criteria_met.append('basic_communication')
        
        # Check for questions
        if '?' in user_input or any(q in user_input_lower for q in ['can i', 'may i', 'would you']):
            score += 1.0
            criteria_met.append('asks_question')
        
        # Final score calculation
        final_score = min(4, max(1, score))
        
        # Pass threshold is lower for marathon (encourage completion)
        threshold = 2.0  # Lower than practice mode
        passed = final_score >= threshold
        
        logger.info(f"Marathon evaluation: score={final_score:.1f}, passed={passed}, criteria={len(criteria_met)}")
        
        return {
            'score': int(final_score),
            'weighted_score': round(final_score, 1),
            'passed': passed,
            'criteria_met': criteria_met,
            'feedback': f'Marathon evaluation: {len(criteria_met)} criteria met',
            'should_continue': True,
            'next_action': 'continue',
            'hang_up_probability': 0.0,
            'source': 'marathon_basic',
            'stage': evaluation_stage
        }

    def _should_hang_up_marathon(self, session: Dict, evaluation: Dict, user_input: str) -> bool:
        """Marathon hang-up logic - much more lenient than practice mode"""
        turn_count = session.get('turn_count', 1)
        
        # NEVER hang up in first 5 turns for marathon
        if turn_count <= 5:
            return False
        
        # Very rare hang-ups in marathon mode
        weighted_score = evaluation.get('weighted_score', evaluation.get('score', 2))
        conversation_quality = session.get('conversation_quality', 0)
        
        # Only hang up in extreme cases
        if turn_count >= 8 and weighted_score <= 0.5 and conversation_quality < 10:
            # Even then, only 10% chance
            return random.random() < 0.1
        
        return False

    def _should_call_continue_marathon(self, session: Dict, evaluation: Dict) -> bool:
        """Marathon call continuation logic - encourages longer conversations"""
        if session.get('hang_up_triggered'):
            return False
        
        if session['current_stage'] == 'call_ended':
            return False
        
        # Marathon allows longer conversations
        max_turns = 15  # Increased from practice mode
        if session['turn_count'] >= max_turns:
            logger.info(f"Marathon call ending: reached maximum turns ({max_turns})")
            return False
        
        # Continue for at least 4 turns
        if session['turn_count'] < 4:
            return True
        
        # Natural progression through stages
        stages_completed = len(session.get('stages_completed', []))
        if stages_completed < 3:  # Need reasonable progression
            return True
        
        # End after good progression
        conversation_quality = session.get('conversation_quality', 0)
        if stages_completed >= 3 and conversation_quality >= 30:
            logger.info(f"Marathon call ending: good progression and quality")
            return False
        
        return True

    def _update_session_state_marathon(self, session: Dict, evaluation: Dict):
        """Update session state for marathon mode"""
        current_stage = session['current_stage']
        should_progress = False
        
        # Marathon progression is more lenient
        if current_stage == 'phone_pickup':
            should_progress = True
        elif current_stage == 'opener_evaluation':
            score = evaluation.get('weighted_score', evaluation.get('score', 0))
            if score >= 1.0 or session['stage_turn_count'] >= 2:
                should_progress = True
        elif current_stage == 'early_objection':
            should_progress = True
        elif current_stage == 'objection_handling':
            score = evaluation.get('weighted_score', evaluation.get('score', 0))
            if score >= 1.0 or session['stage_turn_count'] >= 2:
                should_progress = True
        elif current_stage == 'mini_pitch':
            score = evaluation.get('weighted_score', evaluation.get('score', 0))
            if score >= 1.0 or session['stage_turn_count'] >= 2:
                should_progress = True
        
        if should_progress:
            next_stage = self.config.STAGE_FLOW.get(current_stage)
            if next_stage and next_stage != current_stage:
                if current_stage not in session.get('stages_completed', []):
                    session.setdefault('stages_completed', []).append(current_stage)
                
                session['current_stage'] = next_stage
                session['stage_progression'].append(next_stage)
                session['stage_turn_count'] = 0
                
                logger.info(f"Marathon Call #{session['marathon_state']['current_call_number']}: Progressed from {current_stage} to {next_stage}")

    def _did_call_pass(self, session: Dict) -> bool:
        """Determine if the current call passed - marathon criteria"""
        stages_completed = len(session.get('stages_completed', []))
        conversation_quality = session.get('conversation_quality', 0)
        turn_count = session.get('turn_count', 0)
        
        # Marathon pass criteria (more lenient)
        if turn_count >= 4 and stages_completed >= 2 and conversation_quality >= 25:
            return True
        
        if stages_completed >= 3:  # Good stage progression
            return True
        
        return False

    def _handle_call_success(self, session: Dict) -> Dict[str, Any]:
        """Handle successful call completion"""
        session['marathon_state']['calls_passed'] += 1
        session['overall_call_result'] = 'passed'
        
        logger.info(f"Call #{session['marathon_state']['current_call_number']} PASSED")
        return self._start_next_call(session, "Call passed! Great job.")

    def _handle_call_failure(self, session: Dict, reason: str) -> Dict[str, Any]:
        """Handle failed call"""
        session['marathon_state']['calls_failed'] += 1
        session['overall_call_result'] = 'failed'
        
        logger.info(f"Call #{session['marathon_state']['current_call_number']} FAILED: {reason}")
        return self._start_next_call(session, f"Call ended. {reason}")

    def _start_next_call(self, session: Dict, transition_message: str) -> Dict[str, Any]:
        """Start the next call in the marathon"""
        # Store current call data
        session['all_calls_data'].append({
            'call_number': session['marathon_state']['current_call_number'],
            'conversation_history': session['conversation_history'].copy(),
            'stages_completed': session.get('stages_completed', []).copy(),
            'result': session['overall_call_result'],
            'conversation_quality': session.get('conversation_quality', 0),
            'turn_count': session.get('turn_count', 0)
        })
        
        marathon = session['marathon_state']
        total_calls_completed = marathon['calls_passed'] + marathon['calls_failed']
        
        # Check if marathon is complete
        if total_calls_completed >= self.config.TOTAL_CALLS:
            return self.end_session(session['session_id'])
        
        # Start next call
        marathon['current_call_number'] += 1
        
        # Reset call-specific data
        session['conversation_history'] = []
        session['current_stage'] = 'phone_pickup'
        session['hang_up_triggered'] = False
        session['turn_count'] = 0
        session['stage_turn_count'] = 0
        session['stages_completed'] = []
        session['conversation_quality'] = 0
        session['rubric_scores'] = {}
        session['stage_progression'] = ['phone_pickup']
        session['overall_call_result'] = 'in_progress'
        session['prospect_warmth'] = 0
        session['empathy_shown'] = False
        session['specific_benefits_mentioned'] = False
        session['conversation_flow_score'] = 0
        session['minimum_turns_completed'] = False
        session['valid_opener_received'] = False
        session['conversation_started'] = False
        session['attempts_count'] = 0
        
        # Generate new initial response
        initial_response = self._get_contextual_initial_response(session['user_context'])
        session['conversation_history'].append({
            'role': 'assistant',
            'content': initial_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'phone_pickup',
            'call_number': marathon['current_call_number']
        })
        
        return {
            'success': True,
            'ai_response': initial_response,
            'call_continues': True,
            'marathon_status': marathon,
            'new_call_started': True,
            'transition_message': transition_message
        }

    def _get_unique_objection(self, session: Dict) -> str:
        """Get a unique objection for this marathon run"""
        available = [obj for obj in EARLY_OBJECTIONS if obj not in session['used_objections']]
        if not available:
            session['used_objections'].clear()
            available = EARLY_OBJECTIONS
        
        objection = random.choice(available)
        session['used_objections'].add(objection)
        return objection

    def _generate_contextual_ai_response(self, session: Dict, user_input: str, evaluation: Dict) -> str:
        """Generate contextual AI response for marathon mode"""
        try:
            if self.is_openai_available():
                enhanced_context = {
                    **session['user_context'],
                    'prospect_warmth': session.get('prospect_warmth', 0),
                    'conversation_quality': session.get('conversation_quality', 0),
                    'stage_performance': evaluation,
                    'turn_count': session.get('turn_count', 1),
                    'call_number': session['marathon_state']['current_call_number'],
                    'marathon_mode': True
                }
                
                response_result = self.openai_service.generate_roleplay_response(
                    user_input,
                    session['conversation_history'],
                    enhanced_context,
                    session['current_stage']
                )
                
                if response_result.get('success'):
                    return response_result['response']
            
            return self._get_marathon_fallback_response(session, evaluation, user_input)
            
        except Exception as e:
            logger.error(f"Error generating marathon AI response: {e}")
            return self._get_marathon_fallback_response(session, evaluation, user_input)

    def _get_marathon_fallback_response(self, session: Dict, evaluation: Dict, user_input: str) -> str:
        """Marathon-specific fallback responses"""
        current_stage = session['current_stage']
        turn_count = session.get('turn_count', 1)
        word_count = len(user_input.split())
        
        # Very encouraging responses for marathon mode
        if turn_count <= 2:
            return random.choice([
                "Hello, yes?",
                "Good morning.",
                "What can I do for you?",
                "Hi there.",
                "Yes, this is Alex."
            ])
        
        # Stage-based responses
        if current_stage == 'opener_evaluation':
            if word_count >= 5:
                return random.choice([
                    "Okay, what's this about?",
                    "I'm listening.",
                    "Go ahead.",
                    "What do you need?"
                ])
            else:
                return random.choice([
                    "What's this regarding?",
                    "I'm busy.",
                    "Make it quick."
                ])
        
        elif current_stage in ['early_objection', 'objection_handling']:
            if current_stage == 'early_objection':
                # Give an objection
                return self._get_unique_objection(session)
            else:
                return random.choice([
                    "Go ahead.",
                    "I'm listening.",
                    "Continue.",
                    "What do you mean?"
                ])
        
        elif current_stage == 'mini_pitch':
            return random.choice([
                "Tell me more.",
                "That sounds interesting.",
                "How does that work?",
                "I'm following."
            ])
        
        return random.choice([
            "I see.",
            "Continue.",
            "Go on.",
            "That's interesting."
        ])

    def _handle_silence_trigger(self, session: Dict, trigger: str) -> Dict[str, Any]:
        """Handle silence triggers for marathon mode"""
        if trigger == '[SILENCE_IMPATIENCE]':
            return {
                'success': True,
                'ai_response': random.choice(IMPATIENCE_PHRASES),
                'call_continues': True,
                'marathon_status': session['marathon_state']
            }
        elif trigger == '[SILENCE_HANGUP]':
            return self._handle_call_failure(session, "Hung up due to silence")

    def _update_conversation_metrics(self, session: Dict, evaluation: Dict):
        """Update conversation metrics for marathon mode"""
        try:
            # Update cumulative score
            weighted_score = evaluation.get('weighted_score', evaluation.get('score', 0))
            session['cumulative_score'] += weighted_score
            
            # Update conversation quality (more generous for marathon)
            turn_quality = (weighted_score / 4) * 100
            total_turns = session['turn_count']
            current_quality = session.get('conversation_quality', 0)
            
            if total_turns == 1:
                session['conversation_quality'] = max(turn_quality, 30)  # Higher minimum
            else:
                new_quality = ((current_quality * (total_turns - 1)) + turn_quality) / total_turns
                session['conversation_quality'] = max(new_quality, current_quality * 0.9)  # Less harsh drops
            
            # Track empathy and benefits
            criteria_met = evaluation.get('criteria_met', [])
            if 'shows_empathy' in criteria_met:
                session['empathy_shown'] = True
            if 'specific_benefit' in criteria_met:
                session['specific_benefits_mentioned'] = True
            
            # Update prospect warmth (more generous in marathon)
            if evaluation.get('passed', False):
                session['prospect_warmth'] = min(10, session.get('prospect_warmth', 0) + 2.0)
            elif weighted_score >= 2:
                session['prospect_warmth'] = min(10, session.get('prospect_warmth', 0) + 1.0)
            
        except Exception as e:
            logger.error(f"Error updating marathon conversation metrics: {e}")

    def _validate_conversation_progress(self, session: Dict, user_input: str, evaluation: Dict):
        """Validate conversation progress for marathon mode"""
        turn_count = session['turn_count']
        
        # Mark conversation as started after first turn
        if turn_count >= 1:
            session['conversation_started'] = True
        
        # Marathon is more forgiving about minimum turns
        if turn_count >= 4:  # Lower than practice mode
            session['minimum_turns_completed'] = True
        
        # Check for valid opener (very lenient)
        if turn_count == 1 and len(user_input.split()) >= 1:
            session['valid_opener_received'] = True

    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End marathon session with proper results"""
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
            
            marathon = session['marathon_state']
            passed_marathon = marathon['calls_passed'] >= self.config.CALLS_TO_PASS
            
            # Calculate overall score
            total_calls = marathon['calls_passed'] + marathon['calls_failed']
            if total_calls > 0:
                overall_score = int((marathon['calls_passed'] / total_calls) * 100)
            else:
                overall_score = 0
            
            # Generate coaching
            coaching_result = self._generate_comprehensive_coaching(session)
            
            # Prepare success message
            if passed_marathon:
                completion_message = f"Excellent! You passed {marathon['calls_passed']} out of {total_calls} calls. Marathon completed!"
            else:
                completion_message = f"You completed {total_calls} calls and passed {marathon['calls_passed']}. Keep practicing!"
            
            result = {
                'success': True,
                'duration_minutes': duration_minutes,
                'session_success': passed_marathon,
                'coaching': coaching_result.get('coaching', {'overall': completion_message}),
                'overall_score': overall_score,
                'session_data': session,
                'roleplay_type': 'marathon',
                'marathon_results': {
                    'calls_passed': marathon['calls_passed'],
                    'calls_failed': marathon['calls_failed'],
                    'total_calls': total_calls,
                    'marathon_passed': passed_marathon,
                    'pass_rate': (marathon['calls_passed'] / max(total_calls, 1)) * 100
                }
            }
            
            # Clean up session
            del self.active_sessions[session_id]
            
            logger.info(f"Marathon session {session_id} ended. Passed: {passed_marathon}, Score: {overall_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error ending Marathon session: {e}")
            return {'success': False, 'error': str(e)}

    def _get_evaluation_stage(self, current_stage: str) -> str:
        """Map current stage to evaluation stage"""
        stage_mapping = {
            'phone_pickup': 'opener',
            'opener_evaluation': 'opener',
            'early_objection': 'objection_handling',
            'objection_handling': 'objection_handling',
            'mini_pitch': 'mini_pitch'
        }
        return stage_mapping.get(current_stage, 'opener')
# ===== services/roleplay/roleplay_1_2.py =====

import random
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Set
from .base_roleplay import BaseRoleplay
from .configs.roleplay_1_2_config import Roleplay12Config

logger = logging.getLogger(__name__)

class Roleplay12(BaseRoleplay):
    """Roleplay 1.2 - Marathon Mode: 10 calls, need 6 to pass"""
    
    def __init__(self, openai_service=None):
        super().__init__(openai_service)
        self.config = Roleplay12Config()
        
    def get_roleplay_info(self) -> Dict[str, Any]:
        """Return Roleplay 1.2 configuration"""
        return {
            'id': self.config.ROLEPLAY_ID,
            'name': self.config.NAME,
            'description': self.config.DESCRIPTION,
            'type': 'marathon',
            'total_calls': self.config.TOTAL_CALLS,
            'calls_to_pass': self.config.CALLS_TO_PASS,
            'features': {
                'ai_evaluation': True,
                'multiple_calls': True,
                'random_hangups': True,
                'no_in_call_feedback': True,
                'aggregated_coaching': True,
                'objection_variety': True
            },
            'stages': list(self.config.STAGE_FLOW.keys()),
            'objection_count': len(self.config.EARLY_OBJECTIONS)
        }
    
    def create_session(self, user_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create new Marathon session"""
        try:
            session_id = f"{user_id}_{self.config.ROLEPLAY_ID}_{mode}_{int(datetime.now().timestamp())}"
            
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'roleplay_id': self.config.ROLEPLAY_ID,
                'mode': mode,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'user_context': user_context,
                'session_active': True,
                
                # Marathon specific fields
                'marathon_state': {
                    'current_call': 1,
                    'total_calls': self.config.TOTAL_CALLS,
                    'calls_passed': 0,
                    'calls_failed': 0,
                    'calls_to_pass': self.config.CALLS_TO_PASS,
                    'is_complete': False,
                    'is_passed': False
                },
                
                # Current call state
                'current_call_data': self._initialize_call_data(),
                
                # Marathon tracking
                'all_calls_data': [],  # Store data from completed calls
                'used_objections': set(),  # Track used objections
                'overall_performance': {
                    'total_interactions': 0,
                    'successful_stages': 0,
                    'rubric_scores_aggregate': {}
                }
            }
            
            # Store session
            self.active_sessions[session_id] = session_data
            
            # Generate initial response for first call
            initial_response = self._get_initial_response(user_context)
            
            # Add to current call conversation
            session_data['current_call_data']['conversation_history'].append({
                'role': 'assistant',
                'content': initial_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': 'phone_pickup'
            })
            
            logger.info(f"Created Marathon session {session_id} - Call 1/{self.config.TOTAL_CALLS}")
            
            return {
                'success': True,
                'session_id': session_id,
                'initial_response': initial_response,
                'roleplay_info': self.get_roleplay_info(),
                'marathon_status': self._get_marathon_status(session_data)
            }
            
        except Exception as e:
            logger.error(f"Error creating Marathon session: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input for Marathon mode"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            
            if not session.get('session_active'):
                raise ValueError("Session not active")
            
            # Check if marathon is complete
            if session['marathon_state']['is_complete']:
                return {
                    'success': True,
                    'ai_response': "Marathon complete! Check your results.",
                    'call_continues': False,
                    'marathon_complete': True,
                    'marathon_status': self._get_marathon_status(session)
                }
            
            # Handle silence triggers
            if user_input in ['[SILENCE_IMPATIENCE]', '[SILENCE_HANGUP]']:
                return self._handle_silence_trigger(session, user_input)
            
            current_call = session['current_call_data']
            
            # Increment counters
            current_call['turn_count'] += 1
            current_call['stage_turn_count'] += 1
            session['overall_performance']['total_interactions'] += 1
            
            # Add user input to conversation
            current_call['conversation_history'].append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': current_call['current_stage']
            })
            
            # Evaluate user input
            evaluation_stage = self._get_evaluation_stage(current_call['current_stage'])
            evaluation = self._evaluate_user_input(session, user_input, evaluation_stage)
            
            # Check for random hangup (Marathon specific)
            if self._should_random_hangup(current_call, evaluation):
                logger.info("Random hangup triggered in Marathon mode")
                return self._handle_random_hangup(session)
            
            # Check if should hang up based on performance
            should_hang_up = self._should_hang_up_now(session, evaluation, user_input)
            
            if should_hang_up:
                logger.info("Performance-based hangup in Marathon mode")
                return self._handle_call_failure(session, evaluation, "performance")
            
            # Generate AI response
            ai_response = self._generate_ai_response(session, user_input, evaluation)
            
            # Update session state
            self._update_session_state(session, evaluation)
            
            # Check if current call should end (success)
            call_should_end = self._should_current_call_end(session, evaluation)
            
            if call_should_end:
                return self._handle_call_success(session, ai_response, evaluation)
            
            # Add AI response to conversation
            current_call['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': current_call['current_stage'],
                'evaluation': evaluation
            })
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': True,
                'evaluation': evaluation,
                'session_state': current_call['current_stage'],
                'marathon_status': self._get_marathon_status(session),
                'current_call': session['marathon_state']['current_call'],
                'total_calls': session['marathon_state']['total_calls']
            }
            
        except Exception as e:
            logger.error(f"Error processing Marathon input: {e}")
            return {'success': False, 'error': str(e), 'call_continues': False}
    
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End Marathon session and generate aggregated coaching"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            session['session_active'] = False
            session['ended_at'] = datetime.now(timezone.utc).isoformat()
            
            # If current call is not complete, mark it as failed
            if not session['marathon_state']['is_complete']:
                current_call = session['current_call_data']
                if current_call and current_call.get('call_status') == 'in_progress':
                    current_call['call_status'] = 'failed'
                    current_call['end_reason'] = 'forced_end' if forced_end else 'incomplete'
                    session['all_calls_data'].append(current_call)
                    session['marathon_state']['calls_failed'] += 1
                
                # Mark marathon as complete
                session['marathon_state']['is_complete'] = True
                session['marathon_state']['is_passed'] = (
                    session['marathon_state']['calls_passed'] >= session['marathon_state']['calls_to_pass']
                )
            
            # Calculate duration
            started_at = datetime.fromisoformat(session['started_at'].replace('Z', '+00:00'))
            ended_at = datetime.now(timezone.utc)
            duration_minutes = max(1, int((ended_at - started_at).total_seconds() / 60))
            
            # Generate aggregated coaching
            coaching_result = self._generate_marathon_coaching(session)
            
            # Calculate overall success
            marathon_success = session['marathon_state']['is_passed']
            
            result = {
                'success': True,
                'duration_minutes': duration_minutes,
                'session_success': marathon_success,
                'coaching': coaching_result.get('coaching', {}),
                'overall_score': coaching_result.get('score', 50),
                'session_data': session,
                'roleplay_type': 'marathon',
                'marathon_results': {
                    'calls_passed': session['marathon_state']['calls_passed'],
                    'calls_failed': session['marathon_state']['calls_failed'],
                    'total_calls': len(session['all_calls_data']),
                    'target_calls': session['marathon_state']['calls_to_pass'],
                    'passed': marathon_success
                }
            }
            
            # Clean up session
            del self.active_sessions[session_id]
            
            return result
            
        except Exception as e:
            logger.error(f"Error ending Marathon session: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current Marathon session status"""
        session = self.active_sessions.get(session_id)
        if session:
            current_call = session.get('current_call_data', {})
            return {
                'session_active': session.get('session_active', False),
                'current_stage': current_call.get('current_stage', 'unknown'),
                'current_call': session['marathon_state']['current_call'],
                'total_calls': session['marathon_state']['total_calls'],
                'calls_passed': session['marathon_state']['calls_passed'],
                'calls_failed': session['marathon_state']['calls_failed'],
                'calls_to_pass': session['marathon_state']['calls_to_pass'],
                'is_complete': session['marathon_state']['is_complete'],
                'conversation_length': len(current_call.get('conversation_history', [])),
                'roleplay_type': 'marathon',
                'openai_available': self.is_openai_available()
            }
        return None
    
    # ===== PRIVATE METHODS =====
    
    def _initialize_call_data(self) -> Dict[str, Any]:
        """Initialize data for a new call"""
        return {
            'conversation_history': [],
            'current_stage': 'phone_pickup',
            'turn_count': 0,
            'stage_turn_count': 0,
            'call_status': 'in_progress',  # in_progress, passed, failed
            'end_reason': None,  # success, hangup_random, hangup_performance, silence, etc.
            'stages_completed': [],
            'rubric_scores': {},
            'started_at': datetime.now(timezone.utc).isoformat()
        }
    
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
    
    def _get_marathon_status(self, session: Dict) -> Dict[str, Any]:
        """Get current marathon status"""
        marathon_state = session['marathon_state']
        return {
            'current_call': marathon_state['current_call'],
            'total_calls': marathon_state['total_calls'],
            'calls_passed': marathon_state['calls_passed'],
            'calls_failed': marathon_state['calls_failed'],
            'calls_to_pass': marathon_state['calls_to_pass'],
            'is_complete': marathon_state['is_complete'],
            'is_passed': marathon_state['is_passed'],
            'calls_remaining': marathon_state['total_calls'] - len(session['all_calls_data']),
            'progress_percentage': (len(session['all_calls_data']) / marathon_state['total_calls']) * 100
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
        """Evaluate user input using OpenAI or fallback"""
        try:
            if self.is_openai_available():
                evaluation = self.openai_service.evaluate_user_input(
                    user_input,
                    session['current_call_data']['conversation_history'],
                    evaluation_stage
                )
                
                # Store in current call rubric scores
                session['current_call_data']['rubric_scores'][evaluation_stage] = {
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
        """Basic evaluation fallback - same as Roleplay 1.1"""
        score = 0
        criteria_met = []
        user_input_lower = user_input.lower().strip()
        
        # Use same evaluation logic as Roleplay 1.1
        if evaluation_stage == "opener":
            if len(user_input.strip()) > 15:
                score += 1
                criteria_met.append('substantial_opener')
            
            if any(phrase in user_input_lower for phrase in ["i'm calling", "calling from"]):
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
            'hang_up_probability': 0.4 if score <= 1 else 0.2,
            'source': 'basic',
            'stage': evaluation_stage
        }
    
    def _should_random_hangup(self, current_call: Dict, evaluation: Dict) -> bool:
        """Check if random hangup should occur (Marathon specific)"""
        # Only in opener_evaluation stage and only if opener passed
        if (current_call['current_stage'] == 'opener_evaluation' and 
            evaluation.get('passed', False)):
            
            return random.random() < self.config.RANDOM_HANGUP_CHANCE
        
        return False
    
    def _should_hang_up_now(self, session: Dict, evaluation: Dict, user_input: str) -> bool:
        """Determine if prospect should hang up based on performance"""
        current_call = session['current_call_data']
        
        # Never hang up on first interaction
        if current_call['turn_count'] <= 1:
            return False
        
        # Get hang up probability from evaluation
        hang_up_prob = evaluation.get('hang_up_probability', 0.1)
        
        # Marathon mode is less forgiving than Practice mode
        score = evaluation.get('score', 0)
        current_stage = current_call['current_stage']
        
        if current_stage == 'opener_evaluation':
            if score <= 1:
                hang_up_prob = 0.6  # Higher than Practice mode
            elif score == 2:
                hang_up_prob = 0.3
            else:
                hang_up_prob = 0.05
        elif current_stage in ['objection_handling']:
            if not evaluation.get('passed', True):
                hang_up_prob = 0.5  # Higher than Practice mode
        
        return random.random() < hang_up_prob
    
    def _generate_ai_response(self, session: Dict, user_input: str, evaluation: Dict) -> str:
        """Generate AI prospect response"""
        try:
            if self.is_openai_available():
                response_result = self.openai_service.generate_roleplay_response(
                    user_input,
                    session['current_call_data']['conversation_history'],
                    session['user_context'],
                    session['current_call_data']['current_stage']
                )
                
                if response_result.get('success'):
                    return response_result['response']
            
            # Fallback response
            return self._get_fallback_response(session, evaluation)
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._get_fallback_response(session, evaluation)
    
    def _get_fallback_response(self, session: Dict, evaluation: Dict) -> str:
        """Get fallback response for Marathon mode"""
        current_call = session['current_call_data']
        current_stage = current_call['current_stage']
        passed = evaluation.get('passed', False)
        
        if current_stage == 'early_objection':
            # Get unused objection
            used_objections = session.get('used_objections', set())
            available_objections = [obj for obj in self.config.EARLY_OBJECTIONS 
                                  if obj not in used_objections]
            
            if available_objections:
                objection = random.choice(available_objections)
                session['used_objections'].add(objection)
                return objection
            else:
                # All objections used, use a generic one
                return random.choice(self.config.EARLY_OBJECTIONS[:5])
        
        # For other stages, use similar logic as Roleplay 1.1
        responses_map = {
            'opener_evaluation': {
                True: ["Alright, what's this about?", "I'm listening. Go ahead."],
                False: ["What's this about?", "I'm not interested."]
            },
            'objection_handling': {
                True: ["Okay, you have 30 seconds.", "Go ahead."],
                False: ["I already told you I'm not interested.", "You're not listening."]
            },
            'mini_pitch': {
                True: ["That sounds interesting. Tell me more.", "How does that work?"],
                False: ["I don't understand.", "That's too vague."]
            },
            'soft_discovery': ["Send me some information.", "I'll think about it.", "That makes sense."]
        }
        
        stage_responses = responses_map.get(current_stage, ["I see."])
        
        if isinstance(stage_responses, dict):
            responses = stage_responses.get(passed, stage_responses.get(True, ["I see."]))
        else:
            responses = stage_responses
        
        return random.choice(responses)
    
    def _update_session_state(self, session: Dict, evaluation: Dict):
        """Update session state based on evaluation"""
        current_call = session['current_call_data']
        current_stage = current_call['current_stage']
        should_progress = False
        
        # Stage progression logic (simpler than Practice mode)
        if current_stage == 'phone_pickup':
            should_progress = True
        elif current_stage == 'opener_evaluation':
            if evaluation.get('passed', False):
                should_progress = True
        elif current_stage == 'early_objection':
            should_progress = True
        elif current_stage == 'objection_handling':
            if evaluation.get('passed', False):
                should_progress = True
        elif current_stage == 'mini_pitch':
            if evaluation.get('passed', False):
                should_progress = True
        
        if should_progress:
            next_stage = self.config.STAGE_FLOW.get(current_stage)
            if next_stage and next_stage != current_stage:
                # Mark current stage as completed
                if current_stage not in current_call.get('stages_completed', []):
                    current_call.setdefault('stages_completed', []).append(current_stage)
                    session['overall_performance']['successful_stages'] += 1
                
                current_call['current_stage'] = next_stage
                current_call['stage_turn_count'] = 0
    
    def _should_current_call_end(self, session: Dict, evaluation: Dict) -> bool:
        """Check if current call should end successfully"""
        current_call = session['current_call_data']
        
        # Call ends successfully when reaching soft_discovery stage with passed evaluation
        if (current_call['current_stage'] == 'soft_discovery' and 
            evaluation.get('passed', False)):
            return True
        
        return False
    
    def _handle_call_success(self, session: Dict, ai_response: str, evaluation: Dict) -> Dict[str, Any]:
        """Handle successful call completion"""
        current_call = session['current_call_data']
        marathon_state = session['marathon_state']
        
        # Mark call as successful
        current_call['call_status'] = 'passed'
        current_call['end_reason'] = 'success'
        current_call['ended_at'] = datetime.now(timezone.utc).isoformat()
        
        # Add final AI response
        current_call['conversation_history'].append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': current_call['current_stage'],
            'evaluation': evaluation
        })
        
        # Add positive response for successful completion
        success_response = random.choice([
            "That sounds interesting. Send me some information and let's schedule a follow-up.",
            "I'd like to learn more. Can you send me details?",
            "This could be relevant for us. Let's continue this conversation."
        ])
        
        current_call['conversation_history'].append({
            'role': 'assistant',
            'content': success_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'call_success',
            'final_response': True
        })
        
        # Update marathon state
        marathon_state['calls_passed'] += 1
        session['all_calls_data'].append(current_call)
        
        # Check if marathon is complete
        if marathon_state['current_call'] >= marathon_state['total_calls']:
            # Marathon complete
            marathon_state['is_complete'] = True
            marathon_state['is_passed'] = (
                marathon_state['calls_passed'] >= marathon_state['calls_to_pass']
            )
            
            return {
                'success': True,
                'ai_response': success_response,
                'call_continues': False,
                'call_result': 'passed',
                'marathon_complete': True,
                'marathon_passed': marathon_state['is_passed'],
                'marathon_status': self._get_marathon_status(session)
            }
        else:
            # Start next call
            return self._start_next_call(session, success_response)
    
    def _handle_call_failure(self, session: Dict, evaluation: Dict, reason: str) -> Dict[str, Any]:
        """Handle call failure"""
        current_call = session['current_call_data']
        marathon_state = session['marathon_state']
        
        # Mark call as failed
        current_call['call_status'] = 'failed'
        current_call['end_reason'] = reason
        current_call['ended_at'] = datetime.now(timezone.utc).isoformat()
        
        # Get hangup response
        hangup_response = self._get_hangup_response(current_call['current_stage'], evaluation)
        
        # Add hangup response
        current_call['conversation_history'].append({
            'role': 'assistant',
            'content': hangup_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': current_call['current_stage'],
            'hangup': True
        })
        
        # Update marathon state
        marathon_state['calls_failed'] += 1
        session['all_calls_data'].append(current_call)
        
        # Check if marathon is complete
        if marathon_state['current_call'] >= marathon_state['total_calls']:
            # Marathon complete
            marathon_state['is_complete'] = True
            marathon_state['is_passed'] = (
                marathon_state['calls_passed'] >= marathon_state['calls_to_pass']
            )
            
            return {
                'success': True,
                'ai_response': hangup_response,
                'call_continues': False,
                'call_result': 'failed',
                'marathon_complete': True,
                'marathon_passed': marathon_state['is_passed'],
                'marathon_status': self._get_marathon_status(session)
            }
        else:
            # Start next call
            return self._start_next_call(session, hangup_response)
    
    def _handle_random_hangup(self, session: Dict) -> Dict[str, Any]:
        """Handle random hangup in Marathon mode"""
        random_hangup_responses = [
            "Actually, I'm not interested. Goodbye.",
            "You know what, now is not a good time. Bye.",
            "I have to go. Don't call back.",
            "Not interested. Remove this number."
        ]
        
        hangup_response = random.choice(random_hangup_responses)
        
        return self._handle_call_failure(session, {'reason': 'random_hangup'}, 'random_hangup')
    
    def _start_next_call(self, session: Dict, previous_response: str) -> Dict[str, Any]:
        """Start the next call in marathon"""
        marathon_state = session['marathon_state']
        
        # Increment call number
        marathon_state['current_call'] += 1
        
        # Initialize new call data
        session['current_call_data'] = self._initialize_call_data()
        
        # Generate new initial response
        initial_response = self._get_initial_response(session['user_context'])
        
        # Add to new call conversation
        session['current_call_data']['conversation_history'].append({
            'role': 'assistant',
            'content': initial_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'phone_pickup'
        })
        
        logger.info(f"Started call {marathon_state['current_call']}/{marathon_state['total_calls']}")
        
        return {
            'success': True,
            'ai_response': initial_response,
            'call_continues': True,
            'call_result': 'next_call',
            'previous_call_response': previous_response,
            'marathon_status': self._get_marathon_status(session),
            'new_call_started': True
        }
    
    def _get_hangup_response(self, current_stage: str, evaluation: Dict) -> str:
        """Get appropriate hangup response"""
        hangup_responses = {
            'opener_evaluation': [
                "Not interested. Don't call here again.",
                "Please remove this number from your list.",
                "I'm hanging up now."
            ],
            'objection_handling': [
                "I already told you I'm not interested.",
                "You're not listening. Goodbye.",
                "This is exactly why I hate cold calls."
            ],
            'early_objection': [
                "Not interested. Goodbye.",
                "Don't call here again.",
                "Remove this number."
            ],
            'default': [
                "I have to go. Goodbye.",
                "Not interested. Thanks.",
                "Please don't call again."
            ]
        }
        
        responses = hangup_responses.get(current_stage, hangup_responses['default'])
        return random.choice(responses)
    
    def _handle_silence_trigger(self, session: Dict, trigger: str) -> Dict[str, Any]:
        """Handle silence triggers in Marathon mode"""
        if trigger == '[SILENCE_IMPATIENCE]':
            impatience_phrase = random.choice(self.config.IMPATIENCE_PHRASES)
            
            session['current_call_data']['conversation_history'].append({
                'role': 'assistant',
                'content': impatience_phrase,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'trigger': 'silence_impatience'
            })
            
            return {
                'success': True,
                'ai_response': impatience_phrase,
                'call_continues': True,
                'evaluation': {'trigger': 'impatience'}
            }
        
        elif trigger == '[SILENCE_HANGUP]':
            hangup_response = "I don't have time for this. Goodbye."
            return self._handle_call_failure(session, {'reason': 'silence'}, 'silence_hangup')
    
    def _generate_marathon_coaching(self, session: Dict) -> Dict[str, Any]:
        """Generate aggregated coaching for Marathon mode"""
        try:
            if self.is_openai_available():
                # Aggregate data from all calls
                all_conversations = []
                for call_data in session['all_calls_data']:
                    all_conversations.extend(call_data.get('conversation_history', []))
                
                # Aggregate rubric scores
                aggregated_scores = {}
                for call_data in session['all_calls_data']:
                    for stage, scores in call_data.get('rubric_scores', {}).items():
                        if stage not in aggregated_scores:
                            aggregated_scores[stage] = []
                        aggregated_scores[stage].append(scores)
                
                return self.openai_service.generate_coaching_feedback(
                    all_conversations,
                    aggregated_scores,
                    session['user_context']
                )
            else:
                return self._basic_marathon_coaching(session)
                
        except Exception as e:
            logger.error(f"Marathon coaching generation error: {e}")
            return self._basic_marathon_coaching(session)
    
    def _basic_marathon_coaching(self, session: Dict) -> Dict[str, Any]:
        """Basic coaching for Marathon mode"""
        marathon_state = session['marathon_state']
        calls_passed = marathon_state['calls_passed']
        total_calls = len(session['all_calls_data'])
        
        # Calculate overall score
        if total_calls > 0:
            pass_rate = (calls_passed / total_calls) * 100
            base_score = int(pass_rate)
        else:
            base_score = 50
        
        # Bonus for reaching target
        if marathon_state['is_passed']:
            base_score = min(100, base_score + 20)
        
        # Generate coaching based on performance
        if calls_passed >= marathon_state['calls_to_pass']:
            coaching_tone = "excellent"
        elif calls_passed >= marathon_state['calls_to_pass'] - 2:
            coaching_tone = "good"
        else:
            coaching_tone = "needs_improvement"
        
        coaching_templates = {
            'excellent': {
                'sales_coaching': f'Outstanding! You passed {calls_passed}/{total_calls} calls. Your consistency shows mastery of the marathon format.',
                'grammar_coaching': 'Your grammar was consistent throughout multiple calls. Keep using natural contractions.',
                'vocabulary_coaching': 'Great vocabulary choices across all calls. You maintained simple, effective language.',
                'pronunciation_coaching': 'Excellent pronunciation consistency throughout the marathon session.',
                'rapport_assertiveness': 'You built rapport effectively across multiple prospects. Great adaptability!'
            },
            'good': {
                'sales_coaching': f'Good work! You passed {calls_passed}/{total_calls} calls. Focus on consistency in your opener and objection handling.',
                'grammar_coaching': 'Good grammar overall. Practice using more contractions to sound natural.',
                'vocabulary_coaching': 'Solid vocabulary choices. Work on using more outcome-focused language.',
                'pronunciation_coaching': 'Good pronunciation. Focus on clarity during objection handling.',
                'rapport_assertiveness': 'Good rapport building. Practice showing more empathy in your openers.'
            },
            'needs_improvement': {
                'sales_coaching': f'You passed {calls_passed}/{total_calls} calls. Focus on your opener - it sets the tone for the entire call.',
                'grammar_coaching': 'Work on using more natural grammar with contractions like "I\'m" instead of "I am".',
                'vocabulary_coaching': 'Use simpler words. Say "book a meeting" instead of complex business terms.',
                'pronunciation_coaching': 'Practice speaking clearly and at a steady pace. Record yourself and listen back.',
                'rapport_assertiveness': 'Start with empathy: "I know this is out of the blue" shows you understand their perspective.'
            }
        }
        
        coaching = coaching_templates.get(coaching_tone, coaching_templates['needs_improvement'])
        
        return {
            'success': True,
            'coaching': coaching,
            'score': base_score,
            'source': 'basic_marathon'
        }
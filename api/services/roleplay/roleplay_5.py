# ===== services/roleplay/roleplay_5.py =====
# Power Hour Challenge - 10 consecutive advanced calls for endurance

import random
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from .base_roleplay import BaseRoleplay
from .configs.roleplay_5_config import Roleplay5Config

logger = logging.getLogger(__name__)

class Roleplay5(BaseRoleplay):
    """
    Roleplay 5 - Power Hour Challenge
    10 consecutive advanced cold calls to test endurance and consistency
    """
    
    def __init__(self, openai_service=None):
        super().__init__(openai_service)
        self.config = Roleplay5Config()
        self.roleplay_id = self.config.ROLEPLAY_ID

    def get_roleplay_info(self) -> Dict[str, Any]:
        return {
            'id': self.config.ROLEPLAY_ID,
            'name': self.config.NAME,
            'description': self.config.DESCRIPTION,
            'type': 'endurance_challenge',
            'features': {
                'ai_evaluation': self.is_openai_available(),
                'endurance_testing': True,
                'advanced_scenarios': True,
                'consistency_tracking': True,
                'performance_analytics': True,
                'elite_challenge': True,
                'total_calls': self.config.TOTAL_CALLS
            }
        }

    def create_session(self, user_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Creates a power hour endurance challenge session"""
        session_id = f"{user_id}_{self.config.ROLEPLAY_ID}_{mode}_{int(datetime.now().timestamp())}"
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'roleplay_id': self.config.ROLEPLAY_ID,
            'mode': 'endurance',
            'started_at': datetime.now(timezone.utc).isoformat(),
            'user_context': user_context,
            'session_active': True,
            
            # Power Hour state
            'power_hour_state': {
                'current_call_number': 1,
                'calls_completed': 0,
                'calls_successful': 0,
                'calls_failed': 0,
                'consecutive_successes': 0,
                'longest_success_streak': 0,
                'total_conversation_time': 0,
                'average_call_duration': 0,
                'energy_level': 10,  # Starts at maximum
                'consistency_score': 0,
                'endurance_bonus': 0
            },
            
            # Current call state
            'conversation_history': [],
            'current_stage': 'phone_pickup',
            'turn_count': 0,
            'stage_turn_count': 0,
            'stages_completed': [],
            'call_start_time': None,
            'call_outcome': 'in_progress',
            
            # Advanced tracking
            'performance_metrics': {
                'relationship_building': [],
                'discovery_effectiveness': [],
                'value_communication': [],
                'closing_success': [],
                'objection_handling': [],
                'call_durations': [],
                'stage_completion_rates': []
            },
            
            # Challenge-specific features
            'difficulty_progression': 'standard',  # increases over calls
            'fatigue_factor': 0,  # increases with each call
            'pressure_scenarios': [],
            'personality_variations': [],
            'all_calls_data': [],
            'challenge_complete': False,
            
            # Endurance mechanics
            'used_objections': set(),
            'used_scenarios': set(),
            'escalating_difficulty': True,
            'time_pressure': False,
            'elite_mode': True
        }
        
        self.active_sessions[session_id] = session_data
        
        # Generate power hour opening
        initial_response = self._get_power_hour_initial_response(session_data)
        session_data['call_start_time'] = datetime.now(timezone.utc).timestamp()
        
        session_data['conversation_history'].append({
            'role': 'assistant',
            'content': initial_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'phone_pickup',
            'call_number': 1,
            'difficulty_level': 'standard'
        })
        
        logger.info(f"Power Hour challenge session {session_id} created for user {user_id}")
        return {
            'success': True,
            'session_id': session_id,
            'initial_response': initial_response,
            'roleplay_info': self.get_roleplay_info(),
            'power_hour_info': {
                'total_calls': self.config.TOTAL_CALLS,
                'current_call': 1,
                'energy_level': 10,
                'challenge_type': 'Elite Endurance Challenge'
            }
        }

    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input for power hour endurance challenge"""
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
                'stage': session['current_stage'],
                'call_number': session['power_hour_state']['current_call_number'],
                'turn_number': session['turn_count']
            })
            
            current_call = session['power_hour_state']['current_call_number']
            logger.info(f"Power Hour Call #{current_call} Turn #{session['turn_count']}: Processing '{user_input[:50]}...'")
            
            # Advanced evaluation with fatigue factor
            evaluation = self._evaluate_power_hour_input(session, user_input)
            
            # Update performance metrics
            self._update_performance_metrics(session, evaluation)
            
            # Check for hang-up (more demanding in power hour)
            should_hang_up = self._should_hang_up_power_hour(session, evaluation, user_input)
            
            if should_hang_up:
                ai_response = self._get_contextual_hangup_response(session, evaluation)
                return self._handle_call_failure(session, "Call ended by prospect")
            
            # Generate AI response with increasing difficulty
            ai_response = self._generate_power_hour_response(session, user_input, evaluation)
            
            # Update session progression
            self._update_power_hour_progression(session, evaluation)
            
            # Check if current call should continue
            call_continues = self._should_call_continue_power_hour(session, evaluation)
            
            # Add AI response to conversation
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage'],
                'call_number': current_call,
                'evaluation': evaluation,
                'difficulty_level': session.get('difficulty_progression', 'standard')
            })
            
            if not call_continues:
                # Determine call outcome and move to next call
                if self._determine_power_hour_call_success(session):
                    return self._handle_call_success(session)
                else:
                    return self._handle_call_failure(session, "Call did not meet success criteria")
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': call_continues,
                'evaluation': evaluation,
                'power_hour_state': session['power_hour_state'],
                'turn_count': session['turn_count'],
                'endurance_metrics': {
                    'energy_level': session['power_hour_state']['energy_level'],
                    'fatigue_factor': session.get('fatigue_factor', 0),
                    'current_streak': session['power_hour_state']['consecutive_successes']
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing power hour input: {e}")
            return {'success': False, 'error': str(e), 'call_continues': False}

    def _evaluate_power_hour_input(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Advanced evaluation with endurance factors"""
        try:
            if self.is_openai_available():
                # Enhanced evaluation context for power hour
                power_hour_context = {
                    'current_call': session['power_hour_state']['current_call_number'],
                    'fatigue_factor': session.get('fatigue_factor', 0),
                    'energy_level': session['power_hour_state']['energy_level'],
                    'difficulty_level': session.get('difficulty_progression', 'standard'),
                    'endurance_challenge': True,
                    'consecutive_calls': session['power_hour_state']['calls_completed']
                }
                
                evaluation = self.openai_service.evaluate_user_input(
                    user_input,
                    session['conversation_history'],
                    f"power_hour_{session['current_stage']}",
                    context=power_hour_context
                )
                
                # Apply endurance adjustments
                evaluation = self._apply_endurance_adjustments(evaluation, session)
                
                return evaluation
            else:
                return self._basic_power_hour_evaluation(user_input, session)
                
        except Exception as e:
            logger.error(f"Power hour evaluation error: {e}")
            return self._basic_power_hour_evaluation(user_input, session)

    def _basic_power_hour_evaluation(self, user_input: str, session: Dict) -> Dict[str, Any]:
        """Basic evaluation with power hour difficulty"""
        score = 0
        criteria_met = []
        user_input_lower = user_input.lower().strip()
        
        current_call = session['power_hour_state']['current_call_number']
        fatigue_factor = session.get('fatigue_factor', 0)
        
        # Base evaluation
        word_count = len(user_input.split())
        if word_count >= 5:
            score += 1
            criteria_met.append('sufficient_length')
        
        # Stage-specific evaluation (more demanding)
        current_stage = session['current_stage']
        if current_stage == 'phone_pickup':
            if any(word in user_input_lower for word in ['calling from', 'my name', 'hello']):
                score += 1
                criteria_met.append('proper_introduction')
            if any(word in user_input_lower for word in ['out of the blue', 'interrupting', 'busy']):
                score += 1.5  # Higher weight for empathy in power hour
                criteria_met.append('shows_empathy')
        
        elif current_stage in ['discovery', 'value_proposition']:
            if '?' in user_input or any(q in user_input_lower for q in ['how', 'what', 'when', 'why']):
                score += 1.5
                criteria_met.append('asks_questions')
            if any(word in user_input_lower for word in ['save', 'increase', 'reduce', 'improve']):
                score += 1.5
                criteria_met.append('value_focused')
        
        # Apply difficulty progression (calls get harder)
        difficulty_multiplier = 1.0 + (current_call - 1) * 0.1  # 10% harder each call
        required_score = 2.5 * difficulty_multiplier
        
        # Apply fatigue penalty
        fatigue_penalty = fatigue_factor * 0.2
        final_score = max(0, score - fatigue_penalty)
        
        passed = final_score >= required_score
        
        return {
            'score': round(final_score, 1),
            'passed': passed,
            'criteria_met': criteria_met,
            'difficulty_multiplier': difficulty_multiplier,
            'fatigue_penalty': fatigue_penalty,
            'required_score': required_score,
            'endurance_challenge': True
        }

    def _apply_endurance_adjustments(self, evaluation: Dict, session: Dict) -> Dict[str, Any]:
        """Apply endurance-specific adjustments to evaluation"""
        current_call = session['power_hour_state']['current_call_number']
        energy_level = session['power_hour_state']['energy_level']
        
        # Difficulty scales with call number
        difficulty_factor = 1.0 + (current_call - 1) * 0.15
        
        # Energy affects performance requirements
        energy_factor = energy_level / 10.0
        
        # Adjust score requirements
        base_score = evaluation.get('score', 0)
        adjusted_score = base_score * energy_factor
        required_threshold = 3.0 * difficulty_factor
        
        evaluation['adjusted_score'] = adjusted_score
        evaluation['required_threshold'] = required_threshold
        evaluation['passed'] = adjusted_score >= required_threshold
        evaluation['difficulty_factor'] = difficulty_factor
        evaluation['energy_factor'] = energy_factor
        
        return evaluation

    def _should_hang_up_power_hour(self, session: Dict, evaluation: Dict, user_input: str) -> bool:
        """Power hour hang-up logic (more demanding)"""
        current_call = session['power_hour_state']['current_call_number']
        turn_count = session.get('turn_count', 1)
        
        # Base hang-up probability increases with call number
        base_hangup = 0.1 + (current_call - 1) * 0.05
        
        # Performance affects hang-up probability
        score = evaluation.get('adjusted_score', evaluation.get('score', 2))
        required = evaluation.get('required_threshold', 3.0)
        
        if score < required * 0.6 and turn_count >= 2:
            hangup_probability = base_hangup * 1.5
            return random.random() < hangup_probability
        
        return False

    def _should_call_continue_power_hour(self, session: Dict, evaluation: Dict) -> bool:
        """Determine if power hour call should continue"""
        if session.get('hang_up_triggered'):
            return False
        
        # Power hour calls are shorter but more intense
        max_turns = 12 - session['power_hour_state']['current_call_number']  # Shorter as fatigue increases
        if session['turn_count'] >= max_turns:
            logger.info(f"Power Hour call ending: reached maximum turns ({max_turns})")
            return False
        
        # Must progress through stages efficiently
        stages_completed = len(session.get('stages_completed', []))
        if session['turn_count'] >= 8 and stages_completed >= 3:
            logger.info(f"Power Hour call ending: good progression achieved")
            return False
        
        return True

    def _update_power_hour_progression(self, session: Dict, evaluation: Dict):
        """Update progression for power hour (faster pace required)"""
        current_stage = session['current_stage']
        should_progress = False
        
        # Faster progression required for endurance challenge
        if current_stage == 'phone_pickup':
            if evaluation.get('passed') or session['stage_turn_count'] >= 2:
                should_progress = True
        elif current_stage == 'opener_evaluation':
            if evaluation.get('passed') or session['stage_turn_count'] >= 2:
                should_progress = True
        elif current_stage == 'objection_handling':
            if evaluation.get('passed') or session['stage_turn_count'] >= 2:
                should_progress = True
        elif current_stage == 'discovery':
            if evaluation.get('passed') or session['stage_turn_count'] >= 3:
                should_progress = True
        elif current_stage == 'value_proposition':
            if evaluation.get('passed') or session['stage_turn_count'] >= 2:
                should_progress = True
        
        if should_progress:
            next_stage = self.config.STAGE_FLOW.get(current_stage)
            if next_stage and next_stage != current_stage:
                if current_stage not in session.get('stages_completed', []):
                    session.setdefault('stages_completed', []).append(current_stage)
                
                session['current_stage'] = next_stage
                session['stage_turn_count'] = 0
                
                logger.info(f"Power Hour Call #{session['power_hour_state']['current_call_number']}: Progressed from {current_stage} to {next_stage}")

    def _update_performance_metrics(self, session: Dict, evaluation: Dict):
        """Update comprehensive performance metrics"""
        metrics = session['performance_metrics']
        current_stage = session['current_stage']
        
        # Track stage-specific performance
        if current_stage == 'discovery':
            metrics['discovery_effectiveness'].append(evaluation.get('score', 0))
        elif current_stage == 'value_proposition':
            metrics['value_communication'].append(evaluation.get('score', 0))
        elif 'objection' in current_stage:
            metrics['objection_handling'].append(evaluation.get('score', 0))
        
        # Update energy level based on performance
        if evaluation.get('passed', False):
            session['power_hour_state']['energy_level'] = min(10, session['power_hour_state']['energy_level'] + 0.2)
        else:
            session['power_hour_state']['energy_level'] = max(1, session['power_hour_state']['energy_level'] - 0.5)
        
        # Update fatigue factor
        session['fatigue_factor'] = session.get('fatigue_factor', 0) + 0.1

    def _determine_power_hour_call_success(self, session: Dict) -> bool:
        """Determine if power hour call was successful (higher standards)"""
        stages_completed = len(session.get('stages_completed', []))
        turn_count = session.get('turn_count', 0)
        energy_level = session['power_hour_state']['energy_level']
        current_call = session['power_hour_state']['current_call_number']
        
        # Higher standards for power hour
        required_stages = 3 + (current_call // 3)  # More stages required as calls progress
        min_turns = 6
        min_energy = 3
        
        success = (stages_completed >= required_stages and 
                  turn_count >= min_turns and 
                  energy_level >= min_energy)
        
        logger.info(f"Power Hour Call #{current_call} success check: stages={stages_completed}/{required_stages}, turns={turn_count}/{min_turns}, energy={energy_level}/{min_energy} = {success}")
        
        return success

    def _handle_call_success(self, session: Dict) -> Dict[str, Any]:
        """Handle successful power hour call"""
        power_hour = session['power_hour_state']
        power_hour['calls_successful'] += 1
        power_hour['consecutive_successes'] += 1
        power_hour['longest_success_streak'] = max(power_hour['longest_success_streak'], power_hour['consecutive_successes'])
        
        # Calculate call duration
        if session.get('call_start_time'):
            call_duration = datetime.now(timezone.utc).timestamp() - session['call_start_time']
            session['performance_metrics']['call_durations'].append(call_duration)
            power_hour['total_conversation_time'] += call_duration
        
        session['call_outcome'] = 'success'
        
        current_call = power_hour['current_call_number']
        logger.info(f"Power Hour Call #{current_call} PASSED - Streak: {power_hour['consecutive_successes']}")
        
        return self._start_next_power_hour_call(session, f"Excellent call #{current_call}! Moving to next prospect...")

    def _handle_call_failure(self, session: Dict, reason: str) -> Dict[str, Any]:
        """Handle failed power hour call"""
        power_hour = session['power_hour_state']
        power_hour['calls_failed'] += 1
        power_hour['consecutive_successes'] = 0  # Reset streak
        
        # Calculate call duration
        if session.get('call_start_time'):
            call_duration = datetime.now(timezone.utc).timestamp() - session['call_start_time']
            session['performance_metrics']['call_durations'].append(call_duration)
            power_hour['total_conversation_time'] += call_duration
        
        session['call_outcome'] = 'failed'
        
        current_call = power_hour['current_call_number']
        logger.info(f"Power Hour Call #{current_call} FAILED: {reason} - Streak reset")
        
        return self._start_next_power_hour_call(session, f"Call #{current_call} ended. Next prospect...")

    def _start_next_power_hour_call(self, session: Dict, transition_message: str) -> Dict[str, Any]:
        """Start the next call in power hour sequence"""
        # Store current call data
        session['all_calls_data'].append({
            'call_number': session['power_hour_state']['current_call_number'],
            'conversation_history': session['conversation_history'].copy(),
            'stages_completed': session.get('stages_completed', []).copy(),
            'result': session['call_outcome'],
            'turn_count': session.get('turn_count', 0),
            'duration': datetime.now(timezone.utc).timestamp() - session.get('call_start_time', 0)
        })
        
        power_hour = session['power_hour_state']
        power_hour['calls_completed'] += 1
        
        # Check if power hour is complete
        if power_hour['calls_completed'] >= self.config.TOTAL_CALLS:
            return self._complete_power_hour(session)
        
        # Start next call
        power_hour['current_call_number'] += 1
        
        # Increase difficulty and fatigue
        session['difficulty_progression'] = self._get_difficulty_level(power_hour['current_call_number'])
        session['fatigue_factor'] = session.get('fatigue_factor', 0) + 0.2
        
        # Reset call-specific data
        session['conversation_history'] = []
        session['current_stage'] = 'phone_pickup'
        session['turn_count'] = 0
        session['stage_turn_count'] = 0
        session['stages_completed'] = []
        session['call_start_time'] = datetime.now(timezone.utc).timestamp()
        session['call_outcome'] = 'in_progress'
        
        # Generate new initial response with increased difficulty
        initial_response = self._get_power_hour_initial_response(session)
        
        session['conversation_history'].append({
            'role': 'assistant',
            'content': initial_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'phone_pickup',
            'call_number': power_hour['current_call_number'],
            'difficulty_level': session['difficulty_progression']
        })
        
        return {
            'success': True,
            'ai_response': initial_response,
            'call_continues': True,
            'power_hour_state': power_hour,
            'new_call_started': True,
            'transition_message': transition_message,
            'difficulty_level': session['difficulty_progression']
        }

    def _complete_power_hour(self, session: Dict) -> Dict[str, Any]:
        """Complete the power hour challenge"""
        session['session_active'] = False
        session['challenge_complete'] = True
        
        power_hour = session['power_hour_state']
        
        # Calculate final metrics
        success_rate = (power_hour['calls_successful'] / power_hour['calls_completed']) * 100
        avg_duration = power_hour['total_conversation_time'] / power_hour['calls_completed']
        
        completion_message = f"🏆 Power Hour Complete! {power_hour['calls_successful']}/{power_hour['calls_completed']} successful calls ({success_rate:.1f}%)"
        
        session['conversation_history'].append({
            'role': 'assistant',
            'content': completion_message,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'challenge_complete',
            'final_results': True
        })
        
        return {
            'success': True,
            'ai_response': completion_message,
            'call_continues': False,
            'challenge_complete': True,
            'power_hour_complete': True,
            'final_results': {
                'calls_successful': power_hour['calls_successful'],
                'calls_completed': power_hour['calls_completed'],
                'success_rate': success_rate,
                'longest_streak': power_hour['longest_success_streak'],
                'avg_call_duration': avg_duration,
                'total_time': power_hour['total_conversation_time'],
                'final_energy_level': power_hour['energy_level']
            }
        }

    def _get_difficulty_level(self, call_number: int) -> str:
        """Get difficulty level based on call number"""
        if call_number <= 3:
            return 'standard'
        elif call_number <= 6:
            return 'challenging'
        elif call_number <= 8:
            return 'difficult'
        else:
            return 'elite'

    def _get_power_hour_initial_response(self, session_data: Dict) -> str:
        """Generate initial response with escalating difficulty"""
        call_number = session_data['power_hour_state']['current_call_number']
        difficulty = session_data.get('difficulty_progression', 'standard')
        
        if difficulty == 'standard':
            responses = [
                "Hello?",
                "Good morning, this is Alex.",
                "Alex speaking.",
                "Hi there."
            ]
        elif difficulty == 'challenging':
            responses = [
                "Yeah, what is it?",
                "This better be important.",
                "I'm busy. What do you want?",
                "Make it quick."
            ]
        elif difficulty == 'difficult':
            responses = [
                "I don't take cold calls.",
                "How did you get this number?",
                "We have a no-solicitation policy.",
                "I'm not interested in whatever you're selling."
            ]
        else:  # elite
            responses = [
                "I'm in the middle of a board meeting. This better be life or death.",
                "You've got 10 seconds before I hang up.",
                "I hope you're calling with a million-dollar opportunity.",
                "I don't have time for sales pitches. Period."
            ]
        
        return random.choice(responses)

    def _generate_power_hour_response(self, session: Dict, user_input: str, evaluation: Dict) -> str:
        """Generate AI response with power hour intensity"""
        try:
            if self.is_openai_available():
                enhanced_context = {
                    **session['user_context'],
                    'power_hour_challenge': True,
                    'current_call': session['power_hour_state']['current_call_number'],
                    'difficulty_level': session.get('difficulty_progression', 'standard'),
                    'energy_level': session['power_hour_state']['energy_level'],
                    'fatigue_factor': session.get('fatigue_factor', 0),
                    'consecutive_successes': session['power_hour_state']['consecutive_successes'],
                    'endurance_mode': True
                }
                
                response_result = self.openai_service.generate_roleplay_response(
                    user_input,
                    session['conversation_history'],
                    enhanced_context,
                    session['current_stage']
                )
                
                if response_result.get('success'):
                    return response_result['response']
            
            return self._get_power_hour_fallback_response(session, evaluation, user_input)
            
        except Exception as e:
            logger.error(f"Error generating power hour AI response: {e}")
            return self._get_power_hour_fallback_response(session, evaluation, user_input)

    def _get_power_hour_fallback_response(self, session: Dict, evaluation: Dict, user_input: str) -> str:
        """Power hour specific fallback responses"""
        current_stage = session['current_stage']
        difficulty = session.get('difficulty_progression', 'standard')
        call_number = session['power_hour_state']['current_call_number']
        
        # Responses get tougher with difficulty
        if difficulty == 'elite':
            elite_responses = {
                'phone_pickup': ["What's this about? And it better be good.", "You have 30 seconds.", "This is highly irregular."],
                'objection_handling': ["I've heard it all before.", "Prove it.", "That's what they all say."],
                'discovery': ["I don't have time for twenty questions.", "Get to the point.", "Why should I care?"]
            }
            stage_responses = elite_responses.get(current_stage, ["I'm not convinced.", "Try harder.", "Next."])
        elif difficulty == 'difficult':
            difficult_responses = {
                'phone_pickup': ["I'm skeptical.", "This better be worth my time.", "Go ahead, but make it fast."],
                'objection_handling': ["I have concerns.", "That doesn't sound right.", "I need more proof."],
                'discovery': ["Maybe. Tell me more.", "I'm not sure about this.", "What exactly are you proposing?"]
            }
            stage_responses = difficult_responses.get(current_stage, ["I'm listening.", "Continue.", "What else?"])
        else:
            standard_responses = {
                'phone_pickup': ["Okay, I'm listening.", "What's this about?", "Go ahead."],
                'objection_handling': ["I understand.", "That makes sense.", "Continue."],
                'discovery': ["Tell me more.", "That's interesting.", "How does that work?"]
            }
            stage_responses = standard_responses.get(current_stage, ["I see.", "Go on.", "Tell me more."])
        
        return random.choice(stage_responses)

    def _handle_silence_trigger(self, session: Dict, trigger: str) -> Dict[str, Any]:
        """Handle silence triggers for power hour"""
        if trigger == '[SILENCE_IMPATIENCE]':
            impatience_responses = [
                "Hello? Are you still there?",
                "Did I lose you?",
                "Can you hear me?",
                "Time is money here..."
            ]
            
            return {
                'success': True,
                'ai_response': random.choice(impatience_responses),
                'call_continues': True,
                'power_hour_state': session['power_hour_state']
            }
        elif trigger == '[SILENCE_HANGUP]':
            return self._handle_call_failure(session, "15 seconds of silence - prospect hung up")

    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End power hour challenge with comprehensive analysis"""
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
            
            power_hour = session['power_hour_state']
            
            # Determine overall success
            calls_completed = power_hour['calls_completed']
            calls_successful = power_hour['calls_successful']
            success_rate = (calls_successful / max(calls_completed, 1)) * 100
            
            # Power hour success criteria (high bar)
            session_success = (success_rate >= 70 and 
                             power_hour['longest_success_streak'] >= 3 and
                             calls_completed >= 8)
            
            # Calculate comprehensive score
            overall_score = self._calculate_power_hour_score(session)
            
            # Generate elite coaching
            coaching_result = self._generate_power_hour_coaching(session)
            
            result = {
                'success': True,
                'duration_minutes': duration_minutes,
                'session_success': session_success,
                'coaching': coaching_result.get('coaching', {}),
                'overall_score': overall_score,
                'session_data': session,
                'roleplay_type': 'endurance_challenge',
                'power_hour_results': {
                    'calls_completed': calls_completed,
                    'calls_successful': calls_successful,
                    'calls_failed': power_hour['calls_failed'],
                    'success_rate': success_rate,
                    'longest_success_streak': power_hour['longest_success_streak'],
                    'total_conversation_time': power_hour['total_conversation_time'],
                    'average_call_duration': power_hour['total_conversation_time'] / max(calls_completed, 1),
                    'final_energy_level': power_hour['energy_level'],
                    'endurance_bonus': power_hour.get('endurance_bonus', 0),
                    'consistency_score': self._calculate_consistency_score(session),
                    'challenge_complete': session.get('challenge_complete', False)
                }
            }
            
            # Clean up session
            del self.active_sessions[session_id]
            
            logger.info(f"Power Hour session {session_id} ended. Success: {session_success}, Score: {overall_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error ending power hour session: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_power_hour_score(self, session: Dict) -> int:
        """Calculate comprehensive power hour score"""
        power_hour = session['power_hour_state']
        base_score = 20
        
        # Success rate (40 points max)
        success_rate = (power_hour['calls_successful'] / max(power_hour['calls_completed'], 1)) * 100
        base_score += min(40, int(success_rate * 0.4))
        
        # Consistency/streak bonus (25 points max)
        longest_streak = power_hour['longest_success_streak']
        base_score += min(25, longest_streak * 3)
        
        # Endurance bonus (20 points max)
        final_energy = power_hour['energy_level']
        base_score += min(20, int(final_energy * 2))
        
        # Call completion bonus (15 points max)
        completion_rate = (power_hour['calls_completed'] / self.config.TOTAL_CALLS) * 100
        base_score += min(15, int(completion_rate * 0.15))
        
        return max(0, min(100, base_score))

    def _calculate_consistency_score(self, session: Dict) -> float:
        """Calculate consistency across all calls"""
        all_calls = session.get('all_calls_data', [])
        if not all_calls:
            return 0.0
        
        # Analyze stage completion consistency
        stage_completions = [len(call.get('stages_completed', [])) for call in all_calls]
        avg_stages = sum(stage_completions) / len(stage_completions)
        
        # Analyze duration consistency
        durations = [call.get('duration', 0) for call in all_calls]
        avg_duration = sum(durations) / len(durations)
        
        # Calculate variance (lower is better for consistency)
        stage_variance = sum((x - avg_stages) ** 2 for x in stage_completions) / len(stage_completions)
        duration_variance = sum((x - avg_duration) ** 2 for x in durations) / len(durations)
        
        # Convert to consistency score (0-10 scale)
        consistency_score = max(0, 10 - (stage_variance + duration_variance * 0.001))
        
        return round(consistency_score, 1)

    def _generate_power_hour_coaching(self, session: Dict) -> Dict[str, Any]:
        """Generate comprehensive power hour coaching"""
        try:
            if self.is_openai_available():
                return self.openai_service.generate_coaching_feedback(
                    session.get('all_calls_data', []),
                    session.get('performance_metrics', {}),
                    session.get('user_context', {}),
                    coaching_type='endurance_challenge'
                )
            else:
                return self._generate_fallback_power_hour_coaching(session)
                
        except Exception as e:
            logger.error(f"Error generating power hour coaching: {e}")
            return self._generate_fallback_power_hour_coaching(session)

    def _generate_fallback_power_hour_coaching(self, session: Dict) -> Dict[str, Any]:
        """Generate fallback coaching for power hour"""
        coaching = {}
        power_hour = session['power_hour_state']
        
        # Overall performance
        success_rate = (power_hour['calls_successful'] / max(power_hour['calls_completed'], 1)) * 100
        if success_rate >= 80:
            coaching['overall'] = "Outstanding Power Hour performance! You demonstrated exceptional endurance and consistency."
        elif success_rate >= 60:
            coaching['overall'] = "Strong Power Hour performance! You showed good stamina and maintained quality throughout."
        else:
            coaching['overall'] = "Good effort on the Power Hour challenge! Focus on maintaining energy and consistency across multiple calls."
        
        # Endurance
        final_energy = power_hour['energy_level']
        if final_energy >= 7:
            coaching['endurance'] = "Excellent energy management! You maintained peak performance throughout the challenge."
        elif final_energy >= 4:
            coaching['endurance'] = "Good endurance. Work on pacing yourself better for sustained performance."
        else:
            coaching['endurance'] = "Focus on energy management. Take brief mental breaks between calls to maintain performance."
        
        # Consistency
        longest_streak = power_hour['longest_success_streak']
        if longest_streak >= 5:
            coaching['consistency'] = "Outstanding consistency! You maintained high performance across multiple consecutive calls."
        elif longest_streak >= 3:
            coaching['consistency'] = "Good consistency. Work on maintaining momentum when you hit your stride."
        else:
            coaching['consistency'] = "Focus on building consistency. Develop routines that help you perform reliably call after call."
        
        # Elite performance
        if power_hour['calls_completed'] >= self.config.TOTAL_CALLS:
            coaching['completion'] = "Congratulations on completing the full Power Hour challenge! This demonstrates true sales endurance."
        
        return {'success': True, 'coaching': coaching}
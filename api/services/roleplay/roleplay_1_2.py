# ===== FINAL FIXED: services/roleplay/roleplay_1_2.py =====

import random
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any

from .base_roleplay import BaseRoleplay
from .configs.roleplay_1_2_config import Roleplay12Config
from utils.constants import EARLY_OBJECTIONS, IMPATIENCE_PHRASES

logger = logging.getLogger(__name__)

class Roleplay12(BaseRoleplay):
    """
    Roleplay 1.2 - Marathon Mode.
    Definitive logic for a realistic, multi-turn conversation flow.
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
            'calls_to_pass': self.config.CALLS_TO_PASS
        }

    def create_session(self, user_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Creates a Marathon session, starting at the 'phone_pickup' stage."""
        session_id = f"{user_id}_{self.config.ROLEPLAY_ID}_{mode}_{int(datetime.now().timestamp())}"
        session_data = {
            'session_id': session_id, 'user_id': user_id, 'roleplay_id': self.config.ROLEPLAY_ID,
            'mode': 'marathon', 'started_at': datetime.now(timezone.utc).isoformat(), 'user_context': user_context,
            'session_active': True, 'marathon_state': {'current_call_number': 1, 'calls_passed': 0, 'calls_failed': 0, 'is_complete': False},
            'all_calls_data': [], 'used_objections': [], 'current_call_data': self._initialize_call_data(),
        }
        self.active_sessions[session_id] = session_data
        initial_response = self._get_contextual_initial_response(user_context)
        session_data['current_call_data']['conversation_history'].append({'role': 'assistant', 'content': initial_response})
        return {'success': True, 'session_id': session_id, 'initial_response': initial_response, 'roleplay_info': self.get_roleplay_info(), 'marathon_status': session_data['marathon_state']}

    def _initialize_call_data(self) -> Dict[str, Any]:
        """Initializes a new call within the marathon."""
        return {'conversation_history': [], 'current_stage': 'phone_pickup', 'turn_count': 0, 'call_status': 'in_progress'}

    def _get_evaluation_stage_for_turn(self, call_data: Dict) -> str:
        """
        Determines which rubric to use based on the number of turns the user has taken.
        This is much more reliable than using stage names.
        """
        user_turn_number = call_data['turn_count']
        
        if user_turn_number == 1:
            # The first thing the user says is the opener.
            return 'opener'
        elif user_turn_number == 2:
            # The second thing the user says is the objection handling.
            return 'objection_handling'
        elif user_turn_number == 3:
            # The third thing is the mini-pitch.
            return 'mini_pitch'
        else:
            # No further evaluations in this simple flow.
            return 'none'

    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        session = self.active_sessions[session_id]
        call = session['current_call_data']
        marathon = session['marathon_state']

        if marathon['is_complete']:
            return {'success': False, 'error': 'Marathon is already complete.'}
        
        # Silence handling
        if user_input == '[SILENCE_IMPATIENCE]':
            return {'success': True, 'ai_response': random.choice(IMPATIENCE_PHRASES), 'call_continues': True}
        if user_input == '[SILENCE_HANGUP]':
            return self._handle_call_failure(session, "Hung up due to silence")

        call['turn_count'] += 1
        call['conversation_history'].append({'role': 'user', 'content': user_input})
        
        # Determine if this turn's input needs evaluation
        evaluation_stage = self._get_evaluation_stage_for_turn(call)
        
        if evaluation_stage != 'none':
            logger.info(f"Turn {call['turn_count']}: Evaluating user input as '{evaluation_stage}'.")
            evaluation = self._evaluate_user_input(session, user_input, evaluation_stage)
            
            if not evaluation.get('passed', False):
                return self._handle_call_failure(session, f"Failed evaluation at {evaluation_stage}")
            
            # Special rule: random hang-up only after a SUCCESSFUL opener
            if evaluation_stage == 'opener' and random.random() < self.config.RANDOM_HANGUP_CHANCE:
                return self._handle_call_failure(session, "Random opener hang-up (unlucky!)")
        else:
            # This case should not be hit in the new logic but is safe to have.
            evaluation = {'passed': True, 'feedback': 'Input received.'}

        # Advance the stage to determine the AI's next action
        self._update_session_state(session)
        
        # Check if the call has reached its successful conclusion
        if call['current_stage'] == 'call_ended':
            return self._handle_call_success(session)

        # Generate the AI's response for the new stage
        ai_response = self._generate_ai_response(session)
        call['conversation_history'].append({'role': 'assistant', 'content': ai_response})
        
        return {'success': True, 'ai_response': ai_response, 'call_continues': True, 'marathon_status': marathon, 'evaluation': evaluation}

    def _evaluate_user_input(self, session: Dict, user_input: str, stage: str) -> Dict:
        if not self.is_openai_available():
            return {'passed': len(user_input.split()) > 3, 'score': 3}
        return self.openai_service.evaluate_user_input(user_input, session['current_call_data']['conversation_history'], stage)

    def _update_session_state(self, session: Dict):
        current_stage = session['current_call_data']['current_stage']
        next_stage = self.config.STAGE_FLOW.get(current_stage, 'call_ended')
        session['current_call_data']['current_stage'] = next_stage
        logger.info(f"Session {session['session_id']} moved to stage: {next_stage}")

    def _generate_ai_response(self, session: Dict) -> str:
        current_stage = session['current_call_data']['current_stage']
        
        if current_stage == 'early_objection':
            available_objections = [obj for obj in EARLY_OBJECTIONS if obj not in session['used_objections']]
            if not available_objections:
                session['used_objections'] = []
                available_objections = EARLY_OBJECTIONS
            objection = random.choice(available_objections)
            session['used_objections'].append(objection)
            return objection
        
        # For all other turns, generate a natural, contextual response
        if self.is_openai_available():
            return self.openai_service.generate_roleplay_response(
                session['current_call_data']['conversation_history'][-1]['content'],
                session['current_call_data']['conversation_history'],
                session['user_context'],
                current_stage
            ).get('response', "I'm listening...")
        else:
            return "Okay, go on."

    def _handle_call_success(self, session: Dict) -> Dict:
        session['marathon_state']['calls_passed'] += 1
        session['current_call_data']['call_status'] = 'passed'
        ai_response = "That sounds interesting. I have to run, but send me an email with the details."
        session['current_call_data']['conversation_history'].append({'role': 'assistant', 'content': ai_response})
        return self._start_next_call(session, "Call passed! Great job.")

    def _handle_call_failure(self, session: Dict, reason: str) -> Dict:
        session['marathon_state']['calls_failed'] += 1
        session['current_call_data']['call_status'] = 'failed'
        ai_response = "Sorry, I'm not interested. Goodbye."
        session['current_call_data']['conversation_history'].append({'role': 'assistant', 'content': ai_response})
        logger.warning(f"Call failed for session {session['session_id']}. Reason: {reason}")
        return self._start_next_call(session, f"Call failed: {reason}.")

    def _start_next_call(self, session: Dict, transition_message: str) -> Dict:
        session['all_calls_data'].append(session['current_call_data'])
        marathon = session['marathon_state']
        if marathon['current_call_number'] >= self.config.TOTAL_CALLS:
            marathon['is_complete'] = True
            return {'success': True, 'ai_response': "Marathon complete. Ending the session.", 'call_continues': False, 'marathon_status': marathon}
        marathon['current_call_number'] += 1
        session['current_call_data'] = self._initialize_call_data()
        ai_response = self._get_contextual_initial_response(session['user_context'])
        session['current_call_data']['conversation_history'].append({'role': 'assistant', 'content': ai_response})
        return {'success': True, 'ai_response': ai_response, 'call_continues': True, 'marathon_status': marathon, 'new_call_started': True, 'transition_message': transition_message}
    
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        session = self.active_sessions.pop(session_id, None)
        if not session: return {'success': False, 'error': 'Session not found.'}
        marathon = session['marathon_state']
        if not marathon.get('is_complete'):
            if session['current_call_data']['call_status'] == 'in_progress':
                marathon['calls_failed'] += 1
            marathon['is_complete'] = True
        passed_marathon = marathon['calls_passed'] >= self.config.CALLS_TO_PASS
        if passed_marathon:
            feedback_message = f"Nice work—you passed {marathon['calls_passed']} out of 10! You've unlocked the next modules and earned one shot at Legend Mode. Want to go for Legend now or run another Marathon?"
        else:
            feedback_message = f"You completed all 10 calls and scored {marathon['calls_passed']}/10. Keep practising—the more reps you get, the easier it becomes. Ready to try Marathon again?"
        coaching = {"overall": feedback_message}
        return {
            'success': True, 'session_success': passed_marathon,
            'overall_score': int((marathon['calls_passed'] / self.config.TOTAL_CALLS) * 100),
            'duration_minutes': (datetime.now(timezone.utc) - datetime.fromisoformat(session['started_at'])).total_seconds() / 60,
            'coaching': coaching, 'session_data': session,
            'marathon_results': {'calls_passed': marathon['calls_passed'], 'marathon_passed': passed_marathon, 'is_complete': True}
        }
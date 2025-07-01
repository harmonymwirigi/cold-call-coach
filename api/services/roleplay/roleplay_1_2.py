# ===== FINAL FIXED (v2): services/roleplay/roleplay_1_2.py =====
# This version corrects the typo in the process_user_input method.

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
    Roleplay 1.2 - Marathon Mode.
    Self-contained logic for a structured 10-call run.
    """
    
    def __init__(self, openai_service=None):
        super().__init__(openai_service)
        self.config = Roleplay12Config()
        self.roleplay_id = self.config.ROLEPLAY_ID

    def get_roleplay_info(self) -> Dict[str, Any]:
        return {
            'id': self.config.ROLEPLAY_ID, 'name': self.config.NAME,
            'description': self.config.DESCRIPTION, 'type': 'marathon',
            'total_calls': self.config.TOTAL_CALLS, 'calls_to_pass': self.config.CALLS_TO_PASS
        }

    def create_session(self, user_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Creates a Marathon session."""
        session_id = f"{user_id}_{self.config.ROLEPLAY_ID}_{mode}_{int(datetime.now().timestamp())}"
        session_data = {
            'session_id': session_id, 'user_id': user_id, 'roleplay_id': self.config.ROLEPLAY_ID,
            'mode': 'marathon', 'started_at': datetime.now(timezone.utc).isoformat(), 'user_context': user_context,
            'session_active': True,
            'marathon_state': {'current_call_number': 1, 'calls_passed': 0, 'calls_failed': 0},
            'all_calls_data': [], 'used_objections': set(),
            'current_call_data': self._initialize_call_data(),
        }
        self.active_sessions[session_id] = session_data
        
        initial_response = self._get_contextual_initial_response(user_context)
        session_data['current_call_data']['conversation_history'].append({'role': 'assistant', 'content': initial_response})
        
        logger.info(f"Marathon session {session_id} created for user {user_id}.")
        return {'success': True, 'session_id': session_id, 'initial_response': initial_response, 'roleplay_info': self.get_roleplay_info(), 'marathon_status': session_data['marathon_state']}

    def _initialize_call_data(self) -> Dict[str, Any]:
        """Initializes a new call within the marathon."""
        return {'conversation_history': [], 'current_stage': 'opener', 'turn_count': 0, 'rubric_scores': {}}

    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        session = self.active_sessions[session_id]
        call = session['current_call_data']
        marathon = session['marathon_state']

        if user_input == '[SILENCE_IMPATIENCE]':
            return {'success': True, 'ai_response': random.choice(IMPATIENCE_PHRASES), 'call_continues': True}
        if user_input == '[SILENCE_HANGUP]':
            return self._handle_call_failure(session, "Hung up due to silence")

        call['turn_count'] += 1
        call['conversation_history'].append({'role': 'user', 'content': user_input})
        
        current_stage = call['current_stage']
        logger.info(f"Marathon Turn {call['turn_count']}: Evaluating as '{current_stage}'")
        
        # --- Core Evaluation Logic ---
        evaluation = self._evaluate_user_input(session, user_input, current_stage) # <<< TYPO FIX IS HERE
        call['rubric_scores'][current_stage] = evaluation
        
        if not evaluation.get('passed', False):
            return self._handle_call_failure(session, f"Failed evaluation at {current_stage}")

        if current_stage == 'opener' and random.random() < self.config.RANDOM_HANGUP_CHANCE:
            return self._handle_call_failure(session, "Random opener hang-up (unlucky!)")
        
        # Determine the AI's next action
        if current_stage == 'opener':
            call['current_stage'] = 'objection_handling'
            ai_response = self._get_unique_objection(session)
        elif current_stage == 'objection_handling':
            call['current_stage'] = 'mini_pitch'
            ai_response = "Okay, fair enough. You have 30 seconds, what's this about?"
        elif current_stage == 'mini_pitch':
            return self._handle_call_success(session)
        else:
            return self._handle_call_failure(session, "Unexpected conversation stage.")

        call['conversation_history'].append({'role': 'assistant', 'content': ai_response})
        return {'success': True, 'ai_response': ai_response, 'call_continues': True, 'marathon_status': marathon, 'evaluation': evaluation}

    def _evaluate_user_input(self, session: Dict, user_input: str, stage: str) -> Dict:
        if not self.is_openai_available():
            return {'passed': len(user_input.split()) > 3, 'score': 3}
        return self.openai_service.evaluate_user_input(user_input, session['current_call_data']['conversation_history'], stage)

    def _get_unique_objection(self, session: Dict) -> str:
        available = [obj for obj in EARLY_OBJECTIONS if obj not in session['used_objections']]
        if not available:
            session['used_objections'].clear()
            available = EARLY_OBJECTIONS
        objection = random.choice(available)
        session['used_objections'].add(objection)
        return objection

    def _handle_call_success(self, session: Dict) -> Dict[str, Any]:
        session['marathon_state']['calls_passed'] += 1
        return self._start_next_call(session, "Call passed! Great job.")

    def _handle_call_failure(self, session: Dict, reason: str) -> Dict[str, Any]:
        session['marathon_state']['calls_failed'] += 1
        logger.warning(f"Call failed for {session['session_id']}. Reason: {reason}")
        return self._start_next_call(session, f"Call failed: {reason}.")

    def _start_next_call(self, session: Dict, transition_message: str) -> Dict[str, Any]:
        session['all_calls_data'].append(session['current_call_data'])
        marathon = session['marathon_state']
        
        if (marathon['calls_passed'] + marathon['calls_failed']) >= self.config.TOTAL_CALLS:
            return self.end_session(session['session_id'])

        marathon['current_call_number'] += 1
        session['current_call_data'] = self._initialize_call_data()
        
        initial_response = self._get_contextual_initial_response(session['user_context'])
        session['current_call_data']['conversation_history'].append({'role': 'assistant', 'content': initial_response})
        
        return {
            'success': True, 'ai_response': initial_response, 'call_continues': True,
            'marathon_status': marathon, 'new_call_started': True, 'transition_message': transition_message
        }

    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        session = self.active_sessions.pop(session_id, None)
        if not session: return {'success': True, 'message': 'Session already ended.'}

        marathon = session['marathon_state']
        passed_marathon = marathon['calls_passed'] >= self.config.CALLS_TO_PASS
        
        if passed_marathon:
            completion_message = SUCCESS_MESSAGES["marathon_pass"].format(score=marathon['calls_passed'])
        else:
            completion_message = SUCCESS_MESSAGES["marathon_fail"].format(score=marathon['calls_passed'])

        return {
            'success': True,
            'session_success': passed_marathon,
            'overall_score': int((marathon['calls_passed'] / self.config.TOTAL_CALLS) * 100),
            'duration_minutes': (datetime.now(timezone.utc) - datetime.fromisoformat(session['started_at'])).total_seconds() / 60,
            'coaching': {'overall': completion_message},
            'session_data': session,
            'marathon_results': {'calls_passed': marathon['calls_passed'], 'marathon_passed': passed_marathon}
        }
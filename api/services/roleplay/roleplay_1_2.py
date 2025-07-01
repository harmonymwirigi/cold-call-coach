# ===== FIXED: services/roleplay/roleplay_1_2.py =====
# This version INHERITS from Roleplay11 for intelligent conversation.

import random
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from .roleplay_1_1 import Roleplay11  # <-- Inherit from the working implementation
from .configs.roleplay_1_2_config import Roleplay12Config
from utils.constants import EARLY_OBJECTIONS, SUCCESS_MESSAGES

logger = logging.getLogger(__name__)

class Roleplay12(Roleplay11):
    """
    Roleplay 1.2 - Marathon Mode.
    Manages a sequence of 10 intelligent calls by inheriting from Roleplay11.
    """
    
    def __init__(self, openai_service=None):
        super().__init__(openai_service)  # Initialize the parent Roleplay11 class
        self.config = Roleplay12Config()
        self.roleplay_id = self.config.ROLEPLAY_ID

    def get_roleplay_info(self) -> Dict[str, Any]:
        # Override to provide marathon-specific info
        return {
            'id': self.config.ROLEPLAY_ID, 'name': self.config.NAME,
            'description': self.config.DESCRIPTION, 'type': 'marathon',
            'total_calls': self.config.TOTAL_CALLS, 'calls_to_pass': self.config.CALLS_TO_PASS
        }

    def create_session(self, user_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        # Override to add marathon-specific state
        result = super().create_session(user_id, 'marathon', user_context)
        if not result.get('success'):
            return result
        
        session_id = result['session_id']
        session = self.active_sessions.get(session_id)
        
        session['marathon_state'] = {
            'current_call_number': 1, 'calls_passed': 0, 'calls_failed': 0
        }
        session['used_objections'] = set()
        
        # Override the initial objection to be one from the unused list
        objection = self._get_unique_objection(session)
        session['initial_objection'] = objection

        logger.info(f"Marathon session {session_id} created.")
        return result

    def _get_unique_objection(self, session: Dict) -> str:
        """Picks a unique objection for the current marathon run."""
        available = [obj for obj in EARLY_OBJECTIONS if obj not in session['used_objections']]
        if not available:
            session['used_objections'].clear()
            available = EARLY_OBJECTIONS
        objection = random.choice(available)
        session['used_objections'].add(objection)
        return objection

    def _generate_contextual_ai_response(self, session: Dict, user_input: str, evaluation: Dict) -> str:
        # Override to inject the unique objection at the correct stage
        if session['current_stage'] == 'opener_evaluation':
            return session.get('initial_objection', "I'm not interested.")
        
        # For all other stages, use the intelligent parent logic
        return super()._generate_contextual_ai_response(session, user_input, evaluation)

    def _is_call_successful(self, session: Dict) -> bool:
        """Determines if a single call within the marathon was a pass."""
        # A call passes if all applicable rubric stages were passed.
        # This aligns with the spec: "A call scores PASS only if all applicable rubrics pass".
        rubrics = session.get('rubric_scores', {})
        if not rubrics: return False # Must have at least one evaluation

        # Check if opener and objection handling were passed. Mini-pitch is a bonus.
        opener_passed = rubrics.get('opener', {}).get('passed', False)
        objection_passed = rubrics.get('objection_handling', {}).get('passed', False)

        return opener_passed and objection_passed

    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        # Wrap the parent's logic to handle marathon state transitions
        result = super().process_user_input(session_id, user_input)
        
        session = self.active_sessions.get(session_id)
        if not session: return result

        # Check if the call just ended
        if not result.get('call_continues', True):
            if self._is_call_successful(session):
                return self._handle_call_success(session)
            else:
                return self._handle_call_failure(session, "Call did not meet success criteria")
        
        # The call continues, just return the result from the parent
        result['marathon_status'] = session['marathon_state']
        return result
        
    def _handle_call_success(self, session: Dict) -> Dict[str, Any]:
        session['marathon_state']['calls_passed'] += 1
        return self._start_next_call(session, "Call passed! Great job.")

    def _handle_call_failure(self, session: Dict, reason: str) -> Dict[str, Any]:
        session['marathon_state']['calls_failed'] += 1
        logger.warning(f"Call failed for {session['session_id']}. Reason: {reason}")
        return self._start_next_call(session, f"Call failed: {reason}")

    def _start_next_call(self, session: Dict, transition_message: str) -> Dict[str, Any]:
        marathon = session['marathon_state']
        
        if marathon['current_call_number'] >= self.config.TOTAL_CALLS:
            return self.end_session(session['session_id'])

        marathon['current_call_number'] += 1
        
        # Reset the state for the next call (like in create_session)
        session['conversation_history'] = []
        session['current_stage'] = 'phone_pickup'
        session['hang_up_triggered'] = False
        session['turn_count'] = 0
        session['rubric_scores'] = {}
        session['initial_objection'] = self._get_unique_objection(session)
        
        # Get a new initial "Hello" response
        initial_response = self._get_contextual_initial_response(session['user_context'])
        session['conversation_history'].append({'role': 'assistant', 'content': initial_response})
        
        return {
            'success': True, 'ai_response': initial_response, 'call_continues': True,
            'marathon_status': marathon, 'new_call_started': True, 'transition_message': transition_message
        }

    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        session = self.active_sessions.get(session_id)
        if not session: return {'success': True, 'message': 'Session already ended.'}

        marathon = session['marathon_state']
        passed_marathon = marathon['calls_passed'] >= self.config.CALLS_TO_PASS
        
        if passed_marathon:
            completion_message = SUCCESS_MESSAGES["marathon_pass"].format(score=marathon['calls_passed'])
        else:
            completion_message = SUCCESS_MESSAGES["marathon_fail"].format(score=marathon['calls_passed'])

        # Now, call the parent's end_session to do the cleanup and get a base result
        result = super().end_session(session_id, forced_end)
        
        # Override with marathon-specific results
        result.update({
            'session_success': passed_marathon,
            'overall_score': int((marathon['calls_passed'] / self.config.TOTAL_CALLS) * 100),
            'coaching': {'overall': completion_message},
            'marathon_results': {'calls_passed': marathon['calls_passed'], 'marathon_passed': passed_marathon}
        })
        return result
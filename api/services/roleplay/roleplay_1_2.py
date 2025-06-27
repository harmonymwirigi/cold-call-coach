# ===== FIXED: services/roleplay/roleplay_1_2.py =====

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
    Implements the full, intelligent logic as specified in the PDF document.
    """
    
    def __init__(self, openai_service=None):
        super().__init__(openai_service)
        self.config = Roleplay12Config()
        self.roleplay_id = self.config.ROLEPLAY_ID

    def get_roleplay_info(self) -> Dict[str, Any]:
        """Return Roleplay 1.2 configuration."""
        return {
            'id': self.config.ROLEPLAY_ID,
            'name': self.config.NAME,
            'description': self.config.DESCRIPTION,
            'type': 'marathon',
            'total_calls': self.config.TOTAL_CALLS,
            'calls_to_pass': self.config.CALLS_TO_PASS
        }

    def create_session(self, user_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create a new Marathon session."""
        session_id = f"{user_id}_{self.config.ROLEPLAY_ID}_{mode}_{int(datetime.now().timestamp())}"
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'roleplay_id': self.config.ROLEPLAY_ID,
            'mode': 'marathon',
            'started_at': datetime.now(timezone.utc).isoformat(),
            'user_context': user_context,
            'session_active': True,
            'marathon_state': {
                'current_call_number': 1,
                'calls_passed': 0,
                'calls_failed': 0,
                'is_complete': False,
            },
            'all_calls_data': [],
            'used_objections': [],
            'current_call_data': self._initialize_call_data(),
        }
        
        self.active_sessions[session_id] = session_data
        initial_response = self._get_contextual_initial_response(user_context)
        session_data['current_call_data']['conversation_history'].append({'role': 'assistant', 'content': initial_response})
        
        return {
            'success': True,
            'session_id': session_id,
            'initial_response': initial_response,
            'roleplay_info': self.get_roleplay_info(),
            'marathon_status': session_data['marathon_state']
        }

    def _initialize_call_data(self) -> Dict[str, Any]:
        """Initialize data for a new call within the marathon."""
        return {'conversation_history': [], 'current_stage': 'phone_pickup', 'turn_count': 0, 'call_status': 'in_progress'}

    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input for the current call in the marathon."""
        session = self.active_sessions[session_id]
        call = session['current_call_data']
        marathon = session['marathon_state']

        if marathon['is_complete']:
            return {'success': False, 'error': 'Marathon is already complete.'}
        
        # Handle silence triggers from the frontend
        if user_input == '[SILENCE_IMPATIENCE]':
            return {'success': True, 'ai_response': random.choice(IMPATIENCE_PHRASES), 'call_continues': True}
        if user_input == '[SILENCE_HANGUP]':
            return self._handle_call_failure(session, "Hung up due to silence")

        call['turn_count'] += 1
        call['conversation_history'].append({'role': 'user', 'content': user_input})
        
        evaluation_stage = self._get_evaluation_stage(call['current_stage'])
        evaluation = self._evaluate_user_input(session, user_input, evaluation_stage)
        
        # Rule: Fail at opener -> scripted hang-up
        if evaluation_stage == 'opener' and not evaluation.get('passed', False):
            return self._handle_call_failure(session, "Failed opener evaluation")

        # Rule: Marathon only - random hang-up on PASSED opener
        if evaluation_stage == 'opener' and evaluation.get('passed', True) and random.random() < self.config.RANDOM_HANGUP_CHANCE:
            return self._handle_call_failure(session, "Random opener hang-up (unlucky!)")

        # Rule: Fail at any other stage -> hang-up
        if not evaluation.get('passed', False):
             return self._handle_call_failure(session, f"Failed evaluation at {evaluation_stage}")

        self._update_session_state(session)
        
        # Rule: If pass, respond positively and hang up to start next call
        if call['current_stage'] == 'call_ended':
            return self._handle_call_success(session)

        ai_response = self._generate_ai_response(session)
        call['conversation_history'].append({'role': 'assistant', 'content': ai_response})
        
        return {'success': True, 'ai_response': ai_response, 'call_continues': True, 'marathon_status': marathon, 'evaluation': evaluation}

    def _evaluate_user_input(self, session: Dict, user_input: str, stage: str) -> Dict:
        """Evaluate user input using OpenAI service, based on rubrics."""
        if not self.is_openai_available():
            logger.warning("OpenAI not available, using basic evaluation.")
            return {'passed': len(user_input.split()) > 4, 'score': 3}

        # This now uses the same detailed evaluation as Practice Mode
        evaluation_result = self.openai_service.evaluate_user_input(
            user_input,
            session['current_call_data']['conversation_history'],
            stage
        )
        return evaluation_result

    def _update_session_state(self, session: Dict):
        """Move to the next stage in the call flow."""
        current_stage = session['current_call_data']['current_stage']
        next_stage = self.config.STAGE_FLOW.get(current_stage)
        session['current_call_data']['current_stage'] = next_stage
        logger.info(f"Session {session['session_id']} moved to stage: {next_stage}")

    def _generate_ai_response(self, session: Dict) -> str:
        """Generate the AI's response, such as an objection or positive reply."""
        current_stage = session['current_call_data']['current_stage']
        if current_stage == 'early_objection':
            available_objections = [obj for obj in EARLY_OBJECTIONS if obj not in session['used_objections']]
            if not available_objections:
                session['used_objections'] = []
                available_objections = EARLY_OBJECTIONS
            objection = random.choice(available_objections)
            session['used_objections'].append(objection)
            return objection
        
        return self.openai_service.generate_roleplay_response(
            session['current_call_data']['conversation_history'][-1]['content'],
            session['current_call_data']['conversation_history'],
            session['user_context'],
            current_stage
        ).get('response', "That's interesting. Please continue.")

    def _handle_call_success(self, session: Dict) -> Dict:
        """Handle a successfully completed call."""
        session['marathon_state']['calls_passed'] += 1
        session['current_call_data']['call_status'] = 'passed'
        ai_response = "That's interesting. I have to run, but send me an email with the details."
        session['current_call_data']['conversation_history'].append({'role': 'assistant', 'content': ai_response})
        return self._start_next_call(session, "Call passed! Great job.")

    def _handle_call_failure(self, session: Dict, reason: str) -> Dict:
        """Handle a failed call."""
        session['marathon_state']['calls_failed'] += 1
        session['current_call_data']['call_status'] = 'failed'
        ai_response = "Sorry, I'm not interested. Goodbye."
        session['current_call_data']['conversation_history'].append({'role': 'assistant', 'content': ai_response})
        logger.warning(f"Call failed for session {session['session_id']}. Reason: {reason}")
        return self._start_next_call(session, f"Call failed: {reason}.")

    def _start_next_call(self, session: Dict, transition_message: str) -> Dict:
        """Finalize the current call and set up the next one."""
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
        """Ends the entire marathon session and provides final results."""
        session = self.active_sessions.pop(session_id, None)
        if not session: return {'success': False, 'error': 'Session not found.'}

        marathon = session['marathon_state']
        if not marathon['is_complete']:
             # If ended prematurely, mark the current call as failed
            if session['current_call_data']['call_status'] == 'in_progress':
                marathon['calls_failed'] += 1
                session['all_calls_data'].append(session['current_call_data'])
            marathon['is_complete'] = True
        
        passed_marathon = marathon['calls_passed'] >= self.config.CALLS_TO_PASS
        
        coaching = {"overall": f"Marathon complete! You passed {marathon['calls_passed']} of {self.config.TOTAL_CALLS} calls."}

        return {
            'success': True,
            'session_success': passed_marathon,
            'overall_score': int((marathon['calls_passed'] / self.config.TOTAL_CALLS) * 100),
            'duration_minutes': (datetime.now(timezone.utc) - datetime.fromisoformat(session['started_at'])).total_seconds() / 60,
            'coaching': coaching,
            'session_data': session,
            'marathon_results': {'calls_passed': marathon['calls_passed'], 'marathon_passed': passed_marathon}
        }
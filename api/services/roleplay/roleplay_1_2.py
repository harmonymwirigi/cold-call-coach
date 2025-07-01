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

    def is_opener(self, text: str) -> bool:
        """
        Heuristic to determine if the user's input is the actual opener,
        not just a greeting.
        """
        text = text.lower()
        opener_keywords = ["calling about", "reason for my call", "calling from", "i'm with", "work with", "help companies"]
        # If it's longer than 5 words OR contains opener keywords, it's likely the opener.
        return len(text.split()) > 5 or any(keyword in text for keyword in opener_keywords)

    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        session = self.active_sessions[session_id]
        call = session['current_call_data']
        marathon = session['marathon_state']

        if marathon['is_complete']:
            return {'success': False, 'error': 'Marathon is already complete.'}
        
        if user_input in ['[SILENCE_IMPATIENCE]', '[SILENCE_HANGUP]']:
            # Handle silence triggers separately
            if user_input == '[SILENCE_IMPATIENCE]':
                return {'success': True, 'ai_response': random.choice(IMPATIENCE_PHRASES), 'call_continues': True}
            else: # '[SILENCE_HANGUP]'
                return self._handle_call_failure(session, "Hung up due to silence")

        call['turn_count'] += 1
        call['conversation_history'].append({'role': 'user', 'content': user_input})
        
        current_stage = call['current_stage']
        
        # --- THE DEFINITIVE FIX ---
        # We only evaluate the opener when the conversation is in the 'phone_pickup' stage
        # AND the user's input looks like a real opener, not just "how are you?".
        if current_stage == 'phone_pickup' and self.is_opener(user_input):
            logger.info("Opener detected. Evaluating as 'opener'.")
            evaluation = self._evaluate_user_input(session, user_input, 'opener')
            if not evaluation.get('passed', False):
                return self._handle_call_failure(session, "Failed evaluation at opener")
            
            # Random hang-up after a SUCCESSFUL opener
            if random.random() < self.config.RANDOM_HANGUP_CHANCE:
                return self._handle_call_failure(session, "Random opener hang-up (unlucky!)")
            
            self._update_session_state(session) # Move to the next stage
        
        # This handles the other evaluation points (objection, mini-pitch)
        elif current_stage in ['early_objection', 'objection_handling']:
            evaluation_stage = 'objection_handling' if current_stage == 'early_objection' else 'mini_pitch'
            logger.info(f"Evaluating user input as '{evaluation_stage}'.")
            evaluation = self._evaluate_user_input(session, user_input, evaluation_stage)
            if not evaluation.get('passed', False):
                return self._handle_call_failure(session, f"Failed evaluation at {evaluation_stage}")
            self._update_session_state(session)
        
        # This handles the initial "Hi, how are you?" where no evaluation is needed.
        else:
            logger.info("Greeting received. Not evaluating. Generating AI response.")
            evaluation = {'passed': True, 'feedback': 'Greeting received.'}
            # The stage does NOT advance here. It remains 'phone_pickup'.

        # Check for successful call completion
        if call['current_stage'] == 'call_ended':
            return self._handle_call_success(session)

        ai_response = self._generate_ai_response(session)
        call['conversation_history'].append({'role': 'assistant', 'content': ai_response})
        
        return {'success': True, 'ai_response': ai_response, 'call_continues': True, 'marathon_status': marathon, 'evaluation': evaluation}

    def _evaluate_user_input(self, session: Dict, user_input: str, stage: str) -> Dict:
        # This method is now only called when an evaluation is actually required.
        if not self.is_openai_available():
            return {'passed': len(user_input.split()) > 3, 'score': 3} # Simple fallback
        return self.openai_service.evaluate_user_input(user_input, session['current_call_data']['conversation_history'], stage)

    def _update_session_state(self, session: Dict):
        """Moves to the next stage in the flow."""
        current_stage = session['current_call_data']['current_stage']
        next_stage = self.config.STAGE_FLOW.get(current_stage, 'call_ended') # Default to end if stage not found
        session['current_call_data']['current_stage'] = next_stage
        logger.info(f"Session {session['session_id']} moved to stage: {next_stage}")

    def _generate_ai_response(self, session: Dict) -> str:
        current_stage = session['current_call_data']['current_stage']
        
        # If the stage is 'early_objection', the AI must give an objection.
        if current_stage == 'early_objection':
            available_objections = [obj for obj in EARLY_OBJECTIONS if obj not in session['used_objections']]
            if not available_objections:
                session['used_objections'] = []
                available_objections = EARLY_OBJECTIONS
            objection = random.choice(available_objections)
            session['used_objections'].append(objection)
            return objection
        
        # For all other stages, generate a natural response.
        if self.is_openai_available():
            return self.openai_service.generate_roleplay_response(
                session['current_call_data']['conversation_history'][-1]['content'],
                session['current_call_data']['conversation_history'],
                session['user_context'],
                current_stage
            ).get('response', "I'm listening...")
        else:
            return "Okay, go on."

    # --- The rest of the methods (_handle_call_success, _handle_call_failure, _start_next_call, end_session) are unchanged from the previous version. ---

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
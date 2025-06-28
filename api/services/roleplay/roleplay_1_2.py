# ===== FIXED: services/roleplay/roleplay_1_2.py =====
# This is a complete rewrite to strictly follow the Marathon Mode specification.

import random
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

from .base_roleplay import BaseRoleplay
from .configs.roleplay_1_2_config import Roleplay12Config
from utils.constants import EARLY_OBJECTIONS, IMPATIENCE_PHRASES, ROLEPLAY_1_RUBRICS

logger = logging.getLogger(__name__)

class Roleplay12(BaseRoleplay):
    """
    Roleplay 1.2 - Marathon Mode.
    Implements the structured, game-like flow from the specification.
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
        session_id = f"{user_id}_{self.config.ROLEPLAY_ID}_{mode}_{int(datetime.now().timestamp())}"
        
        session_data = {
            'session_id': session_id, 'user_id': user_id, 'roleplay_id': self.roleplay_id,
            'mode': 'marathon', 'started_at': datetime.now(timezone.utc).isoformat(),
            'user_context': user_context, 'session_active': True,
            'marathon_state': {
                'current_call_number': 1, 'calls_passed': 0, 'calls_failed': 0,
            },
            'all_calls_data': [], 'used_objections': set(),
            'current_call_data': self._initialize_call_data(),
        }
        
        self.active_sessions[session_id] = session_data
        initial_response = self._get_contextual_initial_response(user_context)
        session_data['current_call_data']['conversation_history'].append({'role': 'assistant', 'content': initial_response})
        
        return {
            'success': True, 'session_id': session_id, 'initial_response': initial_response,
            'roleplay_info': self.get_roleplay_info(), 'marathon_status': session_data['marathon_state']
        }

    def _initialize_call_data(self) -> Dict[str, Any]:
        return {
            'conversation_history': [], 'current_stage': 'opener_stage', 'turn_count': 0, 
            'call_status': 'in_progress', 'call_start_time': datetime.now(timezone.utc)
        }

    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        session = self.active_sessions.get(session_id)
        if not session: return {'success': False, 'error': 'Session not found.'}

        # Handle silence triggers first
        if user_input == '[SILENCE_IMPATIENCE]':
            return {'success': True, 'ai_response': random.choice(IMPATIENCE_PHRASES), 'call_continues': True, 'marathon_status': session['marathon_state']}
        if user_input == '[SILENCE_HANGUP]':
            return self._handle_call_failure(session, "Hung up due to silence")

        call = session['current_call_data']
        call['turn_count'] += 1
        call['conversation_history'].append({'role': 'user', 'content': user_input})
        
        # --- CORE STATE MACHINE LOGIC ---
        stage = call['current_stage']
        
        if stage == 'opener_stage':
            passed = self._evaluate_with_rubric(user_input, ROLEPLAY_1_RUBRICS['opener'])
            if not passed:
                return self._handle_call_failure(session, "Failed opener evaluation")
            
            # Random hang-up on pass
            if random.random() < self.config.RANDOM_HANGUP_CHANCE:
                return self._handle_call_failure(session, "Random opener hang-up")
                
            # Move to next stage
            call['current_stage'] = 'objection_stage'
            objection = self._get_unique_objection(session)
            call['conversation_history'].append({'role': 'assistant', 'content': objection})
            return {'success': True, 'ai_response': objection, 'call_continues': True, 'marathon_status': session['marathon_state']}

        elif stage == 'objection_stage':
            passed = self._evaluate_with_rubric(user_input, ROLEPLAY_1_RUBRICS['objection_handling'])
            if not passed:
                return self._handle_call_failure(session, "Failed objection handling")
                
            # Move to next stage
            call['current_stage'] = 'mini_pitch_stage'
            pitch_prompt = "Okay, you have 30 seconds. Go ahead."
            call['conversation_history'].append({'role': 'assistant', 'content': pitch_prompt})
            return {'success': True, 'ai_response': pitch_prompt, 'call_continues': True, 'marathon_status': session['marathon_state']}
            
        elif stage == 'mini_pitch_stage':
            passed = self._evaluate_with_rubric(user_input, ROLEPLAY_1_RUBRICS['mini_pitch'])
            if not passed:
                return self._handle_call_failure(session, "Failed mini-pitch")
            
            # A passed mini-pitch is a successful call in this mode
            return self._handle_call_success(session)

        return self._handle_call_failure(session, "Invalid call stage")

    def _evaluate_with_rubric(self, user_input: str, rubric: dict) -> bool:
        """Uses OpenAI to evaluate input against a rubric, returning True for pass, False for fail."""
        if not self.is_openai_available():
            # Basic fallback: pass if input is reasonably long
            return len(user_input.split()) > 3

        # This reuses the powerful evaluation from the Practice Mode
        evaluation = self.openai_service.evaluate_user_input(
            user_input, [], rubric['name'] # Pass empty history for isolated evaluation
        )
        return evaluation.get('passed', False)

    def _get_unique_objection(self, session: Dict) -> str:
        """Picks a unique objection for the current marathon run."""
        available = [obj for obj in EARLY_OBJECTIONS if obj not in session['used_objections']]
        if not available:
            session['used_objections'].clear() # Reset if all have been used
            available = EARLY_OBJECTIONS
        
        objection = random.choice(available)
        session['used_objections'].add(objection)
        return objection

    def _handle_call_success(self, session: Dict) -> Dict:
        session['marathon_state']['calls_passed'] += 1
        session['current_call_data']['call_status'] = 'passed'
        ai_response = "That sounds interesting. I have to run, but send me an email with the details."
        session['current_call_data']['conversation_history'].append({'role': 'assistant', 'content': ai_response})
        return self._start_next_call(session, "Call passed! Great job.")

    def _handle_call_failure(self, session: Dict, reason: str) -> Dict:
        session['marathon_state']['calls_failed'] += 1
        session['current_call_data']['call_status'] = 'failed'
        ai_response = f"Sorry, I'm not interested. Goodbye."
        session['current_call_data']['conversation_history'].append({'role': 'assistant', 'content': ai_response})
        logger.warning(f"Call failed for session {session['session_id']}. Reason: {reason}")
        return self._start_next_call(session, f"Call failed: {reason}")

    def _start_next_call(self, session: Dict, transition_message: str) -> Dict:
        """Finalize the current call and set up the next one or end the marathon."""
        session['all_calls_data'].append(session['current_call_data'])
        marathon = session['marathon_state']
        
        # Check if marathon is over
        if marathon['current_call_number'] >= self.config.TOTAL_CALLS:
            return self.end_session(session['session_id'])

        # Prepare for the next call
        marathon['current_call_number'] += 1
        session['current_call_data'] = self._initialize_call_data()
        
        ai_response = self._get_contextual_initial_response(session['user_context'])
        session['current_call_data']['conversation_history'].append({'role': 'assistant', 'content': ai_response})
        
        return {
            'success': True, 'ai_response': ai_response, 'call_continues': True,
            'marathon_status': marathon, 'new_call_started': True, 'transition_message': transition_message
        }
    
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """Ends the entire marathon session and provides final results."""
        session = self.active_sessions.pop(session_id, None)
        if not session: return {'success': True, 'message': 'Session already ended.'}

        marathon = session['marathon_state']
        # Ensure final call is accounted for if ended prematurely
        if marathon['current_call_number'] <= self.config.TOTAL_CALLS and session['current_call_data']['call_status'] == 'in_progress':
             session['marathon_state']['calls_failed'] += 1
             session['all_calls_data'].append(session['current_call_data'])

        passed_marathon = marathon['calls_passed'] >= self.config.CALLS_TO_PASS
        
        coaching = {"overall": f"Marathon complete! You passed {marathon['calls_passed']} of {self.config.TOTAL_CALLS} calls."}

        return {
            'success': True, 'session_success': passed_marathon, 'call_continues': False,
            'overall_score': int((marathon['calls_passed'] / self.config.TOTAL_CALLS) * 100),
            'duration_minutes': (datetime.now(timezone.utc) - datetime.fromisoformat(session['started_at'])).total_seconds() / 60,
            'coaching': coaching, 'session_data': session,
            'marathon_results': {'calls_passed': marathon['calls_passed'], 'marathon_passed': passed_marathon}
        }
# ===== services/roleplay/roleplay_1_2.py =====

import random
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any
from .base_roleplay import BaseRoleplay
from .configs.roleplay_1_2_config import Roleplay12Config
from utils.constants import EARLY_OBJECTIONS # Import from constants

logger = logging.getLogger(__name__)

class Roleplay12(BaseRoleplay):
    """Roleplay 1.2 - Marathon Mode: 10 calls, need 6 to pass"""
    
    def __init__(self, openai_service=None):
        super().__init__(openai_service)
        self.config = Roleplay12Config()
        self.roleplay_id = self.config.ROLEPLAY_ID

    def get_roleplay_info(self) -> Dict[str, Any]:
        """Return Roleplay 1.2 configuration"""
        return {
            'id': self.config.ROLEPLAY_ID,
            'name': self.config.NAME,
            'description': self.config.DESCRIPTION,
            'type': 'marathon',
            'total_calls': self.config.TOTAL_CALLS,
            'calls_to_pass': self.config.CALLS_TO_PASS
        }

    def create_session(self, user_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create a new Marathon session"""
        session_id = f"{user_id}_{self.config.ROLEPLAY_ID}_{mode}_{int(datetime.now().timestamp())}"
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'roleplay_id': self.config.ROLEPLAY_ID,
            'mode': mode,
            'started_at': datetime.now(timezone.utc).isoformat(),
            'user_context': user_context,
            'session_active': True,
            
            # Marathon specific state
            'marathon_state': {
                'current_call_number': 1,
                'calls_passed': 0,
                'calls_failed': 0,
                'is_complete': False,
            },
            'all_calls_data': [],
            'used_objections': [], # Use a list to respect order if needed
            'current_call_data': self._initialize_call_data()
        }
        
        self.active_sessions[session_id] = session_data
        
        initial_response = self._get_contextual_initial_response(user_context)
        session_data['current_call_data']['conversation_history'].append({
            'role': 'assistant', 'content': initial_response, 'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        return {
            'success': True,
            'session_id': session_id,
            'initial_response': initial_response,
            'roleplay_info': self.get_roleplay_info(),
            'marathon_status': session_data['marathon_state']
        }

    def _initialize_call_data(self) -> Dict[str, Any]:
        """Initialize data for a new call within the marathon."""
        return {
            'conversation_history': [],
            'current_stage': 'phone_pickup',
            'turn_count': 0,
            'call_status': 'in_progress', # in_progress, passed, failed
            'rubric_scores': {}
        }

    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input for the current call in the marathon."""
        session = self.active_sessions[session_id]
        call = session['current_call_data']
        marathon = session['marathon_state']

        if marathon['is_complete']:
            return {'success': False, 'error': 'Marathon is already complete.'}

        # --- Main Call Logic ---
        call['turn_count'] += 1
        call['conversation_history'].append({'role': 'user', 'content': user_input})
        
        # Evaluate user input based on the current stage
        evaluation = self._evaluate_user_input(session, user_input)
        
        # Check for failure conditions that end the current call
        if not evaluation.get('passed', False):
            return self._handle_call_failure(session, "Failed evaluation")

        # Check for random hang-up on opener pass
        if call['current_stage'] == 'opener_evaluation' and random.random() < self.config.RANDOM_HANGUP_CHANCE:
            return self._handle_call_failure(session, "Random hang-up")

        # Progress to the next stage
        self._update_session_state(session)
        
        # If the call is successfully completed (i.e., passed all stages)
        if call['current_stage'] == 'call_ended':
            return self._handle_call_success(session)

        # Generate the AI's next response (e.g., an objection)
        ai_response = self._generate_ai_response(session)
        call['conversation_history'].append({'role': 'assistant', 'content': ai_response})
        
        return {
            'success': True,
            'ai_response': ai_response,
            'call_continues': True,
            'evaluation': evaluation,
            'marathon_status': marathon
        }

    def _evaluate_user_input(self, session: Dict, user_input: str) -> Dict:
        """Evaluate user input using rubrics. Returns a simple pass/fail."""
        # This would use the same rubric logic from Roleplay 1.1
        # For simplicity, we'll simulate it here. A real implementation would call openai_service
        score = len(user_input.split()) # Simple heuristic
        is_pass = score > 5
        return {'passed': is_pass, 'score': score}

    def _update_session_state(self, session: Dict):
        """Move to the next stage in the call flow."""
        current_stage = session['current_call_data']['current_stage']
        next_stage = self.config.STAGE_FLOW.get(current_stage)
        session['current_call_data']['current_stage'] = next_stage
        logger.info(f"Session {session['session_id']} moved to stage: {next_stage}")

    def _generate_ai_response(self, session: Dict) -> str:
        """Generate the AI's response, such as an objection."""
        if session['current_call_data']['current_stage'] == 'early_objection':
            available_objections = [obj for obj in EARLY_OBJECTIONS if obj not in session['used_objections']]
            if not available_objections: # Reset if we run out
                available_objections = EARLY_OBJECTIONS
            
            objection = random.choice(available_objections)
            session['used_objections'].append(objection)
            return objection
        
        return "That's interesting. What do you mean by that?"

    def _handle_call_success(self, session: Dict) -> Dict:
        """Handle a successfully completed call."""
        session['marathon_state']['calls_passed'] += 1
        session['current_call_data']['call_status'] = 'passed'
        return self._start_next_call(session, "Great job! Next call.")

    def _handle_call_failure(self, session: Dict, reason: str) -> Dict:
        """Handle a failed call."""
        session['marathon_state']['calls_failed'] += 1
        session['current_call_data']['call_status'] = 'failed'
        logger.warning(f"Call failed for session {session['session_id']}. Reason: {reason}")
        return self._start_next_call(session, f"Let's try that again. {reason}. Next call.")

    def _start_next_call(self, session: Dict, transition_message: str) -> Dict:
        """Finalize the current call and set up the next one."""
        # Archive the completed call's data
        session['all_calls_data'].append(session['current_call_data'])
        
        marathon = session['marathon_state']
        if marathon['current_call_number'] >= self.config.TOTAL_CALLS:
            marathon['is_complete'] = True
            # The session will be ended by the main end_session method
            return {
                'success': True,
                'ai_response': "Marathon run complete. Ending session.",
                'call_continues': False,
                'marathon_status': marathon
            }

        # Prepare for the next call
        marathon['current_call_number'] += 1
        session['current_call_data'] = self._initialize_call_data()
        
        # Get the new initial response for the next call
        ai_response = self._get_contextual_initial_response(session['user_context'])
        session['current_call_data']['conversation_history'].append({
            'role': 'assistant', 'content': ai_response
        })
        
        return {
            'success': True,
            'ai_response': ai_response,
            'call_continues': True, # The marathon continues with a new call
            'marathon_status': marathon,
            'new_call_started': True,
            'transition_message': transition_message
        }
    
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """Ends the entire marathon session and provides final results."""
        session = self.active_sessions.pop(session_id, None)
        if not session:
            return {'success': False, 'error': 'Session not found.'}

        marathon = session['marathon_state']
        marathon['is_complete'] = True
        
        passed_marathon = marathon['calls_passed'] >= self.config.CALLS_TO_PASS
        
        # Generate final coaching feedback (simplified)
        coaching = {
            "overall": f"You completed the marathon with {marathon['calls_passed']} successful calls out of {self.config.TOTAL_CALLS}."
        }

        return {
            'success': True,
            'session_success': passed_marathon,
            'overall_score': int((marathon['calls_passed'] / self.config.TOTAL_CALLS) * 100),
            'duration_minutes': (datetime.now(timezone.utc) - datetime.fromisoformat(session['started_at'])).total_seconds() / 60,
            'coaching': coaching,
            'session_data': session, # For saving to DB
            'marathon_results': {
                'calls_passed': marathon['calls_passed'],
                'marathon_passed': passed_marathon
            }
        }
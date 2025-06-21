# ===== services/roleplay/roleplay_1_3.py (Legend Mode) =====

import random
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from .base_roleplay import BaseRoleplay
from .configs.roleplay_1_3_config import Roleplay13Config

logger = logging.getLogger(__name__)

class Roleplay13(BaseRoleplay):
    """Roleplay 1.3 - Legend Mode: 6 perfect calls in a row"""
    
    def __init__(self, openai_service=None):
        super().__init__(openai_service)
        self.config = Roleplay13Config()
        
    def get_roleplay_info(self) -> Dict[str, Any]:
        """Return Roleplay 1.3 configuration"""
        return {
            'id': self.config.ROLEPLAY_ID,
            'name': self.config.NAME,
            'description': self.config.DESCRIPTION,
            'type': 'legend',
            'features': {
                'ai_evaluation': True,
                'perfect_calls_required': True,
                'no_mistakes_allowed': True,
                'elite_challenge': True,
                'bragging_rights': True
            },
            'total_calls': self.config.TOTAL_CALLS,
            'perfect_calls_required': self.config.PERFECT_CALLS_REQUIRED
        }
    
    def create_session(self, user_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create new Legend Mode session"""
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
                
                # Legend specific fields
                'legend_state': {
                    'current_call': 1,
                    'total_calls': self.config.TOTAL_CALLS,
                    'perfect_calls': 0,
                    'failed_calls': 0,
                    'required_perfect': self.config.PERFECT_CALLS_REQUIRED,
                    'is_complete': False,
                    'is_legend': False,
                    'failure_reasons': []
                },
                
                # Current call state
                'current_call_data': self._initialize_call_data(),
                
                # Legend tracking
                'all_calls_data': [],
                'overall_performance': {
                    'total_interactions': 0,
                    'perfect_stages': 0,
                    'rubric_scores_aggregate': {}
                }
            }
            
            # Store session
            self.active_sessions[session_id] = session_data
            
            # Generate initial response
            initial_response = self._get_initial_response(user_context)
            
            # Add to current call conversation
            session_data['current_call_data']['conversation_history'].append({
                'role': 'assistant',
                'content': initial_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': 'phone_pickup'
            })
            
            logger.info(f"Created Legend Mode session {session_id} - Call 1/{self.config.TOTAL_CALLS}")
            
            return {
                'success': True,
                'session_id': session_id,
                'initial_response': initial_response,
                'roleplay_info': self.get_roleplay_info(),
                'legend_status': self._get_legend_status(session_data)
            }
            
        except Exception as e:
            logger.error(f"Error creating Legend Mode session: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input for Legend Mode - VERY strict evaluation"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            
            if not session.get('session_active'):
                raise ValueError("Session not active")
            
            # Check if legend challenge is complete
            if session['legend_state']['is_complete']:
                return {
                    'success': True,
                    'ai_response': "Legend challenge complete! Check your results.",
                    'call_continues': False,
                    'legend_complete': True,
                    'legend_status': self._get_legend_status(session)
                }
            
            current_call = session['current_call_data']
            
            # Increment counters
            current_call['turn_count'] += 1
            session['overall_performance']['total_interactions'] += 1
            
            # Add user input to conversation
            current_call['conversation_history'].append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': current_call['current_stage']
            })
            
            # STRICT evaluation for Legend Mode
            evaluation = self._evaluate_user_input_strict(session, user_input)
            
            # In Legend Mode, any failure immediately ends the call
            if not evaluation.get('perfect', False):
                logger.info("Legend Mode failure - imperfect performance detected")
                return self._handle_legend_failure(session, evaluation)
            
            # Generate AI response for perfect performance
            ai_response = self._generate_ai_response(session, user_input, evaluation)
            
            # Update session state
            self._update_session_state(session, evaluation)
            
            # Check if current call should end (perfect completion)
            call_should_end = self._should_current_call_end(session, evaluation)
            
            if call_should_end:
                return self._handle_perfect_call_completion(session, ai_response, evaluation)
            
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
                'legend_status': self._get_legend_status(session),
                'current_call': session['legend_state']['current_call'],
                'total_calls': session['legend_state']['total_calls']
            }
            
        except Exception as e:
            logger.error(f"Error processing Legend Mode input: {e}")
            return {'success': False, 'error': str(e), 'call_continues': False}
    
    def _evaluate_user_input_strict(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """VERY strict evaluation for Legend Mode - must be perfect"""
        try:
            if self.is_openai_available():
                # Use AI evaluation with LEGEND MODE strictness
                evaluation = self.openai_service.evaluate_user_input(
                    user_input,
                    session['current_call_data']['conversation_history'],
                    'legend_mode_strict'  # Special mode for ultra-strict evaluation
                )
                
                # In Legend Mode, score must be perfect (4/4 or equivalent)
                max_score = evaluation.get('max_score', 4)
                score = evaluation.get('score', 0)
                evaluation['perfect'] = (score >= max_score)
                
                return evaluation
            else:
                return self._basic_strict_evaluation(user_input)
                
        except Exception as e:
            logger.error(f"Legend Mode evaluation error: {e}")
            return self._basic_strict_evaluation(user_input)
    
    def _basic_strict_evaluation(self, user_input: str) -> Dict[str, Any]:
        """Ultra-strict basic evaluation for Legend Mode"""
        score = 0
        criteria_met = []
        user_input_lower = user_input.lower().strip()
        
        # Must meet ALL criteria for each stage
        required_phrases = ["i'm calling", "calling from", "calling about"]
        contractions = ["i'm", "don't", "can't", "won't"]
        empathy_phrases = ["know this is", "out of the blue", "sorry to"]
        
        if len(user_input.strip()) > 20:  # Higher bar
            score += 1
            criteria_met.append('substantial_opener')
        
        if any(phrase in user_input_lower for phrase in required_phrases):
            score += 1
            criteria_met.append('clear_opener')
        
        if any(contraction in user_input_lower for contraction in contractions):
            score += 1
            criteria_met.append('casual_tone')
        
        if any(empathy in user_input_lower for empathy in empathy_phrases):
            score += 1
            criteria_met.append('shows_empathy')
        
        # Legend Mode requires PERFECT score (4/4)
        perfect = (score >= 4)
        
        return {
            'score': score,
            'max_score': 4,
            'perfect': perfect,
            'passed': perfect,
            'criteria_met': criteria_met,
            'feedback': f'Legend evaluation: {score}/4 criteria met',
            'should_continue': perfect,
            'hang_up_probability': 0.0 if perfect else 1.0,  # Immediate failure if not perfect
            'source': 'legend_strict',
            'stage': 'opener'
        }
    
    def _handle_legend_failure(self, session: Dict, evaluation: Dict) -> Dict[str, Any]:
        """Handle failure in Legend Mode"""
        current_call = session['current_call_data']
        legend_state = session['legend_state']
        
        # Mark call as failed
        current_call['call_status'] = 'failed'
        current_call['end_reason'] = 'imperfect_performance'
        current_call['ended_at'] = datetime.now(timezone.utc).isoformat()
        
        # Record failure reason
        failure_reason = f"Call {legend_state['current_call']}: {evaluation.get('feedback', 'Performance not perfect')}"
        legend_state['failure_reasons'].append(failure_reason)
        
        # Update legend state
        legend_state['failed_calls'] += 1
        session['all_calls_data'].append(current_call)
        
        # Legend challenge failed
        legend_state['is_complete'] = True
        legend_state['is_legend'] = False
        
        failure_response = random.choice([
            "Sorry, I'm not interested. Goodbye.",
            "This doesn't sound right. I'm hanging up.",
            "Not what I was expecting. Have a good day."
        ])
        
        current_call['conversation_history'].append({
            'role': 'assistant',
            'content': failure_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': current_call['current_stage'],
            'failure': True
        })
        
        return {
            'success': True,
            'ai_response': failure_response,
            'call_continues': False,
            'call_result': 'failed',
            'legend_complete': True,
            'legend_achieved': False,
            'legend_status': self._get_legend_status(session),
            'failure_reason': failure_reason
        }
    
    def _handle_perfect_call_completion(self, session: Dict, ai_response: str, evaluation: Dict) -> Dict[str, Any]:
        """Handle perfect call completion"""
        current_call = session['current_call_data']
        legend_state = session['legend_state']
        
        # Mark call as perfect
        current_call['call_status'] = 'perfect'
        current_call['end_reason'] = 'perfect_completion'
        current_call['ended_at'] = datetime.now(timezone.utc).isoformat()
        
        # Add final AI response
        success_response = random.choice([
            "That sounds excellent. Send me the details and let's schedule a meeting.",
            "Perfect! I'm very interested. When can we talk more?",
            "Exactly what we need. Please send over the information."
        ])
        
        current_call['conversation_history'].append({
            'role': 'assistant',
            'content': success_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'perfect_completion',
            'perfect': True
        })
        
        # Update legend state
        legend_state['perfect_calls'] += 1
        session['all_calls_data'].append(current_call)
        
        # Check if legend achieved
        if legend_state['perfect_calls'] >= legend_state['required_perfect']:
            # LEGEND ACHIEVED!
            legend_state['is_complete'] = True
            legend_state['is_legend'] = True
            
            return {
                'success': True,
                'ai_response': success_response,
                'call_continues': False,
                'call_result': 'perfect',
                'legend_complete': True,
                'legend_achieved': True,
                'legend_status': self._get_legend_status(session),
                'congratulations': "🏆 LEGEND STATUS ACHIEVED! 🏆"
            }
        else:
            # Continue to next call
            return self._start_next_legend_call(session, success_response)
    
    def _start_next_legend_call(self, session: Dict, previous_response: str) -> Dict[str, Any]:
        """Start the next call in legend challenge"""
        legend_state = session['legend_state']
        
        # Increment call number
        legend_state['current_call'] += 1
        
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
        
        logger.info(f"Started legend call {legend_state['current_call']}/{legend_state['total_calls']}")
        
        return {
            'success': True,
            'ai_response': initial_response,
            'call_continues': True,
            'call_result': 'next_call',
            'previous_call_response': previous_response,
            'legend_status': self._get_legend_status(session),
            'new_call_started': True
        }
    
    def _get_legend_status(self, session: Dict) -> Dict[str, Any]:
        """Get current legend status"""
        legend_state = session['legend_state']
        return {
            'current_call': legend_state['current_call'],
            'total_calls': legend_state['total_calls'],
            'perfect_calls': legend_state['perfect_calls'],
            'failed_calls': legend_state['failed_calls'],
            'required_perfect': legend_state['required_perfect'],
            'is_complete': legend_state['is_complete'],
            'is_legend': legend_state['is_legend'],
            'calls_remaining': legend_state['total_calls'] - len(session['all_calls_data']),
            'progress_percentage': (legend_state['perfect_calls'] / legend_state['required_perfect']) * 100,
            'failure_reasons': legend_state.get('failure_reasons', [])
        }
    
    # ... (Additional methods similar to Marathon mode but with perfect requirements)
    
    def _initialize_call_data(self) -> Dict[str, Any]:
        """Initialize data for a new call"""
        return {
            'conversation_history': [],
            'current_stage': 'phone_pickup',
            'turn_count': 0,
            'call_status': 'in_progress',
            'end_reason': None,
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

# ===== services/roleplay/configs/roleplay_1_3_config.py =====

class Roleplay13Config:
    """Configuration for Roleplay 1.3 - Legend Mode"""
    
    ROLEPLAY_ID = "1.3"
    NAME = "Legend Mode"
    DESCRIPTION = "6 perfect calls in a row - the ultimate challenge"
    
    # Legend specific settings
    TOTAL_CALLS = 6
    PERFECT_CALLS_REQUIRED = 6
    
    # No tolerance for mistakes in Legend Mode
    PERFECTION_REQUIRED = True
    
    # Stage flow (same as other modes but stricter evaluation)
    STAGE_FLOW = {
        'phone_pickup': 'opener_evaluation',
        'opener_evaluation': 'early_objection',
        'early_objection': 'objection_handling',
        'objection_handling': 'mini_pitch',
        'mini_pitch': 'soft_discovery',
        'soft_discovery': 'perfect_completion'
    }
    
    # Silence thresholds (same as other modes)
    IMPATIENCE_THRESHOLD = 10000
    HANGUP_THRESHOLD = 15000
    
    # Perfect thresholds (must score maximum on everything)
    PERFECT_THRESHOLDS = {
        'opener': 4,           # Must get 4/4
        'objection_handling': 4, # Must get 4/4
        'mini_pitch': 4,       # Must get 4/4
        'soft_discovery': 3    # Must get 3/3
    }

# ===== API/SERVICES/ROLEPLAY_ENGINE.PY =====
import random
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from services.openai_service import OpenAIService
from services.supabase_client import SupabaseService
from utils.constants import (
    ROLEPLAY_CONFIG, EARLY_OBJECTIONS, POST_PITCH_OBJECTIONS, 
    PITCH_PROMPTS, PASS_CRITERIA, SUCCESS_MESSAGES, WARMUP_QUESTIONS
)

logger = logging.getLogger(__name__)

class RoleplayEngine:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.supabase_service = SupabaseService()
        
        # Session state tracking
        self.active_sessions = {}
        
    def create_session(self, user_id: str, roleplay_id: int, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create a new roleplay session"""
        try:
            # Validate inputs
            if roleplay_id not in ROLEPLAY_CONFIG:
                raise ValueError(f"Invalid roleplay ID: {roleplay_id}")
            
            config = ROLEPLAY_CONFIG[roleplay_id]
            if mode not in config.get('modes', []):
                raise ValueError(f"Invalid mode '{mode}' for roleplay {roleplay_id}")
            
            # Create session data
            session_id = f"{user_id}_{roleplay_id}_{mode}_{datetime.now().timestamp()}"
            
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'roleplay_id': roleplay_id,
                'mode': mode,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'user_context': user_context,
                'conversation_history': [],
                'current_stage': self._get_initial_stage(roleplay_id),
                'objections_used': [],
                'questions_used': [],
                'call_count': 0,
                'successful_calls': 0,
                'current_call_success': False,
                'session_active': True,
                'hang_up_triggered': False,
                'qualification_achieved': False,
                'meeting_asked': False
            }
            
            # Store session
            self.active_sessions[session_id] = session_data
            
            # Generate initial response
            initial_response = self._generate_initial_response(roleplay_id, mode, user_context)
            
            # Add to conversation history
            if initial_response:
                session_data['conversation_history'].append({
                    'role': 'assistant',
                    'content': initial_response,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'stage': session_data['current_stage']
                })
            
            logger.info(f"Created session {session_id} for user {user_id}")
            
            return {
                'success': True,
                'session_id': session_id,
                'initial_response': initial_response,
                'session_data': session_data
            }
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input and generate AI response"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            
            if not session.get('session_active'):
                raise ValueError("Session is not active")
            
            # Add user input to conversation
            session['conversation_history'].append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage']
            })
            
            # Evaluate user input and determine response
            evaluation = self._evaluate_user_input(session, user_input)
            
            # Check for immediate hang-up conditions
            if evaluation.get('should_hang_up'):
                return self._handle_hang_up(session, evaluation.get('hang_up_reason', 'Poor response'))
            
            # Generate AI response
            ai_response = self._generate_ai_response(session, user_input, evaluation)
            
            # Add AI response to conversation
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage']
            })
            
            # Update session state
            self._update_session_state(session, evaluation)
            
            # Check if call/session should end
            call_continues = self._should_call_continue(session, evaluation)
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': call_continues,
                'evaluation': evaluation,
                'session_state': session['current_stage']
            }
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            return {
                'success': False,
                'error': str(e),
                'call_continues': False
            }
    
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End roleplay session and generate coaching"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            session['session_active'] = False
            session['ended_at'] = datetime.now(timezone.utc).isoformat()
            
            # Calculate session metrics
            started_at = datetime.fromisoformat(session['started_at'].replace('Z', '+00:00'))
            ended_at = datetime.now(timezone.utc)
            duration_minutes = int((ended_at - started_at).total_seconds() / 60)
            
            # Generate coaching feedback
            coaching_result = self.openai_service.generate_coaching_feedback(
                session, session['user_context']
            )
            
            coaching_feedback = coaching_result.get('coaching', {}) if coaching_result['success'] else {}
            overall_score = coaching_result.get('overall_score', 0) if coaching_result['success'] else 0
            
            # Determine session success
            session_success = self._determine_session_success(session)
            
            # Update user progress if applicable
            if session_success and not forced_end:
                self._update_user_progress(session)
            
            # Clean up session
            del self.active_sessions[session_id]
            
            # Generate completion message
            completion_message = self._generate_completion_message(session, session_success)
            
            return {
                'success': True,
                'duration_minutes': duration_minutes,
                'session_success': session_success,
                'coaching': coaching_feedback,
                'overall_score': overall_score,
                'completion_message': completion_message,
                'session_data': session
            }
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_initial_stage(self, roleplay_id: int) -> str:
        """Get initial conversation stage for roleplay"""
        stage_map = {
            1: 'phone_pickup',      # Opener + Early Objections
            2: 'ai_pitch_prompt',   # Pitch + Objections + Close  
            3: 'warmup_question',   # Warm-up Challenge
            4: 'phone_pickup',      # Full Cold Call
            5: 'phone_pickup'       # Power Hour
        }
        return stage_map.get(roleplay_id, 'phone_pickup')
    
    def _generate_initial_response(self, roleplay_id: int, mode: str, user_context: Dict) -> str:
        """Generate initial AI response for the roleplay"""
        if roleplay_id == 2:  # Pitch + Objections starts with AI prompt
            return random.choice(PITCH_PROMPTS)
        elif roleplay_id == 3:  # Warm-up Challenge starts with question
            return self._get_warmup_question()
        else:  # Standard phone pickup
            return "Hello?"
    
    def _get_warmup_question(self) -> str:
        """Get random warmup question"""
        return random.choice(WARMUP_QUESTIONS)
    
    def _evaluate_user_input(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Evaluate user input quality and determine next action"""
        roleplay_id = session['roleplay_id']
        current_stage = session['current_stage']
        conversation_length = len([msg for msg in session['conversation_history'] if msg['role'] == 'user'])
        
        evaluation = {
            'quality_score': 5,  # Default medium score
            'should_hang_up': False,
            'hang_up_reason': None,
            'stage_completed': False,
            'next_stage': current_stage,
            'feedback_notes': []
        }
        
        # Stage-specific evaluation
        if current_stage == 'phone_pickup':
            evaluation = self._evaluate_opener(user_input, evaluation)
        elif current_stage == 'early_objection':
            evaluation = self._evaluate_objection_handling(user_input, evaluation)
        elif current_stage == 'mini_pitch':
            evaluation = self._evaluate_mini_pitch(user_input, evaluation)
        elif current_stage == 'post_pitch_objections':
            evaluation = self._evaluate_post_pitch_response(user_input, evaluation, session)
        elif current_stage == 'warmup_question':
            evaluation = self._evaluate_warmup_answer(user_input, evaluation)
        
        # Check for hang-up conditions (for roleplays 1, 4, 5)
        if roleplay_id in [1, 4, 5] and current_stage == 'phone_pickup':
            hang_up_chance = ROLEPLAY_CONFIG[roleplay_id].get('hang_up_chance', 0)
            if evaluation['quality_score'] <= 3 and random.random() < hang_up_chance:
                evaluation['should_hang_up'] = True
                evaluation['hang_up_reason'] = 'Poor opener quality'
        
        return evaluation
    
    def _evaluate_opener(self, user_input: str, evaluation: Dict) -> Dict:
        """Evaluate opener quality"""
        user_input_lower = user_input.lower()
        
        # Check opener criteria
        criteria_met = 0
        
        # 1. Clear cold call opener
        if any(phrase in user_input_lower for phrase in ['hi', 'hello', 'good morning', 'good afternoon']):
            criteria_met += 1
        
        # 2. Casual, confident tone (contractions)
        if any(contraction in user_input_lower for contraction in ["i'm", "we're", "don't", "won't", "can't"]):
            criteria_met += 1
        
        # 3. Demonstrates empathy
        empathy_phrases = ['out of the blue', "don't know me", 'unexpected', 'interrupting', 'quick question']
        if any(phrase in user_input_lower for phrase in empathy_phrases):
            criteria_met += 1
        
        # 4. Ends with soft question
        if user_input.strip().endswith('?'):
            criteria_met += 1
        
        # Score based on criteria met
        evaluation['quality_score'] = max(1, criteria_met * 2)
        evaluation['criteria_met'] = criteria_met
        
        if criteria_met >= 3:  # Pass threshold
            evaluation['stage_completed'] = True
            evaluation['next_stage'] = 'early_objection'
        
        return evaluation
    
    def _evaluate_objection_handling(self, user_input: str, evaluation: Dict) -> Dict:
        """Evaluate objection handling quality"""
        user_input_lower = user_input.lower()
        
        criteria_met = 0
        
        # 1. Acknowledges calmly
        acknowledge_phrases = ['fair enough', 'totally get', 'understand', 'i hear you', 'makes sense']
        if any(phrase in user_input_lower for phrase in acknowledge_phrases):
            criteria_met += 1
        
        # 2. Doesn't argue immediately
        argument_phrases = ['no', 'but you', "you're wrong", 'actually']
        if not any(phrase in user_input_lower for phrase in argument_phrases):
            criteria_met += 1
        
        # 3. Reframes or buys time
        reframe_phrases = ['quick question', 'before i', 'just curious', 'let me ask']
        if any(phrase in user_input_lower for phrase in reframe_phrases):
            criteria_met += 1
        
        # 4. Ends with forward-moving question
        if user_input.strip().endswith('?') and len(user_input) > 20:
            criteria_met += 1
        
        evaluation['quality_score'] = max(1, criteria_met * 2)
        evaluation['criteria_met'] = criteria_met
        
        if criteria_met >= 3:
            evaluation['stage_completed'] = True
            evaluation['next_stage'] = 'mini_pitch'
        
        return evaluation
    
    def _evaluate_mini_pitch(self, user_input: str, evaluation: Dict) -> Dict:
        """Evaluate mini-pitch quality"""
        criteria_met = 0
        
        # 1. Short (1-2 sentences)
        sentence_count = user_input.count('.') + user_input.count('!') + user_input.count('?')
        if sentence_count <= 3:
            criteria_met += 1
        
        # 2. Focuses on problem solved or outcome
        outcome_phrases = ['help', 'solve', 'improve', 'increase', 'reduce', 'save', 'boost']
        if any(phrase in user_input.lower() for phrase in outcome_phrases):
            criteria_met += 1
        
        # 3. Simple English, no jargon
        if len(user_input.split()) <= 30:  # Keep it short
            criteria_met += 1
        
        # 4. Sounds natural (has question or continues conversation)
        if user_input.strip().endswith('?') or 'would you' in user_input.lower():
            criteria_met += 1
        
        evaluation['quality_score'] = max(1, criteria_met * 2)
        evaluation['criteria_met'] = criteria_met
        
        if criteria_met >= 3:
            evaluation['stage_completed'] = True
            evaluation['next_stage'] = 'call_completed'
        
        return evaluation
    
    def _evaluate_post_pitch_response(self, user_input: str, evaluation: Dict, session: Dict) -> Dict:
        """Evaluate post-pitch objection handling and qualification"""
        user_input_lower = user_input.lower()
        
        # Check for qualification achievement
        qualification_phrases = ['good fit', 'makes sense', 'right for us', 'interested', 'tell me more']
        if any(phrase in user_input_lower for phrase in qualification_phrases):
            session['qualification_achieved'] = True
        
        # Check for meeting ask
        meeting_phrases = ['meeting', 'call', 'demo', 'tomorrow', 'next week', 'available']
        if any(phrase in user_input_lower for phrase in meeting_phrases):
            session['meeting_asked'] = True
        
        # Basic quality evaluation
        evaluation['quality_score'] = 6 if session['qualification_achieved'] else 4
        
        # Check if both qualification and meeting ask completed
        if session['qualification_achieved'] and session['meeting_asked']:
            evaluation['stage_completed'] = True
            evaluation['next_stage'] = 'call_completed'
        
        return evaluation
    
    def _evaluate_warmup_answer(self, user_input: str, evaluation: Dict) -> Dict:
        """Evaluate warmup challenge answer (simplified)"""
        # For now, give a moderate score - real evaluation would be more complex
        evaluation['quality_score'] = 6 if len(user_input.strip()) > 10 else 3
        evaluation['stage_completed'] = True
        evaluation['next_stage'] = 'next_question'
        
        return evaluation
    
    def _generate_ai_response(self, session: Dict, user_input: str, evaluation: Dict) -> str:
        """Generate appropriate AI response based on current stage"""
        roleplay_id = session['roleplay_id']
        current_stage = session['current_stage']
        
        # Use OpenAI service for sophisticated response generation
        roleplay_config = {
            'roleplay_id': roleplay_id,
            'mode': session['mode'],
            'session_id': session['session_id']
        }
        
        response_result = self.openai_service.generate_roleplay_response(
            user_input,
            session['conversation_history'],
            session['user_context'],
            roleplay_config
        )
        
        if response_result['success']:
            return response_result['response']
        
        # Fallback responses if OpenAI fails
        return self._get_fallback_response(current_stage, session)
    
    def _get_fallback_response(self, stage: str, session: Dict) -> str:
        """Get fallback response if AI generation fails"""
        fallback_responses = {
            'phone_pickup': ['Hello?', 'Who is this?'],
            'early_objection': EARLY_OBJECTIONS[:5],
            'mini_pitch': ['Go ahead, what is it?', 'I\'m listening.'],
            'post_pitch_objections': POST_PITCH_OBJECTIONS[:5],
            'warmup_question': WARMUP_QUESTIONS[:5]
        }
        
        responses = fallback_responses.get(stage, ['Can you repeat that?'])
        
        # Avoid recently used responses
        used_responses = session.get('objections_used', [])
        available_responses = [r for r in responses if r not in used_responses]
        
        if not available_responses:
            available_responses = responses
            session['objections_used'] = []  # Reset if all used
        
        selected_response = random.choice(available_responses)
        session['objections_used'].append(selected_response)
        
        return selected_response
    
    def _update_session_state(self, session: Dict, evaluation: Dict) -> None:
        """Update session state based on evaluation"""
        if evaluation.get('stage_completed'):
            session['current_stage'] = evaluation['next_stage']
        
        # Update call tracking for marathon/legend modes
        if session['mode'] in ['marathon', 'legend']:
            if evaluation.get('stage_completed') and evaluation['next_stage'] == 'call_completed':
                session['call_count'] += 1
                if evaluation.get('quality_score', 0) >= 6:
                    session['successful_calls'] += 1
                
                # Check if should start next call
                max_calls = 10 if session['mode'] == 'marathon' else 6
                if session['call_count'] < max_calls:
                    # Start next call
                    session['current_stage'] = 'phone_pickup'
                    session['objections_used'] = []
                    session['qualification_achieved'] = False
                    session['meeting_asked'] = False
    
    def _should_call_continue(self, session: Dict, evaluation: Dict) -> bool:
        """Determine if call should continue"""
        # Call ends if hung up
        if session.get('hang_up_triggered'):
            return False
        
        # Call ends if stage completed and it's a single call mode
        if evaluation.get('stage_completed') and evaluation['next_stage'] == 'call_completed':
            if session['mode'] == 'practice':
                return False
        
        # Marathon/Legend modes continue until all calls completed
        if session['mode'] in ['marathon', 'legend']:
            max_calls = 10 if session['mode'] == 'marathon' else 6
            if session['call_count'] >= max_calls:
                return False
        
        return True
    
    def _handle_hang_up(self, session: Dict, reason: str) -> Dict[str, Any]:
        """Handle prospect hanging up"""
        session['hang_up_triggered'] = True
        session['session_active'] = False
        
        hang_up_responses = [
            "Not interested.",
            "Don't call here again.",
            "I'm hanging up now.",
            "Good bye."
        ]
        
        response = random.choice(hang_up_responses)
        
        # Add hang-up to conversation
        session['conversation_history'].append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'hang_up'
        })
        
        return {
            'success': True,
            'ai_response': response,
            'call_continues': False,
            'hang_up_reason': reason
        }
    
    def _determine_session_success(self, session: Dict) -> bool:
        """Determine if session was successful based on mode and performance"""
        mode = session['mode']
        roleplay_id = session['roleplay_id']
        
        if mode == 'practice':
            # Success if made it through without hanging up
            return not session.get('hang_up_triggered', False)
        
        elif mode == 'marathon':
            # Success if passed threshold (6/10)
            threshold = ROLEPLAY_CONFIG[roleplay_id].get('marathon_threshold', 6)
            return session['successful_calls'] >= threshold
        
        elif mode == 'legend':
            # Success if perfect score
            threshold = ROLEPLAY_CONFIG[roleplay_id].get('legend_threshold', 6)
            return session['successful_calls'] >= threshold
        
        elif mode == 'challenge':  # Warmup challenge
            # Success if passed threshold (would need to track correct answers)
            return True  # Simplified for now
        
        else:
            return not session.get('hang_up_triggered', False)
    
    def _update_user_progress(self, session: Dict) -> None:
        """Update user progress based on successful session"""
        try:
            user_id = session['user_id']
            roleplay_id = session['roleplay_id']
            mode = session['mode']
            
            # Get unlock target
            config = ROLEPLAY_CONFIG[roleplay_id]
            unlock_target = config.get('unlock_target')
            
            if unlock_target and mode in ['marathon', 'challenge', 'simulation']:
                # Update user progress to unlock next roleplay
                user_context = session['user_context']
                access_level = user_context.get('access_level', 'limited_trial')
                
                # Set expiry based on access level
                expires_at = None
                if access_level == 'unlimited_basic':
                    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
                
                # Update progress
                self.supabase_service.update_user_progress(user_id, unlock_target, {
                    'unlocked_at': datetime.now(timezone.utc).isoformat(),
                    'expires_at': expires_at.isoformat() if expires_at else None
                })
                
                logger.info(f"Unlocked roleplay {unlock_target} for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error updating user progress: {e}")
    
    def _generate_completion_message(self, session: Dict, success: bool) -> str:
        """Generate completion message based on session results"""
        mode = session['mode']
        successful_calls = session.get('successful_calls', 0)
        total_calls = session.get('call_count', 0)
        
        if mode == 'marathon':
            if success:
                return SUCCESS_MESSAGES['marathon_pass'].format(score=successful_calls)
            else:
                return SUCCESS_MESSAGES['marathon_fail'].format(score=successful_calls)
        
        elif mode == 'legend':
            if success:
                return SUCCESS_MESSAGES['legend_success']
            else:
                return SUCCESS_MESSAGES['legend_fail']
        
        elif mode == 'challenge':
            # Would need actual score tracking
            score = 20  # Placeholder
            if success:
                return SUCCESS_MESSAGES['warmup_pass'].format(score=score)
            else:
                return SUCCESS_MESSAGES['warmup_fail'].format(score=score)
        
        elif mode in ['simulation', 'power_hour']:
            if success:
                return SUCCESS_MESSAGES.get('simulation_success', 'Great job!')
            else:
                return SUCCESS_MESSAGES.get('simulation_fail', 'Keep practicing!')
        
        else:
            return "Session completed! Keep practicing to improve your skills."
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session status"""
        return self.active_sessions.get(session_id)
    
    def cleanup_expired_sessions(self) -> None:
        """Clean up sessions that have been inactive for too long"""
        try:
            current_time = datetime.now(timezone.utc)
            expired_sessions = []
            
            for session_id, session in self.active_sessions.items():
                started_at = datetime.fromisoformat(session['started_at'].replace('Z', '+00:00'))
                if current_time - started_at > timedelta(hours=2):  # 2 hour timeout
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
                logger.info(f"Cleaned up expired session: {session_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
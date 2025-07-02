# ===== services/roleplay/roleplay_2_1.py =====
# Post-Pitch Conversation Practice Mode

import random
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from .base_roleplay import BaseRoleplay
from .configs.roleplay_2_1_config import Roleplay21Config

logger = logging.getLogger(__name__)

class Roleplay21(BaseRoleplay):
    """
    Roleplay 2.1 - Post-Pitch Practice Mode
    Advanced practice covering pitch → objections/questions → qualification → meeting ask
    """
    
    def __init__(self, openai_service=None):
        super().__init__(openai_service)
        self.config = Roleplay21Config()
        self.roleplay_id = self.config.ROLEPLAY_ID

    def get_roleplay_info(self) -> Dict[str, Any]:
        return {
            'id': self.config.ROLEPLAY_ID,
            'name': self.config.NAME,
            'description': self.config.DESCRIPTION,
            'type': 'advanced_practice',
            'features': {
                'ai_evaluation': self.is_openai_available(),
                'post_pitch_focus': True,
                'advanced_objections': True,
                'qualification_required': True,
                'meeting_ask_required': True,
                'detailed_coaching': True
            }
        }

    def create_session(self, user_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Creates an advanced practice session for post-pitch conversation"""
        session_id = f"{user_id}_{self.config.ROLEPLAY_ID}_{mode}_{int(datetime.now().timestamp())}"
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'roleplay_id': self.config.ROLEPLAY_ID,
            'mode': mode,
            'started_at': datetime.now(timezone.utc).isoformat(),
            'user_context': user_context,
            'session_active': True,
            
            # Advanced conversation state
            'conversation_history': [],
            'current_stage': 'pitch_prompt',
            'stage_progression': ['pitch_prompt'],
            'turn_count': 0,
            'stage_turn_count': 0,
            'stages_completed': [],
            
            # Post-pitch specific tracking
            'pitch_prompt_given': None,
            'pitch_delivered': False,
            'soft_discovery_asked': False,
            'objections_encountered': [],
            'questions_encountered': [],
            'objections_handled': 0,
            'questions_handled': 0,
            'company_fit_qualified': False,
            'decision_maker_confirmed': False,
            'meeting_asked': False,
            'meeting_slots_offered': 0,
            'call_outcome': 'in_progress',
            
            # Evaluation tracking
            'rubric_scores': {},
            'conversation_quality': 0,
            'stage_performance': {},
            'critical_failures': [],
            'hang_up_triggered': False,
            
            # Advanced features
            'used_objections': set(),
            'used_questions': set(),
            'qualification_attempts': 0,
            'meeting_ask_attempts': 0
        }
        
        self.active_sessions[session_id] = session_data
        
        # Get random pitch prompt
        initial_response = self._get_random_pitch_prompt()
        session_data['pitch_prompt_given'] = initial_response
        
        session_data['conversation_history'].append({
            'role': 'assistant',
            'content': initial_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'pitch_prompt',
            'prompt_type': 'pitch_request'
        })
        
        logger.info(f"Advanced practice session {session_id} created for user {user_id}")
        return {
            'success': True,
            'session_id': session_id,
            'initial_response': initial_response,
            'roleplay_info': self.get_roleplay_info(),
            'stage_info': {
                'current_stage': 'pitch_prompt',
                'expected_action': 'Deliver mini pitch + soft discovery question'
            }
        }

    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input for advanced post-pitch conversation"""
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
                'turn_number': session['turn_count']
            })
            
            logger.info(f"2.1 Turn #{session['turn_count']}: Processing '{user_input[:50]}...'")
            
            # Stage-specific processing
            current_stage = session['current_stage']
            
            if current_stage == 'pitch_prompt':
                return self._handle_pitch_delivery(session, user_input)
            elif current_stage == 'objections_questions':
                return self._handle_objections_questions(session, user_input)
            elif current_stage == 'qualification':
                return self._handle_qualification(session, user_input)
            elif current_stage == 'meeting_ask':
                return self._handle_meeting_ask(session, user_input)
            elif current_stage == 'wrap_up':
                return self._handle_wrap_up(session, user_input)
            else:
                # Unknown stage - end call
                return self._handle_call_failure(session, "Unknown conversation stage")
            
        except Exception as e:
            logger.error(f"Error processing 2.1 input: {e}")
            return {'success': False, 'error': str(e), 'call_continues': False}

    def _handle_pitch_delivery(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Handle initial pitch delivery and soft discovery"""
        evaluation = self._evaluate_mini_pitch(session, user_input)
        
        # Store evaluation
        session['rubric_scores']['mini_pitch'] = evaluation
        session['stage_performance']['mini_pitch'] = evaluation
        
        if not evaluation.get('passed', False):
            # Critical failure - hang up
            session['critical_failures'].append('poor_pitch')
            return self._handle_call_failure(session, "Pitch did not meet standards")
        
        # Mark pitch as delivered
        session['pitch_delivered'] = True
        
        # Check if soft discovery question was asked
        if evaluation.get('soft_discovery_asked', False):
            session['soft_discovery_asked'] = True
        
        # Progress to objections/questions stage
        session['current_stage'] = 'objections_questions'
        session['stage_progression'].append('objections_questions')
        session['stages_completed'].append('pitch_prompt')
        session['stage_turn_count'] = 0
        
        # Generate objections/questions response
        ai_response = self._generate_objection_or_question(session)
        
        session['conversation_history'].append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'objections_questions',
            'response_type': 'objection_or_question'
        })
        
        return {
            'success': True,
            'ai_response': ai_response,
            'call_continues': True,
            'evaluation': evaluation,
            'stage_info': {
                'current_stage': 'objections_questions',
                'expected_action': 'Handle objection or question naturally'
            }
        }

    def _handle_objections_questions(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Handle objections and questions phase"""
        evaluation = self._evaluate_objection_handling(session, user_input)
        
        # Store evaluation
        session['rubric_scores'][f'objection_handling_{len(session["objections_encountered"])}'] = evaluation
        
        if not evaluation.get('passed', False):
            # Critical failure - hang up
            session['critical_failures'].append('poor_objection_handling')
            return self._handle_call_failure(session, "Objection handling failed")
        
        # Update counters
        if 'objection' in evaluation.get('response_type', ''):
            session['objections_handled'] += 1
        elif 'question' in evaluation.get('response_type', ''):
            session['questions_handled'] += 1
        
        # Decide next action
        total_handled = session['objections_handled'] + session['questions_handled']
        max_interactions = random.randint(2, 6)  # 1-3 objections + 1-3 questions
        
        if total_handled < max_interactions and random.random() < 0.6:
            # Continue with more objections/questions
            ai_response = self._generate_objection_or_question(session)
            
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': 'objections_questions',
                'response_type': 'objection_or_question'
            })
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': True,
                'evaluation': evaluation,
                'stage_info': {
                    'current_stage': 'objections_questions',
                    'expected_action': 'Continue handling objections/questions'
                }
            }
        else:
            # Move to qualification stage
            session['current_stage'] = 'qualification'
            session['stage_progression'].append('qualification')
            session['stages_completed'].append('objections_questions')
            session['stage_turn_count'] = 0
            
            ai_response = self._generate_qualification_opening()
            
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': 'qualification',
                'response_type': 'qualification_opening'
            })
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': True,
                'evaluation': evaluation,
                'stage_info': {
                    'current_stage': 'qualification',
                    'expected_action': 'Qualify company fit (mandatory)'
                }
            }

    def _handle_qualification(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Handle qualification phase - MANDATORY company fit"""
        evaluation = self._evaluate_qualification(session, user_input)
        
        # Store evaluation
        session['rubric_scores']['qualification'] = evaluation
        session['qualification_attempts'] += 1
        
        if evaluation.get('company_fit_secured', False):
            session['company_fit_qualified'] = True
            
            # Check for decision maker confirmation (coachable, not mandatory)
            if evaluation.get('decision_maker_confirmed', False):
                session['decision_maker_confirmed'] = True
            
            # Progress to meeting ask
            session['current_stage'] = 'meeting_ask'
            session['stage_progression'].append('meeting_ask')
            session['stages_completed'].append('qualification')
            session['stage_turn_count'] = 0
            
            ai_response = self._generate_qualification_success_response()
            
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': 'meeting_ask',
                'response_type': 'qualification_success'
            })
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': True,
                'evaluation': evaluation,
                'stage_info': {
                    'current_stage': 'meeting_ask',
                    'expected_action': 'Ask for meeting with concrete time slots'
                }
            }
        else:
            # No company fit qualification - critical failure
            if session['qualification_attempts'] >= 2:
                session['critical_failures'].append('no_qualification')
                return self._handle_call_failure(session, "Failed to qualify company fit")
            else:
                # Give one more chance
                ai_response = self._generate_qualification_retry()
                
                session['conversation_history'].append({
                    'role': 'assistant',
                    'content': ai_response,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'stage': 'qualification',
                    'response_type': 'qualification_retry'
                })
                
                return {
                    'success': True,
                    'ai_response': ai_response,
                    'call_continues': True,
                    'evaluation': evaluation,
                    'stage_info': {
                        'current_stage': 'qualification',
                        'expected_action': 'Try again to qualify company fit'
                    }
                }

    def _handle_meeting_ask(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Handle meeting ask phase"""
        evaluation = self._evaluate_meeting_ask(session, user_input)
        
        # Store evaluation
        session['rubric_scores']['meeting_ask'] = evaluation
        session['meeting_ask_attempts'] += 1
        
        if evaluation.get('clear_meeting_ask', False):
            session['meeting_asked'] = True
            session['meeting_slots_offered'] = evaluation.get('time_slots_offered', 0)
            
            # Generate response based on quality
            if evaluation.get('passed', False):
                # Good meeting ask - prospect agrees or pushes back reasonably
                ai_response = self._generate_meeting_response(session, evaluation)
                next_stage = 'wrap_up'
            else:
                # Poor meeting ask - prospect objects
                ai_response = self._generate_meeting_pushback(session, evaluation)
                next_stage = 'meeting_ask'  # Stay in same stage for retry
                
            if next_stage == 'wrap_up':
                session['current_stage'] = 'wrap_up'
                session['stage_progression'].append('wrap_up')
                session['stages_completed'].append('meeting_ask')
                session['stage_turn_count'] = 0
                
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage'],
                'response_type': 'meeting_response'
            })
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': next_stage != 'wrap_up' or len(user_input.strip()) > 0,
                'evaluation': evaluation,
                'stage_info': {
                    'current_stage': session['current_stage'],
                    'expected_action': 'Confirm meeting details or handle pushback' if next_stage == 'meeting_ask' else 'Say goodbye to end call'
                }
            }
        else:
            # No clear meeting ask - critical failure
            if session['meeting_ask_attempts'] >= 2:
                session['critical_failures'].append('no_meeting_ask')
                return self._handle_call_failure(session, "Failed to ask for meeting")
            else:
                # Give one more chance
                ai_response = "I'm still not clear on what you're asking for. Could you be more specific?"
                
                session['conversation_history'].append({
                    'role': 'assistant',
                    'content': ai_response,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'stage': 'meeting_ask',
                    'response_type': 'meeting_retry'
                })
                
                return {
                    'success': True,
                    'ai_response': ai_response,
                    'call_continues': True,
                    'evaluation': evaluation,
                    'stage_info': {
                        'current_stage': 'meeting_ask',
                        'expected_action': 'Ask clearly for meeting with specific times'
                    }
                }

    def _handle_wrap_up(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Handle call wrap-up phase"""
        # User should say goodbye or confirm meeting details
        if any(word in user_input.lower() for word in ['thank', 'great', 'perfect', 'goodbye', 'talk soon', 'see you']):
            # Good wrap-up
            session['call_outcome'] = 'success'
            return self._handle_call_success(session)
        elif session['turn_count'] >= 15:
            # Call too long
            session['call_outcome'] = 'success'  # Still count as success
            return self._handle_call_success(session)
        else:
            # Continue conversation briefly
            ai_response = "Anything else before we finish?"
            
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': 'wrap_up',
                'response_type': 'wrap_up_prompt'
            })
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': False,  # End after this
                'evaluation': {'passed': True},
                'stage_info': {
                    'current_stage': 'wrap_up',
                    'expected_action': 'Call ending'
                }
            }

    def _handle_call_success(self, session: Dict) -> Dict[str, Any]:
        """Handle successful call completion"""
        session['call_outcome'] = 'success'
        session['current_stage'] = 'call_ended'
        
        # Generate success message
        ai_response = random.choice([
            "Perfect! I'll send you that calendar invite. Talk soon!",
            "Great, I'll get that meeting set up. Thanks for your time!",
            "Excellent! You'll receive the calendar invite shortly. Have a great day!",
            "Sounds good! I'll send the details over. Looking forward to it!"
        ])
        
        session['conversation_history'].append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'call_ended',
            'response_type': 'success_closing'
        })
        
        return {
            'success': True,
            'ai_response': ai_response,
            'call_continues': False,
            'call_successful': True,
            'evaluation': {'passed': True},
            'final_outcome': 'success'
        }

    def _handle_call_failure(self, session: Dict, reason: str) -> Dict[str, Any]:
        """Handle call failure with abrupt hang-up"""
        session['call_outcome'] = 'failed'
        session['hang_up_triggered'] = True
        session['current_stage'] = 'call_ended'
        
        # Generate abrupt hang-up response
        ai_response = random.choice([
            "I don't think this is going to work. Thanks anyway.",
            "This isn't what I'm looking for. Goodbye.",
            "I'm not interested. Please don't call again.",
            "This is a waste of time. I'm hanging up.",
            "No thanks. *click*"
        ])
        
        session['conversation_history'].append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'call_ended',
            'response_type': 'failure_hangup',
            'failure_reason': reason
        })
        
        logger.info(f"2.1 Call failed: {reason}")
        
        return {
            'success': True,
            'ai_response': ai_response,
            'call_continues': False,
            'call_successful': False,
            'evaluation': {'passed': False},
            'final_outcome': 'failed',
            'failure_reason': reason
        }

    def _handle_silence_trigger(self, session: Dict, trigger: str) -> Dict[str, Any]:
        """Handle silence triggers"""
        if trigger == '[SILENCE_IMPATIENCE]':
            ai_response = random.choice([
                "Hello? Are you still there?",
                "Can you hear me?",
                "Just checking you're still on the line...",
                "Are we still connected?"
            ])
            
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage'],
                'response_type': 'impatience'
            })
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': True,
                'evaluation': {'passed': True}
            }
        elif trigger == '[SILENCE_HANGUP]':
            return self._handle_call_failure(session, "15 seconds of silence - prospect hung up")

    # Evaluation methods
    def _evaluate_mini_pitch(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Evaluate mini pitch delivery"""
        if self.is_openai_available():
            try:
                return self.openai_service.evaluate_user_input(
                    user_input,
                    session['conversation_history'],
                    'mini_pitch_advanced'
                )
            except Exception as e:
                logger.error(f"OpenAI evaluation error: {e}")
        
        # Fallback evaluation
        return self._basic_pitch_evaluation(user_input)

    def _basic_pitch_evaluation(self, user_input: str) -> Dict[str, Any]:
        """Basic pitch evaluation"""
        words = user_input.split()
        score = 0
        criteria_met = []
        
        # Length check (1-2 sentences, roughly 10-30 words)
        if 10 <= len(words) <= 30:
            score += 1
            criteria_met.append('appropriate_length')
        
        # Outcome words
        outcome_words = ['save', 'increase', 'reduce', 'improve', 'help', 'results', 'growth']
        if any(word in user_input.lower() for word in outcome_words):
            score += 1
            criteria_met.append('outcome_focused')
        
        # Question check
        has_question = '?' in user_input or any(q in user_input.lower() for q in ['how', 'what', 'when', 'where'])
        if has_question:
            score += 1
            criteria_met.append('soft_discovery_asked')
        
        # Natural language
        if any(word in user_input.lower() for word in ["i'm", "we're", "don't", "can't"]):
            score += 1
            criteria_met.append('natural_tone')
        
        passed = score >= 3
        
        return {
            'score': score,
            'passed': passed,
            'criteria_met': criteria_met,
            'soft_discovery_asked': has_question,
            'feedback': f'Pitch evaluation: {len(criteria_met)} criteria met'
        }

    def _evaluate_objection_handling(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Evaluate objection/question handling"""
        # Basic evaluation - in real implementation, use OpenAI
        score = 2  # Default passing score for basic handling
        criteria_met = ['basic_response']
        
        # Check for defensive language
        defensive_words = ['but you should', 'you need to', 'actually you']
        if not any(phrase in user_input.lower() for phrase in defensive_words):
            score += 1
            criteria_met.append('not_defensive')
        
        # Check for acknowledgment
        ack_words = ['understand', 'fair', 'get that', 'makes sense']
        if any(word in user_input.lower() for word in ack_words):
            score += 1
            criteria_met.append('acknowledges')
        
        return {
            'score': score,
            'passed': score >= 2,
            'criteria_met': criteria_met,
            'response_type': 'objection_or_question'
        }

    def _evaluate_qualification(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Evaluate qualification attempt"""
        company_fit_indicators = [
            'might help', 'could work', 'sounds relevant', 'worth exploring',
            'makes sense', 'could be useful', 'relevant to us', 'fits our needs'
        ]
        
        decision_maker_indicators = [
            'decision maker', 'make decisions', 'i decide', 'my call', 'up to me'
        ]
        
        company_fit_secured = any(phrase in user_input.lower() for phrase in company_fit_indicators)
        decision_maker_confirmed = any(phrase in user_input.lower() for phrase in decision_maker_indicators)
        
        return {
            'score': 3 if company_fit_secured else 1,
            'passed': company_fit_secured,
            'company_fit_secured': company_fit_secured,
            'decision_maker_confirmed': decision_maker_confirmed,
            'criteria_met': ['company_fit'] if company_fit_secured else []
        }

    def _evaluate_meeting_ask(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Evaluate meeting ask"""
        meeting_words = ['meeting', 'call', 'chat', 'discuss', 'talk', 'demo']
        time_indicators = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 
                          'morning', 'afternoon', 'am', 'pm', 'o\'clock']
        
        clear_meeting_ask = any(word in user_input.lower() for word in meeting_words)
        
        # Count time slots offered
        time_slots_offered = sum(1 for indicator in time_indicators if indicator in user_input.lower())
        
        return {
            'score': 3 if clear_meeting_ask and time_slots_offered >= 1 else 1,
            'passed': clear_meeting_ask and time_slots_offered >= 1,
            'clear_meeting_ask': clear_meeting_ask,
            'time_slots_offered': time_slots_offered,
            'criteria_met': ['meeting_ask'] if clear_meeting_ask else []
        }

    # Response generation methods
    def _get_random_pitch_prompt(self) -> str:
        """Get random pitch prompt from config"""
        return random.choice(self.config.PITCH_PROMPTS)

    def _generate_objection_or_question(self, session: Dict) -> str:
        """Generate objection or question"""
        # Randomly choose between objection and question
        if random.random() < 0.5:
            return self._get_unused_objection(session)
        else:
            return self._get_unused_question(session)

    def _get_unused_objection(self, session: Dict) -> str:
        """Get unused objection"""
        available = [obj for obj in self.config.POST_PITCH_OBJECTIONS 
                    if obj not in session['used_objections']]
        
        if not available:
            # Reset if all used
            session['used_objections'].clear()
            available = self.config.POST_PITCH_OBJECTIONS
        
        objection = random.choice(available)
        session['used_objections'].add(objection)
        session['objections_encountered'].append(objection)
        
        return objection

    def _get_unused_question(self, session: Dict) -> str:
        """Get unused question"""
        questions = [
            "How does this actually work?",
            "What kind of results do you typically see?",
            "How long does implementation take?",
            "What's the pricing structure?",
            "Who else are you working with?",
            "How is this different from what we're doing now?"
        ]
        
        available = [q for q in questions if q not in session['used_questions']]
        
        if not available:
            session['used_questions'].clear()
            available = questions
        
        question = random.choice(available)
        session['used_questions'].add(question)
        session['questions_encountered'].append(question)
        
        return question

    def _generate_qualification_opening(self) -> str:
        """Generate qualification opening"""
        return random.choice([
            "That makes sense. Tell me, does this sound like something that could help your team?",
            "I understand. Based on what I've shared, do you think this might be relevant for your situation?",
            "Got it. From your perspective, could you see this being useful for your company?",
            "Okay. Does this sound like it could address some of the challenges you're facing?"
        ])

    def _generate_qualification_success_response(self) -> str:
        """Generate response when qualification succeeds"""
        return random.choice([
            "Great! It sounds like there's a good fit here.",
            "Perfect! I think we could definitely help with that.",
            "Excellent! This could be exactly what you need.",
            "That's great to hear. I think we're aligned."
        ])

    def _generate_qualification_retry(self) -> str:
        """Generate retry prompt for qualification"""
        return random.choice([
            "Let me ask differently - do you see any potential value in what I've described?",
            "From what I've shared, is there anything that resonates with your current needs?",
            "Based on our conversation, do you think this could be worth exploring further?"
        ])

    def _generate_meeting_response(self, session: Dict, evaluation: Dict) -> str:
        """Generate meeting response based on quality"""
        if evaluation.get('time_slots_offered', 0) >= 2:
            return random.choice([
                "Let me check my calendar. Tuesday morning works better for me.",
                "I prefer Thursday afternoon if that's available.",
                "Either of those times work. Let's go with the earlier one.",
                "Tuesday sounds good. What time were you thinking?"
            ])
        else:
            return random.choice([
                "I might be available. What did you have in mind?",
                "Possibly. Can you send me some options?",
                "Let me think about it. What exactly would we cover?",
                "Maybe. I'd need to check my schedule first."
            ])

    def _generate_meeting_pushback(self, session: Dict, evaluation: Dict) -> str:
        """Generate pushback for poor meeting ask"""
        return random.choice([
            "I'm not sure what you're asking for exactly.",
            "That's pretty vague. What specifically did you want to discuss?",
            "I don't understand what you're proposing.",
            "Can you be more specific about what you want?"
        ])

    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End advanced practice session with comprehensive results"""
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
            
            # Determine success
            session_success = (
                session.get('call_outcome') == 'success' and
                session.get('company_fit_qualified', False) and
                session.get('meeting_asked', False) and
                len(session.get('critical_failures', [])) == 0
            )
            
            # Calculate overall score
            overall_score = self._calculate_advanced_score(session)
            
            # Generate comprehensive coaching
            coaching_result = self._generate_advanced_coaching(session)
            
            result = {
                'success': True,
                'duration_minutes': duration_minutes,
                'session_success': session_success,
                'coaching': coaching_result.get('coaching', {}),
                'overall_score': overall_score,
                'session_data': session,
                'roleplay_type': 'advanced_practice',
                'advanced_results': {
                    'pitch_delivered': session.get('pitch_delivered', False),
                    'objections_handled': session.get('objections_handled', 0),
                    'questions_handled': session.get('questions_handled', 0),
                    'company_fit_qualified': session.get('company_fit_qualified', False),
                    'decision_maker_confirmed': session.get('decision_maker_confirmed', False),
                    'meeting_asked': session.get('meeting_asked', False),
                    'meeting_slots_offered': session.get('meeting_slots_offered', 0),
                    'stages_completed': len(session.get('stages_completed', [])),
                    'critical_failures': session.get('critical_failures', [])
                }
            }
            
            # Clean up session
            del self.active_sessions[session_id]
            
            logger.info(f"Advanced practice session {session_id} ended. Success: {session_success}, Score: {overall_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error ending advanced practice session: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_advanced_score(self, session: Dict) -> int:
        """Calculate advanced scoring for post-pitch conversation"""
        base_score = 50
        
        # Stage completion bonuses
        stages = session.get('stages_completed', [])
        stage_scores = {
            'pitch_prompt': 15,      # Good pitch delivery
            'objections_questions': 20,  # Handled objections/questions
            'qualification': 25,     # Qualified company fit
            'meeting_ask': 20,       # Asked for meeting
            'wrap_up': 10           # Clean wrap-up
        }
        
        for stage in stages:
            if stage in stage_scores:
                base_score += stage_scores[stage]
        
        # Performance bonuses
        if session.get('company_fit_qualified'):
            base_score += 10
        
        if session.get('meeting_slots_offered', 0) >= 2:
            base_score += 5
        
        if session.get('decision_maker_confirmed'):
            base_score += 5
        
        # Penalties for failures
        for failure in session.get('critical_failures', []):
            base_score -= 15
        
        # Conversation quality
        turn_count = session.get('turn_count', 0)
        if 6 <= turn_count <= 12:  # Optimal length
            base_score += 5
        elif turn_count > 15:  # Too long
            base_score -= 5
        
        return max(0, min(100, base_score))

    def _generate_advanced_coaching(self, session: Dict) -> Dict[str, Any]:
        """Generate advanced coaching feedback"""
        try:
            if self.is_openai_available():
                return self.openai_service.generate_coaching_feedback(
                    session.get('conversation_history', []),
                    session.get('rubric_scores', {}),
                    session.get('user_context', {}),
                    coaching_type='advanced_practice'
                )
            else:
                # Fallback coaching
                return self._generate_fallback_advanced_coaching(session)
                
        except Exception as e:
            logger.error(f"Error generating advanced coaching: {e}")
            return self._generate_fallback_advanced_coaching(session)

    def _generate_fallback_advanced_coaching(self, session: Dict) -> Dict[str, Any]:
        """Generate fallback coaching for advanced practice"""
        coaching = {}
        
        # Pitch coaching
        if session.get('pitch_delivered'):
            coaching['pitch_feedback'] = "Good job delivering your pitch! Focus on being concise and outcome-focused."
        else:
            coaching['pitch_feedback'] = "Work on delivering a clear, brief pitch that focuses on outcomes, not features."
        
        # Objection handling
        objections_handled = session.get('objections_handled', 0)
        if objections_handled > 0:
            coaching['objection_handling'] = f"You handled {objections_handled} objections. Stay calm and acknowledge concerns before responding."
        
        # Qualification
        if session.get('company_fit_qualified'):
            coaching['qualification'] = "Excellent! You successfully qualified company fit."
        else:
            coaching['qualification'] = "Remember to confirm that your solution could help their specific situation."
        
        # Meeting ask
        if session.get('meeting_asked'):
            slots = session.get('meeting_slots_offered', 0)
            if slots >= 2:
                coaching['meeting_ask'] = "Perfect! You offered multiple time options."
            else:
                coaching['meeting_ask'] = "Good meeting ask! Next time, offer 2-3 specific time slots."
        else:
            coaching['meeting_ask'] = "Always ask for the meeting with specific day/time options."
        
        # Overall
        if session.get('call_outcome') == 'success':
            coaching['overall'] = "Great advanced practice session! You covered all the key elements of a post-pitch conversation."
        else:
            coaching['overall'] = "Keep practicing the post-pitch flow. Focus on qualification and clear meeting asks."
        
        return {'success': True, 'coaching': coaching}
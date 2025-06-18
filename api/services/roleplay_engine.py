# ===== FIXED API/SERVICES/ROLEPLAY_ENGINE.PY =====
import random
import logging
import asyncio
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
        
        logger.info(f"RoleplayEngine initialized - OpenAI available: {self.openai_service.is_available()}")
        
    def create_session(self, user_id: str, roleplay_id: int, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create a new roleplay session with enhanced context"""
        try:
            # Validate inputs
            if roleplay_id not in ROLEPLAY_CONFIG:
                raise ValueError(f"Invalid roleplay ID: {roleplay_id}")
            
            config = ROLEPLAY_CONFIG[roleplay_id]
            if mode not in config.get('modes', ['practice']):
                logger.warning(f"Mode '{mode}' not in config for roleplay {roleplay_id}, using practice mode")
                mode = 'practice'
            
            # Create unique session ID
            session_id = f"{user_id}_{roleplay_id}_{mode}_{datetime.now().timestamp()}"
            
            # Enhanced session data structure
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
                'meeting_asked': False,
                'performance_metrics': {
                    'opener_quality': 0,
                    'objection_handling': 0,
                    'pitch_effectiveness': 0,
                    'confidence_level': 0,
                    'overall_impression': 0
                },
                'coaching_notes': [],
                'stage_progression': [],
                'evaluation_history': []
            }
            
            # Store session in memory
            self.active_sessions[session_id] = session_data
            
            # Generate intelligent initial response based on roleplay type
            initial_response = self._generate_initial_response(roleplay_id, mode, user_context)
            
            # Add to conversation history if there's an initial response
            if initial_response:
                session_data['conversation_history'].append({
                    'role': 'assistant',
                    'content': initial_response,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'stage': session_data['current_stage']
                })
            
            logger.info(f"Created session {session_id} for user {user_id} - Active sessions: {len(self.active_sessions)}")
            
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
    
    async def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input with enhanced AI conversation"""
        try:
            logger.info(f"Processing input for session {session_id}: {user_input[:50]}...")
            
            if session_id not in self.active_sessions:
                logger.error(f"Session {session_id} not found in active sessions")
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            
            if not session.get('session_active'):
                logger.error(f"Session {session_id} is not active")
                raise ValueError("Session is not active")
            
            # Add user input to conversation
            session['conversation_history'].append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage']
            })
            
            # **KEY FIX**: Always try OpenAI first for natural responses
            ai_response_data = await self._generate_ai_response_with_openai(session, user_input)
            
            if not ai_response_data.get('success'):
                logger.warning("OpenAI response failed, using fallback")
                ai_response_data = self._generate_fallback_response(session, user_input)
            
            ai_response = ai_response_data['response']
            evaluation = ai_response_data.get('evaluation', {})
            
            # Store evaluation in session history
            session['evaluation_history'].append({
                'user_input': user_input,
                'evaluation': evaluation,
                'stage': session['current_stage'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            # Check for hang-up conditions
            if evaluation.get('should_hang_up') or not evaluation.get('should_continue', True):
                return await self._handle_hang_up(session, evaluation.get('hang_up_reason', 'Poor response quality'))
            
            # Add AI response to conversation
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage'],
                'evaluation_data': evaluation
            })
            
            # Update session state based on evaluation
            self._update_session_state(session, evaluation)
            
            # Update performance metrics
            self._update_performance_metrics(session, user_input, evaluation)
            
            # Check if call/session should end
            call_continues = self._should_call_continue(session, evaluation)
            
            # Handle multi-call modes (Marathon/Legend)
            if not call_continues and session['mode'] in ['marathon', 'legend']:
                call_continues = await self._handle_multi_call_progression(session, evaluation)
            
            logger.info(f"Generated AI response: {ai_response[:50]}... Call continues: {call_continues}")
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': call_continues,
                'evaluation': evaluation,
                'session_state': session['current_stage'],
                'performance_hint': self._get_performance_hint(evaluation),
                'call_count': session.get('call_count', 0),
                'successful_calls': session.get('successful_calls', 0)
            }
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            return {
                'success': False,
                'error': str(e),
                'call_continues': False
            }
    
    async def _generate_ai_response_with_openai(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Generate AI response using OpenAI service with proper async handling"""
        try:
            if not self.openai_service.is_available():
                logger.info("OpenAI not available, using fallback")
                return {'success': False}
            
            # Prepare roleplay configuration
            roleplay_config = {
                'roleplay_id': session['roleplay_id'],
                'mode': session['mode'],
                'session_id': session['session_id']
            }
            
            logger.info("Using OpenAI for AI response generation")
            
            # Generate response using OpenAI service
            response_data = await self.openai_service.generate_roleplay_response(
                user_input,
                session['conversation_history'],
                session['user_context'],
                roleplay_config
            )
            
            if response_data.get('success'):
                logger.info(f"OpenAI response generated successfully: {response_data['response'][:50]}...")
                return response_data
            else:
                logger.warning(f"OpenAI failed: {response_data.get('error')}")
                return {'success': False}
                
        except Exception as e:
            logger.error(f"Error in OpenAI response generation: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_fallback_response(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Generate fallback response when OpenAI is unavailable"""
        try:
            current_stage = session['current_stage']
            roleplay_id = session['roleplay_id']
            
            logger.info(f"Generating fallback response for stage: {current_stage}")
            
            # Use more natural fallback logic
            if current_stage in ['phone_pickup']:
                responses = ["Hello?", "Yes?", "Who is this?"]
                
            elif current_stage in ['opener_evaluation']:
                user_messages_count = len([m for m in session['conversation_history'] if m.get('role') == 'user'])
                
                if user_messages_count == 1:
                    # Evaluate opener quality
                    opener_quality = self._evaluate_opener_simple(user_input)
                    logger.info(f"Opener quality score: {opener_quality}/8 for input: '{user_input}'")
                    
                    # More realistic responses based on opener quality
                    if opener_quality <= 2:
                        responses = ["Who is this?", "What's this about?", "I don't know you."]
                    elif opener_quality <= 4:
                        responses = ["What's this about?", "I'm listening.", "Go ahead."]
                    else:
                        responses = ["I'm listening.", "What can I do for you?", "You have my attention."]
                        
                    # Small chance of hang-up for very poor openers
                    if opener_quality <= 1 and random.random() < 0.3:
                        responses = ["Not interested.", "I'm hanging up."]
                        return {
                            'success': True,
                            'response': random.choice(responses),
                            'evaluation': {'should_hang_up': True, 'quality_score': opener_quality}
                        }
                else:
                    responses = ["Hello?", "Who is this?", "What's this about?"]
                    
            elif current_stage == 'early_objection':
                # Use unused objections
                used_objections = session.get('objections_used', [])
                available_objections = [obj for obj in EARLY_OBJECTIONS if obj not in used_objections]
                
                if not available_objections:
                    available_objections = EARLY_OBJECTIONS
                    session['objections_used'] = []
                
                selected_objection = random.choice(available_objections)
                session['objections_used'].append(selected_objection)
                
                return {
                    'success': True,
                    'response': selected_objection,
                    'evaluation': self._evaluate_user_input_simple(user_input, current_stage)
                }
                
            elif current_stage in ['mini_pitch', 'ai_pitch_prompt']:
                if roleplay_id == 2:
                    responses = PITCH_PROMPTS
                else:
                    responses = ["Go ahead, what is it?", "I'm listening.", "You have two minutes."]
                    
            elif current_stage == 'post_pitch_objections':
                # Use unused post-pitch objections
                used_objections = session.get('objections_used', [])
                available_objections = [obj for obj in POST_PITCH_OBJECTIONS if obj not in used_objections]
                
                if not available_objections:
                    available_objections = POST_PITCH_OBJECTIONS
                    session['objections_used'] = []
                
                selected_objection = random.choice(available_objections)
                session['objections_used'].append(selected_objection)
                
                return {
                    'success': True,
                    'response': selected_objection,
                    'evaluation': self._evaluate_user_input_simple(user_input, current_stage)
                }
                
            elif current_stage == 'warmup_question':
                responses = WARMUP_QUESTIONS
                
            else:
                responses = ["I see.", "Tell me more.", "Go on.", "Interesting."]
            
            selected_response = random.choice(responses)
            
            # Basic evaluation
            evaluation = self._evaluate_user_input_simple(user_input, current_stage)
            
            logger.info(f"Selected fallback response: {selected_response}")
            
            return {
                'success': True,
                'response': selected_response,
                'evaluation': evaluation,
                'fallback_used': True
            }
            
        except Exception as e:
            logger.error(f"Error generating fallback response: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "Can you repeat that?"
            }
    
    def _evaluate_opener_simple(self, user_input: str) -> int:
        """Enhanced opener evaluation following PDF rubric"""
        score = 1  # Start with base score
        user_input_lower = user_input.lower()
        
        # Rubric criteria from PDF
        criteria_met = 0
        
        # 1. Clear cold call opener
        if any(opener in user_input_lower for opener in ['hi', 'hello', 'good morning', 'calling from', 'my name is']):
            criteria_met += 1
        
        # 2. Casual, confident tone (contractions and short phrases)
        if any(contraction in user_input for contraction in ["I'm", "don't", "we're", "it's", "you're"]):
            criteria_met += 1
        
        # 3. Demonstrates empathy
        if any(empathy in user_input_lower for empathy in [
            'know this is out of the blue', "don't know me", 'cold call', 
            'interrupting', 'unexpected', 'caught you off guard', 'random'
        ]):
            criteria_met += 1
        
        # 4. Ends with soft question
        if user_input.strip().endswith('?') and any(soft in user_input_lower for soft in [
            'can i tell you', 'may i ask', 'would you be open', 'can i share', 'mind if'
        ]):
            criteria_met += 1
        
        # Score based on criteria met (need 3 of 4 to pass)
        if criteria_met >= 3:
            score = 6 + criteria_met  # Pass score (6-8)
        else:
            score = max(1, criteria_met * 2)  # Fail score (1-4)
        
        return min(score, 8)
    
    def _evaluate_user_input_simple(self, user_input: str, stage: str) -> Dict[str, Any]:
        """Enhanced evaluation logic following PDF rubrics"""
        evaluation = {
            'quality_score': 5,
            'should_continue': True,
            'should_hang_up': False,
            'next_stage': 'in_progress',
            'feedback_notes': []
        }
        
        user_input_lower = user_input.lower()
        
        if stage in ['phone_pickup', 'opener_evaluation']:
            evaluation['quality_score'] = self._evaluate_opener_simple(user_input)
            
            # Pass if score >= 6 (3 of 4 criteria met)
            if evaluation['quality_score'] >= 6:
                evaluation['next_stage'] = 'early_objection'
            else:
                # Fail - but don't always hang up immediately
                if evaluation['quality_score'] <= 2:
                    evaluation['should_hang_up'] = random.random() < 0.3  # 30% chance
                
        elif stage == 'early_objection':
            # Objection handling rubric (need 3 of 4)
            criteria_met = 0
            
            # 1. Acknowledges calmly
            if any(ack in user_input_lower for ack in ['fair enough', 'totally get', 'understand', 'i hear']):
                criteria_met += 1
            
            # 2. Doesn't argue or pitch
            if not any(argue in user_input_lower for argue in ['but you', 'actually', "you're wrong", 'no that']):
                criteria_met += 1
            
            # 3. Reframes or buys time in 1 sentence
            if any(reframe in user_input_lower for reframe in ['let me', 'what if', 'help me understand']):
                criteria_met += 1
            
            # 4. Ends with forward-moving question
            if user_input.strip().endswith('?'):
                criteria_met += 1
            
            evaluation['quality_score'] = 3 + criteria_met
            
            if criteria_met >= 3:
                evaluation['next_stage'] = 'mini_pitch'
            else:
                evaluation['should_hang_up'] = True
                
        elif stage in ['mini_pitch', 'pitch_evaluation']:
            # Mini-pitch rubric (need 3 of 4)
            criteria_met = 0
            
            # 1. Short (1-2 sentences)
            sentences = len([s for s in user_input.split('.') if s.strip()])
            if sentences <= 2:
                criteria_met += 1
            
            # 2. Focuses on problem solved or outcome delivered
            if any(outcome in user_input_lower for outcome in ['help', 'save', 'improve', 'solve', 'reduce']):
                criteria_met += 1
            
            # 3. Simple English (no jargon)
            if len(user_input.split()) < 50:  # Not too long/complex
                criteria_met += 1
            
            # 4. Sounds natural (ends with question)
            if user_input.strip().endswith('?'):
                criteria_met += 1
            
            evaluation['quality_score'] = 3 + criteria_met
            
            if criteria_met >= 3:
                evaluation['next_stage'] = 'post_pitch_objections'
            else:
                evaluation['should_hang_up'] = True
        
        elif stage == 'post_pitch_objections':
            # Similar evaluation for post-pitch handling
            evaluation['quality_score'] = 6  # Default pass for post-pitch
            evaluation['next_stage'] = 'qualification'
        
        return evaluation
    
    async def _handle_hang_up(self, session: Dict, reason: str) -> Dict[str, Any]:
        """Handle prospect hanging up with feedback"""
        session['hang_up_triggered'] = True
        session['session_active'] = False
        
        hang_up_responses = [
            "Not interested. Good bye.",
            "Please don't call here again.",
            "I'm hanging up now.",
            "*click*"
        ]
        
        response = random.choice(hang_up_responses)
        
        # Add hang-up to conversation
        session['conversation_history'].append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'hang_up',
            'hang_up_reason': reason
        })
        
        # For multi-call modes, this ends the current call
        if session['mode'] in ['marathon', 'legend']:
            return await self._handle_multi_call_progression(session, {'pass': False})
        
        return {
            'success': True,
            'ai_response': response,
            'call_continues': False,
            'hang_up_reason': reason,
            'coaching_note': 'The prospect hung up. Focus on improving your approach to create better first impressions.'
        }
    
    async def _handle_multi_call_progression(self, session: Dict, evaluation: Dict) -> bool:
        """Handle progression in Marathon/Legend modes"""
        try:
            session['call_count'] += 1
            
            if evaluation.get('pass', False):
                session['successful_calls'] += 1
            
            # Check if we should continue
            mode = session['mode']
            
            if mode == 'marathon':
                max_calls = 10
                if session['call_count'] >= max_calls:
                    # Marathon complete
                    return False
                else:
                    # Start next call
                    await self._start_next_call(session)
                    return True
                    
            elif mode == 'legend':
                max_calls = 6
                if not evaluation.get('pass', False):
                    # Legend mode - any failure ends the run
                    return False
                elif session['call_count'] >= max_calls:
                    # Legend complete - all 6 passed
                    return False
                else:
                    # Start next call
                    await self._start_next_call(session)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error handling multi-call progression: {e}")
            return False
    
    async def _start_next_call(self, session: Dict):
        """Start the next call in multi-call mode"""
        # Reset call state
        session['current_stage'] = self._get_initial_stage(session['roleplay_id'])
        session['objections_used'] = []
        session['qualification_achieved'] = False
        session['meeting_asked'] = False
        session['hang_up_triggered'] = False
        
        # Add "next call" indicator to conversation
        session['conversation_history'].append({
            'role': 'system',
            'content': f"--- Call {session['call_count'] + 1} ---",
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'call_transition'
        })
        
        # Add initial response for new call
        initial_response = self._generate_initial_response(session['roleplay_id'], session['mode'], session['user_context'])
        if initial_response:
            session['conversation_history'].append({
                'role': 'assistant',
                'content': initial_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage']
            })
    
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
        """Generate context-aware initial response"""
        if roleplay_id == 2:  # Pitch + Objections starts with AI prompt
            return random.choice(PITCH_PROMPTS)
        elif roleplay_id == 3:  # Warm-up Challenge starts with question
            return random.choice(WARMUP_QUESTIONS)
        else:  # Standard phone pickup
            return "Hello?"
    
    def _update_session_state(self, session: Dict, evaluation: Dict) -> None:
        """Update session state based on AI evaluation"""
        next_stage = evaluation.get('next_stage')
        if next_stage and next_stage != 'in_progress':
            session['current_stage'] = next_stage
            
            # Record stage progression
            session['stage_progression'].append({
                'stage': next_stage,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'evaluation_score': evaluation.get('quality_score', 0)
            })
    
    def _update_performance_metrics(self, session: Dict, user_input: str, evaluation: Dict) -> None:
        """Update running performance metrics"""
        metrics = session.get('performance_metrics', {})
        
        stage = session.get('current_stage', 'unknown')
        quality_score = evaluation.get('quality_score', 5)
        
        if stage in ['phone_pickup', 'opener_evaluation']:
            metrics['opener_quality'] = max(metrics.get('opener_quality', 0), quality_score)
        elif stage == 'early_objection':
            metrics['objection_handling'] = max(metrics.get('objection_handling', 0), quality_score)
        elif stage in ['mini_pitch', 'pitch_evaluation']:
            metrics['pitch_effectiveness'] = max(metrics.get('pitch_effectiveness', 0), quality_score)
        
        # Overall confidence based on conversation continuation
        if not session.get('hang_up_triggered'):
            metrics['confidence_level'] = min(metrics.get('confidence_level', 0) + 1, 10)
        
        session['performance_metrics'] = metrics
    
    def _get_performance_hint(self, evaluation: Dict) -> Optional[str]:
        """Get real-time performance hint for user"""
        quality_score = evaluation.get('quality_score', 5)
        
        if quality_score <= 3:
            return "Try showing more empathy and building rapport before pitching."
        elif quality_score >= 7:
            return "Great response! Keep this energy and confidence."
        else:
            return None
    
    def _should_call_continue(self, session: Dict, evaluation: Dict) -> bool:
        """Determine if call should continue"""
        # Call ends if hung up
        if session.get('hang_up_triggered'):
            return False
        
        # Call ends if AI indicates it should end
        if not evaluation.get('should_continue', True):
            return False
        
        # Call ends if stage indicates completion
        if evaluation.get('next_stage') == 'call_completed':
            return False
        
        return True
    
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
            duration_minutes = max(1, int((ended_at - started_at).total_seconds() / 60))
            
            # Generate coaching feedback
            coaching_feedback, overall_score = self._generate_coaching_feedback(session)
            
            # Determine session success
            session_success = self._determine_session_success(session, overall_score)
            
            # Generate completion message
            completion_message = self._generate_completion_message(session, session_success, overall_score)
            
            # Clean up session
            del self.active_sessions[session_id]
            
            logger.info(f"Ended session {session_id} - Active sessions: {len(self.active_sessions)}")
            
            return {
                'success': True,
                'duration_minutes': duration_minutes,
                'session_success': session_success,
                'coaching': coaching_feedback,
                'overall_score': overall_score,
                'completion_message': completion_message,
                'session_data': session,
                'performance_metrics': session.get('performance_metrics', {}),
                'call_count': session.get('call_count', 0),
                'successful_calls': session.get('successful_calls', 0)
            }
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_coaching_feedback(self, session: Dict) -> Tuple[Dict, int]:
        """Generate coaching feedback based on session performance"""
        conversation = session.get('conversation_history', [])
        user_messages = [msg for msg in conversation if msg.get('role') == 'user']
        evaluation_history = session.get('evaluation_history', [])
        
        # Analyze performance across all categories
        coaching = {
            'coaching': {
                'sales_coaching': self._analyze_sales_performance(user_messages, evaluation_history, session),
                'grammar_coaching': self._analyze_grammar_performance(user_messages),
                'vocabulary_coaching': self._analyze_vocabulary_usage(user_messages),
                'pronunciation_coaching': self._analyze_pronunciation_performance(user_messages),
                'rapport_assertiveness': self._analyze_rapport_confidence(user_messages, session)
            }
        }
        
        # Calculate overall score
        score = self._calculate_overall_score(session, evaluation_history)
        
        return coaching, score
    
    def _analyze_sales_performance(self, user_messages: List[Dict], evaluation_history: List[Dict], session: Dict) -> str:
        """Analyze sales performance with specific feedback"""
        if not user_messages:
            return "Complete more of the conversation to get sales coaching."
        
        # Get stage-specific feedback
        stages_completed = set(eval.get('stage') for eval in evaluation_history)
        
        feedback_points = []
        
        if 'opener_evaluation' in stages_completed:
            opener_evals = [e for e in evaluation_history if e.get('stage') == 'opener_evaluation']
            if opener_evals:
                score = opener_evals[0]['evaluation'].get('quality_score', 5)
                if score >= 6:
                    feedback_points.append("Good opener with empathy and professionalism.")
                else:
                    feedback_points.append("Work on your opener - add more empathy like 'I know this is unexpected' and end with a soft question.")
        
        if 'early_objection' in stages_completed:
            feedback_points.append("Good job handling the early objection. Remember to acknowledge first, then redirect.")
        
        if session.get('hang_up_triggered'):
            feedback_points.append("The prospect hung up. Focus on building more rapport in your opening approach.")
        
        if session.get('mode') in ['marathon', 'legend']:
            success_rate = session.get('successful_calls', 0) / max(session.get('call_count', 1), 1)
            if success_rate >= 0.6:
                feedback_points.append(f"Great consistency! You passed {session.get('successful_calls', 0)} out of {session.get('call_count', 0)} calls.")
            else:
                feedback_points.append("Focus on consistency. Practice your opener and objection handling more.")
        
        return ' '.join(feedback_points) if feedback_points else "Keep practicing to improve your sales techniques."
    
    def _analyze_grammar_performance(self, user_messages: List[Dict]) -> str:
        """Analyze grammar patterns"""
        if not user_messages:
            return "Speak more to get grammar feedback."
        
        total_text = ' '.join([msg.get('content', '') for msg in user_messages]).lower()
        
        if any(contraction in total_text for contraction in ["i'm", "don't", "we're", "it's"]):
            return "Great use of contractions! This makes your speech sound more natural and conversational."
        else:
            return "Try using more contractions like 'I'm', 'don't', 'we're' to sound more natural in English conversation."
    
    def _analyze_vocabulary_usage(self, user_messages: List[Dict]) -> str:
        """Analyze vocabulary choices"""
        if not user_messages:
            return "Speak more to get vocabulary feedback."
        
        total_text = ' '.join([msg.get('content', '') for msg in user_messages]).lower()
        
        business_words = ['help', 'solve', 'improve', 'solution', 'business', 'team', 'company']
        if any(word in total_text for word in business_words):
            return "Good use of business vocabulary. This shows professionalism and industry knowledge."
        else:
            return "Try incorporating more business terms like 'solution', 'improve', or 'help' to sound more professional."
    
    def _analyze_pronunciation_performance(self, user_messages: List[Dict]) -> str:
        """Basic pronunciation guidance"""
        return "Continue speaking clearly and at a steady pace. Practice key sales terms for better clarity."
    
    def _analyze_rapport_confidence(self, user_messages: List[Dict], session: Dict) -> str:
        """Analyze rapport and confidence"""
        if session.get('hang_up_triggered'):
            return "The prospect hung up. Work on your opening approach to create better first impressions and build rapport."
        
        if len(user_messages) >= 3:
            return "Great job keeping the conversation going! This shows good rapport-building skills and confidence."
        else:
            return "Try to engage more and ask questions to build stronger rapport with prospects."
    
    def _calculate_overall_score(self, session: Dict, evaluation_history: List[Dict]) -> int:
        """Calculate overall performance score"""
        if not evaluation_history:
            return 50
        
        # Average quality scores from evaluations
        scores = [eval['evaluation'].get('quality_score', 5) for eval in evaluation_history]
        avg_score = sum(scores) / len(scores) if scores else 5
        
        # Convert to 0-100 scale
        base_score = int((avg_score / 8) * 100)
        
        # Adjustments
        if not session.get('hang_up_triggered'):
            base_score += 10  # Bonus for not hanging up
        
        if session.get('mode') in ['marathon', 'legend']:
            success_rate = session.get('successful_calls', 0) / max(session.get('call_count', 1), 1)
            base_score = int(base_score * (0.5 + success_rate * 0.5))
        
        return max(0, min(100, base_score))
    
    def _determine_session_success(self, session: Dict, overall_score: int) -> bool:
        """Determine if session was successful"""
        mode = session['mode']
        roleplay_id = session['roleplay_id']
        
        if mode == 'practice':
            return not session.get('hang_up_triggered', False) and overall_score >= 50
        
        elif mode == 'marathon':
            threshold = ROLEPLAY_CONFIG[roleplay_id].get('marathon_threshold', 6)
            return session['successful_calls'] >= threshold
        
        elif mode == 'legend':
            threshold = ROLEPLAY_CONFIG[roleplay_id].get('legend_threshold', 6)
            return session['successful_calls'] >= threshold
        
        else:
            return overall_score >= 60 and not session.get('hang_up_triggered', False)
    
    def _generate_completion_message(self, session: Dict, success: bool, overall_score: int) -> str:
        """Generate enhanced completion message"""
        mode = session['mode']
        successful_calls = session.get('successful_calls', 0)
        total_calls = session.get('call_count', 0)
        
        if mode == 'marathon':
            if success:
                return f"Outstanding! You passed {successful_calls} out of 10 calls. You've unlocked the next module and earned a Legend Mode attempt!"
            else:
                return f"You completed all 10 calls and passed {successful_calls}. Keep practicing - you're improving with each call!"
        
        elif mode == 'legend':
            if success:
                return "LEGENDARY! Perfect score - you've mastered this module. Very few people achieve this level!"
            else:
                return f"Legend attempt complete. You made it through {successful_calls} calls. To try again, pass Marathon mode first."
        
        else:  # Practice mode
            if overall_score >= 80:
                return f"Excellent work! Score: {overall_score}/100. You're ready for more challenging modes!"
            elif overall_score >= 60:
                return f"Good job! Score: {overall_score}/100. Keep practicing to improve your skills."
            else:
                return f"Nice try! Score: {overall_score}/100. Focus on the coaching feedback to improve."
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session status"""
        session = self.active_sessions.get(session_id)
        if session:
            return {
                **session,
                'openai_available': self.openai_service.is_available()
            }
        return None
    
    def cleanup_expired_sessions(self) -> None:
        """Clean up sessions that have been inactive for too long"""
        try:
            current_time = datetime.now(timezone.utc)
            expired_sessions = []
            
            for session_id, session in self.active_sessions.items():
                started_at = datetime.fromisoformat(session['started_at'].replace('Z', '+00:00'))
                if current_time - started_at > timedelta(hours=2):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
                logger.info(f"Cleaned up expired session: {session_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get overall service status"""
        return {
            'active_sessions': len(self.active_sessions),
            'openai_available': self.openai_service.is_available(),
            'openai_status': self.openai_service.get_status(),
            'engine_status': 'running'
        }
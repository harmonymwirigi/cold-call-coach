# ===== SIMPLIFIED WORKING API/SERVICES/ROLEPLAY_ENGINE.PY =====
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
        
        logger.info(f"RoleplayEngine initialized - OpenAI available: {self.openai_service.is_available()}")
        
    def create_session(self, user_id: str, roleplay_id: int, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create a new roleplay session"""
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
            
            # Session data structure
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
                'call_count': 0,
                'successful_calls': 0,
                'session_active': True,
                'hang_up_triggered': False,
                'performance_metrics': {
                    'opener_quality': 0,
                    'objection_handling': 0,
                    'pitch_effectiveness': 0,
                    'confidence_level': 0
                },
                'evaluation_history': []
            }
            
            # Store session in memory
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
        """Process user input - SIMPLIFIED VERSION"""
        try:
            logger.info(f"Processing input for session {session_id}: '{user_input[:50]}...'")
            
            if session_id not in self.active_sessions:
                logger.error(f"Session {session_id} not found")
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
            
            # Generate AI response - TRY OpenAI first, then fallback
            try:
                logger.info("Attempting OpenAI response generation...")
                
                # Prepare roleplay configuration
                roleplay_config = {
                    'roleplay_id': session['roleplay_id'],
                    'mode': session['mode'],
                    'session_id': session['session_id']
                }
                
                # Call OpenAI service (now synchronous)
                ai_response_data = self.openai_service.generate_roleplay_response(
                    user_input,
                    session['conversation_history'],
                    session['user_context'],
                    roleplay_config
                )
                
                if ai_response_data.get('success'):
                    logger.info("OpenAI response successful")
                    ai_response = ai_response_data['response']
                    evaluation = ai_response_data.get('evaluation', {})
                else:
                    logger.warning("OpenAI response failed, using simple fallback")
                    ai_response, evaluation = self._generate_simple_fallback(session, user_input)
                    
            except Exception as openai_error:
                logger.error(f"OpenAI error: {openai_error}, using simple fallback")
                ai_response, evaluation = self._generate_simple_fallback(session, user_input)
            
            # Store evaluation
            session['evaluation_history'].append({
                'user_input': user_input,
                'evaluation': evaluation,
                'stage': session['current_stage'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            # Check for hang-up conditions
            if evaluation.get('should_hang_up') or not evaluation.get('should_continue', True):
                return self._handle_hang_up(session, evaluation.get('hang_up_reason', 'Call ended'))
            
            # Add AI response to conversation
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage'],
                'evaluation_data': evaluation
            })
            
            # Update session state
            self._update_session_state(session, evaluation)
            
            # Update performance metrics
            self._update_performance_metrics(session, user_input, evaluation)
            
            # Check if call should continue
            call_continues = self._should_call_continue(session, evaluation)
            
            # Handle multi-call modes
            if not call_continues and session['mode'] in ['marathon', 'legend']:
                call_continues = self._handle_multi_call_progression(session, evaluation)
            
            logger.info(f"Response generated: '{ai_response[:50]}...' Call continues: {call_continues}")
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': call_continues,
                'evaluation': evaluation,
                'session_state': session['current_stage'],
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
    
    def _generate_simple_fallback(self, session: Dict, user_input: str) -> Tuple[str, Dict]:
        """Generate simple fallback response when OpenAI fails"""
        try:
            current_stage = session['current_stage']
            roleplay_id = session['roleplay_id']
            
            logger.info(f"Generating simple fallback for stage: {current_stage}")
            
            # Determine response based on stage and conversation history
            user_messages_count = len([m for m in session['conversation_history'] if m.get('role') == 'user'])
            
            if current_stage == 'phone_pickup' or user_messages_count == 1:
                responses = ["Hello?", "Yes?", "Who is this?"]
                
            elif current_stage == 'opener_evaluation' or user_messages_count == 2:
                # Evaluate opener quality for better response
                opener_quality = self._evaluate_opener_simple(user_input)
                
                if opener_quality >= 6:
                    responses = ["I'm listening.", "What can I do for you?", "Go ahead."]
                elif opener_quality >= 4:
                    responses = ["What's this about?", "I'm listening.", "This better be good."]
                else:
                    responses = ["Who is this?", "I'm not interested.", "What's this about?"]
                    
                # Small chance of hang-up for very poor openers
                if opener_quality <= 2 and random.random() < 0.25:
                    responses = ["Not interested.", "I'm hanging up."]
                    evaluation = {
                        'should_hang_up': True,
                        'quality_score': opener_quality,
                        'should_continue': False
                    }
                    return random.choice(responses), evaluation
                    
            elif current_stage == 'early_objection' or user_messages_count == 3:
                # Use unused objections
                used_objections = session.get('objections_used', [])
                available_objections = [obj for obj in EARLY_OBJECTIONS if obj not in used_objections]
                
                if not available_objections:
                    available_objections = EARLY_OBJECTIONS[:10]  # Reset with first 10
                    session['objections_used'] = []
                
                selected_objection = random.choice(available_objections)
                session['objections_used'].append(selected_objection)
                responses = [selected_objection]
                
            elif current_stage in ['mini_pitch', 'ai_pitch_prompt']:
                if roleplay_id == 2:
                    responses = PITCH_PROMPTS
                else:
                    responses = ["Go ahead, what is it?", "I'm listening.", "You have two minutes."]
                    
            elif current_stage == 'post_pitch_objections':
                # Use post-pitch objections
                used_objections = session.get('objections_used', [])
                available_objections = [obj for obj in POST_PITCH_OBJECTIONS if obj not in used_objections]
                
                if not available_objections:
                    available_objections = POST_PITCH_OBJECTIONS[:10]
                    session['objections_used'] = []
                
                selected_objection = random.choice(available_objections)
                session['objections_used'].append(selected_objection)
                responses = [selected_objection]
                
            else:
                responses = ["I see.", "Tell me more.", "Go on.", "Interesting."]
            
            selected_response = random.choice(responses)
            
            # Basic evaluation
            evaluation = self._evaluate_user_input_simple(user_input, current_stage)
            
            logger.info(f"Selected fallback response: {selected_response}")
            
            return selected_response, evaluation
            
        except Exception as e:
            logger.error(f"Error generating simple fallback: {e}")
            return "Can you repeat that?", {'quality_score': 5, 'should_continue': True}
    
    def _evaluate_opener_simple(self, user_input: str) -> int:
        """Simple opener evaluation"""
        score = 2  # Base score
        user_input_lower = user_input.lower()
        
        # Check for greeting
        if any(greeting in user_input_lower for greeting in ['hi', 'hello', 'good morning', 'good afternoon']):
            score += 1
        
        # Check for empathy
        if any(empathy in user_input_lower for empathy in ['know this is', "don't know me", 'out of the blue', 'interrupting']):
            score += 2
        
        # Check for question
        if user_input.strip().endswith('?'):
            score += 1
        
        # Check for reasonable length
        if len(user_input.split()) >= 5:
            score += 1
        
        # Check for politeness
        if any(polite in user_input_lower for polite in ['please', 'thank you', 'appreciate']):
            score += 1
            
        return min(score, 8)
    
   
    
    def _handle_hang_up(self, session: Dict, reason: str) -> Dict[str, Any]:
        """Handle prospect hanging up"""
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
        
        # For multi-call modes, handle progression
        if session['mode'] in ['marathon', 'legend']:
            return {
                'success': True,
                'ai_response': response,
                'call_continues': self._handle_multi_call_progression(session, {'pass': False}),
                'hang_up_reason': reason
            }
        
        return {
            'success': True,
            'ai_response': response,
            'call_continues': False,
            'hang_up_reason': reason,
            'coaching_note': 'The prospect hung up. Focus on improving your approach.'
        }
    
    def _handle_multi_call_progression(self, session: Dict, evaluation: Dict) -> bool:
        """Handle progression in Marathon/Legend modes"""
        try:
            session['call_count'] += 1
            
            if evaluation.get('pass', False):
                session['successful_calls'] += 1
            
            mode = session['mode']
            
            if mode == 'marathon':
                max_calls = 10
                if session['call_count'] >= max_calls:
                    return False  # Marathon complete
                else:
                    self._start_next_call(session)
                    return True
                    
            elif mode == 'legend':
                max_calls = 6
                if not evaluation.get('pass', False):
                    return False  # Legend mode - any failure ends
                elif session['call_count'] >= max_calls:
                    return False  # Legend complete
                else:
                    self._start_next_call(session)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error handling multi-call progression: {e}")
            return False
    
    def _start_next_call(self, session: Dict):
        """Start the next call in multi-call mode"""
        # Reset call state
        session['current_stage'] = self._get_initial_stage(session['roleplay_id'])
        session['objections_used'] = []
        session['hang_up_triggered'] = False
        
        # Add "next call" indicator
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
        """Get initial conversation stage"""
        stage_map = {
            1: 'phone_pickup',
            2: 'ai_pitch_prompt',  
            3: 'warmup_question',
            4: 'phone_pickup',
            5: 'phone_pickup'
        }
        return stage_map.get(roleplay_id, 'phone_pickup')
    
    def _generate_initial_response(self, roleplay_id: int, mode: str, user_context: Dict) -> str:
        """Generate initial response"""
        if roleplay_id == 2:
            return random.choice(PITCH_PROMPTS)
        elif roleplay_id == 3:
            return random.choice(WARMUP_QUESTIONS)
        else:
            return "Hello?"
    
    def _update_session_state(self, session: Dict, evaluation: Dict) -> None:
        """Update session state"""
        next_stage = evaluation.get('next_stage')
        if next_stage and next_stage != 'in_progress':
            session['current_stage'] = next_stage
    
    def _update_performance_metrics(self, session: Dict, user_input: str, evaluation: Dict) -> None:
        """Update performance metrics"""
        metrics = session.get('performance_metrics', {})
        stage = session.get('current_stage', 'unknown')
        quality_score = evaluation.get('quality_score', 5)
        
        if stage in ['phone_pickup', 'opener_evaluation']:
            metrics['opener_quality'] = max(metrics.get('opener_quality', 0), quality_score)
        elif stage == 'early_objection':
            metrics['objection_handling'] = max(metrics.get('objection_handling', 0), quality_score)
        elif stage in ['mini_pitch', 'pitch_evaluation']:
            metrics['pitch_effectiveness'] = max(metrics.get('pitch_effectiveness', 0), quality_score)
        
        if not session.get('hang_up_triggered'):
            metrics['confidence_level'] = min(metrics.get('confidence_level', 0) + 1, 10)
        
        session['performance_metrics'] = metrics
    
    def _should_call_continue(self, session: Dict, evaluation: Dict) -> bool:
        """Determine if call should continue"""
        if session.get('hang_up_triggered'):
            return False
        
        if not evaluation.get('should_continue', True):
            return False
        
        if evaluation.get('next_stage') == 'call_completed':
            return False
        
        return True
    
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End roleplay session"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            session['session_active'] = False
            session['ended_at'] = datetime.now(timezone.utc).isoformat()
            
            # Calculate metrics
            started_at = datetime.fromisoformat(session['started_at'].replace('Z', '+00:00'))
            ended_at = datetime.now(timezone.utc)
            duration_minutes = max(1, int((ended_at - started_at).total_seconds() / 60))
            
            # Generate coaching
            coaching_feedback, overall_score = self._generate_coaching_feedback(session)
            
            # Determine success
            session_success = self._determine_session_success(session, overall_score)
            
            # Generate completion message
            completion_message = self._generate_completion_message(session, session_success, overall_score)
            
            # Clean up
            del self.active_sessions[session_id]
            
            logger.info(f"Ended session {session_id}")
            
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
        """Generate basic coaching feedback"""
        conversation = session.get('conversation_history', [])
        user_messages = [msg for msg in conversation if msg.get('role') == 'user']
        
        coaching = {
            'coaching': {
                'sales_coaching': self._analyze_sales_performance(user_messages, session),
                'grammar_coaching': self._analyze_grammar_performance(user_messages),
                'vocabulary_coaching': self._analyze_vocabulary_usage(user_messages),
                'pronunciation_coaching': "Continue speaking clearly and practice key sales terms.",
                'rapport_assertiveness': self._analyze_rapport_confidence(user_messages, session)
            }
        }
        
        # Calculate score
        score = self._calculate_overall_score(session)
        
        return coaching, score
    
    def _analyze_sales_performance(self, user_messages: List[Dict], session: Dict) -> str:
        """Analyze sales performance"""
        if not user_messages:
            return "Complete more of the conversation to get sales coaching."
        
        if len(user_messages) == 1:
            opener = user_messages[0].get('content', '')
            if len(opener) < 20:
                return "Your opener was very brief. Try including a greeting, reason for calling, and permission to continue."
            elif any(word in opener.lower() for word in ['hello', 'hi']):
                return "Good job starting with a greeting. Work on adding empathy like 'I know this is unexpected'."
            else:
                return "Consider starting with a friendly greeting and showing empathy for the interruption."
        
        if session.get('hang_up_triggered'):
            return "The prospect hung up. Work on your opening approach to create better first impressions."
        
        if session.get('mode') in ['marathon', 'legend']:
            success_rate = session.get('successful_calls', 0) / max(session.get('call_count', 1), 1)
            if success_rate >= 0.6:
                return f"Great consistency! You passed {session.get('successful_calls', 0)} out of {session.get('call_count', 0)} calls."
            else:
                return "Focus on consistency. Practice your opener and objection handling more."
        
        return "Good job continuing the conversation. Focus on acknowledging concerns before redirecting."
    
    def _analyze_grammar_performance(self, user_messages: List[Dict]) -> str:
        """Analyze grammar"""
        if not user_messages:
            return "Speak more to get grammar feedback."
        
        total_text = ' '.join([msg.get('content', '') for msg in user_messages]).lower()
        
        if any(contraction in total_text for contraction in ["i'm", "don't", "we're", "it's"]):
            return "Great use of contractions! This makes your speech sound more natural."
        else:
            return "Try using contractions like 'I'm', 'don't', 'we're' to sound more natural."
    
    def _analyze_vocabulary_usage(self, user_messages: List[Dict]) -> str:
        """Analyze vocabulary"""
        if not user_messages:
            return "Speak more to get vocabulary feedback."
        
        total_text = ' '.join([msg.get('content', '') for msg in user_messages]).lower()
        
        business_words = ['help', 'solve', 'improve', 'solution', 'business', 'team']
        if any(word in total_text for word in business_words):
            return "Good use of business vocabulary. This shows professionalism."
        else:
            return "Try incorporating more business terms like 'solution', 'improve', or 'help'."
    
    def _analyze_rapport_confidence(self, user_messages: List[Dict], session: Dict) -> str:
        """Analyze rapport and confidence"""
        if session.get('hang_up_triggered'):
            return "The prospect hung up. Work on building better first impressions and rapport."
        
        if len(user_messages) >= 3:
            return "Great job keeping the conversation going! This shows good rapport-building skills."
        else:
            return "Try to engage more and ask questions to build stronger rapport."
    
    def _calculate_overall_score(self, session: Dict) -> int:
        """Calculate overall score"""
        evaluation_history = session.get('evaluation_history', [])
        
        if not evaluation_history:
            return 50
        
        # Average quality scores
        scores = [eval['evaluation'].get('quality_score', 5) for eval in evaluation_history]
        avg_score = sum(scores) / len(scores) if scores else 5
        
        # Convert to 0-100 scale
        base_score = int((avg_score / 8) * 100)
        
        # Adjustments
        if not session.get('hang_up_triggered'):
            base_score += 10
        
        if session.get('mode') in ['marathon', 'legend']:
            success_rate = session.get('successful_calls', 0) / max(session.get('call_count', 1), 1)
            base_score = int(base_score * (0.5 + success_rate * 0.5))
        
        return max(0, min(100, base_score))
    
    def _determine_session_success(self, session: Dict, overall_score: int) -> bool:
        """Determine session success"""
        mode = session['mode']
        
        if mode == 'practice':
            return not session.get('hang_up_triggered', False) and overall_score >= 50
        elif mode == 'marathon':
            return session['successful_calls'] >= 6
        elif mode == 'legend':
            return session['successful_calls'] >= 6
        else:
            return overall_score >= 60
    
    def _generate_completion_message(self, session: Dict, success: bool, overall_score: int) -> str:
        """Generate completion message"""
        mode = session['mode']
        successful_calls = session.get('successful_calls', 0)
        
        if mode == 'marathon':
            if success:
                return f"Outstanding! You passed {successful_calls} out of 10 calls. You've unlocked the next module!"
            else:
                return f"You completed all 10 calls and passed {successful_calls}. Keep practicing!"
        elif mode == 'legend':
            if success:
                return "LEGENDARY! Perfect score - you've mastered this module!"
            else:
                return f"Legend attempt complete. You made it through {successful_calls} calls."
        else:
            if overall_score >= 80:
                return f"Excellent work! Score: {overall_score}/100. You're ready for challenging modes!"
            elif overall_score >= 60:
                return f"Good job! Score: {overall_score}/100. Keep practicing to improve."
            else:
                return f"Nice try! Score: {overall_score}/100. Focus on the coaching feedback."
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session status"""
        session = self.active_sessions.get(session_id)
        if session:
            return {
                **session,
                'openai_available': self.openai_service.is_available()
            }
        return None
    
    def cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions"""
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
        """Get service status"""
        return {
            'active_sessions': len(self.active_sessions),
            'openai_available': self.openai_service.is_available(),
            'openai_status': self.openai_service.get_status(),
            'engine_status': 'running'
        }
    
    # ===== FIXED ROLEPLAY RESPONSE PROCESSING =====

    async def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input - FIXED VERSION with better conversation flow"""
        try:
            logger.info(f"Processing input for session {session_id}: '{user_input[:50]}...'")
            
            if session_id not in self.active_sessions:
                logger.error(f"Session {session_id} not found")
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            
            if not session.get('session_active'):
                logger.error(f"Session {session_id} is not active")
                raise ValueError("Session is not active")
            
            # Handle SILENCE_TIMEOUT specifically - don't add to conversation history as user message
            if user_input == '[SILENCE_TIMEOUT]':
                return self._handle_silence_timeout(session)
            
            # Add user input to conversation (only for real user input)
            session['conversation_history'].append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage']
            })
            
            # Update conversation stage based on actual user messages
            self._update_conversation_stage(session)
            
            # Generate AI response - TRY OpenAI first, then fallback
            try:
                logger.info("Attempting OpenAI response generation...")
                
                # Prepare roleplay configuration
                roleplay_config = {
                    'roleplay_id': session['roleplay_id'],
                    'mode': session['mode'],
                    'session_id': session['session_id']
                }
                
                # Call OpenAI service
                ai_response_data = await self.openai_service.generate_roleplay_response(
                    user_input,
                    session['conversation_history'],
                    session['user_context'],
                    roleplay_config
                )
                
                if ai_response_data.get('success'):
                    logger.info("OpenAI response successful")
                    ai_response = ai_response_data['response']
                    evaluation = ai_response_data.get('evaluation', {})
                else:
                    logger.warning("OpenAI response failed, using simple fallback")
                    ai_response, evaluation = self._generate_simple_fallback(session, user_input)
                    
            except Exception as openai_error:
                logger.error(f"OpenAI error: {openai_error}, using simple fallback")
                ai_response, evaluation = self._generate_simple_fallback(session, user_input)
            
            # Store evaluation
            session['evaluation_history'].append({
                'user_input': user_input,
                'evaluation': evaluation,
                'stage': session['current_stage'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            # Check for hang-up conditions
            if evaluation.get('should_hang_up') or not evaluation.get('should_continue', True):
                return self._handle_hang_up(session, evaluation.get('hang_up_reason', 'Call ended'))
            
            # Add AI response to conversation
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage'],
                'evaluation_data': evaluation
            })
            
            # Update session state
            self._update_session_state(session, evaluation)
            
            # Update performance metrics
            self._update_performance_metrics(session, user_input, evaluation)
            
            # Check if call should continue
            call_continues = self._should_call_continue(session, evaluation)
            
            # Handle multi-call modes
            if not call_continues and session['mode'] in ['marathon', 'legend']:
                call_continues = self._handle_multi_call_progression(session, evaluation)
            
            logger.info(f"Response generated: '{ai_response[:50]}...' Call continues: {call_continues}")
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': call_continues,
                'evaluation': evaluation,
                'session_state': session['current_stage'],
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

    def _handle_silence_timeout(self, session: Dict) -> Dict[str, Any]:
        """Handle silence timeout without adding to conversation history"""
        logger.info("Handling silence timeout")
        
        # Get a patience/impatience response based on conversation stage
        user_messages = [
            m for m in session['conversation_history'] 
            if m.get('role') == 'user' and not m.get('content', '').startswith('[SILENCE_TIMEOUT]')
        ]
        
        if len(user_messages) == 0:
            ai_response = random.choice(["Hello? Are you there?", "Did I lose you?", "Anyone there?"])
        elif len(user_messages) == 1:
            ai_response = random.choice(["Are you still there?", "Hello?", "Did you have a question?"])
        else:
            ai_response = random.choice(["I'm waiting...", "Go ahead.", "I don't have all day.", "Are you thinking about it?"])
        
        # Add AI response to conversation history (but not the SILENCE_TIMEOUT)
        session['conversation_history'].append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': session['current_stage'],
            'silence_response': True
        })
        
        return {
            'success': True,
            'ai_response': ai_response,
            'call_continues': True,
            'evaluation': {'quality_score': 3, 'should_continue': True},
            'session_state': session['current_stage']
        }

    def _update_conversation_stage(self, session: Dict) -> None:
        """Update conversation stage based on actual conversation progress"""
        # Count real user messages (not SILENCE_TIMEOUT)
        user_messages = [
            m for m in session['conversation_history'] 
            if m.get('role') == 'user' and not m.get('content', '').startswith('[SILENCE_TIMEOUT]')
        ]
        
        roleplay_id = session['roleplay_id']
        user_count = len(user_messages)
        
        if roleplay_id == 1:  # Opener + Early Objections
            if user_count <= 1:
                session['current_stage'] = 'opener_evaluation'
            elif user_count == 2:
                session['current_stage'] = 'early_objection'
            elif user_count == 3:
                session['current_stage'] = 'objection_response'
            else:
                session['current_stage'] = 'mini_pitch'
        
        logger.info(f"Updated stage to {session['current_stage']} based on {user_count} user messages")

    def _evaluate_user_input_simple(self, user_input: str, stage: str) -> Dict[str, Any]:
        """Simple evaluation logic - IMPROVED"""
        evaluation = {
            'quality_score': 5,
            'should_continue': True,
            'should_hang_up': False,
            'next_stage': 'in_progress',
            'pass': True
        }
        
        user_input_lower = user_input.lower()
        
        if stage in ['phone_pickup', 'opener_evaluation']:
            evaluation['quality_score'] = self._evaluate_opener_simple(user_input)
            evaluation['pass'] = evaluation['quality_score'] >= 4  # Lowered threshold
            
            # Don't end call too easily
            if evaluation['quality_score'] <= 2 and random.random() < 0.15:  # Reduced hang-up chance
                evaluation['should_hang_up'] = True
                evaluation['should_continue'] = False
                evaluation['hang_up_reason'] = 'Poor opener'
            
        elif stage == 'early_objection':
            # Check for acknowledgment and empathy
            if any(ack in user_input_lower for ack in ['understand', 'get that', 'fair enough', 'totally get', 'appreciate']):
                evaluation['quality_score'] += 2
            
            # Check for question or engagement
            if user_input.strip().endswith('?') or any(q in user_input_lower for q in ['can i', 'would you', 'could i']):
                evaluation['quality_score'] += 1
            
            # Check for pushing too hard
            if any(push in user_input_lower for push in ['you should', 'you need', 'you have to']):
                evaluation['quality_score'] -= 1
                
        elif stage in ['objection_response', 'mini_pitch']:
            # Check for value focus
            if any(value in user_input_lower for value in ['help', 'save', 'improve', 'solve', 'benefit']):
                evaluation['quality_score'] += 1
            
            # Check for question
            if user_input.strip().endswith('?'):
                evaluation['quality_score'] += 1
            
            # Check for being too salesy
            if any(sales in user_input_lower for sales in ['amazing', 'incredible', 'guarantee']):
                evaluation['quality_score'] -= 1
        
        # Ensure score stays in reasonable range
        evaluation['quality_score'] = max(1, min(8, evaluation['quality_score']))
        
        return evaluation
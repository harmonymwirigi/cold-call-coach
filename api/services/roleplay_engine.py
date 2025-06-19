# ===== EMERGENCY FIX: API/SERVICES/ROLEPLAY_ENGINE.PY =====
# This version removes the complex evaluation temporarily to get the system working

import random
import logging
import asyncio
import re
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
        
        # Session state tracking - CRITICAL: Keep sessions in memory
        self.active_sessions = {}
        
        logger.info(f"RoleplayEngine initialized - OpenAI available: {self.openai_service.is_available()}")
        
    def create_session(self, user_id: str, roleplay_id: int, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create a new roleplay session with enhanced context"""
        try:
            # Validate inputs
            if roleplay_id not in ROLEPLAY_CONFIG:
                raise ValueError(f"Invalid roleplay ID: {roleplay_id}")
            
            config = ROLEPLAY_CONFIG[roleplay_id]
            if mode not in config.get('modes', ['practice']):  # Default to practice if modes not defined
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
                'coaching_notes': []
            }
            
            # CRITICAL: Store session in memory
            self.active_sessions[session_id] = session_data
            
            # Generate intelligent initial response
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
    
    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input with SIMPLIFIED evaluation for debugging"""
        try:
            logger.info(f"Processing input for session {session_id}: {user_input[:50]}...")
            logger.info(f"Active sessions: {list(self.active_sessions.keys())}")
            
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
            
            # EMERGENCY FIX: Use simple evaluation for ALL roleplays temporarily
            print(f"DEBUG: Processing input for roleplay {session['roleplay_id']}: '{user_input}'")
            
            # Simple evaluation that always allows conversation to continue
            evaluation = {
                'quality_score': 6,  # Good score
                'should_continue': True,
                'should_hang_up': False,
                'next_stage': self._get_next_stage(session['current_stage'], session['roleplay_id']),
                'feedback_notes': [],
                'debug_mode': True
            }
            
            print(f"DEBUG: Evaluation result: {evaluation}")
            
            # Generate AI response using OpenAI service
            ai_response_data = self._generate_ai_response_async(session, user_input, evaluation)
            
            if not ai_response_data.get('success'):
                print(f"DEBUG: AI response failed: {ai_response_data}")
                return {
                    'success': False,
                    'error': ai_response_data.get('error', 'Failed to generate AI response'),
                    'call_continues': False
                }
            
            ai_response = ai_response_data['response']
            print(f"DEBUG: AI response generated: '{ai_response}'")
            
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
            
            logger.info(f"Generated AI response: {ai_response[:50]}... Call continues: {call_continues}")
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': call_continues,
                'evaluation': evaluation,
                'session_state': session['current_stage'],
                'performance_hint': self._get_performance_hint(evaluation),
                'debug_info': {
                    'user_input': user_input,
                    'current_stage': session['current_stage'],
                    'next_stage': evaluation.get('next_stage'),
                    'ai_response_length': len(ai_response)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            print(f"DEBUG: Exception in process_user_input: {e}")
            return {
                'success': False,
                'error': str(e),
                'call_continues': False
            }
    
    def _get_next_stage(self, current_stage: str, roleplay_id: int) -> str:
        """Simple stage progression logic"""
        stage_map = {
            'phone_pickup': 'opener_evaluation',
            'opener_evaluation': 'early_objection', 
            'early_objection': 'mini_pitch',
            'mini_pitch': 'soft_discovery',
            'soft_discovery': 'call_completed'
        }
        
        next_stage = stage_map.get(current_stage, 'in_progress')
        print(f"DEBUG: Stage progression: {current_stage} -> {next_stage}")
        return next_stage
    
    def _generate_ai_response_async(self, session: Dict, user_input: str, evaluation: Dict = None) -> Dict[str, Any]:
        """Generate AI response with simplified logic"""
        try:
            print(f"DEBUG: Generating AI response for stage: {session['current_stage']}")
            
            # Prepare roleplay configuration
            roleplay_config = {
                'roleplay_id': session['roleplay_id'],
                'mode': session['mode'],
                'session_id': session['session_id']
            }
            
            # TRY OpenAI first if available
            if self.openai_service.is_available():
                logger.info("Using OpenAI for AI response generation")
                
                try:
                    # Create event loop if needed
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    if loop.is_running():
                        # Use fallback if loop is running
                        logger.warning("Event loop is running, using fallback")
                        return self._generate_fallback_response(session, user_input, evaluation)
                    else:
                        # Generate response using OpenAI
                        response_data = loop.run_until_complete(
                            self.openai_service.generate_roleplay_response(
                                user_input,
                                session['conversation_history'],
                                session['user_context'],
                                roleplay_config
                            )
                        )
                        
                        if response_data.get('success'):
                            logger.info(f"OpenAI response generated successfully: {response_data['response'][:50]}...")
                            return response_data
                        else:
                            logger.warning(f"OpenAI failed: {response_data.get('error')}, using fallback")
                            return self._generate_fallback_response(session, user_input, evaluation)
                            
                except Exception as openai_error:
                    logger.error(f"OpenAI error: {openai_error}, using fallback")
                    return self._generate_fallback_response(session, user_input, evaluation)
            else:
                logger.info("OpenAI not available, using fallback responses")
                return self._generate_fallback_response(session, user_input, evaluation)
            
        except Exception as e:
            logger.error(f"Error in async AI response generation: {e}")
            return self._generate_fallback_response(session, user_input, evaluation)
    
    def _generate_fallback_response(self, session: Dict, user_input: str, evaluation: Dict = None) -> Dict[str, Any]:
        """Generate fallback response when OpenAI is unavailable - SIMPLIFIED VERSION"""
        try:
            current_stage = session['current_stage']
            roleplay_id = session['roleplay_id']
            
            print(f"DEBUG: Generating fallback response for stage: {current_stage}")
            
            # SIMPLIFIED: Always give appropriate response based on stage
            if current_stage in ['phone_pickup', 'opener_evaluation']:
                responses = [
                    "What's this about?", 
                    "Who is this?", 
                    "I'm listening.", 
                    "Go ahead.",
                    "You have 30 seconds."
                ]
            elif current_stage == 'early_objection':
                responses = EARLY_OBJECTIONS[:5]  # Use first 5 objections
            elif current_stage in ['mini_pitch', 'ai_pitch_prompt']:
                if roleplay_id == 2:
                    responses = PITCH_PROMPTS[:3]
                else:
                    responses = ["Go ahead, what is it?", "I'm listening.", "Tell me more."]
            elif current_stage == 'post_pitch_objections':
                responses = POST_PITCH_OBJECTIONS[:5]
            elif current_stage == 'warmup_question':
                responses = WARMUP_QUESTIONS[:3]
            else:
                responses = ["I see.", "Tell me more.", "Go on.", "Interesting."]
            
            # Avoid recently used responses
            used_responses = session.get('objections_used', [])
            available_responses = [r for r in responses if r not in used_responses]
            
            if not available_responses:
                available_responses = responses
                session['objections_used'] = []  # Reset if all used
            
            selected_response = random.choice(available_responses)
            session['objections_used'].append(selected_response)
            
            # Use provided evaluation or create basic evaluation
            if not evaluation:
                evaluation = {
                    'quality_score': 6,
                    'should_continue': True,
                    'should_hang_up': False,
                    'next_stage': 'in_progress'
                }
            
            print(f"DEBUG: Selected fallback response: '{selected_response}'")
            
            return {
                'success': True,
                'response': selected_response,
                'evaluation': evaluation,
                'fallback_used': True
            }
            
        except Exception as e:
            logger.error(f"Error generating fallback response: {e}")
            print(f"DEBUG: Error in fallback response: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "Can you repeat that?"
            }
    
    # ===== ALL OTHER METHODS UNCHANGED =====
    
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
        if evaluation.get('next_stage') and evaluation.get('next_stage') != 'in_progress':
            old_stage = session['current_stage']
            session['current_stage'] = evaluation.get('next_stage')
            print(f"DEBUG: Updated session stage: {old_stage} -> {session['current_stage']}")
    
    def _update_performance_metrics(self, session: Dict, user_input: str, evaluation: Dict) -> None:
        """Update running performance metrics"""
        metrics = session.get('performance_metrics', {})
        
        # Update based on current stage and evaluation
        stage = session.get('current_stage', 'unknown')
        quality_score = evaluation.get('quality_score', 5)
        
        if stage in ['phone_pickup', 'opener_evaluation']:
            metrics['opener_quality'] = max(metrics.get('opener_quality', 0), quality_score)
        elif stage == 'early_objection':
            metrics['objection_handling'] = max(metrics.get('objection_handling', 0), quality_score)
        elif stage in ['mini_pitch', 'pitch_evaluation']:
            metrics['pitch_effectiveness'] = max(metrics.get('pitch_effectiveness', 0), quality_score)
        
        session['performance_metrics'] = metrics
    
    def _get_performance_hint(self, evaluation: Dict) -> Optional[str]:
        """Get real-time performance hint for user"""
        quality_score = evaluation.get('quality_score', 5)
        
        if quality_score <= 3:
            return "Try showing more empathy and building rapport."
        elif quality_score >= 7:
            return "Great response! Keep this energy."
        else:
            return None
    
    def _should_call_continue(self, session: Dict, evaluation: Dict) -> bool:
        """Determine if call should continue - SIMPLIFIED"""
        # Always continue unless explicitly ended
        if evaluation.get('next_stage') == 'call_completed':
            return False
        
        return True
    
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End roleplay session and generate basic coaching"""
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
            
            # Generate basic coaching
            coaching_feedback, overall_score = self._generate_basic_coaching(session)
            
            # Basic success determination
            session_success = overall_score >= 60 and not session.get('hang_up_triggered', False)
            
            # Generate completion message
            completion_message = f"Session complete! Score: {overall_score}/100. Keep practicing to improve your skills."
            
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
                'performance_metrics': session.get('performance_metrics', {})
            }
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_basic_coaching(self, session: Dict) -> Tuple[Dict, int]:
        """Generate basic coaching"""
        conversation = session.get('conversation_history', [])
        user_messages = [msg for msg in conversation if msg.get('role') == 'user']
        
        coaching = {
            'coaching': {
                'sales_coaching': 'Good job participating in the conversation. Keep practicing your opening and objection handling.',
                'grammar_coaching': 'Your English is clear. Try using more contractions like "I\'m" and "don\'t" to sound natural.',
                'vocabulary_coaching': 'Good word choices. Use simple business terms when appropriate.',
                'pronunciation_coaching': 'Speak clearly and at a steady pace. Practice key sales terms.',
                'rapport_assertiveness': 'Work on building confidence while staying professional.'
            }
        }
        
        # Basic score calculation
        score = 50 + (len(user_messages) * 10)
        score = min(100, max(0, score))
        
        return coaching, score
    
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
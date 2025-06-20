# ===== ENHANCED ROLEPLAY ENGINE - MARATHON MODE SUPPORT =====

import random
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set

logger = logging.getLogger(__name__)

class RoleplayEngine:
    def __init__(self):
        # Import here to avoid circular imports
        try:
            from services.openai_service import OpenAIService
            self.openai_service = OpenAIService()
            logger.info(f"OpenAI service initialized: {self.openai_service.is_available()}")
        except Exception as e:
            logger.error(f"Failed to import OpenAI service: {e}")
            self.openai_service = None
        
        # Session storage
        self.active_sessions = {}
        
        # MARATHON MODE: Early-stage objections (29 items)
        self.early_stage_objections = [
            "What's this about?", "I'm not interested", "We don't take cold calls",
            "Now is not a good time", "I have a meeting", "Can you call me later?",
            "I'm about to go into a meeting", "Send me an email", 
            "Can you send me the information?", "Can you message me on WhatsApp?",
            "Who gave you this number?", "This is my personal number",
            "Where did you get my number?", "What are you trying to sell me?",
            "Is this a sales call?", "Is this a cold call?",
            "Are you trying to sell me something?", "We are ok for the moment",
            "We are all good / all set", "We're not looking for anything right now",
            "We are not changing anything", "How long is this going to take?",
            "Is this going to take long?", "What company are you calling from?",
            "Who are you again?", "Where are you calling from?",
            "I never heard of you", "Not interested right now", "Just send me the details"
        ]
        
        # MARATHON MODE: Impatience phrases (10 items)
        self.impatience_phrases = [
            "Hello? Are you still with me?", "Can you hear me?",
            "Just checking you're there…", "Still on the line?",
            "I don't have much time for this.", "Sounds like you are gone.",
            "Are you an idiot.", "What is going on.",
            "Are you okay to continue?", "I am afraid I have to go"
        ]
        
        # Stage flow for different modes
        self.stage_flow = {
            'practice': {  # Original 1.1 flow with extended conversation
                'phone_pickup': 'opener_evaluation',
                'opener_evaluation': 'early_objection',
                'early_objection': 'objection_handling',
                'objection_handling': 'mini_pitch',
                'mini_pitch': 'soft_discovery',
                'soft_discovery': 'extended_conversation',
                'extended_conversation': 'call_ended'
            },
            'marathon': {  # Marathon multi-call flow
                'phone_pickup': 'opener_evaluation',
                'opener_evaluation': 'early_objection',
                'early_objection': 'objection_handling',
                'objection_handling': 'mini_pitch',
                'mini_pitch': 'soft_discovery',
                'soft_discovery': 'call_completed',
                'call_completed': 'next_call_or_end'
            },
            'legend': {  # Legend mode (same as marathon but 6 calls, sudden death)
                'phone_pickup': 'opener_evaluation',
                'opener_evaluation': 'early_objection',
                'early_objection': 'objection_handling',
                'objection_handling': 'mini_pitch',
                'mini_pitch': 'soft_discovery',
                'soft_discovery': 'call_completed',
                'call_completed': 'next_call_or_end'
            }
        }
        
        # Mode-specific settings
        self.mode_settings = {
            'practice': {
                'max_calls': 1,
                'pass_threshold': 1,
                'real_time_coaching': True,
                'random_hangups': False,
                'max_turns_per_stage': 5,
                'max_total_turns': 25
            },
            'marathon': {
                'max_calls': 10,
                'pass_threshold': 6,
                'real_time_coaching': False,
                'random_hangups': True,
                'random_hangup_chance': 0.25,  # 25% chance (20-30% range)
                'max_turns_per_stage': 3,
                'max_total_turns': 15
            },
            'legend': {
                'max_calls': 6,
                'pass_threshold': 6,
                'real_time_coaching': False,
                'random_hangups': False,
                'sudden_death': True,
                'max_turns_per_stage': 3,
                'max_total_turns': 15
            }
        }
        
        logger.info(f"RoleplayEngine initialized with Marathon/Legend support. OpenAI available: {self.is_openai_available()}")

    def is_openai_available(self) -> bool:
        """Check if OpenAI is available"""
        return self.openai_service and self.openai_service.is_available()

    def create_session(self, user_id: str, roleplay_id: int, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create new Roleplay session (1.1 Practice, 1.2 Marathon, or Legend)"""
        try:
            session_id = f"{user_id}_{roleplay_id}_{mode}_{int(datetime.now().timestamp())}"
            
            # Get mode settings
            settings = self.mode_settings.get(mode, self.mode_settings['practice'])
            
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'roleplay_id': roleplay_id,
                'mode': mode,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'user_context': user_context,
                'session_active': True,
                'settings': settings,
                
                # Multi-call state (Marathon/Legend)
                'current_call': 1,
                'max_calls': settings['max_calls'],
                'calls_passed': 0,
                'calls_failed': 0,
                'pass_threshold': settings['pass_threshold'],
                'run_complete': False,
                'run_success': False,
                
                # Current call state
                'conversation_history': [],
                'current_stage': 'phone_pickup',
                'call_active': False,
                'hang_up_triggered': False,
                'turn_count': 0,
                'stage_turn_count': 0,
                'call_result': None,  # 'pass', 'fail', or None
                
                # Marathon/Legend specific tracking
                'objections_used': set(),  # Track used objections (never repeat)
                'random_hangup_occurred': False,
                'aggregate_coaching_data': [],  # Store data for end-of-run coaching
                
                # Roleplay tracking
                'rubric_scores': {},
                'stage_progression': ['phone_pickup'],
                'overall_call_result': 'in_progress'
            }
            
            # Store session
            self.active_sessions[session_id] = session_data
            
            # Generate initial phone pickup for first call
            initial_response = self._get_phone_pickup_response(user_context)
            
            # Add to conversation
            session_data['conversation_history'].append({
                'role': 'assistant',
                'content': initial_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': 'phone_pickup',
                'call_number': 1
            })
            
            session_data['call_active'] = True
            
            logger.info(f"Created {mode} session {session_id} - Max calls: {settings['max_calls']}")
            
            return {
                'success': True,
                'session_id': session_id,
                'initial_response': initial_response,
                'mode': mode,
                'call_info': {
                    'current_call': 1,
                    'max_calls': settings['max_calls'],
                    'pass_threshold': settings['pass_threshold']
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return {'success': False, 'error': str(e)}

    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input for any roleplay mode"""
        try:
            logger.info(f"Processing input for session {session_id}: {user_input[:50]}...")
            
            if session_id not in self.active_sessions:
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            
            if not session.get('session_active'):
                raise ValueError("Session not active")
            
            if not session.get('call_active'):
                raise ValueError("No active call")
            
            # Handle silence triggers
            if user_input in ['[SILENCE_IMPATIENCE]', '[SILENCE_HANGUP]']:
                return self._handle_silence_trigger(session, user_input)
            
            # Increment turn counters
            session['turn_count'] += 1
            session['stage_turn_count'] += 1
            
            logger.info(f"Call {session['current_call']}/{session['max_calls']} - Turn {session['turn_count']}, Stage: {session['current_stage']}")
            
            # Add user input to conversation
            session['conversation_history'].append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage'],
                'call_number': session['current_call']
            })
            
            # Determine evaluation stage
            evaluation_stage = self._get_evaluation_stage(session['current_stage'])
            
            # Evaluate user input using AI
            evaluation = self._evaluate_user_input(session, user_input, evaluation_stage)
            
            # Update conversation quality tracking (for all modes)
            self._update_conversation_quality(session, evaluation)
            
            # Store evaluation for potential coaching
            if session['mode'] in ['marathon', 'legend']:
                self._store_coaching_data(session, evaluation, user_input, evaluation_stage)
            else:
                # For Practice mode, store individual evaluations for real-time feedback
                session.setdefault('live_evaluations', []).append({
                    'stage': evaluation_stage,
                    'evaluation': evaluation,
                    'user_input': user_input,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            # Check for random hang-up (Marathon mode only, after opener pass)
            random_hangup = self._check_random_hangup(session, evaluation)
            
            if random_hangup:
                logger.info("Random hang-up triggered (Marathon mode)")
                return self._handle_random_hangup(session)
            
            # Check if should hang up based on evaluation
            should_hang_up = self._should_hang_up_now(session, evaluation, user_input)
            
            if should_hang_up:
                logger.info("Triggering hang-up based on evaluation")
                return self._handle_evaluation_hangup(session, evaluation, failed=True)
            
            # Generate AI response based on evaluation and stage
            ai_response = self._generate_ai_response(session, user_input, evaluation)
            
            # Update session state (move to next stage if appropriate)
            stage_changed = self._update_session_state(session, evaluation)
            
            # Check if call should end (completed successfully)
            call_completed = self._check_call_completion(session, evaluation)
            
            if call_completed:
                return self._handle_call_completion(session, passed=True)
            
            # Add AI response to conversation
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage'],
                'evaluation': evaluation,
                'call_number': session['current_call']
            })
            
            # Determine if call should continue
            call_continues = self._should_call_continue(session, evaluation)
            
            logger.info(f"Stage: {session['current_stage']} | Response: {ai_response[:50]}... | Continues: {call_continues}")
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': call_continues,
                'evaluation': evaluation if session['settings']['real_time_coaching'] else {},
                'session_state': session['current_stage'],
                'call_info': {
                    'current_call': session['current_call'],
                    'max_calls': session['max_calls'],
                    'calls_passed': session['calls_passed'],
                    'calls_failed': session['calls_failed']
                },
                # Add real-time coaching for Practice mode
                'live_coaching': self._get_live_coaching(session, evaluation) if session['settings']['real_time_coaching'] else None
            }
            
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return {
                'success': False,
                'error': str(e),
                'call_continues': False
            }

    def _check_random_hangup(self, session: Dict, evaluation: Dict) -> bool:
        """Check for random hang-up in Marathon mode"""
        # Only Marathon mode has random hang-ups
        if session['mode'] != 'marathon':
            return False
        
        # Only after opener evaluation stage
        if session['current_stage'] != 'opener_evaluation':
            return False
        
        # Only if opener passed
        if not evaluation.get('passed', False):
            return False
        
        # Only if not already had a random hang-up this call
        if session.get('random_hangup_occurred', False):
            return False
        
        # 20-30% chance (using 25%)
        hangup_chance = session['settings'].get('random_hangup_chance', 0.25)
        should_hangup = random.random() < hangup_chance
        
        if should_hangup:
            session['random_hangup_occurred'] = True
            logger.info(f"Random hang-up triggered with {hangup_chance*100}% chance")
        
        return should_hangup

    def _handle_random_hangup(self, session: Dict) -> Dict[str, Any]:
        """Handle random hang-up in Marathon mode"""
        hangup_response = "Sorry, I have to take another call. Goodbye."
        
        session['conversation_history'].append({
            'role': 'assistant',
            'content': hangup_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': session['current_stage'],
            'call_number': session['current_call'],
            'random_hangup': True
        })
        
        # Mark call as failed due to random hang-up
        session['call_result'] = 'fail'
        session['calls_failed'] += 1
        session['call_active'] = False
        
        # Check if should start next call or end run
        return self._check_next_call_or_end_run(session, hangup_response)

    def _handle_evaluation_hangup(self, session: Dict, evaluation: Dict, failed: bool) -> Dict[str, Any]:
        """Handle hang-up due to evaluation failure"""
        hangup_response = self._get_hangup_response(session['current_stage'], evaluation)
        
        session['conversation_history'].append({
            'role': 'assistant',
            'content': hangup_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': session['current_stage'],
            'call_number': session['current_call'],
            'evaluation_hangup': True
        })
        
        # Mark call result
        session['call_result'] = 'fail' if failed else 'pass'
        if failed:
            session['calls_failed'] += 1
        else:
            session['calls_passed'] += 1
        
        session['call_active'] = False
        
        # Check if should start next call or end run
        return self._check_next_call_or_end_run(session, hangup_response)

    def _handle_call_completion(self, session: Dict, passed: bool) -> Dict[str, Any]:
        """Handle successful call completion"""
        completion_responses = [
            "That sounds interesting. Send me some information and let's schedule a follow-up.",
            "Alright, I'm intrigued. Email me the details and we can discuss further.",
            "That could be relevant for us. Can you send me a proposal?",
            "I'd like to learn more. Send me the information and let's book a meeting."
        ]
        
        completion_response = random.choice(completion_responses)
        
        session['conversation_history'].append({
            'role': 'assistant',
            'content': completion_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'call_completed',
            'call_number': session['current_call'],
            'call_completed': True
        })
        
        # Mark call as passed
        session['call_result'] = 'pass'
        session['calls_passed'] += 1
        session['call_active'] = False
        
        # Check if should start next call or end run
        return self._check_next_call_or_end_run(session, completion_response)

    def _check_next_call_or_end_run(self, session: Dict, last_response: str) -> Dict[str, Any]:
        """Check whether to start next call or end the run"""
        current_call = session['current_call']
        max_calls = session['max_calls']
        calls_passed = session['calls_passed']
        calls_failed = session['calls_failed']
        mode = session['mode']
        
        # Legend mode: sudden death - fail on first mistake
        if mode == 'legend' and calls_failed > 0:
            logger.info("Legend mode: Failed call, ending run immediately")
            return self._end_run(session, last_response, success=False, sudden_death=True)
        
        # Check if we've completed all calls
        if current_call >= max_calls:
            success = calls_passed >= session['pass_threshold']
            logger.info(f"All calls completed: {calls_passed}/{max_calls} passed. Success: {success}")
            return self._end_run(session, last_response, success=success)
        
        # Legend mode: If we've passed all calls so far, and this is the last call
        if mode == 'legend' and current_call == max_calls and calls_passed == max_calls:
            logger.info("Legend mode: Perfect run completed!")
            return self._end_run(session, last_response, success=True, perfect_run=True)
        
        # Start next call
        logger.info(f"Starting next call: {current_call + 1}/{max_calls}")
        return self._start_next_call(session, last_response)

    def _start_next_call(self, session: Dict, last_response: str) -> Dict[str, Any]:
        """Start the next call in the sequence"""
        # Increment call number
        session['current_call'] += 1
        session['call_active'] = True
        session['call_result'] = None
        session['random_hangup_occurred'] = False
        
        # Reset call state
        session['current_stage'] = 'phone_pickup'
        session['turn_count'] = 0
        session['stage_turn_count'] = 0
        session['hang_up_triggered'] = False
        
        # Generate new phone pickup
        pickup_response = self._get_phone_pickup_response(session['user_context'])
        
        # Add to conversation history
        session['conversation_history'].append({
            'role': 'assistant',
            'content': pickup_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'phone_pickup',
            'call_number': session['current_call'],
            'new_call_start': True
        })
        
        return {
            'success': True,
            'ai_response': pickup_response,
            'call_continues': True,
            'next_call': True,
            'call_info': {
                'current_call': session['current_call'],
                'max_calls': session['max_calls'],
                'calls_passed': session['calls_passed'],
                'calls_failed': session['calls_failed'],
                'last_call_response': last_response
            }
        }

    def _end_run(self, session: Dict, last_response: str, success: bool, sudden_death: bool = False, perfect_run: bool = False) -> Dict[str, Any]:
        """End the entire run (all calls completed or failed)"""
        session['run_complete'] = True
        session['run_success'] = success
        session['session_active'] = False
        session['ended_at'] = datetime.now(timezone.utc).isoformat()
        
        # Generate end-of-run coaching (only for Marathon/Legend)
        if session['mode'] in ['marathon', 'legend']:
            coaching_result = self._generate_end_of_run_coaching(session)
        else:
            coaching_result = {'coaching': {}, 'score': 50}
        
        return {
            'success': True,
            'ai_response': last_response,
            'call_continues': False,
            'run_complete': True,
            'run_success': success,
            'sudden_death': sudden_death,
            'perfect_run': perfect_run,
            'final_stats': {
                'calls_passed': session['calls_passed'],
                'calls_failed': session['calls_failed'],
                'total_calls': session['current_call'],
                'pass_rate': (session['calls_passed'] / session['current_call']) * 100 if session['current_call'] > 0 else 0
            },
            'coaching': coaching_result.get('coaching', {}),
            'overall_score': coaching_result.get('score', 50)
        }

    def _get_phone_pickup_response(self, user_context: Dict) -> str:
        """Get phone pickup response"""
        responses = [
            "Hello?",
            "Hi there.",
            "Good morning.",
            "Yes?",
            f"{user_context.get('first_name', 'Alex')} speaking.",
            "Hello, this is Alex.",
            f"{user_context.get('first_name', 'Alex')} here."
        ]
        return random.choice(responses)

    def _get_unused_objection(self, session: Dict) -> str:
        """Get an unused objection for this run"""
        used_objections = session.get('objections_used', set())
        available_objections = [obj for obj in self.early_stage_objections if obj not in used_objections]
        
        if not available_objections:
            # If all objections used, reset and use any
            logger.warning("All objections used in run, resetting list")
            available_objections = self.early_stage_objections
            session['objections_used'] = set()
        
        selected_objection = random.choice(available_objections)
        session['objections_used'].add(selected_objection)
        
        logger.info(f"Selected objection: '{selected_objection}' ({len(used_objections) + 1}/{len(self.early_stage_objections)} used)")
        
        return selected_objection

    def _store_coaching_data(self, session: Dict, evaluation: Dict, user_input: str, stage: str):
        """Store data for end-of-run coaching"""
        coaching_data = {
            'call_number': session['current_call'],
            'stage': stage,
            'user_input': user_input,
            'evaluation': evaluation,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        session.setdefault('aggregate_coaching_data', []).append(coaching_data)

    def _generate_end_of_run_coaching(self, session: Dict) -> Dict[str, Any]:
        """Generate comprehensive end-of-run coaching for Marathon/Legend modes"""
        try:
            if self.is_openai_available():
                logger.info("Generating end-of-run coaching with OpenAI")
                return self.openai_service.generate_marathon_coaching(
                    session['conversation_history'],
                    session.get('aggregate_coaching_data', []),
                    session['user_context'],
                    session['mode'],
                    {
                        'calls_passed': session['calls_passed'],
                        'calls_failed': session['calls_failed'],
                        'total_calls': session['current_call']
                    }
                )
            else:
                logger.warning("OpenAI not available, using enhanced basic coaching")
                return self._enhanced_marathon_coaching(session)
                
        except Exception as e:
            logger.error(f"End-of-run coaching generation error: {e}")
            return self._enhanced_marathon_coaching(session)

    def _enhanced_marathon_coaching(self, session: Dict) -> Dict[str, Any]:
        """Enhanced basic coaching for Marathon/Legend modes"""
        coaching_data = session.get('aggregate_coaching_data', [])
        calls_passed = session['calls_passed']
        total_calls = session['current_call']
        mode = session['mode']
        
        # Calculate overall score
        pass_rate = (calls_passed / total_calls) * 100 if total_calls > 0 else 0
        base_score = int(pass_rate)
        
        # Mode-specific scoring adjustments
        if mode == 'legend' and calls_passed == total_calls:
            base_score = 100  # Perfect Legend run
        elif mode == 'marathon' and calls_passed >= 6:
            base_score = max(75, base_score)  # Marathon pass bonus
        
        score = min(100, max(30, base_score))
        
        # Generate coaching based on performance patterns
        coaching = self._analyze_performance_patterns(coaching_data, mode, calls_passed, total_calls)
        
        return {
            'success': True,
            'coaching': coaching,
            'score': score,
            'source': 'enhanced_basic_marathon'
        }

    def _analyze_performance_patterns(self, coaching_data: List[Dict], mode: str, calls_passed: int, total_calls: int) -> Dict[str, str]:
        """Analyze performance patterns across all calls"""
        # Count issues by category
        opener_issues = 0
        objection_issues = 0
        pitch_issues = 0
        discovery_issues = 0
        
        for data in coaching_data:
            evaluation = data.get('evaluation', {})
            stage = data.get('stage', '')
            passed = evaluation.get('passed', False)
            
            if not passed:
                if stage == 'opener':
                    opener_issues += 1
                elif stage == 'objection_handling':
                    objection_issues += 1
                elif stage == 'mini_pitch':
                    pitch_issues += 1
                elif stage == 'soft_discovery':
                    discovery_issues += 1
        
        # Generate contextual coaching
        coaching = {}
        
        # Sales coaching
        if calls_passed >= 6:
            coaching['sales_coaching'] = f"Excellent work! You passed {calls_passed}/{total_calls} calls in {mode} mode. Your cold calling skills are developing well."
        elif calls_passed >= 4:
            coaching['sales_coaching'] = f"Good progress! You passed {calls_passed}/{total_calls} calls. Focus on consistency across all stages."
        else:
            coaching['sales_coaching'] = f"Keep practicing! You passed {calls_passed}/{total_calls} calls. The more reps you get, the easier it becomes."
        
        # Grammar coaching (CEFR A2 level)
        coaching['grammar_coaching'] = "Use contractions like 'I'm calling' instead of 'I am calling' to sound more natural in English."
        
        # Vocabulary coaching
        if pitch_issues > 2:
            coaching['vocabulary_coaching'] = "Use simple outcome words like 'help save time' or 'increase sales' instead of complex business terms."
        else:
            coaching['vocabulary_coaching'] = "Great vocabulary! Keep using simple, clear words that prospects understand easily."
        
        # Pronunciation coaching
        coaching['pronunciation_coaching'] = "Practice key phrases slowly: 'Can I tell you why I'm calling?' Remember to speak clearly and not too fast."
        
        # Rapport & assertiveness
        if opener_issues > 2:
            coaching['rapport_assertiveness'] = "Start with empathy: 'I know this is out of the blue' shows you understand you're interrupting."
        else:
            coaching['rapport_assertiveness'] = "Good rapport building! Your empathy and confidence create trust with prospects."
        
        return coaching

    def _evaluate_user_input(self, session: Dict, user_input: str, evaluation_stage: str) -> Dict[str, Any]:
        """Evaluate user input using OpenAI (or fallback)"""
        try:
            if self.is_openai_available():
                logger.info(f"Evaluating with OpenAI: stage={evaluation_stage}")
                evaluation = self.openai_service.evaluate_user_input(
                    user_input,
                    session['conversation_history'],
                    evaluation_stage
                )
                
                # Store in session rubric scores
                session['rubric_scores'][evaluation_stage] = {
                    'score': evaluation.get('score', 0),
                    'passed': evaluation.get('passed', False),
                    'criteria_met': evaluation.get('criteria_met', [])
                }
                
                logger.info(f"OpenAI Evaluation: score={evaluation.get('score', 0)}, passed={evaluation.get('passed', False)}")
                return evaluation
            else:
                logger.warning("OpenAI not available, using basic evaluation")
                return self._basic_evaluation(user_input, evaluation_stage)
                
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return self._basic_evaluation(user_input, evaluation_stage)

    def _get_live_coaching(self, session: Dict, evaluation: Dict) -> Optional[Dict[str, str]]:
        """Provide real-time coaching feedback for Practice mode"""
        if not session['settings'].get('real_time_coaching', False):
            return None
        
        stage = evaluation.get('stage', 'unknown')
        score = evaluation.get('score', 0)
        passed = evaluation.get('passed', False)
        criteria_met = evaluation.get('criteria_met', [])
        
        coaching = {}
        
        # Stage-specific live coaching
        if stage == 'opener':
            if passed:
                coaching['feedback'] = "Great opener! You showed empathy and ended with a question."
                coaching['tip'] = "Keep this natural tone for the rest of the call."
            else:
                missing = []
                if 'shows_empathy' not in criteria_met:
                    missing.append("Try: 'I know this is out of the blue...'")
                if 'casual_tone' not in criteria_met:
                    missing.append("Use contractions: 'I'm calling' not 'I am calling'")
                if 'ends_with_question' not in criteria_met:
                    missing.append("End with: 'Can I tell you why I'm calling?'")
                
                coaching['feedback'] = f"Opener needs work (score: {score}/4)"
                coaching['tip'] = " | ".join(missing[:2])  # Max 2 tips
        
        elif stage == 'objection_handling':
            if passed:
                coaching['feedback'] = "Excellent objection handling! You stayed calm and asked a question."
                coaching['tip'] = "This builds trust and keeps the conversation going."
            else:
                tips = []
                if 'acknowledges_calmly' not in criteria_met:
                    tips.append("Start with: 'Fair enough' or 'I understand'")
                if 'forward_question' not in criteria_met:
                    tips.append("End with a question to move forward")
                
                coaching['feedback'] = f"Objection handling needs improvement (score: {score}/4)"
                coaching['tip'] = " | ".join(tips[:2])
        
        elif stage == 'mini_pitch':
            if passed:
                coaching['feedback'] = "Perfect mini-pitch! Short, outcome-focused, and natural."
                coaching['tip'] = "This is exactly how to present value quickly."
            else:
                tips = []
                if 'short_pitch' not in criteria_met:
                    tips.append("Keep it under 30 words")
                if 'outcome_focused' not in criteria_met:
                    tips.append("Focus on results: 'save time', 'increase sales'")
                
                coaching['feedback'] = f"Mini-pitch needs refinement (score: {score}/4)"
                coaching['tip'] = " | ".join(tips[:2])
        
        elif stage == 'soft_discovery':
            if passed:
                coaching['feedback'] = "Great discovery question! Open-ended and relevant."
                coaching['tip'] = "Listen carefully to their answer for follow-up opportunities."
            else:
                coaching['feedback'] = f"Discovery could be stronger (score: {score}/3)"
                coaching['tip'] = "Ask open questions: 'What's your biggest challenge with...?'"
        
        # Only return coaching if we have something useful to say
        if coaching:
            coaching['stage'] = stage
            coaching['timestamp'] = datetime.now(timezone.utc).isoformat()
            return coaching
        
        return None

    def _update_conversation_quality(self, session: Dict, evaluation: Dict):
        """Track overall conversation quality for better flow decisions"""
        score = evaluation.get('score', 0)
        max_score = 4
        
        # Calculate quality percentage for this turn
        turn_quality = (score / max_score) * 100
        
        # Update running average
        total_turns = session['turn_count']
        current_quality = session.get('conversation_quality', 0)
        
        # Weighted average (recent turns matter more)
        session['conversation_quality'] = ((current_quality * (total_turns - 1)) + turn_quality) / total_turns
        
        logger.info(f"Conversation quality: {session['conversation_quality']:.1f}% (this turn: {turn_quality:.1f}%)")

    def _update_conversation_quality(self, session: Dict, evaluation: Dict):
        """Track overall conversation quality for better flow decisions"""
        score = evaluation.get('score', 0)
        max_score = 4
        
        # Calculate quality percentage for this turn
        turn_quality = (score / max_score) * 100
        
        # Update running average
        total_turns = session['turn_count']
        current_quality = session.get('conversation_quality', 0)
        
        if total_turns == 1:
            # First turn sets the baseline
            session['conversation_quality'] = turn_quality
        else:
            # Weighted average (recent turns matter more)
            session['conversation_quality'] = ((current_quality * (total_turns - 1)) + turn_quality) / total_turns
        
        logger.info(f"Conversation quality: {session['conversation_quality']:.1f}% (this turn: {turn_quality:.1f}%)")

    def _should_hang_up_now(self, session: Dict, evaluation: Dict, user_input: str) -> bool:
        """Determine if prospect should hang up right now - IMPROVED LOGIC"""
        current_stage = session['current_stage']
        mode = session.get('mode', 'practice')
        
        # Never hang up on first interaction (phone pickup response)
        if session['turn_count'] <= 1:
            return False
        
        # Practice mode is more forgiving than Marathon/Legend
        if mode == 'practice':
            # Don't hang up if conversation quality is good
            conversation_quality = session.get('conversation_quality', 0)
            if conversation_quality >= 60:  # If conversation is going well, reduce hang-up chance
                logger.info(f"Good conversation quality ({conversation_quality:.1f}%), reducing hang-up chance")
                return False
        
        # Get hang up probability from evaluation
        hang_up_prob = evaluation.get('hang_up_probability', 0.1)
        
        # Increase probability for poor performance, but be more lenient in Practice mode
        score = evaluation.get('score', 0)
        
        if current_stage == 'opener_evaluation':
            if mode == 'practice':
                if score <= 1:
                    hang_up_prob = 0.3  # More forgiving in Practice
                elif score == 2:
                    hang_up_prob = 0.1
                else:
                    hang_up_prob = 0.02
            else:  # Marathon/Legend
                if score <= 1:
                    hang_up_prob = 0.5  # Less forgiving
                elif score == 2:
                    hang_up_prob = 0.2
                else:
                    hang_up_prob = 0.05
        
        elif current_stage in ['objection_handling', 'early_objection']:
            if not evaluation.get('passed', True):
                hang_up_prob = 0.15 if mode == 'practice' else 0.25
        
        # Practice mode: Reduce hang-up chance as conversation progresses
        if mode == 'practice' and session['turn_count'] >= 3:
            hang_up_prob *= 0.4  # Significantly reduce hang-up chance for longer conversations
        
        # Marathon/Legend: Slightly reduce hang-up chance for longer conversations
        elif mode in ['marathon', 'legend'] and session['turn_count'] >= 3:
            hang_up_prob *= 0.7
        
        # Random decision
        should_hang_up = random.random() < hang_up_prob
        
        if should_hang_up:
            logger.info(f"Hang up triggered: mode={mode}, stage={current_stage}, score={score}, prob={hang_up_prob}")
        
        return should_hang_up

    # Rest of the methods remain the same as in the original implementation...
    
    def _get_evaluation_stage(self, current_stage: str) -> str:
        """Map current stage to evaluation stage"""
        mapping = {
            'phone_pickup': 'opener',
            'opener_evaluation': 'opener',
            'early_objection': 'objection_handling',
            'objection_handling': 'objection_handling',
            'mini_pitch': 'mini_pitch',
            'soft_discovery': 'soft_discovery',
            'extended_conversation': 'soft_discovery'
        }
        return mapping.get(current_stage, 'opener')

    def _should_hang_up_now(self, session: Dict, evaluation: Dict, user_input: str) -> bool:
        """Determine if prospect should hang up right now"""
        # Never hang up on first interaction
        if session['turn_count'] <= 1:
            return False
        
        # Get hang up probability from evaluation
        score = evaluation.get('score', 0)
        hang_up_prob = evaluation.get('hang_up_probability', 0.1)
        
        # Marathon/Legend modes are less forgiving
        if session['mode'] in ['marathon', 'legend']:
            if score <= 1:
                hang_up_prob = 0.6
            elif score == 2:
                hang_up_prob = 0.3
            else:
                hang_up_prob = 0.05
        
        should_hang_up = random.random() < hang_up_prob
        
        if should_hang_up:
            logger.info(f"Hang up triggered: stage={session['current_stage']}, score={score}, prob={hang_up_prob}")
        
        return should_hang_up

    def _should_call_continue(self, session: Dict, evaluation: Dict) -> bool:
        """Determine if current call should continue (all modes)"""
        # End if hung up
        if session.get('hang_up_triggered'):
            logger.info("Call ending: hang up triggered")
            return False
        
        # For Marathon/Legend modes, calls are managed differently
        mode = session.get('mode', 'practice')
        if mode in ['marathon', 'legend']:
            # In Marathon/Legend, calls end through specific completion/failure logic
            # This method mainly checks for basic continuation conditions
            current_stage = session.get('current_stage', 'phone_pickup')
            
            # End if reached maximum turns for this call
            max_turns = session['settings'].get('max_total_turns', 15)
            if session.get('turn_count', 0) >= max_turns:
                logger.info(f"Call ending: reached turn limit ({max_turns}) in {mode} mode")
                return False
            
            # Continue the call unless explicitly ended elsewhere
            return True
        
        # Original Practice mode logic (1.1)
        if mode == 'practice':
            return self._should_call_continue_practice_mode(session, evaluation)
        else:
            return self._should_call_continue_improved(session, evaluation)

    def _should_call_continue_practice_mode(self, session: Dict, evaluation: Dict) -> bool:
        """Practice mode (1.1) call continuation logic with extended conversation"""
        
        # End if hung up
        if session.get('hang_up_triggered'):
            logger.info("Call ending: hang up triggered")
            return False
        
        # End if reached final stage
        if session['current_stage'] == 'call_ended':
            logger.info("Call ending: reached final stage")
            return False
        
        # Don't end at discovery stage immediately - allow extended conversation
        if session['current_stage'] == 'soft_discovery':
            if session['stage_turn_count'] >= 3 and session['turn_count'] >= 6:
                logger.info("Call ending: completed discovery stage with sufficient conversation")
                return False
        
        # Extended conversation can go longer in Practice mode
        if session['current_stage'] == 'extended_conversation':
            # End if conversation has gone on long enough AND quality is declining
            conversation_quality = session.get('conversation_quality', 50)
            if session['stage_turn_count'] >= 4 and session['turn_count'] >= 10:
                if conversation_quality < 40:  # Only end if quality is poor
                    logger.info("Call ending: extended conversation with poor quality")
                    return False
                elif session['turn_count'] >= 20:  # Hard limit for very long conversations
                    logger.info("Call ending: reached maximum conversation length")
                    return False
        
        # Higher turn limit for natural conversations in Practice mode
        max_total_turns = session['settings'].get('max_total_turns', 25)
        if session['turn_count'] >= max_total_turns:
            logger.info(f"Call ending: reached turn limit ({max_total_turns})")
            return False
        
        logger.info(f"Call continuing: stage={session['current_stage']}, turn={session['turn_count']}, quality={session.get('conversation_quality', 0):.1f}%")
        return True

    def _should_call_continue_improved(self, session: Dict, evaluation: Dict) -> bool:
        """IMPROVED: Determine if call should continue with better logic (Practice mode)"""
        
        # End if hung up
        if session.get('hang_up_triggered'):
            logger.info("Call ending: hang up triggered")
            return False
        
        # End if reached final stage
        if session['current_stage'] == 'call_ended':
            logger.info("Call ending: reached final stage")
            return False
        
        # IMPROVED: Don't end at discovery stage immediately
        # Only end if we've had a substantial conversation
        if session['current_stage'] == 'soft_discovery':
            if session['stage_turn_count'] >= 3 and session['turn_count'] >= 6:
                logger.info("Call ending: completed discovery stage with sufficient conversation")
                return False
        
        # IMPROVED: Extended conversation can go longer
        if session['current_stage'] == 'extended_conversation':
            # End if conversation has gone on long enough AND quality is declining
            conversation_quality = session.get('conversation_quality', 50)
            if session['stage_turn_count'] >= 4 and session['turn_count'] >= 10:
                if conversation_quality < 40:  # Only end if quality is poor
                    logger.info("Call ending: extended conversation with poor quality")
                    return False
                elif session['turn_count'] >= 20:  # Hard limit for very long conversations
                    logger.info("Call ending: reached maximum conversation length")
                    return False
        
        # IMPROVED: Higher turn limit for natural conversations
        max_total_turns = session['settings'].get('max_total_turns', 25)
        if session['turn_count'] >= max_total_turns:
            logger.info(f"Call ending: reached turn limit ({max_total_turns})")
            return False
        
        logger.info(f"Call continuing: stage={session['current_stage']}, turn={session['turn_count']}, quality={session.get('conversation_quality', 0):.1f}%")
        return True

    def _check_call_completion(self, session: Dict, evaluation: Dict) -> bool:
        """Check if current call should be completed successfully"""
        # Call completes after successful soft discovery
        if session['current_stage'] == 'soft_discovery' and evaluation.get('passed', False):
            return True
        
        # Or after sufficient turns in discovery
        if session['current_stage'] == 'soft_discovery' and session['stage_turn_count'] >= 2:
            return True
        
        return False

    # Include all other necessary methods from the original implementation...
    # (This is a condensed version focusing on Marathon-specific features)

    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End session and generate coaching"""
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
            
            # Generate coaching based on mode
            if session['mode'] in ['marathon', 'legend']:
                coaching_result = self._generate_end_of_run_coaching(session)
            else:
                coaching_result = self._generate_coaching(session)  # Original practice mode coaching
            
            # Calculate success
            if session['mode'] in ['marathon', 'legend']:
                session_success = session.get('run_success', False)
            else:
                session_success = self._calculate_session_success_improved(session)
            
            logger.info(f"Session {session_id} ended. Mode: {session['mode']}, Success: {session_success}")
            
            return {
                'success': True,
                'duration_minutes': duration_minutes,
                'session_success': session_success,
                'coaching': coaching_result.get('coaching', {}),
                'overall_score': coaching_result.get('score', 50),
                'session_data': session,
                'mode': session['mode'],
                'final_stats': {
                    'calls_passed': session.get('calls_passed', 0),
                    'calls_failed': session.get('calls_failed', 0),
                    'total_calls': session.get('current_call', 1)
                } if session['mode'] in ['marathon', 'legend'] else None
            }
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            # Clean up session
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]

    def _get_hangup_response(self, current_stage: str, evaluation: Dict) -> str:
        """Get appropriate hangup response"""
        hangup_responses = {
            'opener_evaluation': [
                "Not interested. Don't call here again.",
                "Please remove this number from your list.",
                "I'm hanging up now.",
                "Take me off your list."
            ],
            'objection_handling': [
                "I already told you I'm not interested.",
                "You're not listening. Goodbye.",
                "This is exactly why I hate cold calls. Don't call back."
            ],
            'early_objection': [
                "Not interested. Goodbye.",
                "Don't call here again.",
                "Remove this number from your list."
            ],
            'default': [
                "I have to go. Goodbye.",
                "Not interested. Thanks.",
                "Please don't call again."
            ]
        }
        
        responses = hangup_responses.get(current_stage, hangup_responses['default'])
        return random.choice(responses)

    def _handle_silence_trigger(self, session: Dict, trigger: str) -> Dict[str, Any]:
        """Handle silence triggers"""
        if trigger == '[SILENCE_IMPATIENCE]':
            impatience_phrase = random.choice(self.impatience_phrases)
            
            session['conversation_history'].append({
                'role': 'assistant',
                'content': impatience_phrase,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'trigger': 'silence_impatience',
                'call_number': session['current_call']
            })
            
            return {
                'success': True,
                'ai_response': impatience_phrase,
                'call_continues': True,
                'evaluation': {'trigger': 'impatience'}
            }
        
        elif trigger == '[SILENCE_HANGUP]':
            response = "I don't have time for this. Goodbye."
            session['hang_up_triggered'] = True
            session['call_result'] = 'fail'
            session['calls_failed'] += 1
            session['call_active'] = False
            
            session['conversation_history'].append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'trigger': 'silence_hangup',
                'call_number': session['current_call']
            })
            
            # Check if should start next call or end run
            return self._check_next_call_or_end_run(session, response)

    def _generate_ai_response(self, session: Dict, user_input: str, evaluation: Dict) -> str:
        """Generate AI prospect response"""
        try:
            current_stage = session['current_stage']
            
            # Use OpenAI if available
            if self.is_openai_available():
                logger.info("Generating AI response with OpenAI")
                response_result = self.openai_service.generate_roleplay_response(
                    user_input,
                    session['conversation_history'],
                    session['user_context'],
                    current_stage
                )
                
                if response_result.get('success'):
                    return response_result['response']
                else:
                    logger.warning("OpenAI response failed, using fallback")
            
            # Fallback response based on stage and evaluation
            return self._get_smart_fallback_response(current_stage, evaluation, user_input, session)
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._get_smart_fallback_response(current_stage, evaluation, user_input, session)

    def _get_smart_fallback_response(self, current_stage: str, evaluation: Dict, user_input: str, session: Dict = None) -> str:
        """Get intelligent fallback response based on evaluation"""
        score = evaluation.get('score', 0)
        passed = evaluation.get('passed', False)
        
        # Response based on stage and performance
        if current_stage == 'opener_evaluation':
            if passed:
                responses = [
                    "Alright, what's this about?",
                    "I'm listening. Go ahead.", 
                    "You have my attention. What is it?"
                ]
            else:
                responses = [
                    "What's this about?",
                    "I'm not interested.",
                    "Now is not a good time.",
                    "Is this a sales call?"
                ]
                
        elif current_stage == 'early_objection':
            # Always give an objection after opener - get unused objection
            if session:
                return self._get_unused_objection(session)
            else:
                # Fallback if no session provided
                responses = ["I'm not interested.", "We don't take cold calls.", "Now is not a good time."]
            
        elif current_stage == 'objection_handling':
            if passed:
                responses = [
                    "Alright, I'm listening. What do you do?",
                    "Okay, you have 30 seconds.",
                    "Go ahead, but make it quick."
                ]
            else:
                responses = [
                    "I already told you I'm not interested.",
                    "You're not listening.",
                    "This is exactly why I hate cold calls."
                ]
                
        elif current_stage == 'mini_pitch':
            if passed:
                responses = [
                    "That sounds interesting. Tell me more.",
                    "How exactly does that work?",
                    "What would that look like for us?"
                ]
            else:
                responses = [
                    "I don't understand what you're saying.",
                    "That's too vague.",
                    "How is that different from what we already do?"
                ]
                
        elif current_stage in ['soft_discovery']:
            responses = [
                "That's a good question. Tell me more about your approach.",
                "Interesting. How does that compare to other solutions?",
                "I see. What kind of timeline are we talking about?",
                "Hmm, that could be relevant. What's the next step?",
                "Alright, I'm intrigued. Send me some information.",
                "That makes sense. Let me think about it.",
                "I'd need to discuss this with my team first."
            ]
            
        else:
            responses = ["I see. Continue.", "Okay.", "Go on."]
        
        return random.choice(responses)

    def _update_session_state(self, session: Dict, evaluation: Dict) -> bool:
        """Update session state based on evaluation - Returns True if stage changed"""
        current_stage = session['current_stage']
        mode = session.get('mode', 'practice')
        
        # Move to next stage based on performance and stage logic
        should_progress = False
        
        if current_stage == 'phone_pickup':
            # Always move to opener evaluation after first response
            should_progress = True
            
        elif current_stage == 'opener_evaluation':
            # Move to objection if opener was decent OR after attempts
            max_attempts = 3 if mode in ['marathon', 'legend'] else 2
            if evaluation.get('passed', False) or session['stage_turn_count'] >= max_attempts:
                should_progress = True
                
        elif current_stage == 'early_objection':
            # Always move to objection handling after giving objection
            should_progress = True
            
        elif current_stage == 'objection_handling':
            # Move to pitch if objection handled well OR after attempts
            max_attempts = 3 if mode in ['marathon', 'legend'] else 3
            if evaluation.get('passed', False) or session['stage_turn_count'] >= max_attempts:
                should_progress = True
                
        elif current_stage == 'mini_pitch':
            # Move to discovery after pitch OR after attempts
            max_attempts = 2 if mode in ['marathon', 'legend'] else 2
            if evaluation.get('score', 0) >= 2 or session['stage_turn_count'] >= max_attempts:
                should_progress = True
                
        elif current_stage == 'soft_discovery':
            # For Marathon/Legend, discovery completion is handled separately
            if mode not in ['marathon', 'legend']:
                # Practice mode: Move to extended conversation for natural flow
                if session['stage_turn_count'] >= 2:
                    should_progress = True
            else:
                # Marathon/Legend: Check for call completion after discovery
                if evaluation.get('passed', False) and session['stage_turn_count'] >= 1:
                    # Discovery passed, this call is complete
                    should_progress = False  # Handle completion separately
        
        elif current_stage == 'extended_conversation':
            # Practice mode only - can stay here for multiple turns
            pass
        
        if should_progress:
            next_stage = self.stage_flow[mode].get(current_stage)
            if next_stage and next_stage != current_stage:
                # Mark current stage as completed
                if current_stage not in session.get('stages_completed', []):
                    session.setdefault('stages_completed', []).append(current_stage)
                
                session['current_stage'] = next_stage
                session['stage_progression'].append(next_stage)
                session['stage_turn_count'] = 0  # Reset stage turn counter
                logger.info(f"Stage progression: {current_stage} → {next_stage}")
                return True
        
        return False

    def _generate_coaching(self, session: Dict) -> Dict[str, Any]:
        """Generate coaching feedback for Practice mode"""
        try:
            if self.is_openai_available():
                logger.info("Generating coaching with OpenAI")
                return self.openai_service.generate_coaching_feedback(
                    session['conversation_history'],
                    session.get('rubric_scores', {}),
                    session['user_context']
                )
            else:
                logger.warning("OpenAI not available, using enhanced basic coaching")
                return self._enhanced_basic_coaching(session)
                
        except Exception as e:
            logger.error(f"Coaching generation error: {e}")
            return self._enhanced_basic_coaching(session)

    def _enhanced_basic_coaching(self, session: Dict) -> Dict[str, Any]:
        """Enhanced basic coaching based on actual performance"""
        rubric_scores = session.get('rubric_scores', {})
        conversation_history = session.get('conversation_history', [])
        conversation_quality = session.get('conversation_quality', 50)
        stages_completed = len(session.get('stages_completed', []))
        
        # Calculate score based on multiple factors
        base_score = int(conversation_quality)
        
        # Bonus for completing stages
        stage_bonus = stages_completed * 10
        
        # Bonus for conversation length
        turns = session.get('turn_count', 0)
        length_bonus = min(20, turns * 2)  # Up to 20 points for length
        
        total_score = min(100, max(30, base_score + stage_bonus + length_bonus))
        
        # Generate contextual feedback
        coaching = self._generate_contextual_feedback_improved(rubric_scores, conversation_history, stages_completed)
        
        logger.info(f"Enhanced coaching: {total_score}% (base: {base_score}, stages: {stage_bonus}, length: {length_bonus})")
        
        return {
            'success': True,
            'coaching': coaching,
            'score': total_score,
            'source': 'enhanced_basic'
        }

    def _generate_contextual_feedback_improved(self, rubric_scores: Dict, conversation_history: List[Dict], stages_completed: int) -> Dict[str, str]:
        """Generate improved contextual feedback"""
        user_inputs = [msg['content'] for msg in conversation_history if msg['role'] == 'user']
        full_text = ' '.join(user_inputs).lower() if user_inputs else ''
        
        coaching = {}
        
        # Sales coaching based on stages reached
        if stages_completed >= 4:
            coaching['sales_coaching'] = "Excellent progress! You successfully navigated through the opener, objections, and pitch. Your conversation flow was natural and engaging."
        elif stages_completed >= 3:
            coaching['sales_coaching'] = "Good job! You made it through the main conversation stages. Focus on asking more discovery questions to keep the conversation going longer."
        elif stages_completed >= 2:
            coaching['sales_coaching'] = "You handled the opener and objections well. Work on delivering a more compelling mini-pitch to maintain prospect interest."
        else:
            coaching['sales_coaching'] = "Practice your opener with more empathy and confidence. Use 'I know this is out of the blue' to acknowledge the interruption."
        
        # Grammar coaching
        if any(contraction in full_text for contraction in ["i'm", "don't", "can't", "we're"]):
            coaching['grammar_coaching'] = "Great use of contractions! This makes you sound natural and conversational in your speech."
        else:
            coaching['grammar_coaching'] = "Try using more contractions like 'I'm calling' instead of 'I am calling' to sound more natural and less formal."
        
        # Vocabulary coaching
        if any(good_word in full_text for good_word in ['help', 'solve', 'improve', 'save', 'increase']):
            coaching['vocabulary_coaching'] = "Excellent use of outcome-focused language! Continue using words that describe benefits and results."
        else:
            coaching['vocabulary_coaching'] = "Use more outcome words like 'help', 'save time', or 'improve efficiency' instead of focusing on technical features."
        
        # Pronunciation coaching
        coaching['pronunciation_coaching'] = "Focus on speaking clearly and at a moderate pace. Practice key phrases like 'Can I tell you why I'm calling?' for smooth delivery."
        
        # Rapport & assertiveness
        if any(empathy in full_text for empathy in ['know this is', 'out of the blue', 'interrupting', 'busy']):
            coaching['rapport_assertiveness'] = "Excellent empathy! You acknowledged the interruption well, which builds trust and rapport with prospects."
        else:
            coaching['rapport_assertiveness'] = "Start with empathy by saying 'I know this is out of the blue' to acknowledge you're interrupting their day."
        
        return coaching

    def _calculate_session_success_improved(self, session: Dict) -> bool:
        """IMPROVED: Calculate session success based on conversation quality and stages completed"""
        
        # Check conversation quality
        conversation_quality = session.get('conversation_quality', 0)
        stages_completed = session.get('stages_completed', [])
        total_turns = session.get('turn_count', 0)
        
        # Success criteria (more lenient):
        # 1. Reached at least mini_pitch stage (covered main topics)
        # 2. Had at least 4 conversation turns
        # 3. Conversation quality above 40% OR completed most stages
        
        reached_pitch = 'mini_pitch' in stages_completed or session.get('current_stage') in ['mini_pitch', 'soft_discovery', 'extended_conversation']
        sufficient_length = total_turns >= 4
        decent_quality = conversation_quality >= 40
        completed_most_stages = len(stages_completed) >= 3
        
        success = reached_pitch and sufficient_length and (decent_quality or completed_most_stages)
        
        logger.info(f"Session success calculation: reached_pitch={reached_pitch}, sufficient_length={sufficient_length}, decent_quality={decent_quality}, completed_stages={len(stages_completed)}, result={success}")
        
        return success

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session status"""
        session = self.active_sessions.get(session_id)
        if session:
            status = {
                'session_active': session.get('session_active', False),
                'mode': session.get('mode', 'practice'),
                'current_stage': session.get('current_stage', 'unknown'),
                'rubric_scores': session.get('rubric_scores', {}),
                'conversation_length': len(session.get('conversation_history', [])),
                'conversation_quality': session.get('conversation_quality', 0),
                'stages_completed': session.get('stages_completed', []),
                'openai_available': self.is_openai_available(),
                'turn_count': session.get('turn_count', 0)
            }
            
            # Add Marathon/Legend specific status
            if session.get('mode') in ['marathon', 'legend']:
                status['marathon_status'] = {
                    'current_call': session.get('current_call', 1),
                    'max_calls': session.get('max_calls', 1),
                    'calls_passed': session.get('calls_passed', 0),
                    'calls_failed': session.get('calls_failed', 0),
                    'run_complete': session.get('run_complete', False)
                }
            
            return status
        return None

    def cleanup_expired_sessions(self):
        """Clean up old sessions"""
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
            'openai_available': self.is_openai_available(),
            'engine_status': 'running',
            'max_total_turns': self.mode_settings['practice']['max_total_turns'],
            'marathon_support': True,
            'legend_support': True,
            'openai_status': self.openai_service.get_status() if self.openai_service else None
        }
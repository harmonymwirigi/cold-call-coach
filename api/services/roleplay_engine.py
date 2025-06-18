# ===== COMPLETE INTEGRATED API/SERVICES/ROLEPLAY_ENGINE.PY =====
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
    PITCH_PROMPTS, PASS_CRITERIA, SUCCESS_MESSAGES, WARMUP_QUESTIONS,
    # Add the new Roleplay 1 constants
    ROLEPLAY_1_RUBRICS, ROLEPLAY_1_HANGUP_RULES, ROLEPLAY_1_SILENCE_RULES
)

logger = logging.getLogger(__name__)


class RoleplayOneEvaluator:
    """Dedicated evaluator for Roleplay 1 using detailed rubrics"""
    
    def __init__(self):
        self.rubrics = ROLEPLAY_1_RUBRICS
        self.hangup_rules = ROLEPLAY_1_HANGUP_RULES
        self.silence_rules = ROLEPLAY_1_SILENCE_RULES
    
    def evaluate_user_input(self, user_input: str, stage: str, session_context: Dict) -> Dict[str, Any]:
        """Main evaluation method - routes to stage-specific evaluators"""
        
        if stage in ['phone_pickup', 'opener_evaluation']:
            return self.evaluate_opener(user_input, session_context)
        elif stage == 'early_objection':
            return self.evaluate_objection_handling(user_input, session_context) 
        elif stage == 'mini_pitch':
            return self.evaluate_mini_pitch(user_input, session_context)
        elif stage == 'soft_discovery':
            return self.evaluate_soft_discovery(user_input, session_context)
        else:
            # Fallback for unknown stages
            return {
                'stage': stage,
                'passed': True,
                'score': 5,
                'total_possible': 8,
                'criteria_met': [],
                'criteria_failed': [],
                'should_continue': True,
                'next_stage': 'in_progress'
            }
    
    def evaluate_opener(self, user_input: str, session_context: Dict) -> Dict[str, Any]:
        """Evaluate opener using 4-criteria rubric"""
        
        rubric = self.rubrics['opener']
        criteria_results = {}
        score = 0
        
        # Clean input for analysis
        clean_input = user_input.lower().strip()
        word_count = len(clean_input.split())
        
        # Criterion 1: Clear cold call opener
        has_clear_opener = self._check_clear_opener(clean_input, rubric['criteria']['clear_opener'])
        criteria_results['clear_opener'] = has_clear_opener
        if has_clear_opener:
            score += 1
        
        # Criterion 2: Casual, confident tone (contractions)
        has_casual_tone = self._check_casual_tone(clean_input, rubric['criteria']['casual_tone'])
        criteria_results['casual_tone'] = has_casual_tone
        if has_casual_tone:
            score += 1
        
        # Criterion 3: Shows empathy
        shows_empathy = self._check_empathy(clean_input, rubric['criteria']['shows_empathy'])
        criteria_results['shows_empathy'] = shows_empathy
        if shows_empathy:
            score += 1
        
        # Criterion 4: Ends with question
        ends_with_question = self._check_question_ending(user_input, clean_input, rubric['criteria']['ends_with_question'])
        criteria_results['ends_with_question'] = ends_with_question
        if ends_with_question:
            score += 1
        
        # Check auto-fail conditions
        auto_fail_reason = self._check_opener_auto_fail(clean_input, word_count)
        
        # Determine pass/fail
        passed = score >= rubric['pass_requirement'] and not auto_fail_reason
        
        # Calculate hang-up probability
        hangup_chance = self._calculate_opener_hangup_chance(score)
        should_hangup = random.random() < hangup_chance
        
        # Determine next stage
        if should_hangup or auto_fail_reason:
            next_stage = 'call_ended'
            should_continue = False
        elif passed:
            next_stage = 'early_objection'
            should_continue = True
        else:
            next_stage = 'call_ended'  # Failed opener = hang up
            should_continue = False
        
        return {
            'stage': 'opener',
            'passed': passed,
            'score': score,
            'total_possible': rubric['total_criteria'],
            'criteria_results': criteria_results,
            'criteria_met': [k for k, v in criteria_results.items() if v],
            'criteria_failed': [k for k, v in criteria_results.items() if not v],
            'auto_fail_reason': auto_fail_reason,
            'should_continue': should_continue,
            'should_hangup': should_hangup,
            'hangup_chance': hangup_chance,
            'next_stage': next_stage,
            'evaluation_details': {
                'word_count': word_count,
                'has_contractions': has_casual_tone,
                'empathy_detected': shows_empathy,
                'question_detected': ends_with_question
            }
        }
    
    def evaluate_objection_handling(self, user_input: str, session_context: Dict) -> Dict[str, Any]:
        """Evaluate objection handling using 4-criteria rubric"""
        
        rubric = self.rubrics['objection_handling']
        criteria_results = {}
        score = 0
        
        clean_input = user_input.lower().strip()
        
        # Criterion 1: Acknowledges calmly
        acknowledges_calmly = self._check_calm_acknowledgment(clean_input, rubric['criteria']['acknowledges_calmly'])
        criteria_results['acknowledges_calmly'] = acknowledges_calmly
        if acknowledges_calmly:
            score += 1
        
        # Criterion 2: Doesn't argue or pitch immediately
        no_arguing = self._check_no_arguing(clean_input, rubric['criteria']['no_arguing'])
        criteria_results['no_arguing'] = no_arguing
        if no_arguing:
            score += 1
        
        # Criterion 3: Reframes or buys time in 1 sentence
        reframes_appropriately = self._check_reframing(clean_input, rubric['criteria']['reframes_buys_time'])
        criteria_results['reframes_buys_time'] = reframes_appropriately
        if reframes_appropriately:
            score += 1
        
        # Criterion 4: Ends with forward-moving question
        forward_question = self._check_forward_question(user_input, clean_input, rubric['criteria']['forward_question'])
        criteria_results['forward_question'] = forward_question
        if forward_question:
            score += 1
        
        # Check auto-fail conditions
        auto_fail_reason = self._check_objection_auto_fail(clean_input)
        
        # Determine pass/fail
        passed = score >= rubric['pass_requirement'] and not auto_fail_reason
        
        # Small chance of hang-up during objection handling
        hangup_chance = self.hangup_rules['objection_stage']
        should_hangup = random.random() < hangup_chance
        
        # Determine next stage
        if should_hangup or auto_fail_reason:
            next_stage = 'call_ended'
            should_continue = False
        elif passed:
            next_stage = 'mini_pitch'
            should_continue = True
        else:
            next_stage = 'call_ended'  # Failed objection handling = hang up
            should_continue = False
        
        return {
            'stage': 'objection_handling',
            'passed': passed,
            'score': score,
            'total_possible': rubric['total_criteria'],
            'criteria_results': criteria_results,
            'criteria_met': [k for k, v in criteria_results.items() if v],
            'criteria_failed': [k for k, v in criteria_results.items() if not v],
            'auto_fail_reason': auto_fail_reason,
            'should_continue': should_continue,
            'should_hangup': should_hangup,
            'hangup_chance': hangup_chance,
            'next_stage': next_stage
        }
    
    def evaluate_mini_pitch(self, user_input: str, session_context: Dict) -> Dict[str, Any]:
        """Evaluate mini pitch using 4-criteria rubric"""
        
        rubric = self.rubrics['mini_pitch']
        criteria_results = {}
        score = 0
        
        clean_input = user_input.lower().strip()
        word_count = len(clean_input.split())
        sentence_count = len([s for s in clean_input.split('.') if s.strip()])
        
        # Criterion 1: Short (1-2 sentences, under 30 words)
        is_short = self._check_pitch_length(word_count, sentence_count, rubric['criteria']['short_concise'])
        criteria_results['short_concise'] = is_short
        if is_short:
            score += 1
        
        # Criterion 2: Outcome-focused (not feature-focused)
        is_outcome_focused = self._check_outcome_focus(clean_input, rubric['criteria']['outcome_focused'])
        criteria_results['outcome_focused'] = is_outcome_focused
        if is_outcome_focused:
            score += 1
        
        # Criterion 3: Simple language (no jargon)
        uses_simple_language = self._check_simple_language(clean_input, rubric['criteria']['simple_language'])
        criteria_results['simple_language'] = uses_simple_language
        if uses_simple_language:
            score += 1
        
        # Criterion 4: Natural delivery (not robotic)
        sounds_natural = self._check_natural_delivery(clean_input, rubric['criteria']['natural_delivery'])
        criteria_results['natural_delivery'] = sounds_natural
        if sounds_natural:
            score += 1
        
        # Check auto-fail conditions
        auto_fail_reason = self._check_pitch_auto_fail(clean_input, word_count)
        
        # Determine pass/fail
        passed = score >= rubric['pass_requirement'] and not auto_fail_reason
        
        # Very small chance of hang-up during pitch
        hangup_chance = self.hangup_rules['pitch_stage']
        should_hangup = random.random() < hangup_chance
        
        # Determine next stage
        if should_hangup or auto_fail_reason:
            next_stage = 'call_ended'
            should_continue = False
        elif passed:
            next_stage = 'soft_discovery'
            should_continue = True
        else:
            next_stage = 'call_ended'  # Failed pitch = hang up
            should_continue = False
        
        return {
            'stage': 'mini_pitch',
            'passed': passed,
            'score': score,
            'total_possible': rubric['total_criteria'],
            'criteria_results': criteria_results,
            'criteria_met': [k for k, v in criteria_results.items() if v],
            'criteria_failed': [k for k, v in criteria_results.items() if not v],
            'auto_fail_reason': auto_fail_reason,
            'should_continue': should_continue,
            'should_hangup': should_hangup,
            'hangup_chance': hangup_chance,
            'next_stage': next_stage,
            'evaluation_details': {
                'word_count': word_count,
                'sentence_count': sentence_count,
                'outcome_words_found': self._count_outcome_words(clean_input),
                'jargon_detected': self._detect_jargon(clean_input)
            }
        }
    
    def evaluate_soft_discovery(self, user_input: str, session_context: Dict) -> Dict[str, Any]:
        """Evaluate soft discovery question using 3-criteria rubric"""
        
        rubric = self.rubrics['soft_discovery'] 
        criteria_results = {}
        score = 0
        
        clean_input = user_input.lower().strip()
        
        # Criterion 1: Question tied to the pitch
        tied_to_pitch = self._check_tied_question(clean_input, rubric['criteria']['tied_question'])
        criteria_results['tied_question'] = tied_to_pitch
        if tied_to_pitch:
            score += 1
        
        # Criterion 2: Open/curious question
        is_open_curious = self._check_open_question(clean_input, rubric['criteria']['open_curious'])
        criteria_results['open_curious'] = is_open_curious
        if is_open_curious:
            score += 1
        
        # Criterion 3: Soft, non-pushy tone
        has_soft_tone = self._check_soft_tone(clean_input, rubric['criteria']['soft_tone'])
        criteria_results['soft_tone'] = has_soft_tone
        if has_soft_tone:
            score += 1
        
        # Check auto-fail conditions
        auto_fail_reason = self._check_discovery_auto_fail(clean_input)
        
        # Determine pass/fail
        passed = score >= rubric['pass_requirement'] and not auto_fail_reason
        
        # Determine final outcome
        if passed:
            next_stage = 'call_success'
            should_continue = False  # Call ends successfully
        else:
            next_stage = 'call_ended'
            should_continue = False  # Call ends in failure
        
        return {
            'stage': 'soft_discovery',
            'passed': passed,
            'score': score,
            'total_possible': rubric['total_criteria'], 
            'criteria_results': criteria_results,
            'criteria_met': [k for k, v in criteria_results.items() if v],
            'criteria_failed': [k for k, v in criteria_results.items() if not v],
            'auto_fail_reason': auto_fail_reason,
            'should_continue': should_continue,
            'should_hangup': False,
            'next_stage': next_stage,
            'call_result': 'success' if passed else 'failure'
        }
    
    # ===== HELPER METHODS FOR CRITERION CHECKING =====
    
    def _check_clear_opener(self, clean_input: str, criteria: Dict) -> bool:
        """Check if input has clear cold call opener"""
        # Must have some opening purpose/reason, not just greeting
        has_purpose = any(keyword in clean_input for keyword in criteria['keywords'])
        
        # Negative: just greeting alone
        only_greeting = any(clean_input.startswith(greeting) for greeting in criteria['negative_keywords']) and len(clean_input.split()) <= 3
        
        return has_purpose and not only_greeting
    
    def _check_casual_tone(self, clean_input: str, criteria: Dict) -> bool:
        """Check for casual tone through contractions"""
        # Positive: has contractions
        has_contractions = any(contraction in clean_input for contraction in criteria['contractions'])
        
        # Negative: overly formal
        too_formal = any(formal in clean_input for formal in criteria['formal_words'])
        
        return has_contractions and not too_formal
    
    def _check_empathy(self, clean_input: str, criteria: Dict) -> bool:
        """Check for empathy phrases"""
        return any(phrase in clean_input for phrase in criteria['empathy_phrases'])
    
    def _check_question_ending(self, original_input: str, clean_input: str, criteria: Dict) -> bool:
        """Check if ends with appropriate question"""
        ends_with_question_mark = original_input.strip().endswith('?')
        
        has_question_pattern = any(pattern in clean_input for pattern in criteria['question_patterns'])
        
        return ends_with_question_mark or has_question_pattern
    
    def _check_calm_acknowledgment(self, clean_input: str, criteria: Dict) -> bool:
        """Check for calm acknowledgment phrases"""
        return any(phrase in clean_input for phrase in criteria['acknowledge_phrases'])
    
    def _check_no_arguing(self, clean_input: str, criteria: Dict) -> bool:
        """Check that user doesn't argue or get defensive"""
        has_arguing = any(phrase in clean_input for phrase in criteria['negative_phrases'])
        return not has_arguing
    
    def _check_reframing(self, clean_input: str, criteria: Dict) -> bool:
        """Check for appropriate reframing"""
        return any(phrase in clean_input for phrase in criteria['reframe_phrases'])
    
    def _check_forward_question(self, original_input: str, clean_input: str, criteria: Dict) -> bool:
        """Check for forward-moving question"""
        ends_with_question = original_input.strip().endswith('?')
        has_question_words = any(indicator in clean_input for indicator in criteria['question_indicators'])
        
        return ends_with_question or has_question_words
    
    def _check_pitch_length(self, word_count: int, sentence_count: int, criteria: Dict) -> bool:
        """Check if pitch is appropriately short"""
        return word_count <= criteria['max_words'] and sentence_count <= criteria['max_sentences']
    
    def _check_outcome_focus(self, clean_input: str, criteria: Dict) -> bool:
        """Check if pitch focuses on outcomes vs features"""
        outcome_words = sum(1 for word in criteria['outcome_words'] if word in clean_input)
        feature_words = sum(1 for word in criteria['feature_words'] if word in clean_input)
        
        # Must have outcome words and not be dominated by feature words
        return outcome_words > 0 and outcome_words >= feature_words
    
    def _check_simple_language(self, clean_input: str, criteria: Dict) -> bool:
        """Check for simple language without jargon"""
        jargon_count = sum(1 for word in criteria['jargon_words'] if word in clean_input)
        return jargon_count == 0
    
    def _check_natural_delivery(self, clean_input: str, criteria: Dict) -> bool:
        """Check for natural vs robotic delivery"""
        natural_score = sum(1 for phrase in criteria['natural_indicators'] if phrase in clean_input)
        robotic_score = sum(1 for phrase in criteria['robotic_indicators'] if phrase in clean_input)
        
        return natural_score > robotic_score
    
    def _check_tied_question(self, clean_input: str, criteria: Dict) -> bool:
        """Check if question is tied to the pitch"""
        return any(word in clean_input for word in criteria['connection_words'])
    
    def _check_open_question(self, clean_input: str, criteria: Dict) -> bool:
        """Check for open-ended question"""
        open_words = sum(1 for pattern in criteria['open_patterns'] if pattern in clean_input)
        closed_words = sum(1 for pattern in criteria['closed_patterns'] if pattern in clean_input)
        
        return open_words > closed_words
    
    def _check_soft_tone(self, clean_input: str, criteria: Dict) -> bool:
        """Check for soft, non-pushy tone"""
        soft_indicators = sum(1 for phrase in criteria['soft_indicators'] if phrase in clean_input)
        pushy_indicators = sum(1 for phrase in criteria['pushy_indicators'] if phrase in clean_input)
        
        return soft_indicators > pushy_indicators
    
    # ===== AUTO-FAIL CONDITION CHECKERS =====
    
    def _check_opener_auto_fail(self, clean_input: str, word_count: int) -> Optional[str]:
        """Check opener auto-fail conditions"""
        if word_count > 50:
            return "opener_too_long"
        
        rude_words = ["stupid", "waste", "idiot", "annoying"]
        if any(word in clean_input for word in rude_words):
            return "rude_opener"
        
        if len(clean_input.strip()) < 5:
            return "opener_too_short"
        
        return None
    
    def _check_objection_auto_fail(self, clean_input: str) -> Optional[str]:
        """Check objection handling auto-fail conditions"""
        defensive_phrases = ["you're wrong", "that's not true", "everyone needs", "you should"]
        if any(phrase in clean_input for phrase in defensive_phrases):
            return "too_defensive"
        
        if "our solution" in clean_input or "we can help" in clean_input:
            return "pitched_too_early"
        
        return None
    
    def _check_pitch_auto_fail(self, clean_input: str, word_count: int) -> Optional[str]:
        """Check pitch auto-fail conditions"""
        if word_count > 40:
            return "pitch_too_long"
        
        if word_count < 5:
            return "pitch_too_short"
        
        return None
    
    def _check_discovery_auto_fail(self, clean_input: str) -> Optional[str]:
        """Check discovery auto-fail conditions"""
        if "?" not in clean_input:
            return "no_question_asked"
        
        pushy_phrases = ["you need", "everyone", "all companies"]
        if any(phrase in clean_input for phrase in pushy_phrases):
            return "too_pushy"
        
        return None
    
    # ===== UTILITY METHODS =====
    
    def _calculate_opener_hangup_chance(self, score: int) -> float:
        """Calculate hang-up probability based on opener score"""
        rules = self.hangup_rules['opener_stage']
        
        if score <= 1:
            return rules['score_0_1']
        elif score == 2:
            return rules['score_2']
        else:  # score 3-4
            return rules['score_3_4']
    
    def _count_outcome_words(self, clean_input: str) -> int:
        """Count outcome words in input"""
        outcome_words = ["save", "increase", "reduce", "improve", "help", "solve", "fix", "eliminate", "boost", "grow"]
        return sum(1 for word in outcome_words if word in clean_input)
    
    def _detect_jargon(self, clean_input: str) -> List[str]:
        """Detect jargon words in input"""
        jargon_words = ["leverage", "synergies", "paradigm", "scalable", "robust", "enterprise-grade", "cutting-edge"]
        return [word for word in jargon_words if word in clean_input]


class RoleplayEngine:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.supabase_service = SupabaseService()
        
        # Session state tracking - CRITICAL: Keep sessions in memory
        self.active_sessions = {}
        
        # Add Roleplay 1 evaluator
        self.roleplay_1_evaluator = RoleplayOneEvaluator()
        
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
        """Process user input with enhanced AI conversation"""
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
            
            # ENHANCED: Use detailed evaluation for Roleplay 1, simple evaluation for others
            if session['roleplay_id'] == 1:
                # Use detailed Roleplay 1 evaluation
                evaluation = self.roleplay_1_evaluator.evaluate_user_input(
                    user_input, 
                    session['current_stage'], 
                    session
                )
                logger.info(f"Roleplay 1 detailed evaluation: {evaluation}")
            else:
                # Use existing simple evaluation for other roleplays
                evaluation = self._evaluate_user_input_simple(user_input, session['current_stage'])
            
            # Check for hang-up based on evaluation
            if evaluation.get('should_hangup') or not evaluation.get('should_continue', True):
                return self._handle_hang_up(session, evaluation.get('auto_fail_reason', 'Poor response quality'))
            
            # Generate AI response using OpenAI service
            ai_response_data = self._generate_ai_response_async(session, user_input, evaluation)
            
            if not ai_response_data.get('success'):
                return {
                    'success': False,
                    'error': ai_response_data.get('error', 'Failed to generate AI response'),
                    'call_continues': False
                }
            
            ai_response = ai_response_data['response']
            
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
                'performance_hint': self._get_performance_hint(evaluation)
            }
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            return {
                'success': False,
                'error': str(e),
                'call_continues': False
            }
    
    def _generate_ai_response_async(self, session: Dict, user_input: str, evaluation: Dict = None) -> Dict[str, Any]:
        """Generate AI response with async OpenAI call"""
        try:
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
        """Generate fallback response when OpenAI is unavailable"""
        try:
            current_stage = session['current_stage']
            roleplay_id = session['roleplay_id']
            
            logger.info(f"Generating fallback response for stage: {current_stage}")
            
            # For Roleplay 1, use evaluation data if available
            if roleplay_id == 1 and evaluation:
                # If evaluation says hang up, return hang up response
                if evaluation.get('should_hangup'):
                    responses = ["Not interested.", "I'm hanging up.", "Don't call here again."]
                    return {
                        'success': True,
                        'response': random.choice(responses),
                        'evaluation': evaluation
                    }
                
                # Otherwise, give appropriate response based on stage and pass/fail
                if current_stage in ['phone_pickup', 'opener_evaluation']:
                    if evaluation.get('passed'):
                        # Good opener gets mild objection
                        responses = [
                            "I'm listening.", 
                            "Go ahead, what is it?", 
                            "You have my attention.",
                            "What can I do for you?",
                            "I've got a few minutes."
                        ]
                    else:
                        # Poor opener gets basic objection
                        responses = [
                            "Who is this?", 
                            "What's this about?", 
                            "I don't know you.",
                            "What company are you with?",
                            "How did you get this number?"
                        ]
                elif current_stage == 'early_objection':
                    if evaluation.get('passed'):
                        responses = ["Alright, I'm listening.", "Go ahead, what is it?", "You have 30 seconds."]
                    else:
                        responses = ["I already told you I'm not interested.", "Are you not listening to me?"]
                elif current_stage == 'mini_pitch':
                    if evaluation.get('passed'):
                        responses = ["That's interesting. Tell me more.", "How exactly do you do that?", "What does that look like?"]
                    else:
                        responses = ["I don't understand what you're saying.", "That sounds like everything else.", "Too complicated."]
                elif current_stage == 'soft_discovery':
                    if evaluation.get('passed'):
                        responses = ["That's a good question. We do struggle with that.", "Interesting conversation. Send me some information. Goodbye."]
                    else:
                        responses = ["That's not relevant to us.", "This conversation isn't going anywhere."]
                else:
                    responses = ["I see.", "Tell me more.", "Go on."]
            else:
                # Original fallback logic for other roleplays
                if current_stage in ['phone_pickup', 'opener_evaluation']:
                    user_messages_count = len([m for m in session['conversation_history'] if m.get('role') == 'user'])
                    
                    if user_messages_count == 1:
                        # First user message - evaluate opener quality
                        opener_quality = self._evaluate_opener_simple(user_input)
                        logger.info(f"Opener quality score: {opener_quality}/8 for input: '{user_input}'")
                        
                        # FIXED: More realistic hang-up logic
                        if opener_quality <= 1:
                            # Only hang up for really terrible openers (empty, rude, etc.)
                            hang_up_chance = 0.8  # 80% chance
                        elif opener_quality == 2:
                            # Simple greetings get objections, not hang-ups
                            hang_up_chance = 0.1  # 10% chance (rare)
                        else:
                            hang_up_chance = 0.0  # No hang-up for decent openers
                        
                        # Random hang-up decision
                        if random.random() < hang_up_chance:
                            responses = ["Not interested.", "I'm hanging up.", "Don't call here again."]
                            return {
                                'success': True,
                                'response': random.choice(responses),
                                'evaluation': {'should_hang_up': True, 'quality_score': opener_quality}
                            }
                        else:
                            # Give an appropriate objection based on opener quality
                            if opener_quality <= 2:
                                # Simple greeting gets basic objection
                                responses = [
                                    "Who is this?", 
                                    "What's this about?", 
                                    "I don't know you.",
                                    "What company are you with?",
                                    "How did you get this number?"
                                ]
                            elif opener_quality <= 4:
                                # Decent opener gets standard objections
                                responses = EARLY_OBJECTIONS[:8]  # Use first 8 objections
                            else:
                                # Good opener gets engagement
                                responses = [
                                    "I'm listening.", 
                                    "Go ahead, what is it?", 
                                    "You have my attention.",
                                    "What can I do for you?",
                                    "I've got a few minutes."
                                ]
                    else:
                        # Not first message, standard phone pickup responses
                        responses = ["Hello?", "Who is this?", "What's this about?"]
                        
                elif current_stage == 'early_objection':
                    responses = EARLY_OBJECTIONS
                    
                elif current_stage in ['mini_pitch', 'ai_pitch_prompt']:
                    if roleplay_id == 2:
                        responses = PITCH_PROMPTS
                    else:
                        responses = ["Go ahead, what is it?", "I'm listening.", "This better be good."]
                        
                elif current_stage == 'post_pitch_objections':
                    responses = POST_PITCH_OBJECTIONS
                    
                elif current_stage == 'warmup_question':
                    responses = WARMUP_QUESTIONS
                    
                else:
                    responses = ["I see.", "Tell me more.", "Go on.", "What's this about?"]
            
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
        """Simple opener evaluation without OpenAI - More generous scoring"""
        score = 2  # Start with base score of 2 (instead of 1)
        user_input_lower = user_input.lower()
        
        # Basic greeting criteria
        if any(greeting in user_input_lower for greeting in ['hi', 'hello', 'good morning', 'good afternoon', 'hey']):
            score += 1
        
        # Professional greeting
        if any(formal in user_input_lower for formal in ['good morning', 'good afternoon', 'good evening']):
            score += 1  # Bonus for formal greetings
        
        # Empathy/acknowledgment phrases
        if any(empathy in user_input_lower for empathy in ['know this is', "don't know me", 'out of the blue', 'interrupting', 'unexpected']):
            score += 2
        
        # Permission seeking (questions)
        if user_input.strip().endswith('?'):
            score += 1
        
        # Name introduction
        if any(intro in user_input_lower for intro in ['my name is', "i'm ", 'this is ', 'calling from']):
            score += 1
        
        # Company/reason mention
        if any(business in user_input_lower for business in ['company', 'calling about', 'regarding', 'from ']):
            score += 1
        
        # Sufficient length (more than just "hello")
        if len(user_input.split()) >= 3:  # Lowered from 5 to 3
            score += 1
        
        # Bonus for polite words
        if any(polite in user_input_lower for polite in ['please', 'thank you', 'appreciate', 'moment']):
            score += 1
            
        return min(score, 8)  # Cap at 8
    
    def _evaluate_user_input_simple(self, user_input: str, stage: str) -> Dict[str, Any]:
        """Simple evaluation logic for fallback scenarios"""
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
            
            # Progress to early objection stage after opener
            if evaluation['quality_score'] >= 2:
                evaluation['next_stage'] = 'early_objection'
            
            # Only hang up for really bad openers
            if evaluation['quality_score'] <= 1:
                evaluation['should_hang_up'] = random.random() < 0.3  # 30% chance
                
        elif stage == 'early_objection':
            # Check for basic objection handling
            if any(acknowledge in user_input_lower for acknowledge in ['understand', 'totally get', 'fair enough', 'appreciate']):
                evaluation['quality_score'] += 2
            if user_input.strip().endswith('?'):
                evaluation['quality_score'] += 1
            if any(empathy in user_input_lower for empathy in ['know', 'realize', 'understand']):
                evaluation['quality_score'] += 1
                
            # Progress to mini pitch after handling objection
            if evaluation['quality_score'] >= 5:
                evaluation['next_stage'] = 'mini_pitch'
                
        elif stage == 'mini_pitch':
            # Check for basic pitch elements
            if any(value in user_input_lower for value in ['help', 'save', 'improve', 'solve', 'solution']):
                evaluation['quality_score'] += 2
            if len(user_input.split()) < 50:  # Not too long
                evaluation['quality_score'] += 1
            if user_input.strip().endswith('?'):  # Asking for permission/interest
                evaluation['quality_score'] += 1
                
            # Progress to post-pitch objections
            if evaluation['quality_score'] >= 6:
                evaluation['next_stage'] = 'post_pitch_objections'
        
        elif stage == 'post_pitch_objections':
            # Final objection handling
            if any(close in user_input_lower for close in ['meeting', 'call', 'demo', 'discuss']):
                evaluation['quality_score'] += 2
                evaluation['next_stage'] = 'call_completed'  # Success!
        
        return evaluation
    
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End roleplay session and generate comprehensive coaching"""
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
            
            # Generate comprehensive coaching feedback using OpenAI
            coaching_result = self._generate_coaching_async(session)
            
            coaching_feedback = coaching_result.get('coaching', {}) if coaching_result.get('success') else {}
            overall_score = coaching_result.get('overall_score', 0) if coaching_result.get('success') else 0
            
            # If OpenAI coaching failed, use fallback
            if not coaching_result.get('success'):
                coaching_feedback, overall_score = self._generate_fallback_coaching(session)
            
            # Determine session success based on multiple factors
            session_success = self._determine_session_success(session, overall_score)
            
            # Update user progress if applicable
            if session_success and not forced_end:
                self._update_user_progress(session)
            
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
                'performance_metrics': session.get('performance_metrics', {})
            }
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_coaching_async(self, session: Dict) -> Dict[str, Any]:
        """Generate coaching feedback using OpenAI service"""
        try:
            # For now, use fallback coaching
            return {'success': False}
                
        except Exception as e:
            logger.error(f"Error generating async coaching: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_fallback_coaching(self, session: Dict) -> Tuple[Dict, int]:
        """Generate basic coaching when OpenAI is unavailable"""
        conversation = session.get('conversation_history', [])
        user_messages = [msg for msg in conversation if msg.get('role') == 'user']
        performance_metrics = session.get('performance_metrics', {})
        
        # Generate coaching based on conversation analysis
        coaching = {
            'coaching': {
                'sales_coaching': self._analyze_sales_performance(user_messages, session),
                'grammar_coaching': self._analyze_grammar_basics(user_messages),
                'vocabulary_coaching': self._analyze_vocabulary_usage(user_messages),
                'pronunciation_coaching': self._analyze_pronunciation_basics(user_messages),
                'rapport_assertiveness': self._analyze_rapport_confidence(user_messages, session)
            }
        }
        
        # Calculate basic score
        score = self._calculate_basic_score(session, user_messages)
        
        return coaching, score
    
    def _analyze_sales_performance(self, user_messages: List[Dict], session: Dict) -> str:
        """Analyze sales performance from user messages"""
        if not user_messages:
            return "Complete more of the conversation to get sales coaching."
        
        if len(user_messages) == 1:
            # Opener analysis
            opener = user_messages[0].get('content', '')
            if len(opener) < 20:
                return "Your opener was very brief. Try including a greeting, reason for calling, and permission to continue."
            elif 'hello' in opener.lower() or 'hi' in opener.lower():
                return "Good job starting with a greeting. Work on adding empathy like 'I know this is unexpected' to build rapport."
            else:
                return "Consider starting with a friendly greeting and showing empathy for the interruption."
        
        elif len(user_messages) >= 2:
            # Objection handling analysis
            return "Good job continuing the conversation past the first objection. Focus on acknowledging their concerns before redirecting."
        
        return "Keep practicing your conversation flow and objection handling techniques."
    
    def _analyze_grammar_basics(self, user_messages: List[Dict]) -> str:
        """Basic grammar analysis"""
        if not user_messages:
            return "Speak more to get grammar feedback."
        
        total_text = ' '.join([msg.get('content', '') for msg in user_messages])
        
        if "i'm" in total_text.lower() or "don't" in total_text.lower():
            return "Great use of contractions! This makes your speech sound more natural and conversational."
        else:
            return "Try using contractions like 'I'm', 'don't', 'we're' to sound more natural in English conversation."
    
    def _analyze_vocabulary_usage(self, user_messages: List[Dict]) -> str:
        """Basic vocabulary analysis"""
        if not user_messages:
            return "Speak more to get vocabulary feedback."
        
        total_text = ' '.join([msg.get('content', '') for msg in user_messages]).lower()
        
        business_words = ['help', 'solve', 'improve', 'solution', 'business', 'company', 'team']
        if any(word in total_text for word in business_words):
            return "Good use of business vocabulary. This shows professionalism and industry knowledge."
        else:
            return "Try incorporating more business terms like 'solution', 'improve', or 'help' to sound more professional."
    
    def _analyze_pronunciation_basics(self, user_messages: List[Dict]) -> str:
        """Basic pronunciation guidance"""
        return "Continue speaking clearly and at a steady pace. Practice key sales terms for better clarity."
    
    def _analyze_rapport_confidence(self, user_messages: List[Dict], session: Dict) -> str:
        """Analyze rapport and confidence"""
        if session.get('hang_up_triggered'):
            return "The prospect hung up. Work on your opening approach to create better first impressions."
        
        if len(user_messages) >= 3:
            return "Great job keeping the conversation going! This shows good rapport-building skills."
        else:
            return "Try to engage more and ask questions to build stronger rapport with prospects."
    
    def _calculate_basic_score(self, session: Dict, user_messages: List[Dict]) -> int:
        """Calculate basic performance score"""
        score = 50  # Base score
        
        # Participation bonus
        if len(user_messages) >= 4:
            score += 20
        elif len(user_messages) >= 3:
            score += 15
        elif len(user_messages) >= 2:
            score += 10
        
        # No hang-up bonus
        if not session.get('hang_up_triggered'):
            score += 15
        
        # Conversation quality bonus
        total_words = sum(len(msg.get('content', '').split()) for msg in user_messages)
        if total_words >= 50:
            score += 10
        
        # Mode difficulty adjustment
        mode = session.get('mode', 'practice')
        if mode == 'legend':
            score = min(score + 5, 100)
        
        return max(0, min(100, score))
    
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
        if evaluation.get('stage_completed') or evaluation.get('next_stage') != 'in_progress':
            next_stage = evaluation.get('next_stage', session['current_stage'])
            if next_stage != 'in_progress':
                session['current_stage'] = next_stage
        
        # Update call tracking for marathon/legend modes
        if session['mode'] in ['marathon', 'legend']:
            if evaluation.get('call_completed'):
                session['call_count'] += 1
                if evaluation.get('quality_score', 0) >= 6:
                    session['successful_calls'] += 1
                
                # Check if should start next call
                max_calls = 10 if session['mode'] == 'marathon' else 6
                if session['call_count'] < max_calls:
                    # Reset for next call
                    session['current_stage'] = 'phone_pickup'
                    session['objections_used'] = []
                    session['qualification_achieved'] = False
                    session['meeting_asked'] = False
    
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
            return None  # No hint for average performance
    
    def _should_call_continue(self, session: Dict, evaluation: Dict) -> bool:
        """Determine if call should continue based on multiple factors"""
        # Call ends if hung up
        if session.get('hang_up_triggered'):
            return False
        
        # Call ends if AI indicates it should end
        if not evaluation.get('should_continue', True):
            return False
        
        # Call ends if stage indicates completion
        if evaluation.get('next_stage') == 'call_completed':
            return False
        
        # Marathon/Legend modes continue until all calls completed
        if session['mode'] in ['marathon', 'legend']:
            max_calls = 10 if session['mode'] == 'marathon' else 6
            if session['call_count'] >= max_calls:
                return False
        
        return True
    
    def _handle_hang_up(self, session: Dict, reason: str) -> Dict[str, Any]:
        """Handle prospect hanging up with enhanced feedback"""
        session['hang_up_triggered'] = True
        session['session_active'] = False
        
        hang_up_responses = [
            "Not interested. Good bye.",
            "Please don't call here again.",
            "I'm hanging up now.",
            "This is not a good time. *click*"
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
        
        return {
            'success': True,
            'ai_response': response,
            'call_continues': False,
            'hang_up_reason': reason,
            'coaching_note': 'The prospect hung up. Focus on improving your opening approach to create better first impressions.'
        }
    
    def _determine_session_success(self, session: Dict, overall_score: int) -> bool:
        """Determine session success with enhanced criteria"""
        mode = session['mode']
        roleplay_id = session['roleplay_id']
        
        # Base success on overall score and mode requirements
        if mode == 'practice':
            # Practice mode: success if didn't hang up and reasonable score
            return not session.get('hang_up_triggered', False) and overall_score >= 50
        
        elif mode == 'marathon':
            # Marathon mode: need 6 successful calls
            threshold = ROLEPLAY_CONFIG[roleplay_id].get('marathon_threshold', 6)
            return session['successful_calls'] >= threshold
        
        elif mode == 'legend':
            # Legend mode: need perfect score
            threshold = ROLEPLAY_CONFIG[roleplay_id].get('legend_threshold', 6)
            return session['successful_calls'] >= threshold
        
        elif mode == 'challenge':  # Warmup challenge
            # Success based on score
            return overall_score >= 70
        
        else:
            # Default: success if good score and no hang up
            return overall_score >= 60 and not session.get('hang_up_triggered', False)
    
    def _update_user_progress(self, session: Dict) -> None:
        """Update user progress for successful sessions"""
        try:
            user_id = session['user_id']
            roleplay_id = session['roleplay_id']
            mode = session['mode']
            
            # Get unlock target
            config = ROLEPLAY_CONFIG.get(roleplay_id, {})
            unlock_target = config.get('unlock_target')
            
            if unlock_target and mode in ['marathon', 'challenge', 'simulation']:
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
        
        elif mode == 'challenge':
            if success:
                return f"Excellent! Score: {overall_score}/100. You've unlocked the next training module!"
            else:
                return f"Challenge complete! Score: {overall_score}/100. Practice more and try again to unlock the next module."
        
        else:  # Practice mode
            if overall_score >= 80:
                return f"Excellent work! Score: {overall_score}/100. You're ready for more challenging modes!"
            elif overall_score >= 60:
                return f"Good job! Score: {overall_score}/100. Keep practicing to improve your skills."
            else:
                return f"Nice try! Score: {overall_score}/100. Focus on the coaching feedback to improve."
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session status with enhanced metrics"""
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
                if current_time - started_at > timedelta(hours=2):  # 2 hour timeout
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
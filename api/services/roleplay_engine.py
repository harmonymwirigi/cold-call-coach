# ===== UPDATED API/SERVICES/ROLEPLAY_ENGINE.PY - ROLEPLAY 1.1 COMPLIANT =====

import random
import logging
import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from services.openai_service import OpenAIService
from services.supabase_client import SupabaseService

logger = logging.getLogger(__name__)

class RoleplayEngine:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.supabase_service = SupabaseService()
        
        # Session state tracking
        self.active_sessions = {}
        
        # ===== ROLEPLAY 1.1 SPECIFICATIONS =====
        
        # Early-stage objection list (29 items - never repeat consecutively)
        self.early_objections = [
            "What's this about?",
            "I'm not interested",
            "We don't take cold calls",
            "Now is not a good time",
            "I have a meeting",
            "Can you call me later?",
            "I'm about to go into a meeting",
            "Send me an email",
            "Can you send me the information?",
            "Can you message me on WhatsApp?",
            "Who gave you this number?",
            "This is my personal number",
            "Where did you get my number?",
            "What are you trying to sell me?",
            "Is this a sales call?",
            "Is this a cold call?",
            "Are you trying to sell me something?",
            "We are ok for the moment",
            "We are all good / all set",
            "We're not looking for anything right now",
            "We are not changing anything",
            "How long is this going to take?",
            "Is this going to take long?",
            "What company are you calling from?",
            "Who are you again?",
            "Where are you calling from?",
            "I never heard of you",
            "Not interested right now",
            "Just send me the details"
        ]
        
        # Impatience phrases for 10-second silence
        self.impatience_phrases = [
            "Hello? Are you still with me?",
            "Can you hear me?",
            "Just checking you're there…",
            "Still on the line?",
            "I don't have much time for this.",
            "Sounds like you are gone.",
            "Are you an idiot.",
            "What is going on.",
            "Are you okay to continue?",
            "I am afraid I have to go"
        ]
        
        # Roleplay 1.1 Configuration
        self.roleplay_11_config = {
            'opener_hangup_chance': 0.25,  # 20-30% chance of hangup on poor opener
            'silence_impatience_threshold': 10,  # 10 seconds
            'silence_hangup_threshold': 15,      # 15 seconds
            'pass_threshold': 3,  # Need 3/4 criteria for most rubrics
            'soft_discovery_threshold': 2  # Need 2/3 for soft discovery
        }
        
        logger.info(f"RoleplayEngine initialized for Roleplay 1.1 - OpenAI available: {self.openai_service.is_available()}")
        
    def create_session(self, user_id: str, roleplay_id: int, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create a new roleplay session with Roleplay 1.1 specifications"""
        try:
            # Validate roleplay 1.1
            if roleplay_id != 1:
                logger.warning(f"Non-Roleplay 1.1 ID {roleplay_id} - using basic flow")
            
            # Create unique session ID
            session_id = f"{user_id}_{roleplay_id}_{mode}_{datetime.now().timestamp()}"
            
            # Enhanced session data for Roleplay 1.1
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'roleplay_id': roleplay_id,
                'mode': mode,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'user_context': user_context,
                'conversation_history': [],
                'current_stage': 'phone_pickup',  # Roleplay 1.1 always starts with phone pickup
                'session_active': True,
                'hang_up_triggered': False,
                
                # Roleplay 1.1 specific tracking
                'objections_used': [],
                'stage_evaluations': {},
                'rubric_scores': {
                    'opener': {'score': 0, 'criteria_met': [], 'passed': False},
                    'objection_handling': {'score': 0, 'criteria_met': [], 'passed': False},
                    'mini_pitch': {'score': 0, 'criteria_met': [], 'passed': False},
                    'soft_discovery': {'score': 0, 'criteria_met': [], 'passed': False}
                },
                'pronunciation_issues': [],
                'grammar_issues': [],
                'vocabulary_issues': [],
                'overall_call_result': 'in_progress',  # 'pass', 'fail', 'in_progress'
                'coaching_notes': [],
                
                # Performance tracking
                'stage_progression': ['phone_pickup'],
                'silence_events': [],
                'hang_up_reason': None
            }
            
            # Store session in memory
            self.active_sessions[session_id] = session_data
            
            # Generate initial response (phone pickup)
            initial_response = self._generate_roleplay_11_initial_response()
            
            # Add to conversation history
            if initial_response:
                session_data['conversation_history'].append({
                    'role': 'assistant',
                    'content': initial_response,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'stage': 'phone_pickup'
                })
            
            logger.info(f"Created Roleplay 1.1 session {session_id} for user {user_id}")
            
            return {
                'success': True,
                'session_id': session_id,
                'initial_response': initial_response,
                'session_data': session_data
            }
            
        except Exception as e:
            logger.error(f"Error creating Roleplay 1.1 session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input with Roleplay 1.1 evaluation system"""
        try:
            logger.info(f"Processing Roleplay 1.1 input for session {session_id}: {user_input[:50]}...")
            
            if session_id not in self.active_sessions:
                logger.error(f"Session {session_id} not found")
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            
            if not session.get('session_active'):
                logger.error(f"Session {session_id} is not active")
                raise ValueError("Session is not active")
            
            # Handle special silence triggers
            if user_input == '[SILENCE_IMPATIENCE]':
                return self._handle_silence_impatience(session)
            
            if user_input == '[SILENCE_HANGUP]':
                return self._handle_silence_hangup(session)
            
            # Add user input to conversation
            session['conversation_history'].append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage']
            })
            
            # Roleplay 1.1 evaluation based on current stage
            evaluation = self._evaluate_roleplay_11_input(session, user_input)
            
            logger.info(f"Roleplay 1.1 evaluation: {evaluation}")
            
            # Generate AI response based on evaluation
            ai_response_data = self._generate_roleplay_11_response(session, user_input, evaluation)
            
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
            self._update_roleplay_11_session_state(session, evaluation)
            
            # Check if call should end
            call_continues = self._should_roleplay_11_continue(session, evaluation)
            
            logger.info(f"Roleplay 1.1 response: {ai_response[:50]}... Call continues: {call_continues}")
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': call_continues,
                'evaluation': evaluation,
                'session_state': session['current_stage'],
                'stage_passed': evaluation.get('passed', False),
                'overall_progress': self._get_roleplay_11_progress(session)
            }
            
        except Exception as e:
            logger.error(f"Error processing Roleplay 1.1 input: {e}")
            return {
                'success': False,
                'error': str(e),
                'call_continues': False
            }
    
    def _generate_roleplay_11_initial_response(self) -> str:
        """Generate initial phone pickup response for Roleplay 1.1"""
        responses = ["Hello?", "Hi there.", "Good morning.", "Yes?", "Hello, this is Alex."]
        return random.choice(responses)
    
    def _handle_silence_impatience(self, session: Dict) -> Dict[str, Any]:
        """Handle 10-second silence impatience trigger"""
        logger.info("Handling Roleplay 1.1 silence impatience")
        
        # Record silence event
        session['silence_events'].append({
            'type': 'impatience',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': session['current_stage']
        })
        
        # Select random impatience phrase
        phrase = random.choice(self.impatience_phrases)
        
        # Add to conversation
        session['conversation_history'].append({
            'role': 'assistant',
            'content': phrase,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': session['current_stage'],
            'trigger': 'silence_impatience'
        })
        
        return {
            'success': True,
            'ai_response': phrase,
            'call_continues': True,
            'evaluation': {'silence_trigger': 'impatience'},
            'session_state': session['current_stage']
        }
    
    def _handle_silence_hangup(self, session: Dict) -> Dict[str, Any]:
        """Handle 15-second silence hangup trigger"""
        logger.info("Handling Roleplay 1.1 silence hangup")
        
        # Record silence event
        session['silence_events'].append({
            'type': 'hangup',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': session['current_stage']
        })
        
        # Mark call as failed
        session['hang_up_triggered'] = True
        session['hang_up_reason'] = 'silence_15_seconds'
        session['overall_call_result'] = 'fail'
        
        hangup_response = "I don't have time for this. Goodbye."
        
        # Add to conversation
        session['conversation_history'].append({
            'role': 'assistant',
            'content': hangup_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': session['current_stage'],
            'trigger': 'silence_hangup'
        })
        
        return {
            'success': True,
            'ai_response': hangup_response,
            'call_continues': False,  # End the call
            'evaluation': {'silence_trigger': 'hangup', 'call_result': 'fail'},
            'session_state': 'call_ended'
        }
    
    def _evaluate_roleplay_11_input(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Evaluate user input using Roleplay 1.1 rubrics"""
        current_stage = session['current_stage']
        
        logger.info(f"Evaluating Roleplay 1.1 stage: {current_stage}")
        
        if current_stage in ['phone_pickup', 'opener_evaluation']:
            return self._evaluate_opener(session, user_input)
        elif current_stage == 'early_objection':
            return self._evaluate_objection_handling(session, user_input)
        elif current_stage == 'mini_pitch':
            return self._evaluate_mini_pitch(session, user_input)
        elif current_stage == 'soft_discovery':
            return self._evaluate_soft_discovery(session, user_input)
        else:
            # Default evaluation
            return {
                'passed': True,
                'score': 3,
                'criteria_met': [],
                'next_stage': 'in_progress',
                'should_hangup': False
            }
    
    def _evaluate_opener(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Evaluate opener using Roleplay 1.1 rubric (Pass if 3 of 4)"""
        user_input_lower = user_input.lower()
        criteria_met = []
        
        # 1. Clear cold call opener (pattern interrupt, permission-based, or value-first)
        opener_patterns = [
            'know this is out of the blue',
            'caught you at a bad time',
            'quick question',
            'reason for my call',
            'calling because',
            'might be able to help',
            'working with companies like',
            'help companies',
            'permission to tell you why'
        ]
        
        if any(pattern in user_input_lower for pattern in opener_patterns):
            criteria_met.append('clear_opener')
        elif not any(greeting in user_input_lower for greeting in ['hi', 'hello', 'good morning']) or len(user_input) > 20:
            # Give credit if it's not just a greeting and has substance
            criteria_met.append('clear_opener')
        
        # 2. Casual, confident tone (uses contractions and short phrases)
        contractions = ["i'm", "don't", "can't", "we're", "you're", "it's", "that's", "didn't", "won't", "aren't"]
        if any(contraction in user_input_lower for contraction in contractions):
            criteria_met.append('casual_tone')
        
        # 3. Demonstrates empathy (acknowledges interruption, unfamiliarity, randomness)
        empathy_phrases = [
            'know this is out of the blue',
            "don't know me",
            'out of nowhere',
            'interrupting',
            'caught you at a bad time',
            'random call',
            'unexpected',
            'unfamiliar'
        ]
        
        if any(phrase in user_input_lower for phrase in empathy_phrases):
            criteria_met.append('shows_empathy')
        
        # 4. Ends with soft question
        soft_questions = [
            'can i tell you why i\'m calling',
            'can i share why i\'m calling',
            'may i tell you why',
            'can i explain why',
            'would you be open to hearing',
            'can i have 30 seconds',
            'can i have a minute',
            'would you mind if i',
            'is this a bad time'
        ]
        
        if (user_input.strip().endswith('?') and 
            any(question in user_input_lower for question in soft_questions)):
            criteria_met.append('soft_question')
        elif user_input.strip().endswith('?'):
            # Give partial credit for any question
            criteria_met.append('soft_question')
        
        score = len(criteria_met)
        passed = score >= 3  # Need 3 of 4 to pass
        
        # Determine hangup probability based on score
        hangup_chance = 0.0
        if score <= 1:
            hangup_chance = 0.8  # 80% chance
        elif score == 2:
            hangup_chance = 0.3  # 30% chance
        else:
            hangup_chance = 0.1  # 10% chance even for good openers
        
        should_hangup = random.random() < hangup_chance
        
        # Update session rubric tracking
        session['rubric_scores']['opener'] = {
            'score': score,
            'criteria_met': criteria_met,
            'passed': passed
        }
        
        next_stage = 'call_ended' if should_hangup else 'early_objection'
        
        evaluation = {
            'stage': 'opener',
            'passed': passed,
            'score': score,
            'criteria_met': criteria_met,
            'should_hangup': should_hangup,
            'hangup_chance': hangup_chance,
            'next_stage': next_stage,
            'rubric_details': {
                'clear_opener': 'clear_opener' in criteria_met,
                'casual_tone': 'casual_tone' in criteria_met,
                'shows_empathy': 'shows_empathy' in criteria_met,
                'soft_question': 'soft_question' in criteria_met
            }
        }
        
        logger.info(f"Opener evaluation: {evaluation}")
        return evaluation
    
    def _evaluate_objection_handling(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Evaluate objection handling using Roleplay 1.1 rubric (Pass if 3 of 4)"""
        user_input_lower = user_input.lower()
        criteria_met = []
        
        # 1. Acknowledges calmly
        acknowledgments = [
            'fair enough',
            'totally get that',
            'i understand',
            'make sense',
            'appreciate that',
            'respect that',
            'i hear you',
            'completely understand'
        ]
        
        if any(ack in user_input_lower for ack in acknowledgments):
            criteria_met.append('acknowledges_calmly')
        
        # 2. Doesn't argue or pitch immediately
        argument_indicators = [
            'but you',
            'actually',
            "you're wrong",
            'however',
            'let me tell you',
            'listen',
            'well actually'
        ]
        
        pitch_indicators = [
            'our product',
            'we offer',
            'our solution',
            'we provide',
            'our service',
            'what we do is'
        ]
        
        if (not any(arg in user_input_lower for arg in argument_indicators) and
            not any(pitch in user_input_lower for pitch in pitch_indicators)):
            criteria_met.append('no_arguing')
        
        # 3. Reframes or buys time in 1 sentence
        reframe_phrases = [
            'the reason i called',
            'what i meant was',
            'let me be more specific',
            'to be clear',
            'here\'s the thing',
            'what if i told you',
            'imagine if'
        ]
        
        if any(reframe in user_input_lower for reframe in reframe_phrases):
            criteria_met.append('reframes')
        elif len(user_input.split('.')) <= 2:  # Short response
            criteria_met.append('reframes')
        
        # 4. Ends with forward-moving question
        forward_questions = [
            'can i ask you',
            'what if',
            'would you be open',
            'are you familiar',
            'have you ever',
            'do you currently',
            'how are you handling',
            'what\'s your biggest'
        ]
        
        if (user_input.strip().endswith('?') and 
            any(question in user_input_lower for question in forward_questions)):
            criteria_met.append('forward_question')
        
        score = len(criteria_met)
        passed = score >= 3  # Need 3 of 4 to pass
        
        # Update session rubric tracking
        session['rubric_scores']['objection_handling'] = {
            'score': score,
            'criteria_met': criteria_met,
            'passed': passed
        }
        
        # Determine next stage
        if passed:
            next_stage = 'mini_pitch'
        else:
            # Failed objection handling - call ends
            next_stage = 'call_ended'
        
        evaluation = {
            'stage': 'objection_handling',
            'passed': passed,
            'score': score,
            'criteria_met': criteria_met,
            'should_hangup': not passed,
            'next_stage': next_stage,
            'rubric_details': {
                'acknowledges_calmly': 'acknowledges_calmly' in criteria_met,
                'no_arguing': 'no_arguing' in criteria_met,
                'reframes': 'reframes' in criteria_met,
                'forward_question': 'forward_question' in criteria_met
            }
        }
        
        logger.info(f"Objection handling evaluation: {evaluation}")
        return evaluation
    
    def _evaluate_mini_pitch(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Evaluate mini pitch using Roleplay 1.1 rubric (Pass if 3 of 4)"""
        user_input_lower = user_input.lower()
        criteria_met = []
        
        # 1. Short (1-2 sentences, under 30 words)
        word_count = len(user_input.split())
        sentence_count = len([s for s in user_input.split('.') if s.strip()])
        
        if word_count <= 30 and sentence_count <= 2:
            criteria_met.append('short_pitch')
        
        # 2. Focuses on problem solved or outcome delivered (not features)
        outcome_phrases = [
            'help companies',
            'reduce',
            'increase',
            'save',
            'improve',
            'eliminate',
            'solve',
            'fix',
            'boost',
            'cut costs',
            'make more',
            'get more',
            'faster',
            'easier',
            'better results'
        ]
        
        feature_phrases = [
            'our platform',
            'our software',
            'our tool',
            'we have',
            'our system',
            'our technology'
        ]
        
        has_outcomes = any(outcome in user_input_lower for outcome in outcome_phrases)
        has_features = any(feature in user_input_lower for feature in feature_phrases)
        
        if has_outcomes and not has_features:
            criteria_met.append('outcome_focused')
        elif has_outcomes:  # Partial credit if mixed
            criteria_met.append('outcome_focused')
        
        # 3. Simple English (no jargon or buzzwords)
        jargon_phrases = [
            'leverage',
            'synergy',
            'paradigm',
            'optimize',
            'streamline',
            'best-in-class',
            'cutting-edge',
            'next-generation',
            'revolutionary',
            'game-changing',
            'disruptive',
            'innovative solutions'
        ]
        
        if not any(jargon in user_input_lower for jargon in jargon_phrases):
            criteria_met.append('simple_english')
        
        # 4. Sounds natural (not robotic or memorized)
        robotic_indicators = [
            'our company specializes',
            'we are a leading provider',
            'our mission is to',
            'we pride ourselves',
            'industry-leading',
            'state-of-the-art'
        ]
        
        if not any(robotic in user_input_lower for robotic in robotic_indicators):
            criteria_met.append('sounds_natural')
        
        score = len(criteria_met)
        passed = score >= 3  # Need 3 of 4 to pass
        
        # Update session rubric tracking
        session['rubric_scores']['mini_pitch'] = {
            'score': score,
            'criteria_met': criteria_met,
            'passed': passed
        }
        
        # Mini pitch moves to soft discovery regardless of pass/fail
        # The final judgment happens in soft discovery
        next_stage = 'soft_discovery'
        
        evaluation = {
            'stage': 'mini_pitch',
            'passed': passed,
            'score': score,
            'criteria_met': criteria_met,
            'should_hangup': False,  # Don't hang up yet
            'next_stage': next_stage,
            'rubric_details': {
                'short_pitch': 'short_pitch' in criteria_met,
                'outcome_focused': 'outcome_focused' in criteria_met,
                'simple_english': 'simple_english' in criteria_met,
                'sounds_natural': 'sounds_natural' in criteria_met
            }
        }
        
        logger.info(f"Mini pitch evaluation: {evaluation}")
        return evaluation
    
    def _evaluate_soft_discovery(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Evaluate soft discovery using Roleplay 1.1 rubric (Pass if 2 of 3)"""
        user_input_lower = user_input.lower()
        criteria_met = []
        
        # 1. Asks a short question tied to the pitch
        question_starters = [
            'how are you',
            'what\'s your',
            'are you',
            'do you',
            'have you',
            'when did you',
            'where do you',
            'who handles',
            'what happens when',
            'how do you currently'
        ]
        
        if (user_input.strip().endswith('?') and 
            any(starter in user_input_lower for starter in question_starters)):
            criteria_met.append('tied_question')
        
        # 2. Open/curious question (not leading)
        leading_indicators = [
            'wouldn\'t you agree',
            'don\'t you think',
            'wouldn\'t it be better',
            'wouldn\'t you want',
            'isn\'t it true that'
        ]
        
        open_indicators = [
            'how',
            'what',
            'when',
            'where',
            'who',
            'why'
        ]
        
        has_open = any(indicator in user_input_lower for indicator in open_indicators)
        has_leading = any(leading in user_input_lower for leading in leading_indicators)
        
        if has_open and not has_leading:
            criteria_met.append('open_curious')
        
        # 3. Soft, non-pushy tone
        pushy_indicators = [
            'you need to',
            'you should',
            'you have to',
            'you must',
            'obviously',
            'clearly you',
            'surely you'
        ]
        
        soft_indicators = [
            'curious',
            'wondering',
            'by chance',
            'happen to',
            'mind me asking',
            'if you don\'t mind'
        ]
        
        has_pushy = any(pushy in user_input_lower for pushy in pushy_indicators)
        has_soft = any(soft in user_input_lower for soft in soft_indicators)
        
        if not has_pushy or has_soft:
            criteria_met.append('soft_tone')
        
        score = len(criteria_met)
        passed = score >= 2  # Need 2 of 3 to pass
        
        # Update session rubric tracking
        session['rubric_scores']['soft_discovery'] = {
            'score': score,
            'criteria_met': criteria_met,
            'passed': passed
        }
        
        # Determine overall call result
        overall_passed = self._calculate_overall_roleplay_11_result(session, passed)
        
        evaluation = {
            'stage': 'soft_discovery',
            'passed': passed,
            'score': score,
            'criteria_met': criteria_met,
            'should_hangup': True,  # Always hang up after soft discovery
            'next_stage': 'call_ended',
            'overall_call_result': 'pass' if overall_passed else 'fail',
            'rubric_details': {
                'tied_question': 'tied_question' in criteria_met,
                'open_curious': 'open_curious' in criteria_met,
                'soft_tone': 'soft_tone' in criteria_met
            }
        }
        
        # Update session overall result
        session['overall_call_result'] = evaluation['overall_call_result']
        
        logger.info(f"Soft discovery evaluation: {evaluation}")
        return evaluation
    
    def _calculate_overall_roleplay_11_result(self, session: Dict, soft_discovery_passed: bool) -> bool:
        """Calculate overall call result based on all rubrics"""
        rubric_scores = session['rubric_scores']
        
        # Get individual stage results
        opener_passed = rubric_scores.get('opener', {}).get('passed', False)
        objection_passed = rubric_scores.get('objection_handling', {}).get('passed', False)
        mini_pitch_passed = rubric_scores.get('mini_pitch', {}).get('passed', False)
        
        # Call passes only if ALL rubrics pass and call was not ended by hang-up
        overall_passed = (opener_passed and 
                         objection_passed and 
                         mini_pitch_passed and 
                         soft_discovery_passed and
                         not session.get('hang_up_triggered', False))
        
        logger.info(f"Overall Roleplay 1.1 result: {overall_passed} "
                   f"(opener: {opener_passed}, objection: {objection_passed}, "
                   f"pitch: {mini_pitch_passed}, discovery: {soft_discovery_passed})")
        
        return overall_passed
    
    def _generate_roleplay_11_response(self, session: Dict, user_input: str, evaluation: Dict) -> Dict[str, Any]:
        """Generate AI response for Roleplay 1.1 based on evaluation"""
        try:
            current_stage = session['current_stage']
            
            # If should hang up, generate hang up response
            if evaluation.get('should_hangup'):
                return self._generate_hangup_response(session, evaluation)
            
            # Use OpenAI if available
            if self.openai_service.is_available():
                try:
                    response_data = self._generate_openai_roleplay_11_response(session, user_input, evaluation)
                    if response_data.get('success'):
                        return response_data
                except Exception as e:
                    logger.warning(f"OpenAI failed: {e}, using fallback")
            
            # Fallback response generation
            return self._generate_fallback_roleplay_11_response(session, user_input, evaluation)
            
        except Exception as e:
            logger.error(f"Error generating Roleplay 1.1 response: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_hangup_response(self, session: Dict, evaluation: Dict) -> Dict[str, Any]:
        """Generate appropriate hang-up response"""
        stage = evaluation.get('stage', 'unknown')
        passed = evaluation.get('passed', False)
        overall_result = evaluation.get('overall_call_result')
        
        if stage == 'opener' and not passed:
            responses = [
                "Not interested.",
                "Please don't call here again.",
                "I'm hanging up now.",
                "Take me off your list.",
                "Don't have time for this."
            ]
        elif stage == 'objection_handling' and not passed:
            responses = [
                "I already told you I'm not interested.",
                "You're not listening to me. Goodbye.",
                "This is exactly why I hate cold calls.",
                "I said no. Stop calling."
            ]
        elif stage == 'soft_discovery':
            if overall_result == 'pass':
                responses = [
                    "That's a good question. Send me some information.",
                    "Interesting conversation. Email me the details.",
                    "You know what, that's exactly what we're dealing with. Send me your info.",
                    "Actually, yes, that's been an issue. What's your email?"
                ]
            else:
                responses = [
                    "That's not relevant to us. Goodbye.",
                    "This conversation isn't going anywhere.",
                    "I don't have time for this. Bye.",
                    "Not interested. Please remove my number."
                ]
        else:
            responses = ["I have to go. Goodbye.", "Not interested. Thanks."]
        
        response = random.choice(responses)
        
        # Mark session as ending
        session['hang_up_triggered'] = True
        if not session.get('hang_up_reason'):
            session['hang_up_reason'] = f"stage_{stage}_evaluation"
        
        return {
            'success': True,
            'response': response,
            'hangup': True
        }
    
    def _generate_openai_roleplay_11_response(self, session: Dict, user_input: str, evaluation: Dict) -> Dict[str, Any]:
        """Generate OpenAI response for Roleplay 1.1"""
        try:
            # This would integrate with the OpenAI service
            # For now, return fallback
            return self._generate_fallback_roleplay_11_response(session, user_input, evaluation)
        except Exception as e:
            logger.error(f"OpenAI Roleplay 1.1 response error: {e}")
            return self._generate_fallback_roleplay_11_response(session, user_input, evaluation)
    
    def _generate_fallback_roleplay_11_response(self, session: Dict, user_input: str, evaluation: Dict) -> Dict[str, Any]:
        """Generate fallback response for Roleplay 1.1"""
        try:
            current_stage = session['current_stage']
            
            if current_stage in ['phone_pickup', 'opener_evaluation']:
                # Move to objection after opener
                response = self._get_unused_objection(session)
            elif current_stage == 'early_objection':
                # Respond to objection handling
                if evaluation.get('passed'):
                    responses = ["Alright, I'm listening.", "Go ahead, what is it?", "You have 30 seconds."]
                else:
                    responses = ["I already told you I'm not interested.", "Are you not listening to me?"]
                response = random.choice(responses)
            elif current_stage == 'mini_pitch':
                # Respond to mini pitch
                if evaluation.get('passed'):
                    responses = ["That's interesting. Tell me more.", "How exactly do you do that?", "What does that look like?"]
                else:
                    responses = ["I don't understand what you're saying.", "That sounds like everything else.", "Too complicated."]
                response = random.choice(responses)
            elif current_stage == 'soft_discovery':
                # This should trigger hang-up, but provide response just in case
                responses = ["That's a good question.", "Interesting.", "I see."]
                response = random.choice(responses)
            else:
                response = "I see. Go on."
            
            return {
                'success': True,
                'response': response,
                'fallback_used': True
            }
            
        except Exception as e:
            logger.error(f"Error generating fallback Roleplay 1.1 response: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "Can you repeat that?"
            }
    
    def _get_unused_objection(self, session: Dict) -> str:
        """Get an unused objection for Roleplay 1.1"""
        used_objections = session.get('objections_used', [])
        available_objections = [obj for obj in self.early_objections if obj not in used_objections]
        
        if not available_objections:
            # Reset if all used
            available_objections = self.early_objections
            session['objections_used'] = []
        
        selected_objection = random.choice(available_objections)
        session['objections_used'].append(selected_objection)
        
        return selected_objection
    
    def _update_roleplay_11_session_state(self, session: Dict, evaluation: Dict) -> None:
        """Update session state based on Roleplay 1.1 evaluation"""
        current_stage = session['current_stage']
        next_stage = evaluation.get('next_stage', 'in_progress')
        
        if next_stage and next_stage != 'in_progress':
            session['current_stage'] = next_stage
            session['stage_progression'].append(next_stage)
            
            logger.info(f"Roleplay 1.1 stage progression: {current_stage} -> {next_stage}")
        
        # Store stage evaluation
        session['stage_evaluations'][current_stage] = evaluation
    
    def _should_roleplay_11_continue(self, session: Dict, evaluation: Dict) -> bool:
        """Determine if Roleplay 1.1 call should continue"""
        # Check for hang-up conditions
        if evaluation.get('should_hangup') or session.get('hang_up_triggered'):
            return False
        
        # Check if call ended naturally
        if evaluation.get('next_stage') == 'call_ended':
            return False
        
        return True
    
    def _get_roleplay_11_progress(self, session: Dict) -> Dict[str, Any]:
        """Get current Roleplay 1.1 progress"""
        stage_progression = session.get('stage_progression', [])
        rubric_scores = session.get('rubric_scores', {})
        
        return {
            'current_stage': session.get('current_stage'),
            'stages_completed': stage_progression,
            'rubric_scores': rubric_scores,
            'overall_result': session.get('overall_call_result', 'in_progress')
        }
    
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End Roleplay 1.1 session and generate coaching"""
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
            
            # Generate Roleplay 1.1 coaching
            coaching_feedback, overall_score = self._generate_roleplay_11_coaching(session)
            
            # Determine session success
            session_success = session.get('overall_call_result') == 'pass'
            
            # Generate completion message
            if session_success:
                completion_message = f"Congratulations! You passed Roleplay 1.1. Score: {overall_score}/100."
            else:
                completion_message = f"Session complete. Score: {overall_score}/100. Keep practicing to improve!"
            
            # Clean up session
            del self.active_sessions[session_id]
            
            logger.info(f"Ended Roleplay 1.1 session {session_id} - Result: {session.get('overall_call_result')}")
            
            return {
                'success': True,
                'duration_minutes': duration_minutes,
                'session_success': session_success,
                'coaching': coaching_feedback,
                'overall_score': overall_score,
                'completion_message': completion_message,
                'session_data': session,
                'roleplay_11_results': {
                    'rubric_scores': session.get('rubric_scores', {}),
                    'stage_progression': session.get('stage_progression', []),
                    'silence_events': session.get('silence_events', []),
                    'hang_up_reason': session.get('hang_up_reason')
                }
            }
            
        except Exception as e:
            logger.error(f"Error ending Roleplay 1.1 session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_roleplay_11_coaching(self, session: Dict) -> Tuple[Dict, int]:
        """Generate coaching feedback for Roleplay 1.1 (CEFR A2 level)"""
        try:
            conversation = session.get('conversation_history', [])
            user_messages = [msg for msg in conversation if msg.get('role') == 'user']
            rubric_scores = session.get('rubric_scores', {})
            
            # Generate coaching in CEFR A2 English (simple, clear language)
            coaching = {
                'coaching': {
                    'sales_coaching': self._generate_sales_coaching_a2(session, rubric_scores),
                    'grammar_coaching': self._generate_grammar_coaching_a2(session, user_messages),
                    'vocabulary_coaching': self._generate_vocabulary_coaching_a2(session, user_messages),
                    'pronunciation_coaching': self._generate_pronunciation_coaching_a2(session),
                    'rapport_assertiveness': self._generate_rapport_coaching_a2(session, rubric_scores)
                }
            }
            
            # Calculate score based on rubric results
            score = self._calculate_roleplay_11_score(session, rubric_scores)
            
            logger.info(f"Generated Roleplay 1.1 coaching - Score: {score}")
            
            return coaching, score
            
        except Exception as e:
            logger.error(f"Error generating Roleplay 1.1 coaching: {e}")
            return self._generate_basic_coaching(), 50
    
    def _generate_sales_coaching_a2(self, session: Dict, rubric_scores: Dict) -> str:
        """Generate sales coaching in CEFR A2 English"""
        failed_stages = []
        
        for stage, scores in rubric_scores.items():
            if not scores.get('passed', False):
                failed_stages.append(stage)
        
        if not failed_stages:
            return "Great job! You passed all sales steps. Keep practicing to get even better."
        
        stage_tips = {
            'opener': "Your opening needs work. Try: 'Hi, I know this is out of the blue, but can I tell you why I'm calling?'",
            'objection_handling': "When they object, say 'I understand' first. Don't argue. Then ask a question.",
            'mini_pitch': "Keep your pitch short. Talk about the problem you solve, not your product features.",
            'soft_discovery': "Ask open questions like 'How do you handle that now?' Don't be pushy."
        }
        
        first_failed = failed_stages[0]
        return stage_tips.get(first_failed, "Practice your sales skills. Stay calm and ask good questions.")
    
    def _generate_grammar_coaching_a2(self, session: Dict, user_messages: List) -> str:
        """Generate grammar coaching in CEFR A2 English"""
        if not user_messages:
            return "Good grammar! Use contractions like 'I'm' and 'don't' to sound natural."
        
        # Simple grammar analysis
        all_text = ' '.join([msg.get('content', '') for msg in user_messages]).lower()
        
        if 'i am' in all_text and "i'm" not in all_text:
            return "Use 'I'm' instead of 'I am'. It sounds more natural in sales calls."
        elif 'do not' in all_text and "don't" not in all_text:
            return "Use 'don't' instead of 'do not'. Contractions sound friendlier."
        elif all_text.count('the') > len(user_messages) * 2:
            return "You use 'the' too much. Sometimes you don't need it. Example: 'I work with companies' not 'I work with the companies'."
        else:
            return "Good grammar! Keep using contractions like 'I'm' and 'can't' to sound natural."
    
    def _generate_vocabulary_coaching_a2(self, session: Dict, user_messages: List) -> str:
        """Generate vocabulary coaching in CEFR A2 English"""
        if not user_messages:
            return "Good word choices! Use simple, clear business words."
        
        all_text = ' '.join([msg.get('content', '') for msg in user_messages]).lower()
        
        # Check for common Spanish-English false friends
        if 'assist' in all_text:
            return "You said 'assist'. In English, use 'attend' for meetings. 'Assist' means 'help'."
        elif 'realize' in all_text and 'meeting' in all_text:
            return "You said 'realize a meeting'. Say 'have a meeting' instead."
        elif 'win' in all_text and 'meeting' in all_text:
            return "You said 'win a meeting'. Say 'book a meeting' or 'schedule a meeting'."
        elif any(word in all_text for word in ['utilize', 'leverage', 'optimize']):
            return "Use simple words. Say 'use' instead of 'utilize'. Say 'improve' instead of 'optimize'."
        else:
            return "Good word choices! Keep using simple, clear business language."
    
    def _generate_pronunciation_coaching_a2(self, session: Dict) -> str:
        """Generate pronunciation coaching in CEFR A2 English"""
        pronunciation_issues = session.get('pronunciation_issues', [])
        
        if not pronunciation_issues:
            return "Good pronunciation! Speak clearly and not too fast."
        
        # Get the first issue for coaching
        first_issue = pronunciation_issues[0]
        word = first_issue.get('word', 'schedule')
        
        # Common pronunciation tips for Spanish speakers
        pronunciation_tips = {
            'schedule': "Word: 'schedule' - Say it like: 'SKED-jool'",
            'focus': "Word: 'focus' - Say it like: 'FOH-kus'", 
            'business': "Word: 'business' - Say it like: 'BIZ-ness'",
            'company': "Word: 'company' - Say it like: 'KUM-puh-nee'",
            'meeting': "Word: 'meeting' - Say it like: 'MEE-ting'"
        }
        
        return pronunciation_tips.get(word.lower(), f"Practice saying '{word}' clearly. Speak slowly at first.")
    
    def _generate_rapport_coaching_a2(self, session: Dict, rubric_scores: Dict) -> str:
        """Generate rapport coaching in CEFR A2 English"""
        opener_passed = rubric_scores.get('opener', {}).get('passed', False)
        
        if not opener_passed:
            return "Show empathy at the start. Say 'I know this is unexpected' or 'I know you don't know me'."
        
        objection_passed = rubric_scores.get('objection_handling', {}).get('passed', False)
        
        if not objection_passed:
            return "Stay calm when they object. Say 'I understand' and don't argue with them."
        
        return "Good rapport! You sound professional and friendly. Keep being polite but confident."
    
    def _calculate_roleplay_11_score(self, session: Dict, rubric_scores: Dict) -> int:
        """Calculate overall score for Roleplay 1.1"""
        # Base score
        score = 40
        
        # Add points for each passed rubric
        for stage, scores in rubric_scores.items():
            if scores.get('passed', False):
                score += 15  # 15 points per passed stage
        
        # Bonus for completing without hangup
        if not session.get('hang_up_triggered', False):
            score += 10
        
        # Bonus for overall pass
        if session.get('overall_call_result') == 'pass':
            score += 10
        
        return min(100, max(0, score))
    
    def _generate_basic_coaching(self) -> Dict:
        """Basic coaching fallback"""
        return {
            'coaching': {
                'sales_coaching': 'Practice your opening and objection handling.',
                'grammar_coaching': 'Use contractions like "I\'m" and "don\'t" to sound natural.',
                'vocabulary_coaching': 'Use simple, clear business words.',
                'pronunciation_coaching': 'Speak clearly and not too fast.',
                'rapport_assertiveness': 'Be polite but confident in your calls.'
            }
        }
    
    # ===== EXISTING METHODS (unchanged) =====
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session status"""
        session = self.active_sessions.get(session_id)
        if session:
            return {
                **session,
                'openai_available': self.openai_service.is_available(),
                'roleplay_version': '1.1'
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
                logger.info(f"Cleaned up expired Roleplay 1.1 session: {session_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get overall service status"""
        return {
            'active_sessions': len(self.active_sessions),
            'openai_available': self.openai_service.is_available(),
            'openai_status': self.openai_service.get_status(),
            'engine_status': 'running',
            'roleplay_version': '1.1',
            'specifications': {
                'silence_impatience_threshold': 10,
                'silence_hangup_threshold': 15,
                'total_objections': len(self.early_objections),
                'total_impatience_phrases': len(self.impatience_phrases)
            }
        }
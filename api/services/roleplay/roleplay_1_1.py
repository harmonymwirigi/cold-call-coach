# ===== FIXED: services/roleplay/roleplay_1_1.py - PROPER CONVERSATION FLOW =====

import random
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from .base_roleplay import BaseRoleplay
from .configs.roleplay_1_1_config import Roleplay11Config

logger = logging.getLogger(__name__)

class Roleplay11(BaseRoleplay):
    """FIXED Roleplay 1.1 - Practice Mode with Proper Conversation Flow"""
    
    def __init__(self, openai_service=None):
        super().__init__(openai_service)
        self.config = Roleplay11Config()
        self.roleplay_id = self.config.ROLEPLAY_ID
        
        logger.info(f"Roleplay 1.1 initialized with OpenAI: {self.is_openai_available()}")
        
    def get_roleplay_info(self) -> Dict[str, Any]:
        """Return enhanced Roleplay 1.1 configuration"""
        return {
            'id': self.config.ROLEPLAY_ID,
            'name': self.config.NAME,
            'description': self.config.DESCRIPTION,
            'type': 'practice',
            'features': {
                'ai_evaluation': self.is_openai_available(),
                'dynamic_scoring': True,
                'extended_conversation': True,
                'detailed_coaching': True,
                'natural_conversation': True,
                'empathy_scoring': True,
                'outcome_focused_evaluation': True
            },
            'stages': list(self.config.STAGE_FLOW.keys()),
            'max_turns': self.config.CONVERSATION_LIMITS['max_total_turns'],
            'scoring_system': 'weighted_criteria'
        }
    
    def create_session(self, user_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create enhanced Roleplay 1.1 session"""
        try:
            session_id = f"{user_id}_{self.config.ROLEPLAY_ID}_{mode}_{int(datetime.now().timestamp())}"
            
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'roleplay_id': self.roleplay_id,
                'mode': mode,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'user_context': user_context,
                'conversation_history': [],
                'current_stage': 'phone_pickup',
                'session_active': True,
                'hang_up_triggered': False,
                'turn_count': 0,
                'stage_turn_count': 0,
                'stages_completed': [],
                'conversation_quality': 0,
                'rubric_scores': {},
                'stage_progression': ['phone_pickup'],
                'overall_call_result': 'in_progress',
                
                # Enhanced: Additional tracking
                'prospect_warmth': 0,           
                'empathy_shown': False,         
                'specific_benefits_mentioned': False,  
                'conversation_flow_score': 0,   
                'last_evaluation': None,       
                'cumulative_score': 0,
                'minimum_turns_completed': False,  # NEW: Track minimum conversation length
                'valid_opener_received': False,    # NEW: Track if we got a real opener
                'conversation_started': False,     # NEW: Track if conversation has begun
                'attempts_count': 0                # NEW: Track number of attempts
            }
            
            # Store session
            self.active_sessions[session_id] = session_data
            
            # Generate contextual initial response
            initial_response = self._get_contextual_initial_response(user_context)
            
            # Add to conversation
            session_data['conversation_history'].append({
                'role': 'assistant',
                'content': initial_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': 'phone_pickup',
                'prospect_warmth': 0
            })
            
            logger.info(f"Created Roleplay 1.1 session {session_id} with enhanced tracking")
            
            return {
                'success': True,
                'session_id': session_id,
                'initial_response': initial_response,
                'roleplay_info': self.get_roleplay_info()
            }
            
        except Exception as e:
            logger.error(f"Error creating Roleplay 1.1 session: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """FIXED: Process user input with proper conversation flow"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            
            if not session.get('session_active'):
                raise ValueError("Session not active")
            
            # Handle special silence triggers
            if user_input in ['[SILENCE_IMPATIENCE]', '[SILENCE_HANGUP]']:
                return self._handle_silence_trigger(session, user_input)
            
            # Increment counters
            session['turn_count'] += 1
            session['stage_turn_count'] += 1
            session['attempts_count'] += 1
            
            # Add user input to conversation
            session['conversation_history'].append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage']
            })
            
            logger.info(f"Processing input #{session['turn_count']}: '{user_input[:50]}...'")
            
            # FIXED: Better evaluation logic
            evaluation_stage = self._get_evaluation_stage(session['current_stage'])
            evaluation = self._evaluate_user_input_enhanced(session, user_input, evaluation_stage)
            
            # Store evaluation for context
            session['last_evaluation'] = evaluation
            
            # FIXED: Update conversation metrics
            self._update_conversation_metrics(session, evaluation)
            
            # FIXED: Validate conversation progress
            self._validate_conversation_progress(session, user_input, evaluation)
            
            # FIXED: Check if should hang up (much more lenient)
            should_hang_up = self._should_hang_up_enhanced(session, evaluation, user_input)
            
            if should_hang_up:
                ai_response = self._get_contextual_hangup_response(session, evaluation)
                session['hang_up_triggered'] = True
                call_continues = False
                logger.info(f"Session {session_id}: Call ending due to hang-up")
            else:
                # Generate contextual AI response
                ai_response = self._generate_contextual_ai_response(session, user_input, evaluation)
                
                # FIXED: Update session state with proper logic
                self._update_session_state_enhanced(session, evaluation)
                
                # FIXED: Check if call should continue (much more lenient)
                call_continues = self._should_call_continue_enhanced(session, evaluation)
                
                if not call_continues:
                    logger.info(f"Session {session_id}: Call ending naturally after {session['turn_count']} turns")
            
            # Add AI response to conversation
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage'],
                'evaluation': evaluation,
                'prospect_warmth': session.get('prospect_warmth', 0)
            })
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': call_continues,
                'evaluation': evaluation,
                'session_state': session['current_stage'],
                'turn_count': session['turn_count'],
                'conversation_quality': session['conversation_quality'],
                'prospect_warmth': session.get('prospect_warmth', 0),
                'debug_info': {
                    'minimum_turns_completed': session.get('minimum_turns_completed', False),
                    'valid_opener_received': session.get('valid_opener_received', False),
                    'conversation_started': session.get('conversation_started', False),
                    'evaluation_stage': evaluation_stage,
                    'should_hang_up': should_hang_up,
                    'attempts_count': session.get('attempts_count', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing Roleplay 1.1 input: {e}")
            return {'success': False, 'error': str(e), 'call_continues': False}
    
    # ===== FIXED CONVERSATION VALIDATION =====
    
    def _validate_conversation_progress(self, session: Dict, user_input: str, evaluation: Dict):
        """Validate that the conversation is progressing properly"""
        current_stage = session['current_stage']
        turn_count = session['turn_count']
        
        # Check if this is a valid opener (much more lenient)
        if current_stage in ['phone_pickup', 'opener_evaluation']:
            if turn_count == 1:
                # For first attempt, just mark conversation as started
                session['conversation_started'] = True
                
                # Check if it's a valid opener
                if self._is_valid_opener(user_input):
                    session['valid_opener_received'] = True
                    logger.info("Valid opener received")
                else:
                    logger.info(f"Basic opener received: '{user_input}' - giving user chance to improve")
                    # Don't end conversation, give chance to improve
        
        # Mark minimum turns completed (increased threshold)
        if turn_count >= self.config.CONVERSATION_LIMITS['min_turns_for_success']:
            session['minimum_turns_completed'] = True
        
        # Always mark conversation as started after first turn
        if turn_count >= 1:
            session['conversation_started'] = True
    
    def _is_valid_opener(self, user_input: str) -> bool:
        """FIXED: More lenient check for valid conversation opener"""
        user_input = user_input.strip().lower()
        
        # Any input over 2 words is considered an attempt
        if len(user_input.split()) >= 2:
            return True
        
        # Single words that show effort
        effort_words = ['hi', 'hello', 'hey', 'good', 'morning', 'afternoon', 'evening']
        if user_input in effort_words:
            return True
        
        return False
    
    # ===== FIXED CALL CONTINUATION LOGIC =====
    
    def _should_call_continue_enhanced(self, session: Dict, evaluation: Dict) -> bool:
        """FIXED: Much more lenient call continuation logic"""
        
        # Always continue if hung up
        if session.get('hang_up_triggered'):
            return False
        
        # Always continue if stage is call_ended
        if session['current_stage'] == 'call_ended':
            return False
        
        # Check conversation limits (absolute maximum only)
        max_turns = self.config.CONVERSATION_LIMITS['max_total_turns']
        if session['turn_count'] >= max_turns:
            logger.info(f"Ending call: reached maximum turns ({max_turns})")
            return False
        
        # FIXED: Much more lenient early turn logic
        min_turns = self.config.CONVERSATION_LIMITS.get('min_turns_for_success', 6)
        
        # NEVER end before at least 3 turns
        if session['turn_count'] < 3:
            logger.info(f"Continuing call: only {session['turn_count']} turns, need at least 3")
            return True
        
        # For turns 3-6, be very lenient
        if session['turn_count'] < min_turns:
            # Only end if user is clearly not trying (empty inputs, single words repeatedly)
            attempts = session.get('attempts_count', 0)
            if attempts >= 3:
                # Check if user has made any real effort
                conversation_quality = session.get('conversation_quality', 0)
                if conversation_quality < 20:
                    logger.info(f"Ending call: 3+ attempts but quality still very low ({conversation_quality})")
                    return False
            
            logger.info(f"Continuing call: {session['turn_count']} turns, still in learning phase")
            return True
        
        # After minimum turns, use normal logic but still be lenient
        conversation_quality = session.get('conversation_quality', 0)
        prospect_warmth = session.get('prospect_warmth', 0)
        
        # Continue if conversation quality is decent
        if conversation_quality >= 40:
            logger.info(f"Continuing call: good conversation quality ({conversation_quality}%)")
            return True
        
        # Continue if prospect is warming up
        if prospect_warmth >= 2:
            logger.info(f"Continuing call: prospect warming up (warmth={prospect_warmth})")
            return True
        
        # Continue if we're in early stages and user is making effort
        early_stages = ['phone_pickup', 'opener_evaluation', 'early_objection', 'objection_handling']
        if session['current_stage'] in early_stages and session['turn_count'] < 8:
            logger.info(f"Continuing call: in early stage '{session['current_stage']}'")
            return True
        
        # Only end if we've had reasonable length conversation AND poor quality
        if (session['turn_count'] >= 8 and 
            conversation_quality < 30 and 
            prospect_warmth <= 1):
            logger.info(f"Natural conversation end: {session['turn_count']} turns, quality={conversation_quality}, warmth={prospect_warmth}")
            return False
        
        # Default: continue the conversation
        logger.info(f"Continuing call: default continuation (turn {session['turn_count']})")
        return True
    
    # ===== FIXED HANG-UP LOGIC =====
    
    def _should_hang_up_enhanced(self, session: Dict, evaluation: Dict, user_input: str) -> bool:
        """FIXED: Much more lenient hang-up logic"""
        current_stage = session['current_stage']
        turn_count = session['turn_count']
        
        # NEVER hang up in the first 4 turns - give users time to learn
        if turn_count <= 4:
            logger.info("No hang-up: too early in conversation (first 4 turns)")
            return False
        
        # Don't hang up if prospect is warming up at all
        prospect_warmth = session.get('prospect_warmth', 0)
        if prospect_warmth >= 1:
            logger.info(f"No hang-up: prospect showing some warmth ({prospect_warmth})")
            return False
        
        # Don't hang up if conversation quality is above minimum
        conversation_quality = session.get('conversation_quality', 0)
        if conversation_quality >= 25:
            logger.info(f"No hang-up: conversation quality acceptable ({conversation_quality}%)")
            return False
        
        # Very rare hang-up only for extremely poor performance after many tries
        weighted_score = evaluation.get('weighted_score', evaluation.get('score', 2))
        attempts = session.get('attempts_count', 0)
        
        # Only consider hang-up after 6+ turns AND multiple poor attempts
        if turn_count >= 6 and attempts >= 4 and weighted_score <= 0.5 and conversation_quality < 15:
            hang_up_prob = 0.2  # Only 20% chance even then
            should_hang_up = random.random() < hang_up_prob
            
            if should_hang_up:
                logger.info(f"Rare hang-up triggered: turns={turn_count}, attempts={attempts}, score={weighted_score}, quality={conversation_quality}%")
            
            return should_hang_up
        
        # Default: no hang-up
        logger.info("No hang-up: conditions not met for hang-up")
        return False
    
    # ===== FIXED EVALUATION LOGIC =====
    
    def _evaluate_user_input_enhanced(self, session: Dict, user_input: str, evaluation_stage: str) -> Dict[str, Any]:
        """FIXED: Enhanced evaluation with better scoring"""
        try:
            if self.is_openai_available():
                # Use OpenAI with enhanced prompting
                evaluation = self.openai_service.evaluate_user_input(
                    user_input,
                    session['conversation_history'],
                    evaluation_stage
                )
                
                # Apply weighted scoring
                evaluation = self._apply_weighted_scoring(evaluation, evaluation_stage)
                
                # Store in session rubric scores
                session['rubric_scores'][evaluation_stage] = {
                    'score': evaluation.get('score', 0),
                    'weighted_score': evaluation.get('weighted_score', 0),
                    'passed': evaluation.get('passed', False),
                    'criteria_met': evaluation.get('criteria_met', [])
                }
                
                return evaluation
            else:
                return self._enhanced_basic_evaluation(user_input, evaluation_stage, session)
                
        except Exception as e:
            logger.error(f"Enhanced evaluation error: {e}")
            return self._enhanced_basic_evaluation(user_input, evaluation_stage, session)
    
    def _enhanced_basic_evaluation(self, user_input: str, evaluation_stage: str, session: Dict) -> Dict[str, Any]:
        """FIXED: Much more encouraging basic evaluation"""
        score = 0
        weighted_score = 0
        criteria_met = []
        user_input_lower = user_input.lower().strip()
        turn_count = session.get('turn_count', 1)
        
        # Get criteria for this stage
        stage_criteria = self.config.EVALUATION_CRITERIA.get(evaluation_stage, {}).get('criteria', [])
        
        # FIXED: Much more encouraging evaluation, especially for early attempts
        for criterion in stage_criteria:
            weight = criterion.get('weight', 1.0)
            met = False
            
            # Check keywords
            if 'keywords' in criterion:
                if any(keyword in user_input_lower for keyword in criterion['keywords']):
                    met = True
            
            # FIXED: Much more lenient basic criteria
            if criterion.get('name') == 'clear_introduction':
                # Accept any attempt to communicate
                basic_attempts = ['hello', 'hi', 'hey', 'good', 'morning', 'afternoon', 'this is', 'my name', 'calling from']
                if any(word in user_input_lower for word in basic_attempts):
                    met = True
            
            # Give credit for natural tone (any contractions or casual language)
            if criterion.get('check_contractions') or criterion.get('name') == 'natural_tone':
                natural_indicators = ["i'm", "don't", "can't", "we're", "you're", "won't", "isn't", "i", "we", "our"]
                if any(indicator in user_input_lower for indicator in natural_indicators):
                    met = True
            
            # Give credit for any question
            if criterion.get('name') == 'engaging_close':
                if '?' in user_input or any(q in user_input_lower for q in ['can i', 'may i', 'would you', 'could i']):
                    met = True
            
            if met:
                criteria_met.append(criterion['name'])
                score += 1
                weighted_score += weight
        
        # FIXED: Much more generous base scoring
        word_count = len(user_input.split())
        
        # Give credit for effort based on word count
        if word_count >= 1:
            score += 0.5  # Base effort bonus
        if word_count >= 3:
            score += 0.5  # Meaningful attempt bonus
        if word_count >= 5:
            score += 0.5  # Good length bonus
        if word_count >= 8:
            score += 0.5  # Detailed attempt bonus
        
        # FIXED: Very generous scoring for early attempts
        if turn_count <= 2:
            score = max(score, 1.5)  # Minimum score for first attempts
            weighted_score = max(weighted_score, 1.5)
        elif turn_count <= 4:
            score = max(score, 1.0)  # Still generous for early attempts
            weighted_score = max(weighted_score, 1.0)
        
        # Calculate normalized scores
        total_possible_weight = sum(c.get('weight', 1.0) for c in stage_criteria)
        if total_possible_weight > 0:
            normalized_weighted_score = (weighted_score / total_possible_weight) * 4
        else:
            normalized_weighted_score = min(score, 4.0)
        
        # Ensure minimum score for effort
        final_score = max(normalized_weighted_score, 1.0)
        
        # Check pass threshold (more lenient)
        threshold = self.config.EVALUATION_CRITERIA.get(evaluation_stage, {}).get('pass_threshold', 2)
        passed = final_score >= threshold
        
        logger.info(f"Basic evaluation: score={final_score:.1f}, passed={passed}, criteria={len(criteria_met)}, words={word_count}")
        
        return {
            'score': min(4, max(1, int(final_score))),  # Keep in 1-4 range
            'weighted_score': round(final_score, 1),
            'passed': passed,
            'criteria_met': criteria_met,
            'feedback': f'Enhanced evaluation: {len(criteria_met)} criteria met for {evaluation_stage}',
            'should_continue': True,
            'next_action': 'continue',
            'hang_up_probability': 0.0,  # No hang-up from evaluation
            'source': 'enhanced_basic',
            'stage': evaluation_stage
        }
    
    # ===== FIXED AI RESPONSE GENERATION =====
    
    def _generate_contextual_ai_response(self, session: Dict, user_input: str, evaluation: Dict) -> str:
        """Generate contextual AI response based on conversation state"""
        try:
            if self.is_openai_available():
                # Enhanced context for AI response
                enhanced_context = {
                    **session['user_context'],
                    'prospect_warmth': session.get('prospect_warmth', 0),
                    'conversation_quality': session.get('conversation_quality', 0),
                    'empathy_shown': session.get('empathy_shown', False),
                    'stage_performance': evaluation,
                    'turn_count': session.get('turn_count', 1),
                    'conversation_started': session.get('conversation_started', False),
                    'attempts_count': session.get('attempts_count', 0)
                }
                
                response_result = self.openai_service.generate_roleplay_response(
                    user_input,
                    session['conversation_history'],
                    enhanced_context,
                    session['current_stage']
                )
                
                if response_result.get('success'):
                    return response_result['response']
            
            # Enhanced fallback response
            return self._get_enhanced_fallback_response(session, evaluation, user_input)
            
        except Exception as e:
            logger.error(f"Error generating contextual AI response: {e}")
            return self._get_enhanced_fallback_response(session, evaluation, user_input)
    
    def _get_enhanced_fallback_response(self, session: Dict, evaluation: Dict, user_input: str) -> str:
        """FIXED: More encouraging and helpful fallback responses"""
        current_stage = session['current_stage']
        turn_count = session.get('turn_count', 1)
        user_input_lower = user_input.lower().strip()
        word_count = len(user_input.split())
        
        # Very encouraging responses for early attempts
        if turn_count <= 2:
            if word_count <= 2:
                encouraging_responses = [
                    "Hi there. What can I do for you?",
                    "Hello. What's this regarding?",
                    "Good morning. How can I help you?",
                    "Hi. What's this about?"
                ]
                return random.choice(encouraging_responses)
            else:
                return "I'm listening. Go ahead."
        
        # Responses based on stage and quality
        passed = evaluation.get('passed', False)
        prospect_warmth = session.get('prospect_warmth', 0)
        
        # Get appropriate responses from config
        responses_map = self.config.PROSPECT_BEHAVIOR['response_patterns']
        
        if current_stage == 'opener_evaluation':
            if passed and prospect_warmth >= 2:
                responses = responses_map.get('excellent_opener', ["That sounds interesting. Tell me more."])
            elif passed or word_count >= 5:
                responses = responses_map.get('good_opener', ["Okay, I'm listening.", "Go ahead.", "What do you mean?"])
            else:
                # Very encouraging for basic attempts
                responses = [
                    "What's this about?", 
                    "I'm listening.", 
                    "Go ahead.", 
                    "Tell me more.",
                    "Okay, continue.",
                    "What do you need?"
                ]
        
        elif current_stage in ['early_objection', 'objection_handling']:
            if passed and prospect_warmth >= 2:
                responses = responses_map.get('excellent_objection_handling', ["That makes sense. Continue."])
            else:
                responses = [
                    "Go ahead.", 
                    "I'm still listening.", 
                    "Continue.", 
                    "Tell me more.",
                    "What do you mean?",
                    "Okay."
                ]
        
        elif current_stage == 'mini_pitch':
            if passed and prospect_warmth >= 3:
                responses = responses_map.get('excellent_pitch', ["That's interesting. How does that work?"])
            else:
                responses = [
                    "Tell me more.", 
                    "I'm following.", 
                    "Okay.", 
                    "Continue.",
                    "That sounds interesting.",
                    "Go on."
                ]
        else:
            responses = [
                "I see.", 
                "Continue.", 
                "Tell me more.", 
                "Go on.",
                "That's interesting.",
                "Okay, what else?"
            ]
        
        return random.choice(responses)
    
    # ===== FIXED FINAL SCORE CALCULATION =====
    
    def _calculate_final_score(self, session: Dict) -> int:
        """FIXED: Much more accurate final score calculation"""
        turn_count = session.get('turn_count', 0)
        conversation_quality = session.get('conversation_quality', 0)
        prospect_warmth = session.get('prospect_warmth', 0)
        stages_completed = len(session.get('stages_completed', []))
        conversation_started = session.get('conversation_started', False)
        attempts_count = session.get('attempts_count', 0)
        
        logger.info(f"Calculating final score: turns={turn_count}, quality={conversation_quality}, warmth={prospect_warmth}, stages={stages_completed}")
        
        # FIXED: Much more realistic scoring
        if turn_count <= 1:
            # Single turn only
            if conversation_started:
                base_score = 25  # Basic attempt
            else:
                base_score = 15  # Minimal effort
        elif turn_count <= 2:
            # Very short conversation
            base_score = max(20, conversation_quality * 0.6)
        elif turn_count <= 4:
            # Short but meaningful attempt
            base_score = max(30, conversation_quality * 0.8)
        else:
            # Proper conversation length
            base_score = conversation_quality
        
        # Bonuses for progress
        stage_bonus = stages_completed * 5  # Reduced from 8
        warmth_bonus = prospect_warmth * 2   # Reduced from 3
        empathy_bonus = 8 if session.get('empathy_shown', False) else 0
        specificity_bonus = 8 if session.get('specific_benefits_mentioned', False) else 0
        
        # Attempt bonus (reward for trying)
        attempt_bonus = min(attempts_count * 2, 10)
        
        # Calculate total
        total_score = base_score + stage_bonus + warmth_bonus + empathy_bonus + specificity_bonus + attempt_bonus
        
        # Apply realistic limits
        if turn_count <= 1:
            total_score = min(total_score, 35)  # Cap for single turn
        elif turn_count <= 3:
            total_score = min(total_score, 50)  # Cap for very short
        elif turn_count <= 5:
            total_score = min(total_score, 70)  # Cap for short
        
        # Ensure minimum for effort
        if conversation_started and attempts_count >= 1:
            total_score = max(total_score, 20)
        else:
            total_score = max(total_score, 10)
        
        # Final bounds
        final_score = min(100, max(10, int(total_score)))
        
        logger.info(f"Final score calculation: base={base_score}, bonuses={stage_bonus + warmth_bonus + empathy_bonus + specificity_bonus + attempt_bonus}, final={final_score}")
        
        return final_score
    
    # ===== KEEP ALL OTHER EXISTING METHODS =====
    
    def _update_conversation_metrics(self, session: Dict, evaluation: Dict):
        """Update enhanced conversation tracking metrics"""
        try:
            # Update cumulative score
            weighted_score = evaluation.get('weighted_score', evaluation.get('score', 0))
            session['cumulative_score'] += weighted_score
            
            # Update conversation quality (moving average, more generous)
            turn_quality = (weighted_score / 4) * 100  # Convert to percentage
            total_turns = session['turn_count']
            current_quality = session.get('conversation_quality', 0)
            
            # More generous quality calculation
            if total_turns == 1:
                session['conversation_quality'] = max(turn_quality, 25)  # Minimum for first turn
            else:
                new_quality = ((current_quality * (total_turns - 1)) + turn_quality) / total_turns
                session['conversation_quality'] = max(new_quality, current_quality * 0.8)  # Prevent dramatic drops
            
            # Track empathy
            criteria_met = evaluation.get('criteria_met', [])
            if 'shows_empathy' in criteria_met or 'acknowledges_gracefully' in criteria_met:
                session['empathy_shown'] = True
            
            # Track specific benefits
            if 'specific_benefit' in criteria_met or 'outcome_focused' in criteria_met:
                session['specific_benefits_mentioned'] = True
            
            # Update prospect warmth based on performance (more generous)
            if evaluation.get('passed', False):
                session['prospect_warmth'] = min(10, session.get('prospect_warmth', 0) + 1.5)
            elif weighted_score >= 2:  # Decent attempt
                session['prospect_warmth'] = min(10, session.get('prospect_warmth', 0) + 0.8)
            elif weighted_score >= 1.5:  # Some effort
                session['prospect_warmth'] = min(10, session.get('prospect_warmth', 0) + 0.3)
            # No penalty for poor attempts - just no gain
            
            # Update conversation flow score
            if evaluation.get('passed', False) and session['turn_count'] > 1:
                session['conversation_flow_score'] = min(100, session.get('conversation_flow_score', 0) + 15)
            elif weighted_score >= 2:
                session['conversation_flow_score'] = min(100, session.get('conversation_flow_score', 0) + 8)
            
        except Exception as e:
            logger.error(f"Error updating conversation metrics: {e}")
    
    def _update_session_state_enhanced(self, session: Dict, evaluation: Dict):
        """Enhanced: Update session state with better progression logic"""
        current_stage = session['current_stage']
        should_progress = False
        
        # Enhanced stage progression logic (more lenient)
        if current_stage == 'phone_pickup':
            should_progress = True  # Always progress after phone pickup
        elif current_stage == 'opener_evaluation':
            # Progress after 2 tries OR if decent attempt
            score = evaluation.get('weighted_score', evaluation.get('score', 0))
            if score >= 1.5 or session['stage_turn_count'] >= 2:
                should_progress = True
        elif current_stage == 'early_objection':
            should_progress = True  # Always progress from objection to handling
        elif current_stage == 'objection_handling':
            # Progress more easily
            score = evaluation.get('weighted_score', evaluation.get('score', 0))
            if score >= 1.2 or session['stage_turn_count'] >= 2:
                should_progress = True
        elif current_stage == 'mini_pitch':
            # Progress after reasonable attempt
            score = evaluation.get('weighted_score', evaluation.get('score', 0))
            if score >= 1.0 or session['stage_turn_count'] >= 2:
                should_progress = True
        elif current_stage == 'soft_discovery':
            # Progress after question attempt
            if session['stage_turn_count'] >= 1:
                should_progress = True
        
        if should_progress:
            next_stage = self.config.STAGE_FLOW.get(current_stage)
            if next_stage and next_stage != current_stage:
                # Mark current stage as completed
                if current_stage not in session.get('stages_completed', []):
                    session.setdefault('stages_completed', []).append(current_stage)
                
                session['current_stage'] = next_stage
                session['stage_progression'].append(next_stage)
                session['stage_turn_count'] = 0
                
                logger.info(f"Session {session['session_id']}: Progressed from {current_stage} to {next_stage}")
    
    # Keep all other existing methods unchanged...
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End session with proper scoring based on conversation length"""
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
            
            # FIXED: Better final scoring
            final_score = self._calculate_final_score(session)
            
            # Generate coaching
            coaching_result = self._generate_comprehensive_coaching(session)
            
            # Update coaching with calculated score
            if coaching_result.get('success'):
                coaching_result['score'] = final_score
            
            # Calculate success (more lenient)
            session_success = self._calculate_session_success_enhanced(session)
            
            result = {
                'success': True,
                'duration_minutes': duration_minutes,
                'session_success': session_success,
                'coaching': coaching_result.get('coaching', {}),
                'overall_score': final_score,
                'session_data': session,
                'roleplay_type': 'practice_enhanced',
                
                # Enhanced: Additional metrics
                'conversation_metrics': {
                    'stages_completed': len(session.get('stages_completed', [])),
                    'prospect_warmth': session.get('prospect_warmth', 0),
                    'empathy_shown': session.get('empathy_shown', False),
                    'specific_benefits': session.get('specific_benefits_mentioned', False),
                    'conversation_flow': session.get('conversation_flow_score', 0),
                    'total_turns': session.get('turn_count', 0),
                    'conversation_started': session.get('conversation_started', False),
                    'attempts_count': session.get('attempts_count', 0)
                }
            }
            
            # Clean up session
            del self.active_sessions[session_id]
            
            return result
            
        except Exception as e:
            logger.error(f"Error ending Roleplay 1.1 session: {e}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_session_success_enhanced(self, session: Dict) -> bool:
        """Calculate if session was successful (more lenient criteria)"""
        turn_count = session.get('turn_count', 0)
        conversation_quality = session.get('conversation_quality', 0)
        conversation_started = session.get('conversation_started', False)
        
        # Success if:
        # - At least 3 turns and conversation started
        # - OR quality above 40%
        # - OR made it through multiple stages
        stages_completed = len(session.get('stages_completed', []))
        
        if turn_count >= 3 and conversation_started:
            return True
        
        if conversation_quality >= 40:
            return True
            
        if stages_completed >= 2:
            return True
        
        return False
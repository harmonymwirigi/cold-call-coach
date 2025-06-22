# ===== FIXED: services/roleplay/roleplay_1_1.py =====

import random
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from .base_roleplay import BaseRoleplay
from .configs.roleplay_1_1_config import Roleplay11Config

logger = logging.getLogger(__name__)

class Roleplay11(BaseRoleplay):
    """FIXED Roleplay 1.1 - Practice Mode with Enhanced Logic"""
    
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
                'roleplay_id': self.config.ROLEPLAY_ID,
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
                
                # ENHANCED: Additional tracking
                'prospect_warmth': 0,           # How warmed up the prospect is
                'empathy_shown': False,         # Whether user showed empathy
                'specific_benefits_mentioned': False,  # Whether user gave specific benefits
                'conversation_flow_score': 0,   # How natural the conversation feels
                'last_evaluation': None,       # Store last evaluation for context
                'cumulative_score': 0          # Running total for final scoring
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
        """ENHANCED: Process user input with better logic"""
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
            
            # Add user input to conversation
            session['conversation_history'].append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage']
            })
            
            # ENHANCED: Evaluate user input with weighted scoring
            evaluation_stage = self._get_evaluation_stage(session['current_stage'])
            evaluation = self._evaluate_user_input_enhanced(session, user_input, evaluation_stage)
            
            # Store evaluation for context
            session['last_evaluation'] = evaluation
            
            # ENHANCED: Update conversation metrics
            self._update_conversation_metrics(session, evaluation)
            
            # ENHANCED: Check if should hang up (with better logic)
            should_hang_up = self._should_hang_up_enhanced(session, evaluation, user_input)
            
            if should_hang_up:
                ai_response = self._get_contextual_hangup_response(session, evaluation)
                session['hang_up_triggered'] = True
                call_continues = False
            else:
                # ENHANCED: Generate contextual AI response
                ai_response = self._generate_contextual_ai_response(session, user_input, evaluation)
                
                # ENHANCED: Update session state with better logic
                self._update_session_state_enhanced(session, evaluation)
                
                # Check if call should continue
                call_continues = self._should_call_continue_enhanced(session, evaluation)
            
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
                'prospect_warmth': session.get('prospect_warmth', 0)
            }
            
        except Exception as e:
            logger.error(f"Error processing Roleplay 1.1 input: {e}")
            return {'success': False, 'error': str(e), 'call_continues': False}
    
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """ENHANCED: End session with comprehensive scoring"""
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
            
            # ENHANCED: Generate comprehensive coaching
            coaching_result = self._generate_comprehensive_coaching(session)
            
            # ENHANCED: Calculate success with multiple factors
            session_success = self._calculate_session_success_enhanced(session)
            
            result = {
                'success': True,
                'duration_minutes': duration_minutes,
                'session_success': session_success,
                'coaching': coaching_result.get('coaching', {}),
                'overall_score': coaching_result.get('score', 50),
                'session_data': session,
                'roleplay_type': 'practice_enhanced',
                
                # ENHANCED: Additional metrics
                'conversation_metrics': {
                    'stages_completed': len(session.get('stages_completed', [])),
                    'prospect_warmth': session.get('prospect_warmth', 0),
                    'empathy_shown': session.get('empathy_shown', False),
                    'specific_benefits': session.get('specific_benefits_mentioned', False),
                    'conversation_flow': session.get('conversation_flow_score', 0)
                }
            }
            
            # Clean up session
            del self.active_sessions[session_id]
            
            return result
            
        except Exception as e:
            logger.error(f"Error ending Roleplay 1.1 session: {e}")
            return {'success': False, 'error': str(e)}
    
    # ===== ENHANCED PRIVATE METHODS =====
    
    def _get_contextual_initial_response(self, user_context: Dict) -> str:
        """Generate contextual initial response based on user context"""
        name = user_context.get('first_name', 'Alex')
        title = user_context.get('prospect_job_title', 'Manager')
        
        responses = [
            f"Hello?",
            f"Good morning, this is {name}.",
            f"{name} speaking.",
            f"Yes?",
            f"Hi there."
        ]
        
        return random.choice(responses)
    
    def _evaluate_user_input_enhanced(self, session: Dict, user_input: str, evaluation_stage: str) -> Dict[str, Any]:
        """ENHANCED: Evaluate with weighted scoring and context"""
        try:
            if self.is_openai_available():
                # Use OpenAI with enhanced prompting
                evaluation = self.openai_service.evaluate_user_input(
                    user_input,
                    session['conversation_history'],
                    evaluation_stage
                )
                
                # ENHANCED: Add weighted scoring
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
    
    def _apply_weighted_scoring(self, evaluation: Dict, stage: str) -> Dict[str, Any]:
        """Apply weighted scoring based on criteria importance"""
        try:
            criteria = self.config.EVALUATION_CRITERIA.get(stage, {}).get('criteria', [])
            criteria_met = evaluation.get('criteria_met', [])
            
            weighted_score = 0
            total_weight = 0
            
            for criterion in criteria:
                weight = criterion.get('weight', 1.0)
                total_weight += weight
                
                if criterion['name'] in criteria_met:
                    weighted_score += weight
            
            # Normalize to 0-4 scale
            if total_weight > 0:
                normalized_score = (weighted_score / total_weight) * 4
            else:
                normalized_score = evaluation.get('score', 0)
            
            evaluation['weighted_score'] = round(normalized_score, 1)
            evaluation['score'] = round(normalized_score)  # Update main score
            
            # Check if passed with weighted threshold
            threshold = self.config.EVALUATION_CRITERIA.get(stage, {}).get('pass_threshold', 2)
            evaluation['passed'] = normalized_score >= threshold
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error applying weighted scoring: {e}")
            return evaluation
    
    def _enhanced_basic_evaluation(self, user_input: str, evaluation_stage: str, session: Dict) -> Dict[str, Any]:
        """Enhanced basic evaluation with better logic"""
        score = 0
        weighted_score = 0
        criteria_met = []
        user_input_lower = user_input.lower().strip()
        
        # Get criteria for this stage
        stage_criteria = self.config.EVALUATION_CRITERIA.get(evaluation_stage, {}).get('criteria', [])
        
        for criterion in stage_criteria:
            weight = criterion.get('weight', 1.0)
            met = False
            
            # Check keywords
            if 'keywords' in criterion:
                if any(keyword in user_input_lower for keyword in criterion['keywords']):
                    met = True
            
            # Check negative indicators
            if 'negative_keywords' in criterion:
                if any(neg_keyword in user_input_lower for neg_keyword in criterion['negative_keywords']):
                    met = False
            
            # Check word count limits
            if 'max_words' in criterion:
                word_count = len(user_input.split())
                if word_count <= criterion['max_words']:
                    met = True
            
            # Check for contractions (natural tone)
            if criterion.get('check_contractions'):
                contractions = ["i'm", "don't", "can't", "we're", "you're", "won't", "isn't"]
                if any(contraction in user_input_lower for contraction in contractions):
                    met = True
            
            if met:
                criteria_met.append(criterion['name'])
                score += 1
                weighted_score += weight
        
        # Calculate normalized scores
        total_possible_weight = sum(c.get('weight', 1.0) for c in stage_criteria)
        if total_possible_weight > 0:
            normalized_weighted_score = (weighted_score / total_possible_weight) * 4
        else:
            normalized_weighted_score = score
        
        # Check pass threshold
        threshold = self.config.EVALUATION_CRITERIA.get(evaluation_stage, {}).get('pass_threshold', 2)
        passed = normalized_weighted_score >= threshold
        
        return {
            'score': round(normalized_weighted_score),
            'weighted_score': round(normalized_weighted_score, 1),
            'passed': passed,
            'criteria_met': criteria_met,
            'feedback': f'Enhanced evaluation: {len(criteria_met)} criteria met for {evaluation_stage}',
            'should_continue': True,
            'next_action': 'continue',
            'hang_up_probability': 0.3 if score <= 1 else 0.1,
            'source': 'enhanced_basic',
            'stage': evaluation_stage
        }
    
    def _update_conversation_metrics(self, session: Dict, evaluation: Dict):
        """Update enhanced conversation tracking metrics"""
        try:
            # Update cumulative score
            weighted_score = evaluation.get('weighted_score', evaluation.get('score', 0))
            session['cumulative_score'] += weighted_score
            
            # Update conversation quality (moving average)
            turn_quality = (weighted_score / 4) * 100  # Convert to percentage
            total_turns = session['turn_count']
            current_quality = session.get('conversation_quality', 0)
            
            session['conversation_quality'] = ((current_quality * (total_turns - 1)) + turn_quality) / total_turns
            
            # Track empathy
            criteria_met = evaluation.get('criteria_met', [])
            if 'shows_empathy' in criteria_met or 'acknowledges_gracefully' in criteria_met:
                session['empathy_shown'] = True
            
            # Track specific benefits
            if 'specific_benefit' in criteria_met or 'outcome_focused' in criteria_met:
                session['specific_benefits_mentioned'] = True
            
            # Update prospect warmth based on performance
            if evaluation.get('passed', False):
                session['prospect_warmth'] = min(10, session.get('prospect_warmth', 0) + 1)
            elif weighted_score <= 1:
                session['prospect_warmth'] = max(0, session.get('prospect_warmth', 0) - 1)
            
            # Update conversation flow score
            if evaluation.get('passed', False) and session['turn_count'] > 1:
                session['conversation_flow_score'] = min(100, session.get('conversation_flow_score', 0) + 10)
            
        except Exception as e:
            logger.error(f"Error updating conversation metrics: {e}")
    
    def _should_hang_up_enhanced(self, session: Dict, evaluation: Dict, user_input: str) -> bool:
        """ENHANCED: Better hang-up logic based on conversation flow"""
        current_stage = session['current_stage']
        
        # Never hang up on first interaction
        if session['turn_count'] <= 1:
            return False
        
        # Don't hang up if prospect is warming up
        prospect_warmth = session.get('prospect_warmth', 0)
        if prospect_warmth >= 3:
            return False
        
        # Don't hang up if conversation quality is good
        conversation_quality = session.get('conversation_quality', 0)
        if conversation_quality >= 60:
            return False
        
        # Get base hang-up probability
        weighted_score = evaluation.get('weighted_score', evaluation.get('score', 0))
        
        # Immediate hang-up triggers
        if current_stage == 'opener_evaluation' and weighted_score <= 1 and not session.get('empathy_shown'):
            hang_up_prob = self.config.HANGUP_TRIGGERS['immediate_hangup']['no_empathy_opener']
        elif weighted_score <= 0.5:
            hang_up_prob = self.config.HANGUP_TRIGGERS['immediate_hangup']['aggressive_response']
        else:
            # Gradual hang-up based on performance
            base_prob = self.config.HANGUP_TRIGGERS['gradual_hangup'].get('poor_opener', 0.3)
            
            # Adjust based on conversation quality
            if conversation_quality < 30:
                hang_up_prob = base_prob * 1.5
            elif conversation_quality < 50:
                hang_up_prob = base_prob
            else:
                hang_up_prob = base_prob * 0.5
        
        # Reduce hang-up chance as conversation progresses
        if session['turn_count'] >= 4:
            hang_up_prob *= 0.6
        
        return random.random() < hang_up_prob
    
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
                    'stage_performance': evaluation
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
            return self._get_enhanced_fallback_response(session, evaluation)
            
        except Exception as e:
            logger.error(f"Error generating contextual AI response: {e}")
            return self._get_enhanced_fallback_response(session, evaluation)
    
    def _get_enhanced_fallback_response(self, session: Dict, evaluation: Dict) -> str:
        """Get enhanced fallback response based on context"""
        current_stage = session['current_stage']
        passed = evaluation.get('passed', False)
        prospect_warmth = session.get('prospect_warmth', 0)
        
        # Get appropriate responses from config
        responses_map = self.config.PROSPECT_BEHAVIOR['response_patterns']
        
        if current_stage == 'opener_evaluation':
            if passed and prospect_warmth >= 2:
                responses = responses_map['excellent_opener']
            elif passed:
                responses = responses_map['good_opener']
            else:
                responses = responses_map['poor_opener']
        elif current_stage in ['early_objection', 'objection_handling']:
            if passed and prospect_warmth >= 2:
                responses = responses_map['excellent_objection_handling']
            elif passed:
                responses = responses_map['good_objection_handling']
            else:
                responses = responses_map['poor_objection_handling']
        elif current_stage == 'mini_pitch':
            if passed and prospect_warmth >= 3:
                responses = responses_map['excellent_pitch']
            elif passed:
                responses = responses_map['good_pitch']
            else:
                responses = responses_map['poor_pitch']
        else:
            responses = ["I see.", "Continue.", "Tell me more."]
        
        return random.choice(responses)
    
    def _update_session_state_enhanced(self, session: Dict, evaluation: Dict):
        """ENHANCED: Update session state with better progression logic"""
        current_stage = session['current_stage']
        should_progress = False
        
        # Enhanced stage progression logic
        if current_stage == 'phone_pickup':
            should_progress = True
        elif current_stage == 'opener_evaluation':
            # Progress if passed OR if they've had 2 tries
            if evaluation.get('passed', False) or session['stage_turn_count'] >= 2:
                should_progress = True
        elif current_stage == 'early_objection':
            should_progress = True  # Always progress from objection to handling
        elif current_stage == 'objection_handling':
            # Progress if passed OR if prospect is warmed up OR after 3 tries
            prospect_warmth = session.get('prospect_warmth', 0)
            if evaluation.get('passed', False) or prospect_warmth >= 2 or session['stage_turn_count'] >= 3:
                should_progress = True
        elif current_stage == 'mini_pitch':
            # Progress if decent score OR after 2 tries
            score = evaluation.get('weighted_score', evaluation.get('score', 0))
            if score >= 2 or session['stage_turn_count'] >= 2:
                should_progress = True
        elif current_stage == 'soft_discovery':
            # Progress to extended conversation after question
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
    
    def _should_call_continue_enhanced(self, session: Dict, evaluation: Dict) -> bool:
        """ENHANCED: Determine if call should continue with better logic"""
        if session.get('hang_up_triggered'):
            return False
        
        if session['current_stage'] == 'call_ended':
            return False
        
        # Check conversation limits
        max_turns = self.config.CONVERSATION_LIMITS['max_total_turns']
        if session['turn_count'] >= max_turns:
            return False
        
        # Extended conversation logic
        if session['current_stage'] == 'extended_conversation':
            conversation_quality = session.get('conversation_quality', 50)
            prospect_warmth = session.get('prospect_warmth', 0)
            
            # Continue if quality is good and prospect is engaged
            if conversation_quality >= 60 and prospect_warmth >= 3:
                return session['stage_turn_count'] < 6
            elif conversation_quality >= 40:
                return session['stage_turn_count'] < 4
            else:
                return session['stage_turn_count'] < 2
        
        return True
    
    def _generate_comprehensive_coaching(self, session: Dict) -> Dict[str, Any]:
        """Generate comprehensive coaching using enhanced data"""
        try:
            if self.is_openai_available():
                return self.openai_service.generate_coaching_feedback(
                    session['conversation_history'],
                    session.get('rubric_scores', {}),
                    session['user_context']
                )
            else:
                return self._enhanced_basic_coaching(session)
                
        except Exception as e:
            logger.error(f"Enhanced coaching generation error: {e}")
            return self._enhanced_basic_coaching(session)
    
    def _enhanced_basic_coaching(self, session: Dict) -> Dict[str, Any]:
        """Enhanced basic coaching with detailed feedback"""
        conversation_quality = session.get('conversation_quality', 50)
        stages_completed = len(session.get('stages_completed', []))
        empathy_shown = session.get('empathy_shown', False)
        specific_benefits = session.get('specific_benefits_mentioned', False)
        prospect_warmth = session.get('prospect_warmth', 0)
        
        # Calculate enhanced score
        base_score = int(conversation_quality)
        stage_bonus = stages_completed * 8
        empathy_bonus = 10 if empathy_shown else 0
        specificity_bonus = 10 if specific_benefits else 0
        warmth_bonus = prospect_warmth * 2
        
        total_score = min(100, max(30, base_score + stage_bonus + empathy_bonus + specificity_bonus + warmth_bonus))
        
        # Generate detailed coaching
        coaching = {}
        
        # Sales coaching
        if empathy_shown and specific_benefits:
            coaching['sales_coaching'] = 'Excellent! You showed empathy and gave specific benefits. This builds trust and demonstrates value.'
        elif empathy_shown:
            coaching['sales_coaching'] = 'Good empathy! Next time, be more specific about the benefits you provide.'
        elif specific_benefits:
            coaching['sales_coaching'] = 'Good specificity! Start with more empathy to build rapport first.'
        else:
            coaching['sales_coaching'] = 'Focus on empathy first, then give specific benefits. Try: "I know this is unexpected, but we help companies like yours save 30% on..."'
        
        # Grammar and structure
        if conversation_quality >= 70:
            coaching['grammar_coaching'] = 'Your communication was clear and well-structured.'
        else:
            coaching['grammar_coaching'] = 'Work on clearer, more concise communication. Use shorter sentences.'
        
        # Vocabulary coaching
        if specific_benefits:
            coaching['vocabulary_coaching'] = 'Great use of outcome-focused language! Specific benefits resonate better than features.'
        else:
            coaching['vocabulary_coaching'] = 'Use more outcome-focused language. Instead of features, mention specific results and benefits.'
        
        # Pronunciation (inferred)
        coaching['pronunciation_coaching'] = 'Focus on speaking clearly and at a moderate pace for better impact.'
        
        # Rapport and assertiveness
        if prospect_warmth >= 5:
            coaching['rapport_assertiveness'] = 'Excellent rapport building! The prospect warmed up to you during the conversation.'
        elif empathy_shown:
            coaching['rapport_assertiveness'] = 'Good empathy shown. Continue building rapport while being confident about your value.'
        else:
            coaching['rapport_assertiveness'] = 'Show more empathy to build rapport. Acknowledge you\'re interrupting their day before pitching.'
        
        return {
            'success': True,
            'coaching': coaching,
            'score': total_score,
            'source': 'enhanced_basic',
            'performance_summary': {
                'empathy_shown': empathy_shown,
                'specific_benefits': specific_benefits,
                'prospect_warmth': prospect_warmth,
                'stages_completed': stages_completed
            }
        }
    
    def _calculate_session_success_enhanced(self, session: Dict) -> bool:
        """Calculate session success with multiple factors"""
        conversation_quality = session.get('conversation_quality', 0)
        stages_completed = session.get('stages_completed', [])
        total_turns = session.get('turn_count', 0)
        prospect_warmth = session.get('prospect_warmth', 0)
        empathy_shown = session.get('empathy_shown', False)
        
        # Multiple success criteria
        reached_pitch = 'mini_pitch' in stages_completed or session.get('current_stage') in ['mini_pitch', 'soft_discovery', 'extended_conversation']
        sufficient_length = total_turns >= self.config.CONVERSATION_LIMITS['min_turns_for_success']
        good_quality = conversation_quality >= 50
        warmed_prospect = prospect_warmth >= 3
        completed_most_stages = len(stages_completed) >= 3
        
        # Success if multiple criteria met
        success_factors = [reached_pitch, sufficient_length, good_quality, warmed_prospect, completed_most_stages]
        return sum(success_factors) >= 3  # Need at least 3 out of 5 factors
    
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
    
    def _handle_silence_trigger(self, session: Dict, trigger: str) -> Dict[str, Any]:
        """Handle silence triggers (same as original but with enhanced context)"""
        if trigger == '[SILENCE_IMPATIENCE]':
            impatience_phrases = [
                "Hello? Are you still with me?", 
                "Can you hear me?",
                "Just checking you're there…", 
                "Still on the line?",
                "I don't have much time for this."
            ]
            response = random.choice(impatience_phrases)
            
            session['conversation_history'].append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'trigger': 'silence_impatience'
            })
            
            return {
                'success': True,
                'ai_response': response,
                'call_continues': True,
                'evaluation': {'trigger': 'impatience'},
                'session_state': session['current_stage'],
                'turn_count': session['turn_count']
            }
        
        elif trigger == '[SILENCE_HANGUP]':
            response = "I don't have time for this. Goodbye."
            session['hang_up_triggered'] = True
            
            session['conversation_history'].append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'trigger': 'silence_hangup'
            })
            
            return {
                'success': True,
                'ai_response': response,
                'call_continues': False,
                'evaluation': {'trigger': 'hangup'},
                'session_state': session['current_stage'],
                'turn_count': session['turn_count']
            }
    
    def _get_contextual_hangup_response(self, session: Dict, evaluation: Dict) -> str:
        """Get contextual hang-up response based on performance"""
        current_stage = session['current_stage']
        empathy_shown = session.get('empathy_shown', False)
        
        if current_stage == 'opener_evaluation' and not empathy_shown:
            responses = [
                "I'm not interested. Don't call here again.",
                "How did you get this number? Remove it from your list.",
                "We don't take cold calls."
            ]
        elif current_stage == 'objection_handling':
            responses = [
                "I already told you I'm not interested.",
                "You're not listening. Goodbye.",
                "This is exactly why I hate cold calls."
            ]
        else:
            responses = [
                "I have to go. Goodbye.",
                "Not interested. Thanks.",
                "We're all set. Don't call again."
            ]
        
        return random.choice(responses)
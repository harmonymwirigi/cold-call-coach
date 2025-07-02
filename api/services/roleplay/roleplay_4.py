# ===== services/roleplay/roleplay_4.py =====
# Full Cold Call Simulation - Complete end-to-end call practice

import random
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from .base_roleplay import BaseRoleplay
from .configs.roleplay_4_config import Roleplay4Config

logger = logging.getLogger(__name__)

class Roleplay4(BaseRoleplay):
    """
    Roleplay 4 - Full Cold Call Simulation
    Complete end-to-end cold call from phone pickup to close
    """
    
    def __init__(self, openai_service=None):
        super().__init__(openai_service)
        self.config = Roleplay4Config()
        self.roleplay_id = self.config.ROLEPLAY_ID

    def get_roleplay_info(self) -> Dict[str, Any]:
        return {
            'id': self.config.ROLEPLAY_ID,
            'name': self.config.NAME,
            'description': self.config.DESCRIPTION,
            'type': 'simulation',
            'features': {
                'ai_evaluation': self.is_openai_available(),
                'complete_simulation': True,
                'extended_conversation': True,
                'advanced_scenarios': True,
                'comprehensive_coaching': True,
                'realistic_prospects': True
            }
        }

    def create_session(self, user_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Creates a full cold call simulation session"""
        session_id = f"{user_id}_{self.config.ROLEPLAY_ID}_{mode}_{int(datetime.now().timestamp())}"
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'roleplay_id': self.config.ROLEPLAY_ID,
            'mode': 'simulation',
            'started_at': datetime.now(timezone.utc).isoformat(),
            'user_context': user_context,
            'session_active': True,
            
            # Complete simulation state
            'conversation_history': [],
            'current_stage': 'phone_pickup',
            'stage_progression': ['phone_pickup'],
            'turn_count': 0,
            'stage_turn_count': 0,
            'stages_completed': [],
            
            # Extended conversation tracking
            'phone_pickup_completed': False,
            'opener_delivered': False,
            'objections_encountered': [],
            'objections_handled': 0,
            'discovery_questions_asked': 0,
            'pain_points_identified': [],
            'value_propositions_given': [],
            'qualification_completed': False,
            'demo_requested': False,
            'next_steps_defined': False,
            'call_outcome': 'in_progress',
            
            # Simulation-specific features
            'prospect_personality': self._generate_prospect_personality(),
            'company_scenario': self._generate_company_scenario(user_context),
            'conversation_depth': 0,
            'relationship_building': 0,
            'trust_level': 0,
            'interest_level': 0,
            'decision_timeline': None,
            'budget_discussed': False,
            'stakeholders_identified': [],
            
            # Performance tracking
            'rubric_scores': {},
            'conversation_quality': 0,
            'stage_performance': {},
            'critical_successes': [],
            'areas_for_improvement': [],
            'hang_up_triggered': False,
            'simulation_complexity': 'standard'
        }
        
        self.active_sessions[session_id] = session_data
        
        # Generate contextual initial response based on scenario
        initial_response = self._get_contextual_initial_response(session_data)
        
        session_data['conversation_history'].append({
            'role': 'assistant',
            'content': initial_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'phone_pickup',
            'prospect_state': 'answered_phone'
        })
        
        logger.info(f"Full simulation session {session_id} created for user {user_id}")
        return {
            'success': True,
            'session_id': session_id,
            'initial_response': initial_response,
            'roleplay_info': self.get_roleplay_info(),
            'simulation_info': {
                'prospect_personality': session_data['prospect_personality']['type'],
                'company_scenario': session_data['company_scenario']['industry'],
                'complexity_level': session_data['simulation_complexity']
            }
        }

    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input for complete cold call simulation"""
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
            
            logger.info(f"Simulation Turn #{session['turn_count']}: Processing '{user_input[:50]}...'")
            
            # Advanced evaluation based on current stage
            evaluation = self._evaluate_simulation_input(session, user_input)
            
            # Update simulation state
            self._update_simulation_state(session, evaluation, user_input)
            
            # Check for hang-up conditions (more realistic in simulation)
            should_hang_up = self._should_hang_up_simulation(session, evaluation, user_input)
            
            if should_hang_up:
                ai_response = self._get_contextual_hangup_response(session, evaluation)
                return self._handle_call_failure(session, "Call ended by prospect")
            
            # Generate advanced AI response
            ai_response = self._generate_simulation_response(session, user_input, evaluation)
            
            # Update session progression
            self._update_session_progression(session, evaluation)
            
            # Check if call should continue (longer conversations in simulation)
            call_continues = self._should_call_continue_simulation(session, evaluation)
            
            # Add AI response to conversation
            session['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': session['current_stage'],
                'evaluation': evaluation,
                'prospect_state': self._get_prospect_state(session)
            })
            
            if not call_continues:
                # Determine call outcome
                if self._determine_call_success(session):
                    return self._handle_call_success(session)
                else:
                    return self._handle_call_failure(session, "Call ended without clear next steps")
            
            return {
                'success': True,
                'ai_response': ai_response,
                'call_continues': call_continues,
                'evaluation': evaluation,
                'simulation_state': {
                    'current_stage': session['current_stage'],
                    'conversation_depth': session['conversation_depth'],
                    'trust_level': session['trust_level'],
                    'interest_level': session['interest_level'],
                    'stages_completed': len(session['stages_completed'])
                },
                'turn_count': session['turn_count']
            }
            
        except Exception as e:
            logger.error(f"Error processing simulation input: {e}")
            return {'success': False, 'error': str(e), 'call_continues': False}

    def _generate_prospect_personality(self) -> Dict[str, Any]:
        """Generate realistic prospect personality for simulation"""
        personalities = [
            {
                'type': 'analytical',
                'traits': ['data-driven', 'skeptical', 'thorough'],
                'communication_style': 'formal',
                'decision_speed': 'slow',
                'objection_style': 'detailed_questions',
                'trust_building': 'proof_required'
            },
            {
                'type': 'driver',
                'traits': ['results-focused', 'impatient', 'direct'],
                'communication_style': 'concise',
                'decision_speed': 'fast',
                'objection_style': 'blunt_objections',
                'trust_building': 'credibility_focused'
            },
            {
                'type': 'expressive',
                'traits': ['relationship-oriented', 'enthusiastic', 'collaborative'],
                'communication_style': 'friendly',
                'decision_speed': 'medium',
                'objection_style': 'concerns_sharing',
                'trust_building': 'rapport_based'
            },
            {
                'type': 'amiable',
                'traits': ['supportive', 'cautious', 'consensus-seeking'],
                'communication_style': 'polite',
                'decision_speed': 'slow',
                'objection_style': 'gentle_pushback',
                'trust_building': 'relationship_first'
            }
        ]
        
        return random.choice(personalities)

    def _generate_company_scenario(self, user_context: Dict) -> Dict[str, Any]:
        """Generate realistic company scenario"""
        industries = ['technology', 'healthcare', 'finance', 'manufacturing', 'retail']
        company_sizes = ['startup', 'small_business', 'mid_market', 'enterprise']
        current_challenges = [
            'scaling_operations', 'cost_reduction', 'efficiency_improvement',
            'digital_transformation', 'market_expansion', 'compliance_issues'
        ]
        
        return {
            'industry': random.choice(industries),
            'size': random.choice(company_sizes),
            'current_challenge': random.choice(current_challenges),
            'urgency_level': random.choice(['low', 'medium', 'high']),
            'budget_availability': random.choice(['limited', 'moderate', 'flexible']),
            'decision_process': random.choice(['individual', 'committee', 'multi_stage'])
        }

    def _evaluate_simulation_input(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Advanced evaluation for simulation mode"""
        try:
            if self.is_openai_available():
                # Enhanced evaluation with simulation context
                evaluation_context = {
                    'prospect_personality': session['prospect_personality'],
                    'company_scenario': session['company_scenario'],
                    'conversation_history': session['conversation_history'],
                    'current_stage': session['current_stage'],
                    'simulation_mode': True
                }
                
                evaluation = self.openai_service.evaluate_user_input(
                    user_input,
                    session['conversation_history'],
                    f"simulation_{session['current_stage']}",
                    context=evaluation_context
                )
                
                return evaluation
            else:
                return self._basic_simulation_evaluation(user_input, session)
                
        except Exception as e:
            logger.error(f"Simulation evaluation error: {e}")
            return self._basic_simulation_evaluation(user_input, session)

    def _basic_simulation_evaluation(self, user_input: str, session: Dict) -> Dict[str, Any]:
        """Basic evaluation for simulation mode"""
        score = 0
        criteria_met = []
        user_input_lower = user_input.lower().strip()
        current_stage = session['current_stage']
        
        # Stage-specific evaluation
        if current_stage == 'phone_pickup':
            # Opening evaluation
            if any(word in user_input_lower for word in ['hi', 'hello', 'calling from', 'my name']):
                score += 1
                criteria_met.append('proper_introduction')
            
            if any(word in user_input_lower for word in ['out of the blue', 'interrupting', 'busy']):
                score += 1
                criteria_met.append('shows_empathy')
        
        elif current_stage in ['objection_handling', 'discovery']:
            # Objection/discovery evaluation
            if any(word in user_input_lower for word in ['understand', 'appreciate', 'fair enough']):
                score += 1
                criteria_met.append('acknowledges_gracefully')
            
            if '?' in user_input or any(q in user_input_lower for q in ['how', 'what', 'when', 'why']):
                score += 1
                criteria_met.append('asks_questions')
        
        elif current_stage == 'value_proposition':
            # Value prop evaluation
            if any(word in user_input_lower for word in ['save', 'increase', 'reduce', 'improve']):
                score += 1
                criteria_met.append('outcome_focused')
        
        # General communication quality
        word_count = len(user_input.split())
        if word_count >= 10:
            score += 1
            criteria_met.append('sufficient_detail')
        
        # Natural language
        if any(word in user_input_lower for word in ["i'm", "we're", "don't", "can't"]):
            score += 1
            criteria_met.append('natural_tone')
        
        final_score = min(4, max(1, score))
        passed = final_score >= 2  # Lower threshold for simulation encouragement
        
        return {
            'score': int(final_score),
            'passed': passed,
            'criteria_met': criteria_met,
            'feedback': f'Simulation evaluation: {len(criteria_met)} criteria met',
            'stage_specific': True
        }

    def _update_simulation_state(self, session: Dict, evaluation: Dict, user_input: str):
        """Update advanced simulation state"""
        # Update conversation depth
        session['conversation_depth'] += 1
        
        # Update trust and interest based on performance
        if evaluation.get('passed', False):
            session['trust_level'] = min(10, session['trust_level'] + 1)
            session['interest_level'] = min(10, session['interest_level'] + 1)
        
        # Track specific accomplishments
        if 'asks_questions' in evaluation.get('criteria_met', []):
            session['discovery_questions_asked'] += 1
        
        if 'outcome_focused' in evaluation.get('criteria_met', []):
            session['value_propositions_given'].append(user_input[:100])
        
        # Update stage-specific tracking
        current_stage = session['current_stage']
        if current_stage == 'phone_pickup' and evaluation.get('passed'):
            session['opener_delivered'] = True
        elif current_stage == 'qualification' and evaluation.get('passed'):
            session['qualification_completed'] = True

    def _should_hang_up_simulation(self, session: Dict, evaluation: Dict, user_input: str) -> bool:
        """Realistic hang-up logic for simulation"""
        turn_count = session.get('turn_count', 1)
        prospect_personality = session.get('prospect_personality', {})
        
        # Different personalities have different patience levels
        patience_levels = {
            'driver': 0.3,      # High hang-up probability
            'analytical': 0.1,  # Low hang-up probability  
            'expressive': 0.15, # Medium hang-up probability
            'amiable': 0.05     # Very low hang-up probability
        }
        
        base_hangup_chance = patience_levels.get(prospect_personality.get('type', 'amiable'), 0.1)
        
        # Adjust based on performance
        weighted_score = evaluation.get('score', 2)
        trust_level = session.get('trust_level', 0)
        
        if weighted_score <= 1 and trust_level < 3 and turn_count >= 3:
            return random.random() < base_hangup_chance
        
        return False

    def _should_call_continue_simulation(self, session: Dict, evaluation: Dict) -> bool:
        """Determine if simulation should continue (allows longer conversations)"""
        if session.get('hang_up_triggered'):
            return False
        
        # Simulation allows longer conversations
        max_turns = 20  # Extended for complete simulation
        if session['turn_count'] >= max_turns:
            logger.info(f"Simulation ending: reached maximum turns ({max_turns})")
            return False
        
        # Continue if good progression
        stages_completed = len(session.get('stages_completed', []))
        conversation_depth = session.get('conversation_depth', 0)
        
        if stages_completed >= 5 and conversation_depth >= 10:
            logger.info(f"Simulation ending: good progression achieved")
            return False
        
        return True

    def _update_session_progression(self, session: Dict, evaluation: Dict):
        """Update session progression for simulation"""
        current_stage = session['current_stage']
        should_progress = False
        
        # More complex progression logic for simulation
        if current_stage == 'phone_pickup':
            if evaluation.get('passed') or session['stage_turn_count'] >= 2:
                should_progress = True
        elif current_stage == 'opener_evaluation':
            if evaluation.get('passed') or session['stage_turn_count'] >= 3:
                should_progress = True
        elif current_stage == 'objection_handling':
            if evaluation.get('passed') or session['stage_turn_count'] >= 3:
                should_progress = True
        elif current_stage == 'discovery':
            if session['discovery_questions_asked'] >= 2 or session['stage_turn_count'] >= 4:
                should_progress = True
        elif current_stage == 'value_proposition':
            if evaluation.get('passed') or session['stage_turn_count'] >= 3:
                should_progress = True
        elif current_stage == 'qualification':
            if evaluation.get('passed') or session['stage_turn_count'] >= 3:
                should_progress = True
        
        if should_progress:
            next_stage = self.config.STAGE_FLOW.get(current_stage)
            if next_stage and next_stage != current_stage:
                if current_stage not in session.get('stages_completed', []):
                    session.setdefault('stages_completed', []).append(current_stage)
                
                session['current_stage'] = next_stage
                session['stage_progression'].append(next_stage)
                session['stage_turn_count'] = 0
                
                logger.info(f"Simulation: Progressed from {current_stage} to {next_stage}")

    def _generate_simulation_response(self, session: Dict, user_input: str, evaluation: Dict) -> str:
        """Generate contextual response for simulation"""
        try:
            if self.is_openai_available():
                enhanced_context = {
                    **session['user_context'],
                    'prospect_personality': session['prospect_personality'],
                    'company_scenario': session['company_scenario'],
                    'trust_level': session.get('trust_level', 0),
                    'interest_level': session.get('interest_level', 0),
                    'conversation_depth': session.get('conversation_depth', 0),
                    'stage_performance': evaluation,
                    'simulation_mode': True
                }
                
                response_result = self.openai_service.generate_roleplay_response(
                    user_input,
                    session['conversation_history'],
                    enhanced_context,
                    session['current_stage']
                )
                
                if response_result.get('success'):
                    return response_result['response']
            
            return self._get_simulation_fallback_response(session, evaluation, user_input)
            
        except Exception as e:
            logger.error(f"Error generating simulation AI response: {e}")
            return self._get_simulation_fallback_response(session, evaluation, user_input)

    def _get_simulation_fallback_response(self, session: Dict, evaluation: Dict, user_input: str) -> str:
        """Simulation-specific fallback responses"""
        current_stage = session['current_stage']
        personality = session.get('prospect_personality', {}).get('type', 'amiable')
        turn_count = session.get('turn_count', 1)
        
        # Personality-based responses
        if personality == 'driver':
            responses = {
                'phone_pickup': ["What do you want?", "Make it quick.", "I'm busy."],
                'objection_handling': ["Get to the point.", "What's the bottom line?", "How much?"],
                'discovery': ["That's fine. What else?", "Okay. Continue.", "What's next?"]
            }
        elif personality == 'analytical':
            responses = {
                'phone_pickup': ["What company are you with?", "What data do you have?", "I need specifics."],
                'objection_handling': ["I need more information.", "What are your metrics?", "Send me case studies."],
                'discovery': ["That's interesting. Tell me more.", "What evidence supports that?", "How do you measure that?"]
            }
        elif personality == 'expressive':
            responses = {
                'phone_pickup': ["Oh, hi there!", "That sounds interesting!", "Tell me more!"],
                'objection_handling': ["I love learning about new solutions!", "That's exciting!", "How does that work?"],
                'discovery': ["Absolutely! We're always looking to improve!", "That's exactly what we need!", "I'm really interested!"]
            }
        else:  # amiable
            responses = {
                'phone_pickup': ["Sure, I can listen.", "Okay, go ahead.", "I have a few minutes."],
                'objection_handling': ["I understand. Continue.", "That makes sense.", "I appreciate that."],
                'discovery': ["That sounds reasonable.", "I'd like to know more.", "That could be helpful."]
            }
        
        stage_responses = responses.get(current_stage, ["I see.", "Continue.", "Tell me more."])
        return random.choice(stage_responses)

    def _get_prospect_state(self, session: Dict) -> Dict[str, Any]:
        """Get current prospect emotional/interest state"""
        return {
            'trust_level': session.get('trust_level', 0),
            'interest_level': session.get('interest_level', 0),
            'personality_type': session.get('prospect_personality', {}).get('type'),
            'stage': session.get('current_stage'),
            'engagement': 'high' if session.get('conversation_depth', 0) > 5 else 'medium'
        }

    def _determine_call_success(self, session: Dict) -> bool:
        """Determine if simulation was successful"""
        stages_completed = len(session.get('stages_completed', []))
        conversation_depth = session.get('conversation_depth', 0)
        trust_level = session.get('trust_level', 0)
        qualification_completed = session.get('qualification_completed', False)
        
        # Success criteria for simulation
        if (stages_completed >= 4 and 
            conversation_depth >= 8 and 
            trust_level >= 5 and 
            qualification_completed):
            return True
        
        return False

    def _handle_call_success(self, session: Dict) -> Dict[str, Any]:
        """Handle successful simulation completion"""
        session['call_outcome'] = 'success'
        session['next_steps_defined'] = True
        
        success_responses = [
            "This sounds very promising! Let's set up a follow-up call to discuss this further.",
            "I'm definitely interested. Can you send me more information and we'll schedule a demo?",
            "Great conversation! I'd like to involve my team. When can we meet?",
            "This could be exactly what we need. What are the next steps?"
        ]
        
        ai_response = random.choice(success_responses)
        
        session['conversation_history'].append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'call_ended',
            'response_type': 'success_close'
        })
        
        return {
            'success': True,
            'ai_response': ai_response,
            'call_continues': False,
            'call_successful': True,
            'simulation_outcome': 'success'
        }

    def _handle_call_failure(self, session: Dict, reason: str) -> Dict[str, Any]:
        """Handle simulation failure"""
        session['call_outcome'] = 'failed'
        session['hang_up_triggered'] = True
        
        failure_responses = [
            "I don't think this is for us. Thanks anyway.",
            "We're not interested right now. Please don't call back.",
            "This isn't a good fit. Goodbye.",
            "I need to go. We're all set with our current solutions."
        ]
        
        ai_response = random.choice(failure_responses)
        
        session['conversation_history'].append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'call_ended',
            'response_type': 'failure_hangup',
            'failure_reason': reason
        })
        
        logger.info(f"Simulation failed: {reason}")
        
        return {
            'success': True,
            'ai_response': ai_response,
            'call_continues': False,
            'call_successful': False,
            'simulation_outcome': 'failed',
            'failure_reason': reason
        }

    def _handle_silence_trigger(self, session: Dict, trigger: str) -> Dict[str, Any]:
        """Handle silence triggers for simulation"""
        if trigger == '[SILENCE_IMPATIENCE]':
            impatience_responses = [
                "Hello? Are you still there?",
                "Did I lose you?", 
                "Can you hear me okay?",
                "Just checking we're still connected..."
            ]
            
            return {
                'success': True,
                'ai_response': random.choice(impatience_responses),
                'call_continues': True
            }
        elif trigger == '[SILENCE_HANGUP]':
            return self._handle_call_failure(session, "15 seconds of silence - prospect hung up")

    def _get_contextual_initial_response(self, session_data: Dict) -> str:
        """Generate contextual phone pickup based on prospect personality"""
        personality = session_data['prospect_personality']['type']
        
        responses = {
            'driver': [
                "Yeah, what is it?",
                "This is John. Make it quick.",
                "You've got 30 seconds."
            ],
            'analytical': [
                "Hello, this is Sarah speaking.",
                "Good morning, how can I help you?",
                "This is Sarah. What's this regarding?"
            ],
            'expressive': [
                "Hi there! This is Mike!",
                "Good morning! Mike speaking!",
                "Hello! What can I do for you?"
            ],
            'amiable': [
                "Hello, this is Jennifer.",
                "Good morning, Jennifer speaking.",
                "Hi, how can I help you today?"
            ]
        }
        
        return random.choice(responses.get(personality, responses['amiable']))

    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End simulation with comprehensive analysis"""
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
            session_success = session.get('call_outcome') == 'success'
            
            # Calculate comprehensive score
            overall_score = self._calculate_simulation_score(session)
            
            # Generate detailed coaching
            coaching_result = self._generate_simulation_coaching(session)
            
            result = {
                'success': True,
                'duration_minutes': duration_minutes,
                'session_success': session_success,
                'coaching': coaching_result.get('coaching', {}),
                'overall_score': overall_score,
                'session_data': session,
                'roleplay_type': 'simulation',
                'simulation_results': {
                    'call_outcome': session.get('call_outcome', 'incomplete'),
                    'stages_completed': len(session.get('stages_completed', [])),
                    'conversation_depth': session.get('conversation_depth', 0),
                    'trust_level': session.get('trust_level', 0),
                    'interest_level': session.get('interest_level', 0),
                    'discovery_questions_asked': session.get('discovery_questions_asked', 0),
                    'qualification_completed': session.get('qualification_completed', False),
                    'prospect_personality': session.get('prospect_personality', {}).get('type'),
                    'company_scenario': session.get('company_scenario', {}),
                    'critical_successes': session.get('critical_successes', []),
                    'areas_for_improvement': session.get('areas_for_improvement', [])
                }
            }
            
            # Clean up session
            del self.active_sessions[session_id]
            
            logger.info(f"Simulation session {session_id} ended. Success: {session_success}, Score: {overall_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error ending simulation session: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_simulation_score(self, session: Dict) -> int:
        """Calculate comprehensive simulation score"""
        base_score = 40
        
        # Stage completion (30 points max)
        stages_completed = len(session.get('stages_completed', []))
        base_score += min(30, stages_completed * 5)
        
        # Relationship building (20 points max)
        trust_level = session.get('trust_level', 0)
        base_score += min(20, trust_level * 2)
        
        # Conversation quality (20 points max)
        conversation_depth = session.get('conversation_depth', 0)
        base_score += min(20, conversation_depth)
        
        # Specific accomplishments (30 points max)
        if session.get('opener_delivered'):
            base_score += 5
        if session.get('qualification_completed'):
            base_score += 10
        if session.get('discovery_questions_asked', 0) >= 3:
            base_score += 5
        if session.get('call_outcome') == 'success':
            base_score += 10
        
        return max(0, min(100, base_score))

    def _generate_simulation_coaching(self, session: Dict) -> Dict[str, Any]:
        """Generate comprehensive simulation coaching"""
        try:
            if self.is_openai_available():
                return self.openai_service.generate_coaching_feedback(
                    session.get('conversation_history', []),
                    session.get('rubric_scores', {}),
                    session.get('user_context', {}),
                    coaching_type='full_simulation'
                )
            else:
                return self._generate_fallback_simulation_coaching(session)
                
        except Exception as e:
            logger.error(f"Error generating simulation coaching: {e}")
            return self._generate_fallback_simulation_coaching(session)

    def _generate_fallback_simulation_coaching(self, session: Dict) -> Dict[str, Any]:
        """Generate fallback coaching for simulation"""
        coaching = {}
        
        # Overall performance
        call_outcome = session.get('call_outcome', 'incomplete')
        if call_outcome == 'success':
            coaching['overall'] = "Excellent simulation! You successfully navigated a complete cold call conversation."
        else:
            coaching['overall'] = "Good simulation practice! Focus on building stronger relationships and qualifying needs."
        
        # Relationship building
        trust_level = session.get('trust_level', 0)
        if trust_level >= 7:
            coaching['relationship_building'] = "Outstanding rapport building! You established strong trust."
        elif trust_level >= 4:
            coaching['relationship_building'] = "Good relationship building. Continue working on empathy and understanding."
        else:
            coaching['relationship_building'] = "Focus on building stronger relationships. Show more empathy and ask about their situation."
        
        # Discovery
        questions_asked = session.get('discovery_questions_asked', 0)
        if questions_asked >= 3:
            coaching['discovery'] = "Great discovery skills! You asked meaningful questions to understand their needs."
        else:
            coaching['discovery'] = "Ask more discovery questions to better understand their challenges and priorities."
        
        # Stage progression
        stages_completed = len(session.get('stages_completed', []))
        if stages_completed >= 5:
            coaching['progression'] = "Excellent conversation flow! You guided the call through all key stages."
        else:
            coaching['progression'] = "Work on guiding the conversation through more stages for better outcomes."
        
        return {'success': True, 'coaching': coaching}
# ===== API/SERVICES/OPENAI_SERVICE.PY (COMPLETE IMPLEMENTATION) =====
import openai
import os
import json
import random
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv('REACT_APP_OPENAI_API_KEY')
        self.model = "gpt-4o-mini"  # Using the efficient model for faster responses
        self.is_enabled = bool(self.api_key)
        
        if self.api_key:
            openai.api_key = self.api_key
            logger.info("OpenAI service initialized successfully")
        else:
            logger.warning("OpenAI API key not provided - using fallback responses")
        
        # Load system prompts and training data
        self.system_prompts = self._load_system_prompts()
        self.coaching_prompts = self._load_coaching_prompts()
        
        # Response fallbacks for when OpenAI is unavailable
        self.fallback_responses = self._load_fallback_responses()

    def _load_system_prompts(self) -> Dict[str, str]:
        """Load system prompts for different roleplay scenarios"""
        return {
            "base_prospect": """You are an AI-powered English Cold Calling Coach specifically designed to simulate realistic prospect conversations during cold calls. Your mission is to role-play as a business professional receiving a cold call while providing challenging but fair training scenarios.

## CRITICAL BEHAVIOR RULES

**STAY IN CHARACTER**: You are the PROSPECT, not the coach. Never break character during the roleplay.

**REALISTIC RESPONSES**: 
- Show authentic skepticism and resistance that real prospects display
- Use natural conversation patterns and interruptions
- Display time constraints and competing priorities
- React realistically to poor openers (hang up, strong objections)
- Reward good techniques with engagement

**DYNAMIC DIFFICULTY**:
- Adapt your resistance level based on the SDR's skill demonstration
- Increase engagement when they show empathy and professionalism
- Become more difficult if they're too pushy or generic
- Always stay challenging but fair - this is training, not punishment

**NATURAL SPEECH PATTERNS**:
- Use contractions, incomplete sentences, realistic interruptions
- Show impatience, curiosity, or interest as appropriate
- Include natural conversation fillers and authentic reactions
- Vary your response length based on engagement level""",

            "industry_specific": """## INDUSTRY & ROLE CONTEXT
You are a {job_title} at a {industry} company. Respond with the knowledge, concerns, and communication style typical of someone in this position.

**Industry Knowledge**: Demonstrate understanding of {industry} challenges, terminology, and business priorities.
**Role Responsibilities**: Respond from the perspective of someone with {job_title} level authority and concerns.
**Decision Making**: Show appropriate level of decision-making power and budget authority for your role.
**Pain Points**: Reference realistic challenges someone in your position would face.""",

            "conversation_stage": """## CONVERSATION STAGE: {stage}

{stage_instructions}

**Response Guidelines**:
- Keep responses natural and conversational (1-3 sentences typically)
- Show realistic prospect behavior for this stage
- Don't make it too easy, but don't be impossible
- React appropriately to the SDR's approach and skill level"""
        }

    def _load_coaching_prompts(self) -> Dict[str, str]:
        """Load coaching analysis prompts"""
        return {
            "performance_analysis": """Analyze this cold calling roleplay session and provide coaching feedback specifically designed for Spanish-speaking Sales Development Representatives learning English.

## CONVERSATION ANALYSIS
Roleplay Type: {roleplay_type}
Prospect: {prospect_job_title} in {prospect_industry}
Mode: {mode}

## CONVERSATION TRANSCRIPT
{conversation_transcript}

## COACHING REQUIREMENTS

Provide feedback in exactly these 5 categories using simple English (A2 level) suitable for Spanish speakers:

### 1. SALES COACHING
Focus on sales techniques and effectiveness:
- Opening approach and first impression
- Objection handling skills
- Value proposition clarity
- Meeting/next step requests
- Professional confidence level

### 2. GRAMMAR COACHING  
Identify Spanish→English interference patterns:
- Verb tenses (present perfect, past simple confusion)
- Article usage (a, an, the)
- Word order (adjective placement, question formation)
- False friends (Spanish words that look like English but differ)
- Preposition usage

### 3. VOCABULARY COACHING
Highlight unnatural word choices:
- Business terminology appropriateness
- Register level (too formal/informal for context)
- Natural vs. literal translations from Spanish
- Industry-specific vocabulary usage
- Phrasal verbs and idioms

### 4. PRONUNCIATION COACHING
Note words that may be unclear (based on common Spanish speaker challenges):
- Words with unclear consonant clusters
- Vowel sounds that differ from Spanish
- Word stress patterns
- Silent letters and difficult sounds
- Key sales terms that need clarity

### 5. RAPPORT & ASSERTIVENESS
Evaluate tone and confidence:
- Professional confidence level
- Natural conversation flow
- Empathy and active listening
- Assertiveness without aggression
- Cultural communication adaptation

## OUTPUT FORMAT
For each category, provide:
- ONE specific observation (what they did well OR what needs improvement)
- ONE actionable tip in simple English
- Maximum 2 sentences per category

Focus on the MOST impactful improvements that will make the biggest difference in their next call.""",

            "score_calculation": """Based on the conversation analysis, calculate an overall performance score (0-100) considering:

**Sales Skills (40%)**:
- Opener effectiveness (10%)
- Objection handling (10%) 
- Value communication (10%)
- Closing/next steps (10%)

**Communication Quality (35%)**:
- Grammar accuracy (10%)
- Vocabulary appropriateness (10%)
- Pronunciation clarity (8%)
- Conversation flow (7%)

**Professional Presence (25%)**:
- Confidence level (10%)
- Rapport building (8%)
- Assertiveness (7%)

Return just the numerical score (0-100) based on the conversation provided."""
        }

    def _load_fallback_responses(self) -> Dict[str, List[str]]:
        """Load fallback responses when OpenAI is unavailable"""
        return {
            "phone_pickup": [
                "Hello?",
                "Who is this?", 
                "What's this about?",
                "This better be important.",
                "You have 30 seconds."
            ],
            "early_objection": [
                "I'm not interested.",
                "We don't take cold calls.",
                "Now is not a good time.",
                "Can you send me an email?",
                "Who gave you this number?",
                "What are you trying to sell me?",
                "We're all set, thanks.",
                "I'm about to go into a meeting.",
                "This is my personal number.",
                "How long is this going to take?"
            ],
            "mini_pitch": [
                "Go ahead, what is it?",
                "I'm listening.",
                "You've got two minutes.",
                "This better be good.",
                "What exactly do you do?",
                "How is this relevant to me?",
                "I've heard this before.",
                "What makes you different?"
            ],
            "post_pitch_objections": [
                "It's too expensive for us.",
                "We have no budget right now.",
                "Your competitor is cheaper.",
                "We already use [competitor].",
                "We built something similar ourselves.",
                "I'm not the decision-maker.",
                "I need approval from my team first.",
                "How do I know this will really work?",
                "We're busy with other projects right now.",
                "Call me back next quarter."
            ]
        }

    async def generate_roleplay_response(self, user_input: str, conversation_history: List[Dict], 
                                       user_context: Dict, roleplay_config: Dict) -> Dict[str, Any]:
        """Generate AI response during roleplay with full context awareness"""
        try:
            if not self.is_enabled:
                return self._generate_fallback_response(user_input, conversation_history, roleplay_config)
            
            # Build context-aware prompt
            prompt = self._build_roleplay_prompt(user_input, conversation_history, user_context, roleplay_config)
            
            # Generate response using OpenAI
            response = await self._call_openai_chat(prompt, user_input)
            
            if response:
                # Evaluate the user input for coaching insights
                evaluation = await self._quick_evaluate_input(user_input, conversation_history, roleplay_config)
                
                return {
                    'success': True,
                    'response': response,
                    'evaluation': evaluation,
                    'should_continue': evaluation.get('should_continue', True),
                    'stage': evaluation.get('next_stage', 'in_progress')
                }
            else:
                # Fallback if OpenAI fails
                return self._generate_fallback_response(user_input, conversation_history, roleplay_config)
            
        except Exception as e:
            logger.error(f"Error generating roleplay response: {e}")
            return self._generate_fallback_response(user_input, conversation_history, roleplay_config)

    def _build_roleplay_prompt(self, user_input: str, conversation_history: List[Dict], 
                             user_context: Dict, roleplay_config: Dict) -> str:
        """Build context-aware prompt for roleplay response generation"""
        roleplay_id = roleplay_config.get('roleplay_id', 1)
        mode = roleplay_config.get('mode', 'practice')
        
        # Get prospect persona details
        prospect_title = user_context.get('prospect_job_title', 'Manager')
        prospect_industry = user_context.get('prospect_industry', 'Technology')
        custom_notes = user_context.get('custom_ai_notes', '')
        
        # Determine current conversation stage
        current_stage = self._determine_conversation_stage(conversation_history, roleplay_id)
        stage_instructions = self._get_stage_instructions(current_stage, roleplay_id)
        
        # Format conversation history
        conversation_context = self._format_conversation_history(conversation_history)
        
        # Build the complete prompt
        base_prompt = self.system_prompts["base_prospect"]
        
        industry_context = self.system_prompts["industry_specific"].format(
            job_title=prospect_title,
            industry=prospect_industry
        )
        
        stage_context = self.system_prompts["conversation_stage"].format(
            stage=current_stage,
            stage_instructions=stage_instructions
        )
        
        custom_context = f"\n## CUSTOM BEHAVIOR NOTES\n{custom_notes}" if custom_notes else ""
        
        full_prompt = f"""{base_prompt}

{industry_context}

{stage_context}

## CURRENT CONVERSATION
{conversation_context}

## LATEST SDR MESSAGE
"{user_input}"

{custom_context}

## RESPONSE INSTRUCTIONS
- Respond as the {prospect_title} would in this situation
- Keep your response natural and conversational (1-3 sentences typically)  
- Show realistic prospect behavior for the {current_stage} stage
- React appropriately to the SDR's approach and skill level
- Don't make it too easy, but don't be impossible
- Use natural speech patterns with contractions and authentic tone
- If the SDR's approach is poor, show realistic negative reactions
- If the SDR shows good technique, engage more positively
- Remember: You are the PROSPECT, not the coach

Respond now as the prospect:"""

        return full_prompt

    def _determine_conversation_stage(self, conversation_history: List[Dict], roleplay_id: int) -> str:
        """Determine current conversation stage based on history"""
        if not conversation_history:
            return "phone_pickup"
        
        # Count user messages to determine stage
        user_messages = [msg for msg in conversation_history if msg.get('role') == 'user']
        
        if roleplay_id == 2:  # Pitch + Objections starts with AI giving prompt
            if len(user_messages) == 0:
                return "ai_pitch_prompt"
            elif len(user_messages) == 1:
                return "pitch_evaluation"
            else:
                return "post_pitch_objections"
        
        elif roleplay_id == 3:  # Warm-up Challenge
            return "warmup_question"
        
        else:  # Standard cold call flow (1, 4, 5)
            if len(user_messages) == 0:
                return "phone_pickup"
            elif len(user_messages) == 1:
                return "opener_evaluation"
            elif len(user_messages) == 2:
                return "early_objection"
            elif len(user_messages) >= 3:
                return "mini_pitch"
            
        return "in_progress"

    def _get_stage_instructions(self, stage: str, roleplay_id: int) -> str:
        """Get specific instructions for current conversation stage"""
        instructions = {
            "phone_pickup": "Answer the phone as a busy professional. Say 'Hello?' or similar. Be neutral but slightly guarded.",
            
            "opener_evaluation": """The SDR just gave their opening line. Evaluate it:
- If it's a poor opener (too salesy, confusing, no empathy): Respond with strong objection or hang up
- If it's mediocre: Give a standard early objection 
- If it's good (shows empathy, pattern interrupt, professional): Engage with curiosity but still show some resistance
- Be realistic - most cold calls get objections even with good openers""",
            
            "early_objection": """Give a realistic early objection. Choose from common ones like:
'What's this about?', 'I'm not interested', 'We don't take cold calls', 'Now is not a good time', 'I have a meeting', 'Send me an email', 'Who gave you this number?', 'What are you trying to sell me?'
Make it natural and conversational.""",
            
            "mini_pitch": """The SDR handled your objection. Now decide:
- If they handled it well: Show some interest, ask a follow-up question
- If they were pushy or generic: Give another objection or become more resistant  
- If they were empathetic and professional: Engage more, but still show healthy skepticism
- Keep the prospect mindset - you're busy and need convincing""",
            
            "ai_pitch_prompt": "Give the SDR a prompt to deliver their pitch. Use phrases like 'Alright, go ahead — what's this about?' or 'You've got 30 seconds. Impress me.' or 'I'm listening. What do you do?'",
            
            "pitch_evaluation": """The SDR just gave their pitch. Respond based on quality:
- If compelling and relevant: Show interest, ask follow-up questions
- If generic or unclear: Push back with objections or skepticism
- If completely off-target: Show confusion or disinterest
- Remember to be a realistic prospect - even good pitches get questioned""",
            
            "post_pitch_objections": """Give realistic post-pitch objections like:
'It's too expensive', 'We have no budget', 'Your competitor is cheaper', 'We already use [competitor]', 'I'm not the decision-maker', 'How do I know this will work?', 'We're busy with other projects'
Choose based on your industry and role.""",
            
            "warmup_question": "Ask a challenging but fair cold calling question that tests their quick thinking and skills."
        }
        
        return instructions.get(stage, "Continue the natural conversation flow as a realistic prospect.")

    async def _call_openai_chat(self, system_prompt: str, user_message: str) -> Optional[str]:
        """Make API call to OpenAI with error handling"""
        try:
            import openai
            
            # Set the API key
            openai.api_key = self.api_key
            
            logger.info(f"Making OpenAI API call for message: {user_message[:50]}...")
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.8,  # Higher temperature for more natural variation
                max_tokens=200,   # Keep responses concise for roleplay
                presence_penalty=0.1,  # Encourage some variety
                frequency_penalty=0.1   # Reduce repetition
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Clean up the response
            ai_response = self._clean_ai_response(ai_response)
            
            logger.info(f"OpenAI response generated: {ai_response[:100]}...")
            return ai_response
            
        except Exception as e:
            # Import here to avoid circular imports
            if 'openai' in str(e).lower():
                if 'rate_limit' in str(e).lower():
                    logger.warning("OpenAI rate limit exceeded")
                elif 'authentication' in str(e).lower() or 'api_key' in str(e).lower():
                    logger.error("OpenAI authentication failed - check API key")
                elif 'insufficient_quota' in str(e).lower():
                    logger.error("OpenAI quota exceeded - add billing to your account")
                else:
                    logger.error(f"OpenAI API error: {e}")
            else:
                logger.error(f"Unexpected error calling OpenAI: {e}")
            
            return None

    def _clean_ai_response(self, response: str) -> str:
        """Clean and format AI response for realistic conversation"""
        # Remove common AI artifacts
        response = response.replace('"', '').replace("*", "").strip()
        
        # Remove stage directions or meta-commentary
        if response.startswith("As a") or response.startswith("I am"):
            # Try to extract just the dialogue
            lines = response.split('\n')
            for line in lines:
                if len(line.strip()) > 0 and not line.startswith("As") and not line.startswith("I am"):
                    response = line.strip()
                    break
        
        # Ensure response isn't too long (realistic for phone conversation)
        if len(response) > 300:
            sentences = response.split('. ')
            response = '. '.join(sentences[:2])
            if not response.endswith('.'):
                response += '.'
        
        return response

    async def _quick_evaluate_input(self, user_input: str, conversation_history: List[Dict], 
                                  roleplay_config: Dict) -> Dict[str, Any]:
        """Quick evaluation of user input for immediate feedback"""
        try:
            stage = self._determine_conversation_stage(conversation_history, roleplay_config.get('roleplay_id', 1))
            
            # Basic evaluation criteria
            evaluation = {
                'quality_score': 5,  # Default medium score
                'should_continue': True,
                'next_stage': 'in_progress',
                'feedback_notes': []
            }
            
            # Simple heuristic evaluation (could be enhanced with OpenAI later)
            user_input_lower = user_input.lower()
            
            if stage == "opener_evaluation":
                # Check for basic opener criteria
                score = 3  # Start with low score
                
                if any(greeting in user_input_lower for greeting in ['hi', 'hello', 'good morning', 'good afternoon']):
                    score += 1
                
                if any(empathy in user_input_lower for empathy in ['know this is', "don't know me", 'out of the blue', 'interrupting']):
                    score += 2
                
                if user_input.strip().endswith('?'):
                    score += 1
                    
                evaluation['quality_score'] = min(score, 8)
                
            elif stage == "early_objection":
                # Check objection handling
                if any(acknowledge in user_input_lower for acknowledge in ['understand', 'totally get', 'fair enough', 'makes sense']):
                    evaluation['quality_score'] += 2
                
                if not any(pushback in user_input_lower for pushback in ['but you', 'actually', "you're wrong"]):
                    evaluation['quality_score'] += 1
            
            # Determine if conversation should continue
            if evaluation['quality_score'] <= 2 and stage == "opener_evaluation":
                # Poor opener might result in hang up
                evaluation['should_continue'] = random.random() > 0.3  # 70% chance of hang up
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error in quick evaluation: {e}")
            return {'quality_score': 5, 'should_continue': True, 'next_stage': 'in_progress'}

    def _generate_fallback_response(self, user_input: str, conversation_history: List[Dict], 
                                  roleplay_config: Dict) -> Dict[str, Any]:
        """Generate fallback response when OpenAI is unavailable"""
        try:
            stage = self._determine_conversation_stage(conversation_history, roleplay_config.get('roleplay_id', 1))
            
            # Map stages to fallback response categories
            if stage in ["phone_pickup", "opener_evaluation"]:
                responses = self.fallback_responses["phone_pickup"]
            elif stage in ["early_objection"]:
                responses = self.fallback_responses["early_objection"]
            elif stage in ["mini_pitch", "ai_pitch_prompt"]:
                responses = self.fallback_responses["mini_pitch"]
            elif stage in ["post_pitch_objections"]:
                responses = self.fallback_responses["post_pitch_objections"]
            else:
                responses = ["I see. Tell me more.", "That's interesting.", "Go on."]
            
            # Select a random response
            selected_response = random.choice(responses)
            
            # Basic evaluation
            evaluation = {
                'quality_score': 5,
                'should_continue': True,
                'next_stage': 'in_progress'
            }
            
            logger.info(f"Using fallback response: {selected_response}")
            
            return {
                'success': True,
                'response': selected_response,
                'evaluation': evaluation,
                'should_continue': True,
                'stage': 'in_progress',
                'fallback_used': True
            }
            
        except Exception as e:
            logger.error(f"Error generating fallback response: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "Can you repeat that?",
                'evaluation': {'quality_score': 5, 'should_continue': True}
            }

    async def generate_coaching_feedback(self, session_data: Dict, user_context: Dict) -> Dict[str, Any]:
        """Generate comprehensive coaching feedback after roleplay session"""
        try:
            if not self.is_enabled:
                return self._generate_fallback_coaching(session_data)
            
            conversation = session_data.get('conversation_history', [])
            roleplay_id = session_data.get('roleplay_id', 1)
            mode = session_data.get('mode', 'practice')
            
            # Format conversation for analysis
            conversation_transcript = self._format_conversation_for_coaching(conversation)
            
            # Build coaching prompt
            coaching_prompt = self.coaching_prompts["performance_analysis"].format(
                roleplay_type=self._get_roleplay_name(roleplay_id),
                prospect_job_title=user_context.get('prospect_job_title', 'Manager'),
                prospect_industry=user_context.get('prospect_industry', 'Technology'),
                mode=mode,
                conversation_transcript=conversation_transcript
            )
            
            # Generate coaching feedback
            coaching_response = await self._call_openai_chat(coaching_prompt, "Analyze this session.")
            
            if coaching_response:
                # Parse coaching into categories
                coaching_feedback = self._parse_coaching_response(coaching_response)
                
                # Calculate overall score
                overall_score = await self._calculate_performance_score(conversation, session_data)
                
                return {
                    'success': True,
                    'coaching': coaching_feedback,
                    'overall_score': overall_score,
                    'raw_feedback': coaching_response
                }
            else:
                return self._generate_fallback_coaching(session_data)
            
        except Exception as e:
            logger.error(f"Error generating coaching feedback: {e}")
            return self._generate_fallback_coaching(session_data)

    def _generate_fallback_coaching(self, session_data: Dict) -> Dict[str, Any]:
        """Generate basic coaching when OpenAI is unavailable"""
        conversation = session_data.get('conversation_history', [])
        user_messages = [msg for msg in conversation if msg.get('role') == 'user']
        
        # Basic coaching based on conversation length and participation
        coaching = {
            'sales_coaching': 'Good job participating in the roleplay. Focus on building rapport and asking discovery questions.',
            'grammar_coaching': 'Your grammar was generally clear. Practice using contractions to sound more natural.',
            'vocabulary_coaching': 'Good word choices overall. Try using more industry-specific terminology when appropriate.',
            'pronunciation_coaching': 'Speech was clear and understandable. Practice key sales terms for better clarity.',
            'rapport_assertiveness': 'Good conversational tone. Work on building more confidence in your delivery.'
        }
        
        # Basic score calculation
        if len(user_messages) >= 3:
            score = 75  # Good participation
        elif len(user_messages) >= 2:
            score = 60  # Moderate participation
        else:
            score = 45  # Limited participation
        
        return {
            'success': True,
            'coaching': {'coaching': coaching},
            'overall_score': score,
            'fallback_used': True
        }

    async def _calculate_performance_score(self, conversation: List[Dict], session_data: Dict) -> int:
        """Calculate performance score using OpenAI or fallback method"""
        try:
            if not self.is_enabled:
                return self._calculate_fallback_score(conversation, session_data)
            
            conversation_text = self._format_conversation_for_coaching(conversation)
            score_prompt = self.coaching_prompts["score_calculation"]
            
            score_response = await self._call_openai_chat(score_prompt, f"Score this conversation:\n{conversation_text}")
            
            if score_response:
                # Extract numerical score from response
                try:
                    score = int(''.join(filter(str.isdigit, score_response)))
                    return max(0, min(100, score))  # Ensure score is between 0-100
                except:
                    return self._calculate_fallback_score(conversation, session_data)
            else:
                return self._calculate_fallback_score(conversation, session_data)
                
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return self._calculate_fallback_score(conversation, session_data)

    def _calculate_fallback_score(self, conversation: List[Dict], session_data: Dict) -> int:
        """Calculate basic performance score without OpenAI"""
        user_messages = [msg for msg in conversation if msg.get('role') == 'user']
        
        # Base score on participation and session success
        base_score = 50
        
        # Participation bonus
        if len(user_messages) >= 4:
            base_score += 20
        elif len(user_messages) >= 3:
            base_score += 15
        elif len(user_messages) >= 2:
            base_score += 10
        
        # Session completion bonus
        if not session_data.get('hang_up_triggered', False):
            base_score += 15
        
        # Mode difficulty bonus
        mode = session_data.get('mode', 'practice')
        if mode == 'legend':
            base_score += 10
        elif mode == 'marathon':
            base_score += 5
        
        return max(0, min(100, base_score))

    def _parse_coaching_response(self, coaching_text: str) -> Dict[str, str]:
        """Parse coaching feedback into structured categories"""
        try:
            # Try to extract sections based on headers
            categories = {
                'sales_coaching': '',
                'grammar_coaching': '',
                'vocabulary_coaching': '',
                'pronunciation_coaching': '',
                'rapport_assertiveness': ''
            }
            
            # Simple parsing - look for numbered sections or headers
            current_category = None
            lines = coaching_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check for category headers
                if 'sales' in line.lower() and ('1.' in line or '#' in line):
                    current_category = 'sales_coaching'
                elif 'grammar' in line.lower() and ('2.' in line or '#' in line):
                    current_category = 'grammar_coaching'
                elif 'vocabulary' in line.lower() and ('3.' in line or '#' in line):
                    current_category = 'vocabulary_coaching'
                elif 'pronunciation' in line.lower() and ('4.' in line or '#' in line):
                    current_category = 'pronunciation_coaching'
                elif 'rapport' in line.lower() or 'assertiveness' in line.lower() and ('5.' in line or '#' in line):
                    current_category = 'rapport_assertiveness'
                elif current_category and line and not line.startswith('#'):
                    # Add content to current category
                    if categories[current_category]:
                        categories[current_category] += ' ' + line
                    else:
                        categories[current_category] = line
            
            # Fallback: if parsing failed, use the whole text for sales coaching
            if not any(categories.values()):
                categories['sales_coaching'] = coaching_text[:200]  # Truncate if too long
                categories['grammar_coaching'] = 'Focus on using natural contractions and clear pronunciation.'
                categories['vocabulary_coaching'] = 'Use industry-specific terms when appropriate.'
                categories['pronunciation_coaching'] = 'Speak clearly and at an appropriate pace.'
                categories['rapport_assertiveness'] = 'Show confidence while remaining professional and empathetic.'
            
            return {'coaching': categories}
            
        except Exception as e:
            logger.error(f"Error parsing coaching response: {e}")
            return self._generate_fallback_coaching({}).get('coaching', {})

    def _format_conversation_history(self, conversation: List[Dict]) -> str:
        """Format conversation for prompt context"""
        if not conversation:
            return "No conversation yet."
        
        formatted = []
        for msg in conversation[-10:]:  # Last 10 messages
            role = "SDR" if msg.get('role') == 'user' else "Prospect"
            content = msg.get('content', '')
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)

    def _format_conversation_for_coaching(self, conversation: List[Dict]) -> str:
        """Format conversation for coaching analysis"""
        if not conversation:
            return "No conversation to analyze."
        
        formatted = []
        for i, msg in enumerate(conversation, 1):
            role = "SDR" if msg.get('role') == 'user' else "Prospect"
            content = msg.get('content', '')
            formatted.append(f"{i}. {role}: {content}")
        return "\n".join(formatted)

    def _get_roleplay_name(self, roleplay_id: int) -> str:
        """Get roleplay name by ID"""
        names = {
            1: "Opener + Early Objections",
            2: "Pitch + Objections + Close", 
            3: "Warm-up Challenge",
            4: "Full Cold Call Simulation",
            5: "Power Hour Challenge"
        }
        return names.get(roleplay_id, f"Roleplay {roleplay_id}")

    def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.is_enabled

    def get_status(self) -> Dict[str, Any]:
        """Get service status information"""
        return {
            'enabled': self.is_enabled,
            'api_key_configured': bool(self.api_key),
            'model': self.model,
            'status': 'ready' if self.is_enabled else 'fallback_mode'
        }
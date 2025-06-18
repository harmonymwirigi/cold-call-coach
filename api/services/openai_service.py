# ===== UPDATED API/SERVICES/OPENAI_SERVICE.PY (Add these methods to your existing file) =====

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

            "roleplay_1_prospect": """You are a {job_title} at a {industry} company receiving a cold call. You speak fluent, native-level English (CEFR C2).

## ROLEPLAY 1 BEHAVIOR RULES

**CORE IDENTITY**: You are the PROSPECT, not a coach. Stay in character always.

**LANGUAGE LEVEL**: Speak at CEFR C2 level - use sophisticated vocabulary, complex sentences, and natural native speaker patterns.

**RESPONSE LENGTH**: Keep responses short and realistic (1-2 sentences typically). Real prospects don't give long speeches.

**HANG-UP RULES**:
- You will hang up on poor openers (20-30% chance based on quality)
- You have zero tolerance for pushiness or rudeness
- You'll hang up after 15 seconds of silence
- You're a busy professional with limited patience

**CURRENT CONVERSATION**:
{conversation_context}

**LATEST SDR MESSAGE**: "{user_input}"

**RESPONSE INSTRUCTIONS**:
- Respond as a real {job_title} would in this exact situation
- Use sophisticated, native-level English vocabulary and grammar
- Keep your response conversational and brief (1-2 sentences)
- Show realistic prospect behavior for this stage
- Be challenging but fair - this is training, not punishment""",

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

    # ===== NEW: ROLEPLAY 1 SPECIALIZED METHODS =====

    async def generate_roleplay_response(self, user_input: str, conversation_history: List[Dict], 
                                       user_context: Dict, roleplay_config: Dict) -> Dict[str, Any]:
        """Enhanced roleplay response generation with Roleplay 1 specialization"""
        try:
            roleplay_id = roleplay_config.get('roleplay_id', 1)
            
            if roleplay_id == 1:
                # Use specialized Roleplay 1 handling
                return await self._generate_roleplay_1_response(user_input, conversation_history, user_context, roleplay_config)
            else:
                # Use existing general handling for other roleplays
                return await self._generate_general_roleplay_response(user_input, conversation_history, user_context, roleplay_config)
                
        except Exception as e:
            logger.error(f"Error generating roleplay response: {e}")
            return self._generate_fallback_response(user_input, conversation_history, roleplay_config)

    async def _generate_roleplay_1_response(self, user_input: str, conversation_history: List[Dict], 
                                          user_context: Dict, roleplay_config: Dict) -> Dict[str, Any]:
        """Specialized response generation for Roleplay 1"""
        try:
            # Build the specialized Roleplay 1 prompt
            prompt = self._build_roleplay_1_prompt(user_input, conversation_history, user_context)
            
            # Generate AI response
            ai_response = await self._call_openai_chat(prompt, user_input)
            
            if ai_response:
                # Quick evaluation for immediate feedback
                evaluation = await self._quick_evaluate_roleplay_1(user_input, conversation_history, roleplay_config)
                
                return {
                    'success': True,
                    'response': ai_response,
                    'evaluation': evaluation,
                    'should_continue': evaluation.get('should_continue', True),
                    'stage': evaluation.get('next_stage', 'in_progress'),
                    'roleplay_1_enhanced': True
                }
            else:
                # Fallback if OpenAI fails
                return self._generate_fallback_response(user_input, conversation_history, roleplay_config)
                
        except Exception as e:
            logger.error(f"Error in Roleplay 1 response generation: {e}")
            return self._generate_fallback_response(user_input, conversation_history, roleplay_config)

    def _build_roleplay_1_prompt(self, user_input: str, conversation_history: List[Dict], 
                               user_context: Dict) -> str:
        """Build specialized prompt for Roleplay 1 with rubric awareness"""
        
        # Get prospect persona details
        prospect_title = user_context.get('prospect_job_title', 'Manager')
        prospect_industry = user_context.get('prospect_industry', 'Technology')
        custom_notes = user_context.get('custom_ai_notes', '')
        
        # Determine current stage
        current_stage = self._determine_conversation_stage(conversation_history, 1)
        
        # Build stage-specific instructions
        stage_instructions = self._get_roleplay_1_stage_instructions(current_stage)
        
        # Format conversation context
        conversation_context = self._format_conversation_history(conversation_history)
        
        # Build the specialized Roleplay 1 prompt
        base_prompt = self.system_prompts["roleplay_1_prospect"].format(
            job_title=prospect_title,
            industry=prospect_industry,
            conversation_context=conversation_context,
            user_input=user_input
        )
        
        stage_context = f"\n## STAGE-SPECIFIC BEHAVIOR:\n{stage_instructions}"
        
        custom_context = f"\n## CUSTOM BEHAVIOR NOTES\n{custom_notes}" if custom_notes else ""
        
        full_prompt = f"""{base_prompt}

{stage_context}

{custom_context}

Respond now as the prospect:"""

        return full_prompt

    def _get_roleplay_1_stage_instructions(self, stage: str) -> str:
        """Get detailed stage instructions for Roleplay 1"""
        
        instructions = {
            "phone_pickup": """**PHONE PICKUP STAGE**
Answer the phone like a busy professional. Say "Hello?" or similar short greeting. Be neutral but slightly guarded since you don't recognize the number.""",

            "opener_evaluation": """**OPENER EVALUATION STAGE** 
The SDR just gave their opening line. Evaluate it based on these criteria:
- Clear cold call opener (not just "Hi, how are you?")
- Casual, confident tone with contractions
- Shows empathy for the interruption ("I know this is out of the blue...")
- Ends with a soft question

**Response Rules**:
- If opener scores 0-1 criteria: 80% chance to hang up immediately ("Not interested. *click*")
- If opener scores 2 criteria: 30% chance to hang up, otherwise give early objection
- If opener scores 3-4 criteria: 10% chance to hang up, otherwise engage with mild objection
- Always be realistic - even good openers get objections

**Sample hang-up responses**: "Not interested.", "Please don't call here again.", "I'm hanging up now."
**Sample objection responses**: "What's this about?", "I'm not interested", "Now is not a good time", "Who is this?""",

            "early_objection": """**OBJECTION STAGE**
You gave an objection. Now evaluate how they handle it:
- Do they acknowledge calmly? ("Fair enough", "I understand")
- Do they avoid arguing or immediate pitching?
- Do they reframe briefly in 1 sentence?
- Do they end with a forward-moving question?

**Response Rules**:
- If they handle it well (3+ criteria): Show mild interest but maintain skepticism
- If they handle it poorly (defensive, pushy): Give stronger objection or hang up
- If they pitch immediately: "I didn't ask for a sales pitch. Goodbye."
- Small (5%) chance of random hang-up even if handled well

**Engagement examples**: "Alright, I'm listening.", "Go ahead, what is it?", "You have 30 seconds."
**Resistance examples**: "I already told you I'm not interested.", "Are you not listening to me?"
""",

            "mini_pitch": """**MINI-PITCH STAGE**
Listen to their pitch and evaluate:
- Is it short (1-2 sentences, under 30 words)?
- Does it focus on outcomes/benefits, not features?
- Is the language simple and jargon-free?
- Does it sound natural, not robotic?

**Response Rules**:
- If pitch is good (3+ criteria): Show interest, ask follow-up question
- If pitch is poor (too long, jargony, feature-focused): Show confusion or disinterest
- Look for their soft discovery question after the pitch
- Very small (2%) chance of random hang-up

**Positive responses**: "That's interesting. Tell me more.", "How exactly do you do that?", "What does that look like?"
**Negative responses**: "I don't understand what you're saying.", "That sounds like everything else.", "Too complicated."
""",

            "soft_discovery": """**SOFT DISCOVERY STAGE**
They should ask a soft discovery question. Evaluate:
- Is the question tied to their pitch?
- Is it open-ended and curious (not leading)?
- Is the tone soft and non-pushy?

**Response Rules**:
- If question is good (2+ criteria): Answer briefly and positively, then hang up ("Interesting conversation. Send me some information. Goodbye.")
- If question is poor: Show disinterest and hang up ("This isn't relevant to us. Goodbye.")
- This stage determines PASS/FAIL for the entire call

**Success responses**: "That's a good question. We do struggle with that.", "Actually, yes, that's been an issue.", "You know what, that's exactly what we're dealing with."
**Failure responses**: "That's not relevant to us.", "I don't have time for this.", "This conversation isn't going anywhere."
"""
        }
        
        return instructions.get(stage, "Continue the natural conversation flow as a realistic prospect.")

    async def _quick_evaluate_roleplay_1(self, user_input: str, conversation_history: List[Dict], 
                                       roleplay_config: Dict) -> Dict[str, Any]:
        """Quick evaluation for Roleplay 1 using OpenAI"""
        try:
            # Build evaluation prompt
            eval_prompt = self._enhance_roleplay_1_evaluation_prompt(user_input, conversation_history, roleplay_config)
            
            # Get evaluation from OpenAI
            eval_response = await self._call_openai_chat(eval_prompt, "Evaluate this interaction.")
            
            if eval_response:
                # Parse the evaluation response
                return self._parse_roleplay_1_evaluation(eval_response)
            else:
                # Fallback evaluation
                return self._basic_roleplay_1_evaluation(user_input, conversation_history)
                
        except Exception as e:
            logger.error(f"Error in Roleplay 1 evaluation: {e}")
            return self._basic_roleplay_1_evaluation(user_input, conversation_history)

    def _enhance_roleplay_1_evaluation_prompt(self, user_input: str, conversation_history: List[Dict], 
                                            roleplay_config: Dict) -> str:
        """Enhanced evaluation prompt that understands Roleplay 1 rubrics"""
        
        stage = self._determine_conversation_stage(conversation_history, 1)
        
        evaluation_prompt = f"""Analyze this Roleplay 1 interaction for a Spanish-speaking SDR learning English:

**STAGE**: {stage}
**SDR INPUT**: "{user_input}"

**EVALUATION CRITERIA FOR {stage.upper()}**:
"""

        if stage in ['phone_pickup', 'opener_evaluation']:
            evaluation_prompt += """
**OPENER RUBRIC** (Need 3/4 to pass):
1. Clear cold call opener (pattern interrupt, permission-based, or value-first) - NOT just greeting
2. Casual, confident tone (uses contractions like "I'm", "don't", "we're")
3. Shows empathy ("I know this is out of the blue", "You don't know me", etc.)
4. Ends with soft question ("Can I tell you why I'm calling?")

**AUTO-FAIL CONDITIONS**: Robotic/overly formal, no empathy, pushy or too long, no question

**HANG-UP PROBABILITY**: 
- 0-1 criteria met: 80% hang-up chance
- 2 criteria met: 30% hang-up chance  
- 3-4 criteria met: 10% hang-up chance"""

        elif stage == 'early_objection':
            evaluation_prompt += """
**OBJECTION HANDLING RUBRIC** (Need 3/4 to pass):
1. Acknowledges calmly ("Fair enough", "Totally get that", "I understand")
2. Doesn't argue or pitch immediately
3. Reframes or buys time in 1 sentence
4. Ends with forward-moving question

**AUTO-FAIL CONDITIONS**: Gets defensive/pushy, ignores objection, pitches immediately, no forward question"""

        elif stage == 'mini_pitch':
            evaluation_prompt += """
**MINI-PITCH RUBRIC** (Need 3/4 to pass):
1. Short (1-2 sentences, under 30 words)
2. Focuses on problem solved or outcome delivered (not features)
3. Simple English, no jargon or buzzwords
4. Sounds natural, not robotic or memorized

**AUTO-FAIL CONDITIONS**: Too long/detailed, focuses on features, uses jargon, sounds scripted"""

        elif stage == 'soft_discovery':
            evaluation_prompt += """
**SOFT DISCOVERY RUBRIC** (Need 2/3 to pass):
1. Short question tied to the pitch
2. Open/curious question (not leading)
3. Soft, non-pushy tone

**AUTO-FAIL CONDITIONS**: No question asked, too broad/generic, sounds scripted/pushy"""

        evaluation_prompt += f"""

**RESPONSE FORMAT**:
- PASS/FAIL: [Pass/Fail]
- CRITERIA MET: [List which criteria were met]
- CRITERIA MISSED: [List which criteria were missed]
- SHOULD_HANGUP: [True/False]
- HANGUP_REASON: [If applicable]
- NEXT_STAGE: [Next conversation stage]

Analyze the SDR's input "{user_input}" against these criteria and provide the evaluation."""

        return evaluation_prompt

    def _parse_roleplay_1_evaluation(self, eval_response: str) -> Dict[str, Any]:
        """Parse OpenAI evaluation response for Roleplay 1"""
        try:
            # Simple parsing of the evaluation response
            response_lower = eval_response.lower()
            
            # Extract pass/fail
            passed = 'pass' in response_lower and 'fail' not in response_lower.replace('pass', '')
            
            # Extract hang-up decision
            should_hangup = 'should_hangup: true' in response_lower or 'hang up' in response_lower
            
            # Extract criteria information
            criteria_met = []
            criteria_missed = []
            
            # Basic keyword extraction (could be enhanced with regex)
            if 'clear opener' in response_lower:
                criteria_met.append('clear_opener')
            if 'casual tone' in response_lower:
                criteria_met.append('casual_tone')
            if 'empathy' in response_lower:
                criteria_met.append('shows_empathy')
            if 'question' in response_lower:
                criteria_met.append('ends_with_question')
            
            return {
                'passed': passed,
                'should_continue': not should_hangup,
                'should_hangup': should_hangup,
                'criteria_met': criteria_met,
                'criteria_missed': criteria_missed,
                'quality_score': len(criteria_met),
                'evaluation_source': 'openai',
                'raw_evaluation': eval_response
            }
            
        except Exception as e:
            logger.error(f"Error parsing evaluation response: {e}")
            return self._basic_roleplay_1_evaluation("", [])

    def _basic_roleplay_1_evaluation(self, user_input: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Basic fallback evaluation for Roleplay 1"""
        # Simple heuristic evaluation as fallback
        score = 2  # Base score
        user_input_lower = user_input.lower()
        
        # Basic checks
        if any(contraction in user_input_lower for contraction in ["i'm", "don't", "can't", "we're"]):
            score += 1
        
        if any(empathy in user_input_lower for empathy in ["know this is", "out of the blue", "don't know me"]):
            score += 2
        
        if user_input.strip().endswith('?'):
            score += 1
        
        return {
            'passed': score >= 4,
            'should_continue': score >= 3,
            'should_hangup': score < 2,
            'quality_score': score,
            'evaluation_source': 'fallback'
        }

    # ===== EXISTING METHODS (Enhanced for Roleplay 1) =====

    async def _generate_general_roleplay_response(self, user_input: str, conversation_history: List[Dict], 
                                                user_context: Dict, roleplay_config: Dict) -> Dict[str, Any]:
        """General roleplay response generation for non-Roleplay 1 scenarios"""
        try:
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
            logger.error(f"Error generating general roleplay response: {e}")
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

    # ===== EXISTING COACHING METHODS (unchanged) =====

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

    # ===== HELPER METHODS =====

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

    # ===== PLACEHOLDER METHODS (implement if needed) =====

    def _generate_fallback_coaching(self, session_data: Dict) -> Dict[str, Any]:
        """Basic coaching when OpenAI unavailable"""
        return {
            'success': True,
            'coaching': {
                'coaching': {
                    'sales_coaching': 'Practice your opening and objection handling techniques.',
                    'grammar_coaching': 'Use contractions to sound more natural.',
                    'vocabulary_coaching': 'Good word choices. Keep it simple and clear.',
                    'pronunciation_coaching': 'Speak clearly and at a steady pace.',
                    'rapport_assertiveness': 'Work on building confidence in your delivery.'
                }
            },
            'overall_score': 65,
            'fallback_used': True
        }

    async def _calculate_performance_score(self, conversation: List[Dict], session_data: Dict) -> int:
        """Calculate basic performance score"""
        user_messages = [msg for msg in conversation if msg.get('role') == 'user']
        base_score = 50 + (len(user_messages) * 10)
        return min(100, base_score)

    def _parse_coaching_response(self, coaching_text: str) -> Dict[str, str]:
        """Parse coaching feedback into categories"""
        return {
            'coaching': {
                'sales_coaching': 'Focus on improving your sales techniques.',
                'grammar_coaching': 'Work on using natural contractions.',
                'vocabulary_coaching': 'Use simple, clear business language.',
                'pronunciation_coaching': 'Speak clearly and confidently.',
                'rapport_assertiveness': 'Build rapport while staying professional.'
            }
        }
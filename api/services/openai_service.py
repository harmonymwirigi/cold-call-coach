# ===== UPDATED API/SERVICES/OPENAI_SERVICE.PY - ROLEPLAY 1.1 COMPLIANT =====

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
        self.model = "gpt-4o-mini"  # Using efficient model for faster responses
        self.is_enabled = bool(self.api_key)
        
        if self.api_key:
            openai.api_key = self.api_key
            logger.info("OpenAI service initialized for Roleplay 1.1")
        else:
            logger.warning("OpenAI API key not provided - using fallback responses")
        
        # Load Roleplay 1.1 system prompts
        self.system_prompts = self._load_roleplay_11_prompts()
        self.coaching_prompts = self._load_roleplay_11_coaching_prompts()
        
        # Roleplay 1.1 fallback responses
        self.fallback_responses = self._load_roleplay_11_fallbacks()
        
        # Roleplay 1.1 specifications
        self.roleplay_11_specs = {
            'early_objections': [
                "What's this about?", "I'm not interested", "We don't take cold calls",
                "Now is not a good time", "I have a meeting", "Can you call me later?",
                "I'm about to go into a meeting", "Send me an email", "Can you send me the information?",
                "Can you message me on WhatsApp?", "Who gave you this number?", "This is my personal number",
                "Where did you get my number?", "What are you trying to sell me?", "Is this a sales call?",
                "Is this a cold call?", "Are you trying to sell me something?", "We are ok for the moment",
                "We are all good / all set", "We're not looking for anything right now",
                "We are not changing anything", "How long is this going to take?", "Is this going to take long?",
                "What company are you calling from?", "Who are you again?", "Where are you calling from?",
                "I never heard of you", "Not interested right now", "Just send me the details"
            ],
            'impatience_phrases': [
                "Hello? Are you still with me?", "Can you hear me?", "Just checking you're there…",
                "Still on the line?", "I don't have much time for this.", "Sounds like you are gone.",
                "Are you an idiot.", "What is going on.", "Are you okay to continue?", "I am afraid I have to go"
            ]
        }

    def _load_roleplay_11_prompts(self) -> Dict[str, str]:
        """Load system prompts specifically for Roleplay 1.1"""
        return {
            "roleplay_11_prospect": """You are an AI-powered English Cold Calling Coach simulating Roleplay 1.1: "Opener + Early Objection + Mini-Pitch (Practice Mode)".

## CRITICAL BEHAVIOR RULES FOR ROLEPLAY 1.1

**STAY IN CHARACTER**: You are the PROSPECT receiving a cold call, NOT the coach. Never break character.

**ROLEPLAY 1.1 FLOW**:
1. Phone Pickup → SDR gives opener → Evaluate opener (pass/fail)
2. If opener passes → Give early objection → SDR handles objection → Evaluate handling (pass/fail)  
3. If objection handling passes → SDR gives mini-pitch → Evaluate pitch (pass/fail)
4. SDR asks soft discovery question → Evaluate question (pass/fail) → End call

**LANGUAGE SPECIFICATIONS**:
- You speak CEFR C2 level English (sophisticated, native-level)
- Use complex vocabulary, natural contractions, realistic interruptions
- Keep responses SHORT (1-2 sentences typically)
- No mid-call feedback or coaching - stay in character always

**PROSPECT PERSONA**: You are a {job_title} at a {industry} company.

**CURRENT STAGE**: {current_stage}
**CONVERSATION HISTORY**: 
{conversation_context}

**LATEST SDR INPUT**: "{user_input}"

**STAGE-SPECIFIC BEHAVIOR**:
{stage_instructions}

**RESPONSE INSTRUCTIONS**:
- Respond as the {job_title} would in this exact situation
- Use sophisticated, native-level English (CEFR C2)
- Keep response brief and conversational (1-2 sentences)
- Show realistic prospect behavior for current stage
- Be challenging but fair - this is training
- Never give coaching or feedback - stay in character

Respond now as the prospect:""",

            "opener_evaluation": """**OPENER EVALUATION STAGE**
The SDR just delivered their opening line. Evaluate based on these criteria:
- Clear cold call opener (not just greeting)
- Casual, confident tone with contractions
- Shows empathy for the interruption  
- Ends with soft question

**Response Rules**:
- If opener scores 0-1 criteria: 80% chance to hang up ("Not interested. *click*")
- If opener scores 2 criteria: 30% chance to hang up, otherwise early objection
- If opener scores 3-4 criteria: 10% chance to hang up, otherwise engage with mild objection

**Hang-up responses**: "Not interested.", "Please don't call here again.", "I'm hanging up now."
**Objection responses**: Choose from the 29-item early objection list, never repeat consecutively.""",

            "objection_handling": """**OBJECTION HANDLING STAGE**
You gave an objection. Evaluate how they handle it:
- Do they acknowledge calmly? ("Fair enough", "I understand")
- Do they avoid arguing or immediate pitching?
- Do they reframe briefly in 1 sentence?
- Do they end with forward-moving question?

**Response Rules**:
- If handled well (3+ criteria): Show mild interest but maintain skepticism
- If handled poorly: Give stronger objection or hang up
- If they pitch immediately: "I didn't ask for a sales pitch. Goodbye."

**Engagement**: "Alright, I'm listening.", "Go ahead, what is it?", "You have 30 seconds."
**Resistance**: "I already told you I'm not interested.", "Are you not listening to me?""",

            "mini_pitch_evaluation": """**MINI-PITCH EVALUATION STAGE**
Listen to their pitch and evaluate:
- Is it short (1-2 sentences, under 30 words)?
- Does it focus on outcomes/benefits, not features?
- Is the language simple and jargon-free?
- Does it sound natural, not robotic?

**Response Rules**:
- If pitch is good (3+ criteria): Show interest, ask follow-up
- If pitch is poor: Show confusion or disinterest
- Lead them to soft discovery question

**Positive**: "That's interesting. Tell me more.", "How exactly do you do that?"
**Negative**: "I don't understand.", "That sounds like everything else.""",

            "soft_discovery": """**SOFT DISCOVERY STAGE**
They should ask a soft discovery question. Evaluate:
- Is question tied to their pitch?
- Is it open-ended and curious?
- Is tone soft and non-pushy?

**Response Rules**:
- If question is good (2+ criteria): Answer positively, then hang up with interest
- If question is poor: Show disinterest and hang up
- This determines final PASS/FAIL

**Success**: "That's a good question. Send me information. Goodbye."
**Failure**: "That's not relevant. This isn't going anywhere. Goodbye.""",

            "silence_impatience": """**SILENCE IMPATIENCE (10 seconds)**
The SDR has been silent for 10 seconds. Show impatience with one of these phrases:
"Hello? Are you still with me?", "Can you hear me?", "Just checking you're there…",
"Still on the line?", "I don't have much time for this.", "Sounds like you are gone.",
"Are you an idiot.", "What is going on.", "Are you okay to continue?", "I am afraid I have to go"

Use exactly one phrase, then wait for their response.""",

            "silence_hangup": """**SILENCE HANGUP (15 seconds)**
The SDR has been silent for 15 seconds total. Hang up immediately:
"I don't have time for this. Goodbye." or "Are you there? I'm hanging up."

The call ends here - mark as FAIL."""
        }

    def _load_roleplay_11_coaching_prompts(self) -> Dict[str, str]:
        """Load coaching prompts specifically for Roleplay 1.1"""
        return {
            "roleplay_11_coaching": """Analyze this Roleplay 1.1 session and provide coaching feedback in CEFR A2 English (simple, clear language for Spanish speakers learning English).

## SESSION ANALYSIS
**Roleplay**: 1.1 - Opener + Early Objection + Mini-Pitch
**Prospect**: {prospect_job_title} in {prospect_industry}
**Mode**: Practice

## CONVERSATION TRANSCRIPT
{conversation_transcript}

## RUBRIC RESULTS
{rubric_results}

## COACHING REQUIREMENTS (CEFR A2 English - Simple and Clear)

Provide exactly ONE item per category using simple English:

### 1. SALES COACHING
Focus on sales performance based on rubric results:
- If opener failed: "Your opening needs work. Try: 'Hi, I know this is out of the blue, but can I tell you why I'm calling?'"
- If objection handling failed: "When they object, say 'I understand' first. Don't argue. Then ask a question."
- If mini-pitch failed: "Keep your pitch short. Talk about the problem you solve, not your product features."
- If soft discovery failed: "Ask open questions like 'How do you handle that now?' Don't be pushy."
- If all passed: "Great job! You passed all sales steps. Keep practicing to get even better."

### 2. GRAMMAR COACHING
Look for Spanish→English interference patterns:
- Contractions: "Use 'I'm' instead of 'I am'. It sounds more natural."
- Articles: "You use 'the' too much. Sometimes you don't need it."
- Word order: Focus on most common mistakes
- If good: "Good grammar! Keep using contractions like 'I'm' and 'can't'."

### 3. VOCABULARY COACHING  
Check for unnatural word choices:
- False friends: "You said 'assist'. Use 'attend' for meetings. 'Assist' means 'help'."
- Business terms: "Say 'book a meeting' not 'win a meeting'."
- Jargon: "Use simple words. Say 'use' instead of 'utilize'."
- If good: "Good word choices! Keep using simple, clear business language."

### 4. PRONUNCIATION COACHING
Note unclear words (based on low ASR confidence if available):
- Format: "Word: 'schedule' - Say it like: 'SKED-jool'"
- Common issues for Spanish speakers
- If good: "Good pronunciation! Speak clearly and not too fast."

### 5. RAPPORT & ASSERTIVENESS
Evaluate confidence and empathy:
- Low confidence: "Show empathy at the start. Say 'I know this is unexpected'."
- Too pushy: "Stay calm when they object. Say 'I understand' and don't argue."
- If good: "Good rapport! You sound professional and friendly."

## OUTPUT FORMAT
Return exactly this structure:
```
SALES: [One specific tip based on failed rubric or praise if passed]
GRAMMAR: [One grammar tip in simple English]
VOCABULARY: [One vocabulary tip focusing on business language]  
PRONUNCIATION: [One pronunciation tip or praise]
RAPPORT: [One tip about confidence/empathy or praise]
```

Keep all feedback in CEFR A2 level English - short sentences, simple words, clear instructions.""",

            "score_calculation": """Calculate Roleplay 1.1 performance score (0-100) based on:

**Rubric Performance (60%)**:
- Opener passed: +15 points
- Objection handling passed: +15 points  
- Mini-pitch passed: +15 points
- Soft discovery passed: +15 points

**Completion Bonus (40%)**:
- Completed without hang-up: +10 points
- Overall call passed (all rubrics): +10 points
- Participation (reached each stage): +20 points

**Base Score**: 40 points (for attempting the roleplay)

Return only the numerical score (0-100)."""
        }

    def _load_roleplay_11_fallbacks(self) -> Dict[str, List[str]]:
        """Load fallback responses for Roleplay 1.1 when OpenAI unavailable"""
        return {
            "phone_pickup": ["Hello?", "Hi there.", "Good morning.", "Yes?"],
            
            "early_objection": [
                "What's this about?", "I'm not interested", "We don't take cold calls",
                "Now is not a good time", "I have a meeting", "Send me an email",
                "Who gave you this number?", "What are you trying to sell me?",
                "Is this a sales call?", "We are all good", "How long is this going to take?"
            ],
            
            "objection_response": [
                "Alright, I'm listening.", "Go ahead, what is it?", "You have 30 seconds.",
                "This better be good.", "What exactly do you do?", "I'm still not interested.",
                "Are you not listening to me?"
            ],
            
            "mini_pitch_response": [
                "That's interesting. Tell me more.", "How exactly do you do that?",
                "What does that look like?", "I don't understand what you're saying.",
                "That sounds like everything else.", "Too complicated."
            ],
            
            "hangup_responses": {
                "opener_fail": ["Not interested.", "Please don't call here again.", "I'm hanging up now."],
                "objection_fail": ["I already told you I'm not interested.", "You're not listening. Goodbye."],
                "discovery_success": ["That's a good question. Send me information. Goodbye."],
                "discovery_fail": ["That's not relevant to us. Goodbye.", "This isn't going anywhere."],
                "silence": ["I don't have time for this. Goodbye.", "Are you there? I'm hanging up."]
            }
        }

    # ===== ROLEPLAY 1.1 SPECIALIZED METHODS =====

    async def generate_roleplay_response(self, user_input: str, conversation_history: List[Dict], 
                                       user_context: Dict, roleplay_config: Dict) -> Dict[str, Any]:
        """Generate roleplay response with Roleplay 1.1 specialization"""
        try:
            roleplay_id = roleplay_config.get('roleplay_id', 1)
            
            if roleplay_id == 1:
                # Use specialized Roleplay 1.1 handling
                return await self._generate_roleplay_11_response(user_input, conversation_history, user_context, roleplay_config)
            else:
                # Use existing general handling for other roleplays
                return await self._generate_general_roleplay_response(user_input, conversation_history, user_context, roleplay_config)
                
        except Exception as e:
            logger.error(f"Error generating roleplay response: {e}")
            return self._generate_fallback_response(user_input, conversation_history, roleplay_config)

    async def _generate_roleplay_11_response(self, user_input: str, conversation_history: List[Dict], 
                                          user_context: Dict, roleplay_config: Dict) -> Dict[str, Any]:
        """Specialized response generation for Roleplay 1.1"""
        try:
            # Build the specialized Roleplay 1.1 prompt
            prompt = self._build_roleplay_11_prompt(user_input, conversation_history, user_context, roleplay_config)
            
            # Generate AI response using OpenAI
            ai_response = await self._call_openai_chat(prompt, user_input)
            
            if ai_response:
                # Quick evaluation for Roleplay 1.1
                evaluation = await self._quick_evaluate_roleplay_11(user_input, conversation_history, roleplay_config)
                
                return {
                    'success': True,
                    'response': ai_response,
                    'evaluation': evaluation,
                    'should_continue': evaluation.get('should_continue', True),
                    'stage': evaluation.get('next_stage', 'in_progress'),
                    'roleplay_11_enhanced': True
                }
            else:
                # Fallback if OpenAI fails
                return self._generate_roleplay_11_fallback(user_input, conversation_history, roleplay_config)
                
        except Exception as e:
            logger.error(f"Error in Roleplay 1.1 response generation: {e}")
            return self._generate_roleplay_11_fallback(user_input, conversation_history, roleplay_config)

    def _build_roleplay_11_prompt(self, user_input: str, conversation_history: List[Dict], 
                               user_context: Dict, roleplay_config: Dict) -> str:
        """Build specialized prompt for Roleplay 1.1"""
        
        # Get prospect persona details
        prospect_title = user_context.get('prospect_job_title', 'CTO')
        prospect_industry = user_context.get('prospect_industry', 'Technology')
        
        # Determine current stage
        current_stage = self._determine_roleplay_11_stage(conversation_history)
        
        # Get stage-specific instructions
        stage_instructions = self._get_roleplay_11_stage_instructions(current_stage)
        
        # Format conversation context
        conversation_context = self._format_conversation_history(conversation_history)
        
        # Build the specialized Roleplay 1.1 prompt
        prompt = self.system_prompts["roleplay_11_prospect"].format(
            job_title=prospect_title,
            industry=prospect_industry,
            current_stage=current_stage,
            conversation_context=conversation_context,
            user_input=user_input,
            stage_instructions=stage_instructions
        )
        
        return prompt

    def _determine_roleplay_11_stage(self, conversation_history: List[Dict]) -> str:
        """Determine current stage in Roleplay 1.1 flow"""
        if not conversation_history:
            return "phone_pickup"
        
        # Count user messages to determine stage
        user_messages = [msg for msg in conversation_history if msg.get('role') == 'user']
        
        if len(user_messages) == 0:
            return "phone_pickup"
        elif len(user_messages) == 1:
            return "opener_evaluation"
        elif len(user_messages) == 2:
            return "objection_handling"
        elif len(user_messages) == 3:
            return "mini_pitch_evaluation"
        elif len(user_messages) >= 4:
            return "soft_discovery"
        
        return "in_progress"

    def _get_roleplay_11_stage_instructions(self, stage: str) -> str:
        """Get detailed stage instructions for Roleplay 1.1"""
        
        instructions = {
            "phone_pickup": "Answer the phone like a busy professional. Say 'Hello?' or similar short greeting.",
            
            "opener_evaluation": self.system_prompts["opener_evaluation"],
            
            "objection_handling": self.system_prompts["objection_handling"],
            
            "mini_pitch_evaluation": self.system_prompts["mini_pitch_evaluation"],
            
            "soft_discovery": self.system_prompts["soft_discovery"],
            
            "silence_impatience": self.system_prompts["silence_impatience"],
            
            "silence_hangup": self.system_prompts["silence_hangup"]
        }
        
        return instructions.get(stage, "Continue natural conversation as a realistic prospect.")

    async def _quick_evaluate_roleplay_11(self, user_input: str, conversation_history: List[Dict], 
                                       roleplay_config: Dict) -> Dict[str, Any]:
        """Quick evaluation for Roleplay 1.1 using OpenAI"""
        try:
            # Build evaluation prompt
            eval_prompt = self._build_roleplay_11_evaluation_prompt(user_input, conversation_history)
            
            # Get evaluation from OpenAI
            eval_response = await self._call_openai_chat(eval_prompt, "Evaluate this Roleplay 1.1 interaction.")
            
            if eval_response:
                # Parse the evaluation response
                return self._parse_roleplay_11_evaluation(eval_response)
            else:
                # Fallback evaluation
                return self._basic_roleplay_11_evaluation(user_input, conversation_history)
                
        except Exception as e:
            logger.error(f"Error in Roleplay 1.1 evaluation: {e}")
            return self._basic_roleplay_11_evaluation(user_input, conversation_history)

    def _build_roleplay_11_evaluation_prompt(self, user_input: str, conversation_history: List[Dict]) -> str:
        """Build evaluation prompt for Roleplay 1.1 rubrics"""
        
        stage = self._determine_roleplay_11_stage(conversation_history)
        
        evaluation_prompt = f"""Analyze this Roleplay 1.1 interaction for evaluation:

**CURRENT STAGE**: {stage}
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

**HANG-UP PROBABILITY**: 
- 0-1 criteria: 80% hang-up chance
- 2 criteria: 30% hang-up chance  
- 3-4 criteria: 10% hang-up chance"""

        elif stage == 'objection_handling':
            evaluation_prompt += """
**OBJECTION HANDLING RUBRIC** (Need 3/4 to pass):
1. Acknowledges calmly ("Fair enough", "Totally get that", "I understand")
2. Doesn't argue or pitch immediately
3. Reframes or buys time in 1 sentence
4. Ends with forward-moving question

**AUTO-FAIL**: Gets defensive, ignores objection, pitches immediately"""

        elif stage == 'mini_pitch_evaluation':
            evaluation_prompt += """
**MINI-PITCH RUBRIC** (Need 3/4 to pass):
1. Short (1-2 sentences, under 30 words)
2. Focuses on problem solved or outcome delivered (not features)
3. Simple English, no jargon or buzzwords
4. Sounds natural, not robotic or memorized

**AUTO-FAIL**: Too long, feature-focused, jargon-heavy, scripted"""

        elif stage == 'soft_discovery':
            evaluation_prompt += """
**SOFT DISCOVERY RUBRIC** (Need 2/3 to pass):
1. Short question tied to the pitch
2. Open/curious question (not leading)
3. Soft, non-pushy tone

**AUTO-FAIL**: No question, too broad, sounds pushy"""

        evaluation_prompt += f"""

**RESPONSE FORMAT**:
- PASS/FAIL: [Pass/Fail]
- SCORE: [0-4 for criteria met]
- CRITERIA_MET: [List specific criteria met]
- SHOULD_HANGUP: [True/False]
- NEXT_STAGE: [Next conversation stage]

Analyze: "{user_input}" """

        return evaluation_prompt

    def _parse_roleplay_11_evaluation(self, eval_response: str) -> Dict[str, Any]:
        """Parse OpenAI evaluation response for Roleplay 1.1"""
        try:
            response_lower = eval_response.lower()
            
            # Extract pass/fail
            passed = 'pass' in response_lower and 'fail' not in response_lower.replace('pass', '')
            
            # Extract hang-up decision
            should_hangup = 'should_hangup: true' in response_lower or 'hang up' in response_lower
            
            # Extract score (look for numbers)
            import re
            score_match = re.search(r'score[:\s]*(\d+)', response_lower)
            score = int(score_match.group(1)) if score_match else (3 if passed else 1)
            
            # Extract criteria
            criteria_met = []
            if 'clear opener' in response_lower or 'clear cold call' in response_lower:
                criteria_met.append('clear_opener')
            if 'casual' in response_lower or 'contractions' in response_lower:
                criteria_met.append('casual_tone')
            if 'empathy' in response_lower or 'out of the blue' in response_lower:
                criteria_met.append('shows_empathy')
            if 'question' in response_lower and 'soft' in response_lower:
                criteria_met.append('soft_question')
            
            return {
                'passed': passed,
                'should_continue': not should_hangup,
                'should_hangup': should_hangup,
                'criteria_met': criteria_met,
                'quality_score': score,
                'evaluation_source': 'openai',
                'raw_evaluation': eval_response
            }
            
        except Exception as e:
            logger.error(f"Error parsing Roleplay 1.1 evaluation: {e}")
            return self._basic_roleplay_11_evaluation("", [])

    def _basic_roleplay_11_evaluation(self, user_input: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Basic fallback evaluation for Roleplay 1.1"""
        # Simple heuristic evaluation
        user_input_lower = user_input.lower()
        score = 2  # Base score
        
        # Basic checks for opener
        if any(contraction in user_input_lower for contraction in ["i'm", "don't", "can't", "we're"]):
            score += 1
        
        if any(empathy in user_input_lower for empathy in ["know this is", "out of the blue", "don't know me"]):
            score += 2
        
        if user_input.strip().endswith('?'):
            score += 1
        
        return {
            'passed': score >= 3,
            'should_continue': score >= 2,
            'should_hangup': score < 2,
            'quality_score': score,
            'evaluation_source': 'fallback'
        }

    def _generate_roleplay_11_fallback(self, user_input: str, conversation_history: List[Dict], 
                                     roleplay_config: Dict) -> Dict[str, Any]:
        """Generate fallback response for Roleplay 1.1"""
        try:
            stage = self._determine_roleplay_11_stage(conversation_history)
            
            # Map stages to appropriate responses
            if stage in ["phone_pickup", "opener_evaluation"]:
                # Use early objection
                responses = self.roleplay_11_specs['early_objections'][:10]
            elif stage == "objection_handling":
                responses = self.fallback_responses["objection_response"]
            elif stage == "mini_pitch_evaluation":
                responses = self.fallback_responses["mini_pitch_response"]
            elif stage == "soft_discovery":
                # Determine if hanging up positively or negatively
                responses = self.fallback_responses["hangup_responses"]["discovery_success"]
            else:
                responses = ["I see. Tell me more.", "Go on.", "That's interesting."]
            
            selected_response = random.choice(responses)
            
            # Basic evaluation
            evaluation = {
                'quality_score': 3,
                'should_continue': stage != "soft_discovery",
                'next_stage': 'in_progress'
            }
            
            logger.info(f"Using Roleplay 1.1 fallback response: {selected_response}")
            
            return {
                'success': True,
                'response': selected_response,
                'evaluation': evaluation,
                'should_continue': evaluation['should_continue'],
                'stage': 'in_progress',
                'fallback_used': True
            }
            
        except Exception as e:
            logger.error(f"Error generating Roleplay 1.1 fallback: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "Can you repeat that?",
                'evaluation': {'quality_score': 3, 'should_continue': True}
            }

    # ===== ROLEPLAY 1.1 COACHING METHODS =====

    async def generate_coaching_feedback(self, session_data: Dict, user_context: Dict) -> Dict[str, Any]:
        """Generate comprehensive coaching feedback for Roleplay 1.1"""
        try:
            if not self.is_enabled:
                return self._generate_roleplay_11_fallback_coaching(session_data)
            
            conversation = session_data.get('conversation_history', [])
            rubric_scores = session_data.get('rubric_scores', {})
            
            # Format conversation for analysis
            conversation_transcript = self._format_conversation_for_coaching(conversation)
            rubric_results = self._format_rubric_results(rubric_scores)
            
            # Build coaching prompt
            coaching_prompt = self.coaching_prompts["roleplay_11_coaching"].format(
                prospect_job_title=user_context.get('prospect_job_title', 'CTO'),
                prospect_industry=user_context.get('prospect_industry', 'Technology'),
                conversation_transcript=conversation_transcript,
                rubric_results=rubric_results
            )
            
            # Generate coaching feedback
            coaching_response = await self._call_openai_chat(coaching_prompt, "Generate Roleplay 1.1 coaching.")
            
            if coaching_response:
                # Parse coaching into categories
                coaching_feedback = self._parse_roleplay_11_coaching(coaching_response)
                
                # Calculate overall score
                overall_score = self._calculate_roleplay_11_score(session_data, rubric_scores)
                
                return {
                    'success': True,
                    'coaching': coaching_feedback,
                    'overall_score': overall_score,
                    'raw_feedback': coaching_response
                }
            else:
                return self._generate_roleplay_11_fallback_coaching(session_data)
            
        except Exception as e:
            logger.error(f"Error generating Roleplay 1.1 coaching: {e}")
            return self._generate_roleplay_11_fallback_coaching(session_data)

    def _format_rubric_results(self, rubric_scores: Dict) -> str:
        """Format rubric results for coaching prompt"""
        if not rubric_scores:
            return "No rubric data available."
        
        formatted = []
        for stage, scores in rubric_scores.items():
            passed = scores.get('passed', False)
            criteria_met = scores.get('criteria_met', [])
            score = scores.get('score', 0)
            
            formatted.append(f"{stage.upper()}: {'PASS' if passed else 'FAIL'} ({score}/4 criteria)")
            if criteria_met:
                formatted.append(f"  - Criteria met: {', '.join(criteria_met)}")
        
        return "\n".join(formatted)

    def _parse_roleplay_11_coaching(self, coaching_text: str) -> Dict[str, str]:
        """Parse coaching feedback into Roleplay 1.1 categories"""
        try:
            # Look for the structured format
            lines = coaching_text.split('\n')
            coaching = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('SALES:'):
                    coaching['sales_coaching'] = line.replace('SALES:', '').strip()
                elif line.startswith('GRAMMAR:'):
                    coaching['grammar_coaching'] = line.replace('GRAMMAR:', '').strip()
                elif line.startswith('VOCABULARY:'):
                    coaching['vocabulary_coaching'] = line.replace('VOCABULARY:', '').strip()
                elif line.startswith('PRONUNCIATION:'):
                    coaching['pronunciation_coaching'] = line.replace('PRONUNCIATION:', '').strip()
                elif line.startswith('RAPPORT:'):
                    coaching['rapport_assertiveness'] = line.replace('RAPPORT:', '').strip()
            
            # Fill in missing categories with defaults
            if 'sales_coaching' not in coaching:
                coaching['sales_coaching'] = 'Practice your opening and objection handling techniques.'
            if 'grammar_coaching' not in coaching:
                coaching['grammar_coaching'] = 'Use contractions like "I\'m" and "don\'t" to sound natural.'
            if 'vocabulary_coaching' not in coaching:
                coaching['vocabulary_coaching'] = 'Use simple, clear business language.'
            if 'pronunciation_coaching' not in coaching:
                coaching['pronunciation_coaching'] = 'Speak clearly and not too fast.'
            if 'rapport_assertiveness' not in coaching:
                coaching['rapport_assertiveness'] = 'Be polite but confident in your delivery.'
            
            return {'coaching': coaching}
            
        except Exception as e:
            logger.error(f"Error parsing Roleplay 1.1 coaching: {e}")
            return self._generate_roleplay_11_fallback_coaching({})['coaching']

    def _calculate_roleplay_11_score(self, session_data: Dict, rubric_scores: Dict) -> int:
        """Calculate score for Roleplay 1.1 based on rubric performance"""
        base_score = 40  # Base participation score
        
        # Add points for each passed rubric (15 points each)
        for stage, scores in rubric_scores.items():
            if scores.get('passed', False):
                base_score += 15
        
        # Bonus for completion without hang-up
        if not session_data.get('hang_up_triggered', False):
            base_score += 10
        
        # Bonus for overall pass
        if session_data.get('overall_call_result') == 'pass':
            base_score += 10
        
        return min(100, max(0, base_score))

    def _generate_roleplay_11_fallback_coaching(self, session_data: Dict) -> Dict[str, Any]:
        """Generate basic coaching when OpenAI unavailable"""
        return {
            'success': True,
            'coaching': {
                'coaching': {
                    'sales_coaching': 'Practice your opening with empathy. Say "I know this is out of the blue".',
                    'grammar_coaching': 'Use contractions like "I\'m" and "don\'t" to sound natural.',
                    'vocabulary_coaching': 'Use simple, clear business words. Say "book a meeting".',
                    'pronunciation_coaching': 'Speak clearly and not too fast. Practice key words.',
                    'rapport_assertiveness': 'Be polite but confident. Show empathy first.'
                }
            },
            'overall_score': 65,
            'fallback_used': True
        }

    # ===== GENERAL METHODS (existing functionality) =====

    async def _generate_general_roleplay_response(self, user_input: str, conversation_history: List[Dict], 
                                                user_context: Dict, roleplay_config: Dict) -> Dict[str, Any]:
        """General roleplay response for non-Roleplay 1.1 scenarios"""
        try:
            # Use existing general roleplay logic
            prompt = self._build_general_roleplay_prompt(user_input, conversation_history, user_context, roleplay_config)
            response = await self._call_openai_chat(prompt, user_input)
            
            if response:
                evaluation = await self._quick_evaluate_input(user_input, conversation_history, roleplay_config)
                return {
                    'success': True,
                    'response': response,
                    'evaluation': evaluation,
                    'should_continue': evaluation.get('should_continue', True),
                    'stage': evaluation.get('next_stage', 'in_progress')
                }
            else:
                return self._generate_fallback_response(user_input, conversation_history, roleplay_config)
            
        except Exception as e:
            logger.error(f"Error generating general roleplay response: {e}")
            return self._generate_fallback_response(user_input, conversation_history, roleplay_config)

    def _build_general_roleplay_prompt(self, user_input: str, conversation_history: List[Dict], 
                                     user_context: Dict, roleplay_config: Dict) -> str:
        """Build general roleplay prompt for non-1.1 scenarios"""
        # Use existing prompt building logic
        return f"""You are a business professional receiving a cold call. 
        Respond naturally and realistically to: "{user_input}"
        Keep responses brief and conversational."""

    async def _call_openai_chat(self, system_prompt: str, user_message: str) -> Optional[str]:
        """Make API call to OpenAI with error handling"""
        try:
            import openai
            
            openai.api_key = self.api_key
            
            logger.info(f"Making OpenAI API call for Roleplay 1.1: {user_message[:50]}...")
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.8,  # Higher temperature for natural variation
                max_tokens=150,   # Shorter responses for realistic phone conversation
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            ai_response = response.choices[0].message.content.strip()
            ai_response = self._clean_ai_response(ai_response)
            
            logger.info(f"OpenAI Roleplay 1.1 response: {ai_response[:100]}...")
            return ai_response
            
        except Exception as e:
            if 'openai' in str(e).lower():
                if 'rate_limit' in str(e).lower():
                    logger.warning("OpenAI rate limit exceeded")
                elif 'authentication' in str(e).lower():
                    logger.error("OpenAI authentication failed - check API key")
                elif 'insufficient_quota' in str(e).lower():
                    logger.error("OpenAI quota exceeded - add billing")
                else:
                    logger.error(f"OpenAI API error: {e}")
            else:
                logger.error(f"Unexpected error calling OpenAI: {e}")
            
            return None

    def _clean_ai_response(self, response: str) -> str:
        """Clean AI response for realistic conversation"""
        # Remove quotes and artifacts
        response = response.replace('"', '').replace("*", "").strip()
        
        # Remove meta-commentary
        if response.startswith("As a") or response.startswith("I am"):
            lines = response.split('\n')
            for line in lines:
                if len(line.strip()) > 0 and not line.startswith("As") and not line.startswith("I am"):
                    response = line.strip()
                    break
        
        # Keep responses realistic length for phone conversation
        if len(response) > 200:
            sentences = response.split('. ')
            response = '. '.join(sentences[:2])
            if not response.endswith('.'):
                response += '.'
        
        return response

    # ===== UTILITY METHODS =====

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

    async def _quick_evaluate_input(self, user_input: str, conversation_history: List[Dict], 
                                  roleplay_config: Dict) -> Dict[str, Any]:
        """Quick evaluation for general roleplays"""
        return {
            'quality_score': 5,
            'should_continue': True,
            'next_stage': 'in_progress',
            'feedback_notes': []
        }

    def _generate_fallback_response(self, user_input: str, conversation_history: List[Dict], 
                                  roleplay_config: Dict) -> Dict[str, Any]:
        """Generate fallback response for any roleplay"""
        responses = ["I see. Tell me more.", "That's interesting.", "Go on.", "Can you explain that?"]
        selected_response = random.choice(responses)
        
        return {
            'success': True,
            'response': selected_response,
            'evaluation': {'quality_score': 5, 'should_continue': True},
            'should_continue': True,
            'stage': 'in_progress',
            'fallback_used': True
        }

    def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.is_enabled

    def get_status(self) -> Dict[str, Any]:
        """Get service status information"""
        return {
            'enabled': self.is_enabled,
            'api_key_configured': bool(self.api_key),
            'model': self.model,
            'status': 'ready' if self.is_enabled else 'fallback_mode',
            'roleplay_11_ready': True,
            'specifications': {
                'early_objections_count': len(self.roleplay_11_specs['early_objections']),
                'impatience_phrases_count': len(self.roleplay_11_specs['impatience_phrases'])
            }
        }
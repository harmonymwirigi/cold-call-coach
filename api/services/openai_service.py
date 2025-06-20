# ===== FIXED API/SERVICES/OPENAI_SERVICE.PY - SIMPLE & WORKING =====

import os
import json
import random
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Use the correct OpenAI import for 2024
try:
    from openai import OpenAI
except ImportError:
    print("ERROR: Please install openai: pip install openai")
    OpenAI = None

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv('REACT_APP_OPENAI_API_KEY')
        self.model = "gpt-4o-mini"  # Fast and efficient model
        self.is_enabled = bool(self.api_key and OpenAI)
        
        if self.is_enabled:
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI service initialized successfully")
            # Test the connection
            self._test_connection()
        else:
            logger.warning("OpenAI service disabled - no API key or library not installed")
            self.client = None
        
        # Load roleplay prompts and fallbacks
        self._load_roleplay_1_prompts()
        self._load_fallback_responses()

    def _test_connection(self):
        """Test OpenAI connection and log the result"""
        try:
            # Simple test call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            logger.info("✅ OpenAI connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ OpenAI connection test failed: {e}")
            self.is_enabled = False
            return False

    def _load_roleplay_1_prompts(self):
        """Load Roleplay 1.1 specific prompts"""
        self.roleplay_1_prompts = {
            "prospect_system": """You are a realistic business prospect receiving a COLD CALL. This is Roleplay 1.1 training.

CRITICAL: Stay in character as the prospect at all times. Never break character.

YOU ARE: {job_title} at a {industry} company
CURRENT STAGE: {stage}

ROLEPLAY 1.1 FLOW:
1. Phone Pickup → SDR gives opener
2. Evaluate opener → Give early objection if good, hang up if bad  
3. SDR handles objection → Give mini-pitch opportunity if handled well
4. SDR gives mini-pitch → Give discovery opportunity if good
5. SDR asks discovery → End call with result

STAGE-SPECIFIC BEHAVIOR:
{stage_instructions}

Keep responses SHORT (1-2 sentences). Be realistic and challenging but fair.
This is training - help them learn by being a realistic prospect.""",

            "evaluation_system": """Evaluate this Roleplay 1.1 interaction as an expert sales trainer.

CONVERSATION:
{conversation}

USER'S LATEST INPUT: "{user_input}"
CURRENT STAGE: {stage}

EVALUATE BASED ON ROLEPLAY 1.1 RUBRIC:
{rubric_criteria}

RESPOND WITH VALID JSON:
{
  "score": <0-4>,
  "passed": <true/false>,
  "criteria_met": ["criterion1", "criterion2"],
  "feedback": "Brief feedback",
  "should_continue": <true/false>,
  "next_action": "continue|objection|pitch|discovery|hangup"
}"""
        }

        self.stage_instructions = {
            "phone_pickup": "Answer like a busy professional: 'Hello?' or 'Hi there.'",
            
            "opener_evaluation": """Evaluate their opener:
- 0-1 criteria met: 80% chance hang up ("Not interested. *click*")  
- 2 criteria met: 30% chance hang up, otherwise give objection
- 3-4 criteria met: 10% chance hang up, otherwise give mild objection

Criteria: 1) Clear opener (not just greeting) 2) Casual tone with contractions 3) Shows empathy 4) Ends with soft question""",

            "early_objection": """Give ONE of these objections:
"What's this about?", "I'm not interested", "Now is not a good time", "I have a meeting", 
"Send me an email", "Who gave you this number?", "Is this a sales call?", "We're all good"

Be realistic and challenging.""",

            "objection_handling": """They should: 1) Acknowledge calmly 2) Not argue 3) Reframe briefly 4) Ask forward question
If handled well: "Alright, I'm listening" / "Go ahead, what is it?"
If handled poorly: Stronger objection or hang up""",

            "mini_pitch": """They should give short pitch focused on outcomes, not features.
If good pitch: "That's interesting. Tell me more." / "How exactly do you do that?"
If poor pitch: "I don't understand" / "That sounds like everything else" """,

            "soft_discovery": """They should ask open question tied to their pitch.
If good question: End positively "That's a good question. Send me info. Goodbye."
If poor question: End negatively "Not relevant. This isn't going anywhere." """
        }

        self.rubric_criteria = {
            "opener": """OPENER RUBRIC (need 3/4 to pass):
1. Clear cold call opener (not just greeting)
2. Casual tone (uses contractions like "I'm", "don't") 
3. Shows empathy ("I know this is out of the blue")
4. Ends with soft question ("Can I tell you why I'm calling?")""",

            "objection_handling": """OBJECTION HANDLING RUBRIC (need 3/4 to pass):
1. Acknowledges calmly ("Fair enough", "I understand")
2. Doesn't argue or pitch immediately  
3. Reframes or buys time in 1 sentence
4. Ends with forward-moving question""",

            "mini_pitch": """MINI-PITCH RUBRIC (need 3/4 to pass):
1. Short (1-2 sentences, under 30 words)
2. Focuses on outcomes/problems solved (not features)
3. Simple English, no jargon 
4. Sounds natural, not robotic""",

            "soft_discovery": """SOFT DISCOVERY RUBRIC (need 2/3 to pass):
1. Short question tied to the pitch
2. Open/curious question (not leading)
3. Soft, non-pushy tone"""
        }

    def _load_fallback_responses(self):
        """Load fallback responses when OpenAI fails"""
        self.fallbacks = {
            "phone_pickup": ["Hello?", "Hi there.", "Good morning.", "Yes?"],
            
            "early_objections": [
                "What's this about?", "I'm not interested", "Now is not a good time",
                "I have a meeting", "Send me an email", "Who gave you this number?",
                "Is this a sales call?", "We're all good"
            ],
            
            "objection_responses": [
                "Alright, I'm listening.", "Go ahead, what is it?", "You have 30 seconds.",
                "This better be good.", "What exactly do you do?"
            ],
            
            "pitch_responses": [
                "That's interesting. Tell me more.", "How exactly do you do that?",
                "What does that look like?", "I don't understand what you're saying."
            ],
            
            "discovery_endings": {
                "positive": ["That's a good question. Send me information. Goodbye.",
                           "Interesting. Email me the details."],
                "negative": ["That's not relevant to us. Goodbye.",
                           "This conversation isn't going anywhere."]
            }
        }

    # ===== MAIN ROLEPLAY 1.1 METHODS =====

    def generate_roleplay_response(self, user_input: str, conversation_history: List[Dict], 
                                 user_context: Dict, current_stage: str) -> Dict[str, Any]:
        """Generate AI prospect response for Roleplay 1.1"""
        try:
            logger.info(f"Generating response for stage: {current_stage}")
            
            if not self.is_enabled:
                logger.warning("OpenAI disabled, using fallback")
                return self._generate_fallback_response(current_stage, user_input)
            
            # Build the prompt
            prompt = self._build_prospect_prompt(user_input, conversation_history, user_context, current_stage)
            
            # Call OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"User said: '{user_input}'. Respond as the prospect."}
                ],
                temperature=0.8,
                max_tokens=100,  # Keep responses short
                timeout=10
            )
            
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"OpenAI response: {ai_response[:50]}...")
            
            return {
                'success': True,
                'response': ai_response,
                'source': 'openai'
            }
            
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return self._generate_fallback_response(current_stage, user_input)

    def evaluate_user_input(self, user_input: str, conversation_history: List[Dict], 
                          current_stage: str) -> Dict[str, Any]:
        """Evaluate user input using Roleplay 1.1 rubrics"""
        try:
            logger.info(f"Evaluating input for stage: {current_stage}")
            
            if not self.is_enabled:
                logger.warning("OpenAI disabled, using basic evaluation")
                return self._basic_evaluation(user_input, current_stage)
            
            # Build evaluation prompt
            conversation_text = self._format_conversation(conversation_history)
            rubric = self.rubric_criteria.get(current_stage, "Evaluate the input quality (1-5)")
            
            prompt = self.roleplay_1_prompts["evaluation_system"].format(
                conversation=conversation_text,
                user_input=user_input,
                stage=current_stage,
                rubric_criteria=rubric
            )
            
            # Call OpenAI for evaluation
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower temperature for consistent evaluation
                max_tokens=200,
                timeout=10
            )
            
            # Parse the JSON response
            eval_text = response.choices[0].message.content.strip()
            logger.info(f"Evaluation response: {eval_text}")
            
            try:
                evaluation = json.loads(eval_text)
                evaluation['source'] = 'openai'
                return evaluation
            except json.JSONDecodeError:
                logger.warning("Failed to parse evaluation JSON, using basic evaluation")
                return self._basic_evaluation(user_input, current_stage)
                
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return self._basic_evaluation(user_input, current_stage)

    def generate_coaching_feedback(self, conversation_history: List[Dict], 
                                 rubric_scores: Dict, user_context: Dict) -> Dict[str, Any]:
        """Generate CEFR A2 coaching feedback"""
        try:
            if not self.is_enabled:
                return self._basic_coaching(rubric_scores)
            
            conversation_text = self._format_conversation(conversation_history)
            
            coaching_prompt = f"""Analyze this Roleplay 1.1 session and provide coaching in CEFR A2 English (simple, clear language for Spanish speakers learning English).

CONVERSATION:
{conversation_text}

RUBRIC RESULTS:
{json.dumps(rubric_scores, indent=2)}

Provide EXACTLY this format:
SALES: [One specific tip about sales performance]
GRAMMAR: [One grammar tip in simple English] 
VOCABULARY: [One vocabulary tip about business language]
PRONUNCIATION: [One pronunciation tip or praise]
RAPPORT: [One tip about confidence/empathy or praise]

Keep all feedback in CEFR A2 level - short sentences, simple words, clear instructions."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": coaching_prompt}],
                temperature=0.5,
                max_tokens=300,
                timeout=15
            )
            
            coaching_text = response.choices[0].message.content.strip()
            coaching = self._parse_coaching_response(coaching_text)
            
            # Calculate score
            score = self._calculate_score(rubric_scores)
            
            return {
                'success': True,
                'coaching': coaching,
                'score': score,
                'source': 'openai'
            }
            
        except Exception as e:
            logger.error(f"Coaching generation error: {e}")
            return self._basic_coaching(rubric_scores)

    # ===== HELPER METHODS =====

    def _build_prospect_prompt(self, user_input: str, conversation_history: List[Dict], 
                             user_context: Dict, current_stage: str) -> str:
        """Build the prospect system prompt"""
        job_title = user_context.get('prospect_job_title', 'CTO')
        industry = user_context.get('prospect_industry', 'Technology')
        stage_instructions = self.stage_instructions.get(current_stage, "Continue natural conversation")
        
        return self.roleplay_1_prompts["prospect_system"].format(
            job_title=job_title,
            industry=industry,
            stage=current_stage,
            stage_instructions=stage_instructions
        )

    def _format_conversation(self, conversation_history: List[Dict]) -> str:
        """Format conversation history for prompts"""
        if not conversation_history:
            return "No conversation yet."
        
        formatted = []
        for msg in conversation_history[-6:]:  # Last 6 messages
            role = "SDR" if msg.get('role') == 'user' else "Prospect"
            content = msg.get('content', '')
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)

    def _generate_fallback_response(self, current_stage: str, user_input: str = "") -> Dict[str, Any]:
        """Generate fallback response when OpenAI fails"""
        try:
            if current_stage == "phone_pickup":
                response = random.choice(self.fallbacks["phone_pickup"])
            elif current_stage in ["opener_evaluation", "early_objection"]:
                response = random.choice(self.fallbacks["early_objections"])
            elif current_stage == "objection_handling":
                response = random.choice(self.fallbacks["objection_responses"])
            elif current_stage == "mini_pitch":
                response = random.choice(self.fallbacks["pitch_responses"])
            elif current_stage == "soft_discovery":
                # Randomly pick positive or negative ending
                ending_type = "positive" if random.random() > 0.5 else "negative"
                response = random.choice(self.fallbacks["discovery_endings"][ending_type])
            else:
                response = "I see. Continue."
            
            logger.info(f"Using fallback response: {response}")
            
            return {
                'success': True,
                'response': response,
                'source': 'fallback'
            }
            
        except Exception as e:
            logger.error(f"Fallback generation error: {e}")
            return {
                'success': True,
                'response': "Can you repeat that?",
                'source': 'emergency'
            }

    def _basic_evaluation(self, user_input: str, current_stage: str) -> Dict[str, Any]:
        """Basic evaluation when OpenAI fails"""
        # Simple heuristic scoring
        score = 2  # Base score
        criteria_met = []
        
        user_input_lower = user_input.lower()
        
        # Basic checks based on stage
        if current_stage == "opener":
            if any(word in user_input_lower for word in ["i'm", "don't", "can't"]):
                score += 1
                criteria_met.append("casual_tone")
            
            if any(phrase in user_input_lower for phrase in ["out of the blue", "don't know me"]):
                score += 1
                criteria_met.append("shows_empathy")
            
            if user_input.strip().endswith('?'):
                score += 1
                criteria_met.append("ends_with_question")
        
        elif current_stage == "objection_handling":
            if any(word in user_input_lower for word in ["understand", "fair enough", "get that"]):
                score += 1
                criteria_met.append("acknowledges_calmly")
            
            if user_input.strip().endswith('?'):
                score += 1
                criteria_met.append("forward_question")
        
        passed = score >= 3
        
        return {
            'score': score,
            'passed': passed,
            'criteria_met': criteria_met,
            'feedback': f'Basic evaluation: {score}/4 criteria met',
            'should_continue': True,
            'next_action': 'continue',
            'source': 'basic'
        }

    def _parse_coaching_response(self, coaching_text: str) -> Dict[str, str]:
        """Parse coaching response into categories"""
        coaching = {}
        
        lines = coaching_text.split('\n')
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
        
        # Fill in defaults if missing
        if 'sales_coaching' not in coaching:
            coaching['sales_coaching'] = 'Practice your opening and objection handling.'
        if 'grammar_coaching' not in coaching:
            coaching['grammar_coaching'] = 'Use contractions like "I\'m" and "don\'t" to sound natural.'
        if 'vocabulary_coaching' not in coaching:
            coaching['vocabulary_coaching'] = 'Use simple, clear business words.'
        if 'pronunciation_coaching' not in coaching:
            coaching['pronunciation_coaching'] = 'Speak clearly and not too fast.'
        if 'rapport_assertiveness' not in coaching:
            coaching['rapport_assertiveness'] = 'Be polite but confident.'
        
        return coaching

    def _calculate_score(self, rubric_scores: Dict) -> int:
        """Calculate overall score from rubric results"""
        base_score = 40  # Base participation score
        
        # Add points for each passed rubric (15 points each)
        for stage_scores in rubric_scores.values():
            if stage_scores.get('passed', False):
                base_score += 15
        
        return min(100, max(0, base_score))

    def _basic_coaching(self, rubric_scores: Dict) -> Dict[str, Any]:
        """Basic coaching when OpenAI fails"""
        score = self._calculate_score(rubric_scores)
        
        coaching = {
            'sales_coaching': 'Practice your opening with empathy. Use "I know this is out of the blue".',
            'grammar_coaching': 'Use contractions like "I\'m" and "don\'t" to sound natural.',
            'vocabulary_coaching': 'Use simple, clear business words. Say "book a meeting".',
            'pronunciation_coaching': 'Speak clearly and not too fast. Practice key words.',
            'rapport_assertiveness': 'Be polite but confident. Show empathy first.'
        }
        
        return {
            'success': True,
            'coaching': coaching,
            'score': score,
            'source': 'basic'
        }

    # ===== STATUS METHODS =====

    def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.is_enabled

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        status = {
            'enabled': self.is_enabled,
            'api_key_configured': bool(self.api_key),
            'model': self.model,
            'client_available': bool(self.client)
        }
        
        if self.is_enabled and self.client:
            # Test connection
            try:
                test_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1
                )
                status['connection_test'] = 'success'
            except Exception as e:
                status['connection_test'] = f'failed: {str(e)}'
        else:
            status['connection_test'] = 'not_tested'
        
        return status

    def test_roleplay_flow(self) -> Dict[str, Any]:
        """Test the complete roleplay flow"""
        if not self.is_enabled:
            return {'success': False, 'error': 'OpenAI not enabled'}
        
        try:
            # Test prospect response
            user_context = {'prospect_job_title': 'CTO', 'prospect_industry': 'Technology'}
            response_result = self.generate_roleplay_response(
                "Hi, I know this is out of the blue, but can I tell you why I'm calling?",
                [],
                user_context,
                "opener_evaluation"
            )
            
            # Test evaluation
            eval_result = self.evaluate_user_input(
                "Hi, I know this is out of the blue, but can I tell you why I'm calling?",
                [],
                "opener"
            )
            
            return {
                'success': True,
                'prospect_response': response_result,
                'evaluation': eval_result
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
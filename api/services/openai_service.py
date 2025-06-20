# ===== FIXED API/SERVICES/OPENAI_SERVICE.PY - JSON PARSING FIXED =====

import os
import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        """Initialize OpenAI service with proper error handling"""
        self.api_key = os.getenv('REACT_APP_OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
        self.client = None
        self.model = "gpt-4o-mini"  # Fast and cost-effective
        self.is_enabled = False
        
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.is_enabled = True
                logger.info("OpenAI service initialized successfully")
                
                # Test the connection
                self._test_connection()
                
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")
                self.is_enabled = False
        else:
            logger.warning("OpenAI API key not found in environment variables")
    
    def _test_connection(self):
        """Test OpenAI connection"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5,
                timeout=10
            )
            logger.info("✅ OpenAI connection test successful")
            return True
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            self.is_enabled = False
            return False
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.is_enabled and self.client is not None
    
    def evaluate_user_input(self, user_input: str, conversation_history: List[Dict], evaluation_stage: str) -> Dict[str, Any]:
        """Evaluate user input using OpenAI for Roleplay 1.1"""
        if not self.is_available():
            logger.warning("OpenAI not available for evaluation")
            return self._fallback_evaluation(user_input, evaluation_stage)
        
        try:
            logger.info(f"Evaluating input for stage: {evaluation_stage}")
            
            # Build conversation context
            context = self._build_conversation_context(conversation_history)
            
            # Create evaluation prompt based on stage
            evaluation_prompt = self._create_evaluation_prompt(user_input, evaluation_stage, context)
            
            # Call OpenAI with structured output request
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert cold calling coach. Evaluate sales conversations and respond ONLY with valid JSON. No explanations, no markdown, just JSON."
                    },
                    {
                        "role": "user", 
                        "content": evaluation_prompt
                    }
                ],
                temperature=0.2,
                max_tokens=800,
                timeout=15
            )
            
            # Parse response with improved error handling
            evaluation_text = response.choices[0].message.content.strip()
            logger.info(f"Raw OpenAI response: {evaluation_text[:200]}...")
            
            evaluation = self._parse_evaluation_response_robust(evaluation_text, evaluation_stage)
            
            logger.info(f"✅ OpenAI evaluation successful: score={evaluation.get('score', 0)}, passed={evaluation.get('passed', False)}")
            return evaluation
            
        except Exception as e:
            logger.error(f"OpenAI evaluation failed: {e}")
            return self._fallback_evaluation(user_input, evaluation_stage)
    
    def _create_evaluation_prompt(self, user_input: str, stage: str, context: str) -> str:
        """Create evaluation prompt for specific stage"""
        
        base_prompt = f"""
EVALUATE ROLEPLAY 1.1 - {stage.upper()} STAGE

Context: {context}

User Input: "{user_input}"

Criteria for {stage}:
"""
        
        if stage == "opener":
            criteria_prompt = """
1. Clear opener (NOT just "hello") - mentions calling reason/company
2. Casual tone - uses contractions like "I'm", "don't"  
3. Shows empathy - "I know this is out of the blue", "You don't know me"
4. Ends with question - "Can I tell you why I'm calling?"

Pass: 3/4 criteria needed
"""
        elif stage == "objection_handling":
            criteria_prompt = """
1. Acknowledges calmly - "Fair enough", "I understand"
2. No arguing/defending - doesn't get defensive
3. Brief reframe - explains why calling in 1 sentence
4. Forward question - moves conversation ahead

Pass: 3/4 criteria needed
"""
        elif stage == "mini_pitch":
            criteria_prompt = """
1. Short - under 30 words, 1-2 sentences
2. Outcome focused - mentions benefits/results not features
3. Simple language - no jargon or buzzwords
4. Natural tone - conversational not robotic

Pass: 3/4 criteria needed
"""
        elif stage == "soft_discovery":
            criteria_prompt = """
1. Asks question tied to pitch
2. Open question - "How", "What", not yes/no
3. Soft tone - curious not pushy

Pass: 2/3 criteria needed
"""
        else:
            criteria_prompt = """
1. Professional communication
2. Clear message
3. Appropriate response
4. Moves conversation forward

Pass: 3/4 criteria needed
"""
        
        return base_prompt + criteria_prompt + """

Respond with ONLY this JSON format:
{
"score": [number 0-4],
"passed": [true/false],
"criteria_met": ["criterion1", "criterion2"],
"feedback": "Brief specific feedback",
"should_continue": true,
"next_action": "continue",
"hang_up_probability": [0.0-1.0]
}

No other text, no markdown, just JSON.
"""
    
    def _parse_evaluation_response_robust(self, response_text: str, stage: str) -> Dict[str, Any]:
        """Robust JSON parsing with multiple fallback strategies"""
        try:
            # Strategy 1: Direct JSON parse
            try:
                evaluation = json.loads(response_text)
                return self._validate_and_clean_evaluation(evaluation, stage)
            except json.JSONDecodeError:
                pass
            
            # Strategy 2: Find JSON block in response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    evaluation = json.loads(json_str)
                    return self._validate_and_clean_evaluation(evaluation, stage)
                except json.JSONDecodeError:
                    pass
            
            # Strategy 3: Clean and try again
            cleaned_text = response_text.strip()
            # Remove markdown code blocks
            cleaned_text = re.sub(r'```json\s*', '', cleaned_text)
            cleaned_text = re.sub(r'```\s*', '', cleaned_text)
            # Remove extra whitespace and newlines
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
            
            try:
                evaluation = json.loads(cleaned_text)
                return self._validate_and_clean_evaluation(evaluation, stage)
            except json.JSONDecodeError:
                pass
                
            # Strategy 4: Extract values manually
            logger.warning("JSON parsing failed, attempting manual extraction")
            evaluation = self._manual_extract_evaluation(response_text, stage)
            if evaluation:
                return evaluation
            
            # Strategy 5: Fallback
            logger.error(f"All parsing strategies failed for: {response_text[:100]}...")
            return self._fallback_evaluation("", stage)
                
        except Exception as e:
            logger.error(f"Critical parsing error: {e}")
            return self._fallback_evaluation("", stage)
    
    def _manual_extract_evaluation(self, text: str, stage: str) -> Optional[Dict[str, Any]]:
        """Manually extract evaluation data from text"""
        try:
            # Extract score
            score_match = re.search(r'"score":\s*(\d+)', text)
            score = int(score_match.group(1)) if score_match else 2
            
            # Extract passed
            passed_match = re.search(r'"passed":\s*(true|false)', text)
            passed = passed_match.group(1) == 'true' if passed_match else (score >= 3)
            
            # Extract feedback
            feedback_match = re.search(r'"feedback":\s*"([^"]*)"', text)
            feedback = feedback_match.group(1) if feedback_match else f"Manual extraction for {stage}"
            
            # Extract criteria
            criteria_pattern = r'"criteria_met":\s*\[(.*?)\]'
            criteria_match = re.search(criteria_pattern, text, re.DOTALL)
            criteria_met = []
            if criteria_match:
                criteria_text = criteria_match.group(1)
                criteria_items = re.findall(r'"([^"]*)"', criteria_text)
                criteria_met = criteria_items
            
            evaluation = {
                'score': score,
                'passed': passed,
                'criteria_met': criteria_met,
                'feedback': feedback,
                'should_continue': True,
                'next_action': 'continue',
                'hang_up_probability': 0.8 if score <= 1 else (0.3 if score == 2 else 0.1),
                'source': 'manual_extraction',
                'stage': stage
            }
            
            logger.info(f"Manual extraction successful: {evaluation}")
            return evaluation
            
        except Exception as e:
            logger.error(f"Manual extraction failed: {e}")
            return None
    
    def _validate_and_clean_evaluation(self, evaluation: Dict, stage: str) -> Dict[str, Any]:
        """Validate and clean up evaluation data"""
        try:
            # Ensure required fields with defaults
            cleaned = {
                'score': max(0, min(4, int(evaluation.get('score', 0)))),
                'passed': bool(evaluation.get('passed', False)),
                'criteria_met': evaluation.get('criteria_met', []),
                'feedback': str(evaluation.get('feedback', 'No feedback provided')),
                'should_continue': bool(evaluation.get('should_continue', True)),
                'next_action': evaluation.get('next_action', 'continue'),
                'hang_up_probability': float(evaluation.get('hang_up_probability', 0.1)),
                'source': 'openai',
                'stage': stage
            }
            
            # Ensure criteria_met is a list
            if not isinstance(cleaned['criteria_met'], list):
                cleaned['criteria_met'] = []
            
            # Validate hang_up_probability range
            cleaned['hang_up_probability'] = max(0.0, min(1.0, cleaned['hang_up_probability']))
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return self._fallback_evaluation("", stage)
    
    def generate_roleplay_response(self, user_input: str, conversation_history: List[Dict], 
                                 user_context: Dict, current_stage: str) -> Dict[str, Any]:
        """Generate AI prospect response"""
        if not self.is_available():
            logger.warning("OpenAI not available for response generation")
            return {
                'success': False,
                'response': self._get_fallback_response(current_stage),
                'source': 'fallback'
            }
        
        try:
            logger.info(f"Generating response for stage: {current_stage}")
            
            # Build context
            context = self._build_conversation_context(conversation_history)
            prospect_info = self._get_prospect_info(user_context)
            
            # Create response prompt
            response_prompt = f"""
You are a {prospect_info['job_title']} at a {prospect_info['industry']} company receiving a cold call.

STAGE: {current_stage}
CONVERSATION: {context}
CALLER JUST SAID: "{user_input}"

Be realistic and natural. Keep responses 1-2 sentences.

Stage behavior:
- opener_evaluation: Show mild skepticism, ask "What's this about?"
- early_objection: Give common objection like "Not interested" or "No time"  
- objection_handling: If they handle well, show slight interest
- mini_pitch: If pitch is good, ask follow-up question
- soft_discovery: Answer briefly then wrap up

Respond as the prospect (no quotes, just what you'd say):
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a realistic business prospect in a cold call. Be natural and brief."},
                    {"role": "user", "content": response_prompt}
                ],
                temperature=0.7,
                max_tokens=100,
                timeout=15
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Clean up response
            ai_response = ai_response.replace('"', '').strip()
            if ai_response.startswith("Prospect:"):
                ai_response = ai_response.replace("Prospect:", "").strip()
            
            logger.info(f"OpenAI response: {ai_response[:50]}...")
            
            return {
                'success': True,
                'response': ai_response,
                'source': 'openai'
            }
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return {
                'success': False,
                'response': self._get_fallback_response(current_stage),
                'source': 'fallback'
            }
    
    def generate_coaching_feedback(self, conversation_history: List[Dict], 
                                 rubric_scores: Dict, user_context: Dict) -> Dict[str, Any]:
        """Generate coaching feedback using OpenAI"""
        if not self.is_available():
            logger.warning("OpenAI not available for coaching")
            return self._fallback_coaching(rubric_scores)
        
        try:
            logger.info("Generating coaching feedback with OpenAI")
            
            # Build conversation summary
            conversation_text = self._build_full_conversation(conversation_history)
            scores_summary = self._build_scores_summary(rubric_scores)
            
            coaching_prompt = f"""
COACHING FEEDBACK - ROLEPLAY 1.1

CONVERSATION:
{conversation_text}

SCORES:
{scores_summary}

USER: {user_context.get('prospect_job_title', 'Executive')} in {user_context.get('prospect_industry', 'Technology')}

Provide specific coaching in these 5 areas (2-3 sentences each):

1. SALES COACHING: Opener, objection handling, pitch effectiveness
2. GRAMMAR COACHING: Sentence structure, verb tenses, articles  
3. VOCABULARY COACHING: Word choice, business terms
4. PRONUNCIATION COACHING: Speech clarity tips
5. RAPPORT & ASSERTIVENESS: Tone, confidence, empathy

Respond with ONLY this JSON:
{{
"sales_coaching": "Specific sales advice...",
"grammar_coaching": "Grammar tips...",
"vocabulary_coaching": "Vocabulary suggestions...",
"pronunciation_coaching": "Pronunciation advice...",
"rapport_assertiveness": "Tone and confidence tips...",
"overall_score": [0-100 number]
}}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a cold calling coach. Respond only with JSON."},
                    {"role": "user", "content": coaching_prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
                timeout=20
            )
            
            coaching_text = response.choices[0].message.content.strip()
            coaching_data = self._parse_coaching_response_robust(coaching_text, rubric_scores)
            
            logger.info(f"Coaching generated successfully")
            
            return {
                'success': True,
                'coaching': coaching_data['coaching'],
                'score': coaching_data['score'],
                'source': 'openai'
            }
            
        except Exception as e:
            logger.error(f"Coaching generation failed: {e}")
            return self._fallback_coaching(rubric_scores)
    
    def _parse_coaching_response_robust(self, response_text: str, rubric_scores: Dict) -> Dict[str, Any]:
        """Robust coaching response parsing"""
        try:
            # Try direct JSON parse
            try:
                coaching_data = json.loads(response_text)
                return self._validate_coaching_data(coaching_data, rubric_scores)
            except json.JSONDecodeError:
                pass
            
            # Try finding JSON in text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    coaching_data = json.loads(json_match.group(0))
                    return self._validate_coaching_data(coaching_data, rubric_scores)
                except json.JSONDecodeError:
                    pass
            
            # Manual extraction
            logger.warning("Using manual coaching extraction")
            return self._manual_extract_coaching(response_text, rubric_scores)
                
        except Exception as e:
            logger.error(f"Coaching parsing failed: {e}")
            return self._fallback_coaching(rubric_scores)
    
    def _manual_extract_coaching(self, text: str, rubric_scores: Dict) -> Dict[str, Any]:
        """Manually extract coaching from text"""
        try:
            coaching = {}
            
            # Extract each coaching category
            categories = [
                'sales_coaching',
                'grammar_coaching', 
                'vocabulary_coaching',
                'pronunciation_coaching',
                'rapport_assertiveness'
            ]
            
            for category in categories:
                pattern = f'"{category}":\\s*"([^"]*)"'
                match = re.search(pattern, text)
                if match:
                    coaching[category] = match.group(1)
                else:
                    coaching[category] = f"Practice your {category.replace('_', ' ')} skills."
            
            # Extract overall score
            score_match = re.search(r'"overall_score":\s*(\d+)', text)
            score = int(score_match.group(1)) if score_match else self._calculate_score_from_rubrics(rubric_scores)
            
            return {
                'coaching': coaching,
                'score': score
            }
            
        except Exception as e:
            logger.error(f"Manual coaching extraction failed: {e}")
            return self._fallback_coaching(rubric_scores)
    
    def _validate_coaching_data(self, coaching_data: Dict, rubric_scores: Dict) -> Dict[str, Any]:
        """Validate coaching data"""
        try:
            categories = [
                'sales_coaching',
                'grammar_coaching',
                'vocabulary_coaching', 
                'pronunciation_coaching',
                'rapport_assertiveness'
            ]
            
            coaching = {}
            for category in categories:
                coaching[category] = str(coaching_data.get(category, f"Practice {category.replace('_', ' ')}."))
            
            score = max(0, min(100, int(coaching_data.get('overall_score', 50))))
            
            return {
                'coaching': coaching,
                'score': score
            }
            
        except Exception as e:
            logger.error(f"Coaching validation failed: {e}")
            return self._fallback_coaching(rubric_scores)
    
    def _calculate_score_from_rubrics(self, rubric_scores: Dict) -> int:
        """Calculate score from rubric scores"""
        if not rubric_scores:
            return 50
        
        total_score = sum(scores.get('score', 0) for scores in rubric_scores.values())
        max_possible = len(rubric_scores) * 4
        
        if max_possible > 0:
            percentage = int((total_score / max_possible) * 100)
            return max(30, min(100, percentage))
        
        return 50
    
    # Helper methods
    
    def _build_conversation_context(self, conversation_history: List[Dict]) -> str:
        """Build conversation context string"""
        if not conversation_history:
            return "Prospect just answered phone."
        
        context_lines = []
        for msg in conversation_history[-4:]:  # Last 4 messages
            role = "Prospect" if msg.get('role') == 'assistant' else "Caller"
            content = msg.get('content', '')
            context_lines.append(f"{role}: {content}")
        
        return " | ".join(context_lines)
    
    def _build_full_conversation(self, conversation_history: List[Dict]) -> str:
        """Build full conversation text"""
        conversation_lines = []
        for msg in conversation_history:
            role = "Prospect" if msg.get('role') == 'assistant' else "Caller"
            content = msg.get('content', '')
            conversation_lines.append(f"{role}: {content}")
        
        return "\n".join(conversation_lines) if conversation_lines else "No conversation"
    
    def _build_scores_summary(self, rubric_scores: Dict) -> str:
        """Build scores summary"""
        if not rubric_scores:
            return "No scores"
        
        summary_lines = []
        for stage, scores in rubric_scores.items():
            score = scores.get('score', 0)
            passed = "PASSED" if scores.get('passed', False) else "FAILED"
            summary_lines.append(f"{stage}: {score}/4 {passed}")
        
        return " | ".join(summary_lines)
    
    def _get_prospect_info(self, user_context: Dict) -> Dict[str, str]:
        """Extract prospect information"""
        return {
            'job_title': user_context.get('prospect_job_title', 'CTO'),
            'industry': user_context.get('prospect_industry', 'Technology')
        }
    
    def _get_fallback_response(self, stage: str) -> str:
        """Get fallback response when OpenAI fails"""
        responses = {
            'opener_evaluation': ["What's this about?", "I'm not interested.", "Now is not a good time."],
            'early_objection': ["Not interested.", "We don't take cold calls.", "Send me an email."],
            'objection_handling': ["Alright, I'm listening.", "Go ahead.", "You have 30 seconds."],
            'mini_pitch': ["Tell me more.", "How does that work?", "I don't understand."],
            'soft_discovery': ["Send me information.", "Not relevant to us.", "I'll think about it."]
        }
        
        import random
        stage_responses = responses.get(stage, ["I see."])
        return random.choice(stage_responses)
    
    def _fallback_evaluation(self, user_input: str, stage: str) -> Dict[str, Any]:
        """Enhanced fallback evaluation"""
        logger.info(f"Using fallback evaluation for {stage}")
        
        score = 0
        criteria_met = []
        user_input_lower = user_input.lower().strip()
        
        # Basic analysis
        if len(user_input.strip()) > 15:
            score += 1
            criteria_met.append('substantial_input')
        
        if any(contraction in user_input_lower for contraction in ["i'm", "don't", "can't", "we're"]):
            score += 1
            criteria_met.append('casual_tone')
        
        if any(empathy in user_input_lower for empathy in ["know this is", "out of the blue", "interrupting"]):
            score += 1
            criteria_met.append('shows_empathy')
        
        if user_input.strip().endswith('?'):
            score += 1
            criteria_met.append('ends_with_question')
        
        passed = score >= 2
        
        return {
            'score': score,
            'passed': passed,
            'criteria_met': criteria_met,
            'feedback': f'Basic evaluation: {score}/4 criteria met',
            'should_continue': True,
            'next_action': 'continue',
            'hang_up_probability': 0.8 if score <= 1 else (0.3 if score == 2 else 0.1),
            'source': 'basic',
            'stage': stage
        }
    
    def _fallback_coaching(self, rubric_scores: Dict) -> Dict[str, Any]:
        """Enhanced fallback coaching"""
        logger.info("Using fallback coaching")
        
        score = self._calculate_score_from_rubrics(rubric_scores)
        
        coaching = {
            'sales_coaching': 'Practice your opener with empathy. Use "I know this is out of the blue" to show understanding.',
            'grammar_coaching': 'Use contractions like "I\'m calling" instead of "I am calling" to sound natural.',
            'vocabulary_coaching': 'Use simple words like "book a meeting" instead of complex business terms.',
            'pronunciation_coaching': 'Speak clearly and at a moderate pace. Practice key phrases.',
            'rapport_assertiveness': 'Show empathy first, then be confident. Acknowledge you\'re interrupting their day.'
        }
        
        return {
            'success': True,
            'coaching': coaching,
            'score': score,
            'source': 'fallback'
        }
    
    def test_roleplay_flow(self) -> Dict[str, Any]:
        """Test the complete roleplay flow"""
        try:
            if not self.is_available():
                return {'success': False, 'error': 'OpenAI not available'}
            
            # Test prospect response
            response_result = self.generate_roleplay_response(
                "Hi, I know this is out of the blue, but can I tell you why I'm calling?",
                [],
                {'prospect_job_title': 'CTO', 'prospect_industry': 'Technology'},
                'opener_evaluation'
            )
            
            # Test evaluation
            evaluation = self.evaluate_user_input(
                "Hi, I know this is out of the blue, but can I tell you why I'm calling?",
                [],
                'opener'
            )
            
            return {
                'success': True,
                'prospect_response': response_result,
                'evaluation': evaluation
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed service status"""
        status = {
            'enabled': self.is_enabled,
            'api_key_configured': bool(self.api_key),
            'model': self.model,
            'client_available': bool(self.client)
        }
        
        if self.is_available():
            try:
                test_result = self._test_connection()
                status['connection_test'] = 'success' if test_result else 'failed'
            except:
                status['connection_test'] = 'failed'
        else:
            status['connection_test'] = 'not_tested'
        
        return status
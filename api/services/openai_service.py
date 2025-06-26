# ===== FIXED: services/openai_service.py (OpenAI SDK v1.0+ Compatible) =====

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Use the modern OpenAI library
from openai import OpenAI, RateLimitError, APIError, AuthenticationError

logger = logging.getLogger(__name__)

class OpenAIService:
    """Enhanced OpenAI service specifically designed for Roleplay 1.1"""
    
    def __init__(self):
        self.client: Optional[OpenAI] = None
        self.is_configured = False
        self.model = "gpt-4o-mini" # Using a more modern, cost-effective model
        
        try:
            # Use the same environment variable as the rest of your application
            api_key = os.getenv('REACT_APP_OPENAI_API_KEY')
            if api_key:
                # NEW: Initialize the OpenAI client with the API key
                self.client = OpenAI(api_key=api_key)
                self.is_configured = True
                logger.info(f"✅ OpenAI service initialized successfully with model: {self.model}")
            else:
                logger.warning("⚠️ OpenAI API key ('REACT_APP_OPENAI_API_KEY') not found. Service will use fallback methods.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI: {e}")
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.is_configured and self.client is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'available': self.is_available(),
            'configured': self.is_configured,
            'model': self.model,
            'timestamp': datetime.now().isoformat()
        }
    
    def evaluate_user_input(self, user_input: str, conversation_history: List[Dict], evaluation_stage: str) -> Dict[str, Any]:
        """
        Evaluate user input based on Roleplay 1.1 criteria
        Returns detailed evaluation with scoring
        """
        if not self.is_available():
            return self._fallback_evaluation(user_input, evaluation_stage)
        
        try:
            # Build context for AI evaluation
            context = self._build_evaluation_context(conversation_history, evaluation_stage)
            
            # Create evaluation prompt
            prompt = self._create_evaluation_prompt(user_input, context, evaluation_stage)
            
            # NEW: Use the updated client.chat.completions.create method
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_evaluator_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            # NEW: Access the response content from the message object
            result = self._parse_evaluation_response(response.choices[0].message.content)
            result['source'] = 'openai'
            result['stage'] = evaluation_stage
            
            logger.info(f"✅ AI evaluation complete: {result.get('score', 0)}/4 for {evaluation_stage}")
            return result
            
        except (APIError, RateLimitError, AuthenticationError) as e:
            logger.error(f"❌ OpenAI API error during evaluation: {type(e).__name__} - {e}")
            return self._fallback_evaluation(user_input, evaluation_stage)
        except Exception as e:
            logger.error(f"❌ Unexpected error during OpenAI evaluation: {e}")
            return self._fallback_evaluation(user_input, evaluation_stage)
    
    def generate_roleplay_response(self, user_input: str, conversation_history: List[Dict], 
                                     user_context: Dict, current_stage: str) -> Dict[str, Any]:
        """
        Generate AI prospect response for Roleplay 1.1
        Returns contextual, logical response
        """
        if not self.is_available():
            return self._fallback_response(current_stage)
        
        try:
            # Build conversation context
            context = self._build_conversation_context(conversation_history, user_context, current_stage)
            
            # Create response prompt
            prompt = self._create_response_prompt(user_input, context, current_stage)
            
            # NEW: Use the updated client.chat.completions.create method
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_prospect_system_prompt(user_context)},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150  # Keep responses concise
            )
            
            # NEW: Access the response content from the message object
            ai_response = response.choices[0].message.content.strip()
            
            # Clean up response
            ai_response = self._clean_ai_response(ai_response)
            
            logger.info(f"✅ AI response generated: '{ai_response[:50]}...'")
            return {
                'success': True,
                'response': ai_response,
                'stage': current_stage
            }
            
        except (APIError, RateLimitError, AuthenticationError) as e:
            logger.error(f"❌ OpenAI API error during response generation: {type(e).__name__} - {e}")
            return self._fallback_response(current_stage)
        except Exception as e:
            logger.error(f"❌ Unexpected error during OpenAI response generation: {e}")
            return self._fallback_response(current_stage)
    
    def generate_coaching_feedback(self, conversation_history: List[Dict], 
                                     rubric_scores: Dict, user_context: Dict) -> Dict[str, Any]:
        """
        Generate detailed coaching feedback for Roleplay 1.1
        """
        if not self.is_available():
            return self._fallback_coaching(rubric_scores)
        
        try:
            # Build coaching context
            context = self._build_coaching_context(conversation_history, rubric_scores, user_context)
            
            # Create coaching prompt
            prompt = self._create_coaching_prompt(context)
            
            # NEW: Use the updated client.chat.completions.create method
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_coach_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1000
            )
            
            # NEW: Access the response content from the message object
            result = self._parse_coaching_response(response.choices[0].message.content)
            result['source'] = 'openai'
            
            logger.info(f"✅ AI coaching generated: Score {result.get('score', 75)}")
            return result
            
        except (APIError, RateLimitError, AuthenticationError) as e:
            logger.error(f"❌ OpenAI API error during coaching generation: {type(e).__name__} - {e}")
            return self._fallback_coaching(rubric_scores)
        except Exception as e:
            logger.error(f"❌ Unexpected error during OpenAI coaching: {e}")
            return self._fallback_coaching(rubric_scores)
    
    # ===== SYSTEM PROMPTS (No changes needed) =====
    
    def _get_evaluator_system_prompt(self) -> str:
        """System prompt for evaluation AI"""
        return """You are an expert cold calling coach evaluating sales performance.
Your role:
- Evaluate user input against specific criteria for each stage
- Be objective and constructive
- Focus on cold calling best practices
- Consider natural conversation flow

Evaluation criteria for each stage:
OPENER: Clear introduction, empathy, natural tone, ends with question
OBJECTION_HANDLING: Acknowledges calmly, brief reframe, forward question
MINI_PITCH: Short (under 30 words), outcome-focused, natural language
SOFT_DISCOVERY: Tied to pitch, open-ended question, curious tone

Return evaluation in this format:
SCORE: X/4
PASSED: Yes/No
CRITERIA_MET: [list criteria names that were met]
FEEDBACK: [specific coaching advice]
HANG_UP_PROBABILITY: 0.X (0.0-1.0)
NEXT_ACTION: continue/improve"""
    
    def _get_prospect_system_prompt(self, user_context: Dict) -> str:
        """System prompt for AI prospect"""
        name = user_context.get('first_name', 'Alex')
        title = user_context.get('prospect_job_title', 'CTO')
        industry = user_context.get('prospect_industry', 'Technology')
        
        return f"""You are {name}, a {title} in the {industry} industry.
Your personality:
- Busy professional, mildly skeptical of cold calls
- Direct but not rude
- Will listen if approached professionally
- Appreciates empathy and brevity
- Responds naturally to good cold calling techniques

Your behavior:
- Start with mild resistance 
- Warm up if user shows empathy and professionalism
- Give clear objections when appropriate
- Ask clarifying questions if interested
- Speak naturally and conversationally

Keep responses under 25 words. Be realistic and human-like.
Never mention you're an AI or break character."""
    
    def _get_coach_system_prompt(self) -> str:
        """System prompt for coaching AI"""
        return """You are an expert cold calling coach providing detailed feedback.
Your role:
- Analyze the complete conversation objectively
- Provide specific, actionable coaching advice
- Focus on areas for improvement
- Be encouraging but honest
- Use simple, clear language

Coaching categories:
- Sales Performance: Opening, objection handling, conversation flow
- Grammar & Structure: Sentence construction, clarity
- Vocabulary: Word choice, professional language
- Pronunciation: Speaking clearly (inferred from text)
- Rapport & Confidence: Building connection, assertiveness

Provide specific examples and improvement suggestions for each category."""
    
    # ===== PROMPT BUILDERS (No changes needed) =====
    
    def _create_evaluation_prompt(self, user_input: str, context: str, stage: str) -> str:
        """Create evaluation prompt"""
        return f"""Evaluate this cold call input for the {stage.upper()} stage:

CONTEXT:
{context}

USER INPUT: "{user_input}"

STAGE: {stage}

Please evaluate based on the criteria for this stage and return your assessment."""
    
    def _create_response_prompt(self, user_input: str, context: str, stage: str) -> str:
        """Create response generation prompt"""
        return f"""Generate a realistic prospect response to this cold call:

CONVERSATION CONTEXT:
{context}

CURRENT STAGE: {stage}
USER JUST SAID: "{user_input}"

Respond as the prospect would naturally. Keep it under 25 words and conversational."""
    
    def _create_coaching_prompt(self, context: str) -> str:
        """Create coaching prompt"""
        return f"""Provide detailed coaching feedback for this cold call:

{context}

Analyze the conversation and provide:
1. Overall score (0-100)
2. Specific coaching for each category
3. What they did well
4. Areas for improvement
5. Actionable next steps

Be constructive and specific."""
    
    # ===== CONTEXT BUILDERS (No changes needed) =====
    
    def _build_evaluation_context(self, conversation_history: List[Dict], stage: str) -> str:
        """Build context for evaluation"""
        context = f"EVALUATION STAGE: {stage}\n\n"
        context += "CONVERSATION SO FAR:\n"
        
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            role = "USER" if msg['role'] == 'user' else "PROSPECT"
            context += f"{role}: {msg['content']}\n"
        
        return context
    
    def _build_conversation_context(self, conversation_history: List[Dict], 
                                  user_context: Dict, stage: str) -> str:
        """Build context for response generation"""
        context = f"CURRENT STAGE: {stage}\n"
        context += f"PROSPECT: {user_context.get('first_name', 'Alex')} ({user_context.get('prospect_job_title', 'CTO')})\n\n"
        context += "CONVERSATION:\n"
        
        for msg in conversation_history[-8:]:  # More context for better responses
            role = "CALLER" if msg['role'] == 'user' else "YOU"
            context += f"{role}: {msg['content']}\n"
        
        return context
    
    def _build_coaching_context(self, conversation_history: List[Dict], 
                              rubric_scores: Dict, user_context: Dict) -> str:
        """Build context for coaching"""
        context = f"USER PROFILE: {user_context.get('first_name', 'User')}\n"
        context += f"TARGET: {user_context.get('prospect_job_title', 'CTO')} at {user_context.get('prospect_industry', 'Technology')} company\n\n"
        
        context += "CONVERSATION TRANSCRIPT:\n"
        for i, msg in enumerate(conversation_history):
            role = "USER" if msg['role'] == 'user' else "PROSPECT"
            context += f"{i+1}. {role}: {msg['content']}\n"
        
        context += f"\nRUBRIC SCORES: {rubric_scores}\n"
        context += f"TOTAL TURNS: {len([m for m in conversation_history if m['role'] == 'user'])}"
        
        return context
    
    # ===== RESPONSE PARSERS (No changes needed) =====
    
    def _parse_evaluation_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI evaluation response"""
        try:
            lines = response_text.strip().split('\n')
            result = {
                'score': 2,
                'passed': False,
                'criteria_met': [],
                'feedback': 'Basic evaluation completed.',
                'hang_up_probability': 0.2,
                'next_action': 'continue'
            }
            
            for line in lines:
                line = line.strip()
                if line.startswith('SCORE:'):
                    score_part = line.split(':')[1].strip()
                    if '/' in score_part:
                        result['score'] = int(score_part.split('/')[0])
                    else:
                        result['score'] = int(score_part)
                elif line.startswith('PASSED:'):
                    result['passed'] = 'yes' in line.lower()
                elif line.startswith('CRITERIA_MET:'):
                    criteria_text = line.split(':', 1)[1].strip()
                    result['criteria_met'] = [c.strip() for c in criteria_text.split(',') if c.strip()]
                elif line.startswith('FEEDBACK:'):
                    result['feedback'] = line.split(':', 1)[1].strip()
                elif line.startswith('HANG_UP_PROBABILITY:'):
                    try:
                        result['hang_up_probability'] = float(line.split(':')[1].strip())
                    except:
                        result['hang_up_probability'] = 0.2
                elif line.startswith('NEXT_ACTION:'):
                    result['next_action'] = line.split(':')[1].strip()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse evaluation response: {e}")
            return {
                'score': 2,
                'passed': False,
                'criteria_met': [],
                'feedback': 'Evaluation completed.',
                'hang_up_probability': 0.2,
                'next_action': 'continue'
            }
    
    def _parse_coaching_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI coaching response"""
        try:
            # Extract overall score
            score = 75  # default
            if 'SCORE:' in response_text or 'Score:' in response_text:
                import re
                score_match = re.search(r'[Ss]core:?\s*(\d+)', response_text)
                if score_match:
                    score = int(score_match.group(1))
            
            # Split into coaching categories
            coaching = {
                'sales_coaching': self._extract_coaching_section(response_text, ['sales', 'performance', 'opening']),
                'grammar_coaching': self._extract_coaching_section(response_text, ['grammar', 'structure']),
                'vocabulary_coaching': self._extract_coaching_section(response_text, ['vocabulary', 'word choice']),
                'pronunciation_coaching': self._extract_coaching_section(response_text, ['pronunciation', 'speaking']),
                'rapport_assertiveness': self._extract_coaching_section(response_text, ['rapport', 'confidence', 'assertiveness'])
            }
            
            return {
                'success': True,
                'score': score,
                'coaching': coaching
            }
            
        except Exception as e:
            logger.error(f"Failed to parse coaching response: {e}")
            return self._fallback_coaching({})
    
    def _extract_coaching_section(self, text: str, keywords: List[str]) -> str:
        """Extract coaching section based on keywords"""
        lines = text.split('\n')
        relevant_lines = []
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in keywords):
                relevant_lines.append(line.strip())
                # Get next few lines as well
                line_index = lines.index(line)
                for i in range(1, 3):
                    if line_index + i < len(lines):
                        next_line = lines[line_index + i].strip()
                        if next_line and not any(k in next_line.lower() for k in ['score', 'category', '###']):
                            relevant_lines.append(next_line)
        
        if relevant_lines:
            return ' '.join(relevant_lines)
        
        # Fallback messages
        fallback_messages = {
            'sales': 'Good effort on your cold calling approach. Focus on being more empathetic in your opener.',
            'grammar': 'Your grammar and sentence structure were clear and professional.',
            'vocabulary': 'Good vocabulary choice. Consider using more outcome-focused language.',
            'pronunciation': 'Speak clearly and at a steady pace for better impact.',
            'rapport': 'Build more rapport by showing empathy and confidence in your approach.'
        }
        
        for keyword in keywords:
            if keyword in fallback_messages:
                return fallback_messages[keyword]
        
        return 'Continue practicing to improve your skills.'
    
    # ===== UTILITY METHODS (No changes needed) =====
    
    def _clean_ai_response(self, response: str) -> str:
        """Clean and format AI response"""
        # Remove common AI artifacts
        response = response.replace('AI:', '').replace('Prospect:', '').strip()
        
        # Remove quotes if the entire response is quoted
        if response.startswith('"') and response.endswith('"'):
            response = response[1:-1]
        
        # Ensure proper capitalization
        if response and response[0].islower():
            response = response[0].upper() + response[1:]
        
        # Limit length
        if len(response) > 200:
            sentences = response.split('. ')
            response = '. '.join(sentences[:2])
            if not response.endswith('.'):
                response += '.'
        
        return response.strip()
    
    # ===== FALLBACK METHODS (No changes needed) =====
    
    def _fallback_evaluation(self, user_input: str, stage: str) -> Dict[str, Any]:
        """Fallback evaluation when OpenAI unavailable"""
        score = len(user_input.split()) // 3  # Basic scoring
        score = min(4, max(1, score))
        
        return {
            'score': score,
            'passed': score >= 2,
            'criteria_met': ['basic_response'],
            'feedback': f'Basic evaluation for {stage}. Keep practicing!',
            'hang_up_probability': 0.3 if score <= 1 else 0.1,
            'next_action': 'continue',
            'source': 'fallback',
            'stage': stage
        }
    
    def _fallback_response(self, stage: str) -> Dict[str, Any]:
        """Fallback response when OpenAI unavailable"""
        responses = {
            'phone_pickup': ['Hello?', 'Yes?'],
            'opener_evaluation': ["What's this about?", "I'm listening."],
            'early_objection': ["I'm not interested.", "We don't take cold calls."],
            'objection_handling': ["Alright, what do you do?", "You have 30 seconds."],
            'mini_pitch': ["That sounds interesting.", "Tell me more."],
            'soft_discovery': ["Good question.", "I'd need to think about it."]
        }
        
        import random
        response_list = responses.get(stage, ['I see. Please continue.'])
        
        return {
            'success': True,
            'response': random.choice(response_list),
            'stage': stage
        }
    
    def _fallback_coaching(self, rubric_scores: Dict) -> Dict[str, Any]:
        """Fallback coaching when OpenAI unavailable"""
        avg_score = 75
        if rubric_scores:
            scores = [data.get('score', 0) for data in rubric_scores.values()]
            if scores:
                avg_score = int(sum(scores) / len(scores) * 25)
        
        return {
            'success': True,
            'score': avg_score,
            'coaching': {
                'sales_coaching': 'Good effort on the call. Keep practicing your opening to build more rapport.',
                'grammar_coaching': 'Your grammar was clear and understandable.',
                'vocabulary_coaching': 'Try using more confident and direct language.',
                'pronunciation_coaching': 'Speak clearly and at a moderate pace.',
                'rapport_assertiveness': 'Focus on showing empathy at the beginning of the call.'
            }
        }
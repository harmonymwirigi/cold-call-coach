# ===== UPDATED API/SERVICES/OPENAI_SERVICE.PY (v1.0+ Compatible) =====
import os
import json
import random
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv('REACT_APP_OPENAI_API_KEY')
        self.model = "gpt-4o-mini"
        self.is_enabled = bool(self.api_key)
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI service initialized successfully")
        else:
            self.client = None
            logger.warning("OpenAI API key not provided - using fallback responses")

    async def generate_roleplay_response(self, user_input: str, conversation_history: List[Dict], 
                                       user_context: Dict, roleplay_config: Dict) -> Dict[str, Any]:
        """Generate natural AI response with evaluation - UPDATED FOR v1.0+"""
        try:
            if not self.is_enabled:
                logger.info("OpenAI not available, using fallback")
                return self._generate_fallback_response(user_input, conversation_history, roleplay_config)
            
            # Determine conversation stage
            stage_info = self._analyze_conversation_stage(conversation_history, roleplay_config)
            
            # Generate natural AI response
            ai_response = self._generate_natural_response_sync(
                user_input, conversation_history, user_context, roleplay_config, stage_info
            )
            
            if not ai_response:
                logger.warning("OpenAI response failed, using fallback")
                return self._generate_fallback_response(user_input, conversation_history, roleplay_config)
            
            # Evaluate user input
            evaluation = self._evaluate_user_response_simple(user_input, stage_info)
            
            logger.info(f"Generated OpenAI response: {ai_response[:50]}...")
            
            return {
                'success': True,
                'response': ai_response,
                'evaluation': evaluation,
                'should_continue': evaluation.get('should_continue', True),
                'stage': stage_info['current_stage']
            }
            
        except Exception as e:
            logger.error(f"Error generating roleplay response: {e}")
            return self._generate_fallback_response(user_input, conversation_history, roleplay_config)

    def _analyze_conversation_stage(self, conversation_history: List[Dict], roleplay_config: Dict) -> Dict:
        """Analyze current conversation stage"""
        roleplay_id = roleplay_config.get('roleplay_id', 1)
        user_messages = [msg for msg in conversation_history if msg.get('role') == 'user']
        
        stage_info = {
            'roleplay_id': roleplay_id,
            'turn_count': len(user_messages),
            'current_stage': 'phone_pickup',
            'context': {}
        }
        
        # Determine stage based on roleplay type and conversation progress
        if roleplay_id == 1:  # Opener + Early Objections
            if len(user_messages) == 0:
                stage_info['current_stage'] = 'phone_pickup'
            elif len(user_messages) == 1:
                stage_info['current_stage'] = 'opener_evaluation'
            elif len(user_messages) == 2:
                stage_info['current_stage'] = 'early_objection'
            else:
                stage_info['current_stage'] = 'mini_pitch'
                
        elif roleplay_id == 2:  # Pitch + Objections
            if len(user_messages) == 0:
                stage_info['current_stage'] = 'ai_pitch_prompt'
            elif len(user_messages) == 1:
                stage_info['current_stage'] = 'pitch_evaluation'
            else:
                stage_info['current_stage'] = 'post_pitch_objections'
        
        return stage_info

    def _generate_natural_response_sync(self, user_input: str, conversation_history: List[Dict],
                                       user_context: Dict, roleplay_config: Dict, stage_info: Dict) -> str:
        """Generate natural AI response using NEW OpenAI v1.0+ API"""
        try:
            # Build context-aware prompt
            system_prompt = self._build_natural_response_prompt(user_context, roleplay_config, stage_info)
            
            # Format conversation history
            conversation_context = self._format_conversation_for_ai(conversation_history)
            
            # Create user message
            user_message = f"""
CONVERSATION SO FAR:
{conversation_context}

LATEST USER INPUT: "{user_input}"

Respond naturally as the prospect. Keep it conversational (1-2 sentences). Stay in character.
"""

            # Call OpenAI using NEW v1.0+ API
            logger.info("Making OpenAI API call...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.8,
                max_tokens=150,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Clean response
            cleaned_response = self._clean_ai_response(ai_response)
            logger.info(f"OpenAI response: {cleaned_response}")
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    def _build_natural_response_prompt(self, user_context: Dict, roleplay_config: Dict, stage_info: Dict) -> str:
        """Build system prompt for natural responses"""
        job_title = user_context.get('prospect_job_title', 'Manager')
        industry = user_context.get('prospect_industry', 'Technology')
        stage = stage_info['current_stage']
        
        base_prompt = f"""You are a {job_title} at a {industry} company receiving a cold call.

CRITICAL INSTRUCTIONS:
- Respond naturally and realistically 
- Keep responses short (1-2 sentences)
- Show realistic prospect behavior - skeptical but professional
- Stay in character as a busy business professional
- DO NOT break character or give coaching

CURRENT STAGE: {stage}"""

        # Add stage-specific guidance
        if stage == 'opener_evaluation':
            base_prompt += """

The caller just gave their opening. Respond based on how good it was:
- If professional with empathy: Show mild interest but some skepticism
- If generic or pushy: Give a standard objection  
- If terrible: Be more resistant"""

        elif stage == 'early_objection':
            base_prompt += """

Give a realistic early objection like:
- "What's this about?"
- "I'm not interested" 
- "Now is not a good time"
- "Who is this?"
Choose what feels natural."""

        elif stage == 'mini_pitch':
            base_prompt += """

The caller handled your objection. React realistically:
- If they did well: Show some interest, ask a follow-up
- If they were pushy: Give another objection
- Stay skeptical but fair."""

        return base_prompt

    def _evaluate_user_response_simple(self, user_input: str, stage_info: Dict) -> Dict:
        """Simple evaluation of user response"""
        stage = stage_info['current_stage']
        
        evaluation = {
            'quality_score': 5,
            'should_continue': True,
            'should_hang_up': False,
            'next_stage': 'in_progress',
            'pass': True
        }
        
        user_input_lower = user_input.lower()
        
        if stage == 'opener_evaluation':
            # Basic opener evaluation
            score = 3
            
            # Check for greeting
            if any(greeting in user_input_lower for greeting in ['hi', 'hello', 'good morning']):
                score += 1
                
            # Check for empathy
            if any(empathy in user_input_lower for empathy in ['know this is', "don't know me", 'out of the blue']):
                score += 2
                
            # Check for question
            if user_input.strip().endswith('?'):
                score += 1
                
            evaluation['quality_score'] = min(score, 8)
            evaluation['pass'] = score >= 5
            evaluation['next_stage'] = 'early_objection' if evaluation['pass'] else 'call_failed'
            
            # Small chance of hang-up for poor openers
            if score <= 2 and random.random() < 0.2:
                evaluation['should_hang_up'] = True
                evaluation['should_continue'] = False
                
        elif stage == 'early_objection':
            # Check objection handling
            if any(ack in user_input_lower for ack in ['understand', 'get that', 'fair enough']):
                evaluation['quality_score'] += 1
                
            if user_input.strip().endswith('?'):
                evaluation['quality_score'] += 1
                
            evaluation['next_stage'] = 'mini_pitch'
            
        return evaluation

    def _clean_ai_response(self, response: str) -> str:
        """Clean AI response"""
        # Remove quotes and asterisks
        response = response.replace('"', '').replace('*', '').strip()
        
        # Keep it short
        if len(response) > 200:
            sentences = response.split('. ')
            response = sentences[0]
            if not response.endswith('.'):
                response += '.'
        
        return response

    def _format_conversation_for_ai(self, conversation_history: List[Dict]) -> str:
        """Format conversation for AI context"""
        if not conversation_history:
            return "No conversation yet."
        
        formatted = []
        for msg in conversation_history[-4:]:  # Last 4 messages
            role = "Caller" if msg.get('role') == 'user' else "You"
            content = msg.get('content', '')
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)

    def _generate_fallback_response(self, user_input: str, conversation_history: List[Dict], 
                                  roleplay_config: Dict) -> Dict[str, Any]:
        """Generate fallback response when OpenAI fails"""
        from utils.constants import EARLY_OBJECTIONS, POST_PITCH_OBJECTIONS, PITCH_PROMPTS
        
        # Determine response based on conversation length
        user_messages = len([m for m in conversation_history if m.get('role') == 'user'])
        roleplay_id = roleplay_config.get('roleplay_id', 1)
        
        logger.info(f"Using fallback response for {user_messages} user messages, roleplay {roleplay_id}")
        
        if user_messages == 0:
            response = "Hello?"
        elif user_messages == 1:
            if roleplay_id == 2:
                response = random.choice(PITCH_PROMPTS)
            else:
                # Evaluate opener quality for better response
                opener_quality = self._evaluate_opener_simple(user_input)
                if opener_quality >= 5:
                    responses = ["What's this about?", "I'm listening.", "Go ahead."]
                else:
                    responses = ["Who is this?", "I'm not interested.", "What's this about?"]
                response = random.choice(responses)
        else:
            # Use objections
            if user_messages == 2:
                responses = EARLY_OBJECTIONS[:10]
            else:
                responses = ["I see.", "Tell me more.", "Go on."]
            response = random.choice(responses)
        
        # Simple evaluation
        evaluation = {
            'quality_score': 5,
            'should_continue': True,
            'should_hang_up': False,
            'next_stage': 'in_progress',
            'pass': True
        }
        
        logger.info(f"Fallback response: {response}")
        
        return {
            'success': True,
            'response': response,
            'evaluation': evaluation,
            'should_continue': True,
            'stage': 'in_progress',
            'fallback_used': True
        }

    def _evaluate_opener_simple(self, user_input: str) -> int:
        """Simple opener evaluation"""
        score = 2  # Base score
        user_input_lower = user_input.lower()
        
        if any(greeting in user_input_lower for greeting in ['hi', 'hello', 'good morning']):
            score += 1
        
        if any(empathy in user_input_lower for empathy in ['know this is', "don't know me", 'out of the blue']):
            score += 2
        
        if user_input.strip().endswith('?'):
            score += 1
        
        if len(user_input.split()) >= 5:
            score += 1
            
        return min(score, 8)

    def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.is_enabled

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'enabled': self.is_enabled,
            'api_key_configured': bool(self.api_key),
            'model': self.model,
            'status': 'ready' if self.is_enabled else 'fallback_mode'
        }
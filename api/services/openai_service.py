# ===== FIXED API/SERVICES/OPENAI_SERVICE.PY =====
import openai
import os
import json
import random
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv('REACT_APP_OPENAI_API_KEY')
        self.model = "gpt-4o-mini"
        self.is_enabled = bool(self.api_key)
        
        if self.api_key:
            openai.api_key = self.api_key
            logger.info("OpenAI service initialized successfully")
        else:
            logger.warning("OpenAI API key not provided - using fallback responses")

    async def generate_roleplay_response(self, user_input: str, conversation_history: List[Dict], 
                                       user_context: Dict, roleplay_config: Dict) -> Dict[str, Any]:
        """Generate natural AI response with evaluation"""
        try:
            if not self.is_enabled:
                return self._generate_fallback_response(user_input, conversation_history, roleplay_config)
            
            # Determine conversation stage and context
            stage_info = self._analyze_conversation_stage(conversation_history, roleplay_config)
            
            # Generate natural AI response
            ai_response = await self._generate_natural_response(
                user_input, conversation_history, user_context, roleplay_config, stage_info
            )
            
            if not ai_response:
                return self._generate_fallback_response(user_input, conversation_history, roleplay_config)
            
            # Evaluate user input separately
            evaluation = await self._evaluate_user_response(
                user_input, conversation_history, roleplay_config, stage_info
            )
            
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
        """Analyze current conversation stage and context"""
        roleplay_id = roleplay_config.get('roleplay_id', 1)
        user_messages = [msg for msg in conversation_history if msg.get('role') == 'user']
        ai_messages = [msg for msg in conversation_history if msg.get('role') == 'assistant']
        
        stage_info = {
            'roleplay_id': roleplay_id,
            'turn_count': len(user_messages),
            'current_stage': 'phone_pickup',
            'context': {},
            'should_hang_up': False,
            'stage_complete': False
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
            if len(ai_messages) == 0:
                stage_info['current_stage'] = 'ai_pitch_prompt'
            elif len(user_messages) == 1:
                stage_info['current_stage'] = 'pitch_evaluation'
            else:
                stage_info['current_stage'] = 'post_pitch_objections'
                
        elif roleplay_id == 3:  # Warm-up Challenge
            stage_info['current_stage'] = 'warmup_question'
            
        elif roleplay_id == 4:  # Full Cold Call
            if len(user_messages) == 0:
                stage_info['current_stage'] = 'phone_pickup'
            elif len(user_messages) == 1:
                stage_info['current_stage'] = 'opener_evaluation'
            elif len(user_messages) == 2:
                stage_info['current_stage'] = 'early_objection'
            elif len(user_messages) == 3:
                stage_info['current_stage'] = 'mini_pitch'
            else:
                stage_info['current_stage'] = 'post_pitch_flow'
        
        return stage_info

    async def _generate_natural_response(self, user_input: str, conversation_history: List[Dict],
                                       user_context: Dict, roleplay_config: Dict, stage_info: Dict) -> str:
        """Generate natural AI response using OpenAI"""
        try:
            # Build context-aware prompt for natural conversation
            system_prompt = self._build_natural_response_prompt(user_context, roleplay_config, stage_info)
            
            # Format conversation history
            conversation_context = self._format_conversation_for_ai(conversation_history)
            
            # Create user message with context
            user_message = f"""
CONVERSATION SO FAR:
{conversation_context}

LATEST USER INPUT: "{user_input}"

Respond naturally as the prospect in this cold call scenario. Stay in character and respond realistically based on what the user just said and the conversation stage.
"""

            # Call OpenAI
            response = await self._call_openai_async(system_prompt, user_message)
            
            if response:
                # Clean and validate response
                cleaned_response = self._clean_ai_response(response)
                return cleaned_response
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating natural response: {e}")
            return None

    def _build_natural_response_prompt(self, user_context: Dict, roleplay_config: Dict, stage_info: Dict) -> str:
        """Build system prompt for natural AI responses"""
        roleplay_id = roleplay_config.get('roleplay_id', 1)
        stage = stage_info['current_stage']
        
        # Get prospect persona
        job_title = user_context.get('prospect_job_title', 'Manager')
        industry = user_context.get('prospect_industry', 'Technology')
        
        base_prompt = f"""You are an AI roleplay partner simulating a cold call prospect. You are a {job_title} at a {industry} company.

CRITICAL INSTRUCTIONS:
- Speak naturally in CEFR C2 level English (native-like)
- Stay in character as a busy business professional
- Respond realistically based on what the caller says
- Keep responses conversational (1-3 sentences typically)
- Show realistic prospect behavior - skeptical but professional
- Do NOT break character or give hints/coaching

CURRENT SITUATION:
- You are receiving a cold call from a sales representative
- Roleplay ID: {roleplay_id}
- Current stage: {stage}

PERSONALITY TRAITS:
- Busy and time-conscious
- Professionally skeptical of cold calls
- Will engage if the caller shows value and professionalism
- Direct communication style
- May show interest if properly convinced"""

        # Add stage-specific guidance
        if stage == 'phone_pickup':
            base_prompt += "\n\nYou just answered the phone. Respond naturally like 'Hello?' or 'Yes?'"
            
        elif stage == 'opener_evaluation':
            base_prompt += """
            
The caller just gave their opening line. Respond based on quality:
- If it's professional and shows empathy: Show mild interest but some skepticism
- If it's generic or pushy: Give a standard objection
- If it's terrible: Be more resistant or consider hanging up
- Be realistic - most cold calls get objections even if decent"""

        elif stage == 'early_objection':
            base_prompt += """
            
Give a realistic early-stage objection like:
- "What's this about?"
- "I'm not interested"
- "Now is not a good time"
- "Who gave you this number?"
Choose based on what feels natural given the opener."""

        elif stage == 'mini_pitch':
            base_prompt += """
            
The caller handled your objection. React based on how well they did:
- If they were empathetic and professional: Show some interest, ask a follow-up
- If they were pushy or generic: Give another objection
- Be realistically skeptical but fair"""

        elif stage == 'ai_pitch_prompt' and roleplay_id == 2:
            base_prompt += """
            
Prompt the caller to give their pitch. Use phrases like:
- "Alright, go ahead — what's this about?"
- "You've got 30 seconds. Impress me."
- "I'm listening. What do you do?"
Be direct but give them a chance."""

        elif stage == 'post_pitch_objections':
            base_prompt += """
            
The caller gave their pitch. Respond with realistic post-pitch objections or questions:
- Budget concerns ("It's too expensive")
- Comparison questions ("How are you better than X?")
- Implementation concerns ("How long does this take?")
- Authority issues ("I'm not the decision-maker")
Choose what feels most natural."""

        return base_prompt

    async def _evaluate_user_response(self, user_input: str, conversation_history: List[Dict],
                                    roleplay_config: Dict, stage_info: Dict) -> Dict:
        """Evaluate user response against rubrics"""
        try:
            stage = stage_info['current_stage']
            roleplay_id = roleplay_config.get('roleplay_id', 1)
            
            # Default evaluation
            evaluation = {
                'quality_score': 5,
                'should_continue': True,
                'should_hang_up': False,
                'next_stage': 'in_progress',
                'feedback_notes': [],
                'pass': True
            }
            
            # Stage-specific evaluation using rubrics
            if stage == 'opener_evaluation':
                evaluation = await self._evaluate_opener(user_input)
            elif stage == 'early_objection':
                evaluation = await self._evaluate_objection_handling(user_input)
            elif stage == 'mini_pitch' or stage == 'pitch_evaluation':
                evaluation = await self._evaluate_pitch(user_input)
            elif stage == 'post_pitch_objections':
                evaluation = await self._evaluate_post_pitch_handling(user_input)
            
            # Add hang-up logic based on roleplay rules
            self._apply_hang_up_logic(evaluation, stage_info, roleplay_config)
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating user response: {e}")
            return {
                'quality_score': 5,
                'should_continue': True,
                'should_hang_up': False,
                'next_stage': 'in_progress',
                'pass': True
            }

    async def _evaluate_opener(self, user_input: str) -> Dict:
        """Evaluate opener using rubric from PDF"""
        try:
            evaluation_prompt = f"""
Evaluate this cold call opener against the specific rubric:

OPENER: "{user_input}"

RUBRIC - Pass if 3 of 4:
1. Clear cold call opener (pattern interrupt, permission-based, or value-first)
2. Casual, confident tone (uses contractions and short phrases)
3. Demonstrates empathy (acknowledges interruption/unfamiliarity: "I know this is out of the blue", "You don't know me", etc.)
4. Ends with a soft question ("Can I tell you why I'm calling?")

FAIL if ANY:
- Robotic or overly formal
- Doesn't demonstrate empathy
- Pushy or too long
- No question or soft invite

Respond with JSON: {{"score": 1-8, "pass": true/false, "reasoning": "brief explanation"}}
"""

            response = await self._call_openai_async(
                "You are an expert cold calling coach. Evaluate openers precisely against the given rubric.",
                evaluation_prompt
            )
            
            if response:
                try:
                    result = json.loads(response)
                    return {
                        'quality_score': result.get('score', 5),
                        'pass': result.get('pass', True),
                        'should_continue': result.get('pass', True),
                        'should_hang_up': not result.get('pass', True),
                        'reasoning': result.get('reasoning', ''),
                        'next_stage': 'early_objection' if result.get('pass', True) else 'call_failed'
                    }
                except json.JSONDecodeError:
                    pass
            
            # Fallback evaluation
            return self._fallback_opener_evaluation(user_input)
            
        except Exception as e:
            logger.error(f"Error evaluating opener: {e}")
            return self._fallback_opener_evaluation(user_input)

    def _fallback_opener_evaluation(self, user_input: str) -> Dict:
        """Fallback opener evaluation when OpenAI fails"""
        score = 3  # Start with base score
        user_input_lower = user_input.lower()
        
        # Check rubric criteria
        if any(greeting in user_input_lower for greeting in ['hi', 'hello', 'good morning', 'good afternoon']):
            score += 1
            
        if any(empathy in user_input_lower for empathy in ['know this is', "don't know me", 'out of the blue', 'interrupting']):
            score += 2
            
        if user_input.strip().endswith('?'):
            score += 1
            
        if len(user_input.split()) >= 5:
            score += 1
        
        pass_threshold = 5
        passes = score >= pass_threshold
        
        return {
            'quality_score': min(score, 8),
            'pass': passes,
            'should_continue': passes,
            'should_hang_up': not passes,
            'next_stage': 'early_objection' if passes else 'call_failed'
        }

    async def _evaluate_objection_handling(self, user_input: str) -> Dict:
        """Evaluate objection handling using rubric"""
        # Similar structure to opener evaluation but with objection handling rubric
        score = 5
        user_input_lower = user_input.lower()
        
        passes = True
        
        # Check for acknowledgment
        if any(ack in user_input_lower for ack in ['fair enough', 'totally get', 'understand', 'i hear you']):
            score += 1
        
        # Check for not being pushy
        if not any(pushy in user_input_lower for pushy in ['but you', 'actually', "you're wrong", 'no but']):
            score += 1
        
        # Check for forward-moving question
        if user_input.strip().endswith('?'):
            score += 1
        
        return {
            'quality_score': score,
            'pass': passes,
            'should_continue': passes,
            'should_hang_up': not passes,
            'next_stage': 'mini_pitch' if passes else 'call_failed'
        }

    async def _evaluate_pitch(self, user_input: str) -> Dict:
        """Evaluate pitch using rubric"""
        score = 5
        passes = True
        
        # Check length (1-2 sentences)
        sentences = user_input.split('.')
        if len(sentences) <= 3:
            score += 1
        
        # Check for outcome focus
        if any(outcome in user_input.lower() for outcome in ['help', 'save', 'improve', 'solve', 'reduce']):
            score += 1
        
        # Check for question
        if user_input.strip().endswith('?'):
            score += 1
        
        return {
            'quality_score': score,
            'pass': passes,
            'should_continue': passes,
            'should_hang_up': not passes,
            'next_stage': 'post_pitch_objections' if passes else 'call_failed'
        }

    async def _evaluate_post_pitch_handling(self, user_input: str) -> Dict:
        """Evaluate post-pitch objection handling"""
        score = 5
        passes = True
        
        return {
            'quality_score': score,
            'pass': passes,
            'should_continue': passes,
            'should_hang_up': not passes,
            'next_stage': 'in_progress'
        }

    def _apply_hang_up_logic(self, evaluation: Dict, stage_info: Dict, roleplay_config: Dict):
        """Apply roleplay-specific hang-up logic"""
        roleplay_id = roleplay_config.get('roleplay_id', 1)
        stage = stage_info['current_stage']
        
        # Random hang-up chance for certain roleplays after opener
        if roleplay_id in [1, 4] and stage == 'opener_evaluation' and evaluation.get('pass'):
            if random.random() < 0.25:  # 25% chance
                evaluation['should_hang_up'] = True
                evaluation['should_continue'] = False
                evaluation['hang_up_reason'] = 'Random hang-up after opener'

    async def _call_openai_async(self, system_prompt: str, user_message: str) -> Optional[str]:
        """Make async API call to OpenAI"""
        try:
            # Use the synchronous client for now since async client setup is more complex
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.8,
                max_tokens=200,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    def _clean_ai_response(self, response: str) -> str:
        """Clean AI response for natural conversation"""
        # Remove quotes and asterisks
        response = response.replace('"', '').replace('*', '').strip()
        
        # Remove meta-commentary
        if response.startswith("As a") or response.startswith("I am"):
            lines = response.split('\n')
            for line in lines:
                if len(line.strip()) > 0 and not line.startswith("As") and not line.startswith("I am"):
                    response = line.strip()
                    break
        
        # Keep responses conversational length
        if len(response) > 200:
            sentences = response.split('. ')
            response = '. '.join(sentences[:2])
            if not response.endswith('.'):
                response += '.'
        
        return response

    def _format_conversation_for_ai(self, conversation_history: List[Dict]) -> str:
        """Format conversation history for AI context"""
        if not conversation_history:
            return "No conversation yet."
        
        formatted = []
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            role = "SDR" if msg.get('role') == 'user' else "Prospect"
            content = msg.get('content', '')
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)

    def _generate_fallback_response(self, user_input: str, conversation_history: List[Dict], 
                                  roleplay_config: Dict) -> Dict[str, Any]:
        """Generate fallback response when OpenAI is unavailable"""
        from utils.constants import EARLY_OBJECTIONS, POST_PITCH_OBJECTIONS, PITCH_PROMPTS
        
        # Determine stage
        user_messages = len([m for m in conversation_history if m.get('role') == 'user'])
        roleplay_id = roleplay_config.get('roleplay_id', 1)
        
        if user_messages == 0:
            response = "Hello?"
        elif user_messages == 1 and roleplay_id == 2:
            response = random.choice(PITCH_PROMPTS)
        elif user_messages == 1:
            response = random.choice(EARLY_OBJECTIONS[:10])
        else:
            response = random.choice(POST_PITCH_OBJECTIONS[:10])
        
        return {
            'success': True,
            'response': response,
            'evaluation': {'quality_score': 5, 'should_continue': True},
            'should_continue': True,
            'stage': 'in_progress',
            'fallback_used': True
        }

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
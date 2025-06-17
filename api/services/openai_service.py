# ===== API/SERVICES/OPENAI_SERVICE.PY =====
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
        self.client = openai.OpenAI(api_key=os.getenv('REACT_APP_OPENAI_API_KEY'))
        self.model = "gpt-4-turbo-preview"
        
        # Load system prompt template
        self.system_prompt_template = self._load_system_prompt()
        
        # Roleplay-specific data
        self.early_objections = [
            "What's this about?", "I'm not interested", "We don't take cold calls",
            "Now is not a good time", "I have a meeting", "Can you call me later?",
            "I'm about to go into a meeting", "Send me an email", 
            "Can you send me the information?", "Can you message me on WhatsApp?",
            "Who gave you this number?", "This is my personal number",
            "Where did you get my number?", "What are you trying to sell me?",
            "Is this a sales call?", "Is this a cold call?",
            "Are you trying to sell me something?", "We are ok for the moment",
            "We are all good / all set", "We're not looking for anything right now",
            "We are not changing anything", "How long is this going to take?",
            "Is this going to take long?", "What company are you calling from?",
            "Who are you again?", "Where are you calling from?",
            "I never heard of you", "Not interested right now", "Just send me the details"
        ]
        
        self.post_pitch_objections = [
            "It's too expensive for us", "We have no budget for this right now",
            "Your competitor is cheaper", "Can you give us a discount?",
            "This isn't a good time", "We've already set this year's budget",
            "Call me back next quarter", "We're busy with other projects right now",
            "We already use [competitor] and we're happy", "We built something similar ourselves",
            "How exactly are you better than [competitor]?", "Switching providers seems like a lot of work",
            "I've never heard of your company", "Who else like us have you worked with?",
            "Can you send customer testimonials?", "How do I know this will really work?",
            "I'm not the decision-maker", "I need approval from my team first",
            "Can you send details so I can forward them?", "We'll need buy-in from other departments",
            "How long does this take to implement?", "We don't have time to learn a new system",
            "I'm concerned this won't integrate with our existing tools", 
            "What happens if this doesn't work as promised?"
        ]
        
        self.pitch_prompts = [
            "Alright, go ahead — what's this about?",
            "So… what are you calling me about?",
            "You've got 30 seconds. Impress me.",
            "I'm listening. What do you do?",
            "This better be good. What is it?",
            "Okay. Tell me why you're calling.",
            "Go on — what's the offer?",
            "Convince me.",
            "What's your pitch?",
            "Let's hear it."
        ]
        
        self.impatience_phrases = [
            "Hello? Are you still with me?", "Can you hear me?", "Just checking you're there…",
            "Still on the line?", "I don't have much time for this.", "Sounds like you are gone.",
            "Are you an idiot.", "What is going on.", "Are you okay to continue?", "I am afraid I have to go"
        ]

    def _load_system_prompt(self) -> str:
        """Load the master system prompt"""
        return """
You are an AI-powered English Cold Calling Coach specifically designed for non-native Spanish-speaking Sales Development Representatives (SDRs). Your mission is to simulate realistic prospect conversations during cold calls while providing sophisticated coaching to improve their English communication skills, sales techniques, and confidence.

## CRITICAL LANGUAGE REQUIREMENTS

**DURING ROLEPLAY**: Speak at **CEFR C2 level** (native-like fluency)
- Use natural, fluent English with authentic speech patterns
- Include contractions, idioms, and conversational flow
- Vary sentence structure and vocabulary sophistication
- Display realistic prospect behaviors and personalities

**DURING COACHING**: Communicate at **CEFR A2 level** (basic proficiency)
- Use simple, clear sentences and common vocabulary
- Avoid complex grammar structures
- Focus on practical, actionable advice
- Remember your audience is learning English as a second language

## BEHAVIORAL ADAPTATION RULES

### Industry-Specific Behavior
Adapt your responses based on prospect industry:

**Technology/IT**: 
- Mention concerns about security, scalability, integration
- Reference technical challenges and digital transformation
- Use industry terminology appropriately

**Healthcare**: 
- Focus on patient outcomes, compliance, efficiency
- Mention HIPAA, regulatory requirements
- Show understanding of healthcare workflows

**Finance/Banking**: 
- Emphasize ROI, risk management, compliance
- Reference financial regulations and audit requirements
- Show cost-consciousness and conservative decision-making

### Job Title-Specific Behavior
Adapt personality and concerns based on prospect job title:

**C-Level (CEO, CTO, CFO)**: 
- Time-constrained, strategic thinking
- Focus on big picture, ROI, competitive advantage
- More likely to delegate or request executive summary

**Directors/VPs**: 
- Balance strategy and tactics
- Concerned with team impact and departmental goals
- May need stakeholder buy-in

**Managers**: 
- Focus on team efficiency and practical implementation
- Concerned with training, adoption, day-to-day operations
- Often need approval from above

## SILENCE & IMPATIENCE MANAGEMENT

### Silence Rules
- **10 seconds**: Play random impatience phrase
- **15 seconds total**: Hang up (call FAIL)

## CRITICAL EXECUTION RULES

### Never Break Character
- Stay in prospect role throughout the call
- No coaching or feedback during active roleplay
- Maintain consistent personality and industry knowledge

### Realistic Behavior
- Show authentic prospect reactions
- Include natural conversational flow
- Display appropriate skepticism and objections
- React realistically to poor performance (hang up)
"""

    def generate_roleplay_response(self, user_input: str, conversation_history: List[Dict], 
                                 user_context: Dict, roleplay_config: Dict) -> Dict[str, Any]:
        """Generate AI response during roleplay"""
        try:
            # Build context-aware prompt
            prompt = self._build_roleplay_prompt(user_input, conversation_history, user_context, roleplay_config)
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.8,
                max_tokens=300
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Evaluate response and determine next action
            evaluation = self._evaluate_user_input(user_input, conversation_history, roleplay_config)
            
            return {
                'success': True,
                'response': ai_response,
                'evaluation': evaluation,
                'should_continue': evaluation.get('should_continue', True),
                'stage': evaluation.get('next_stage', 'in_progress')
            }
            
        except Exception as e:
            logger.error(f"Error generating roleplay response: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "I'm sorry, I didn't catch that. Could you repeat?"
            }

    def _build_roleplay_prompt(self, user_input: str, conversation_history: List[Dict], 
                             user_context: Dict, roleplay_config: Dict) -> str:
        """Build context-aware prompt for roleplay"""
        roleplay_id = roleplay_config.get('roleplay_id', 1)
        mode = roleplay_config.get('mode', 'practice')
        
        # Get prospect persona
        prospect_title = user_context.get('prospect_job_title', 'Manager')
        prospect_industry = user_context.get('prospect_industry', 'Technology')
        custom_notes = user_context.get('custom_ai_notes', '')
        
        # Determine current stage based on conversation
        current_stage = self._determine_conversation_stage(conversation_history, roleplay_id)
        
        prompt = f"""
{self.system_prompt_template}

## CURRENT SESSION CONTEXT
- Prospect Role: {prospect_title} in {prospect_industry}
- Roleplay Type: {roleplay_id} ({self._get_roleplay_name(roleplay_id)})
- Mode: {mode}
- Current Stage: {current_stage}
- Custom Behavior Notes: {custom_notes}

## CONVERSATION HISTORY
{self._format_conversation_history(conversation_history)}

## INSTRUCTIONS FOR THIS RESPONSE
{self._get_stage_instructions(current_stage, roleplay_id)}

Respond as the prospect would, staying in character. Be realistic and challenging but fair.
"""
        return prompt

    def _determine_conversation_stage(self, conversation_history: List[Dict], roleplay_id: int) -> str:
        """Determine what stage of the conversation we're in"""
        if not conversation_history:
            return "phone_pickup"
        
        # Count exchanges
        user_messages = [msg for msg in conversation_history if msg.get('role') == 'user']
        ai_messages = [msg for msg in conversation_history if msg.get('role') == 'assistant']
        
        if len(user_messages) == 0:
            return "phone_pickup"
        elif len(user_messages) == 1:
            return "opener_evaluation"
        elif len(user_messages) == 2:
            return "early_objection" if roleplay_id in [1, 4] else "pitch_response"
        elif len(user_messages) >= 3:
            return "pitch_and_objections"
        
        return "in_progress"

    def _get_stage_instructions(self, stage: str, roleplay_id: int) -> str:
        """Get specific instructions for current conversation stage"""
        instructions = {
            "phone_pickup": "Answer the phone professionally. Say 'Hello?' or similar phone greeting.",
            
            "opener_evaluation": """
Evaluate the opener. If it's poor (no pattern interrupt, too salesy, confusing):
- 70-80% chance: Respond with early objection
- 20-30% chance: Hang up immediately (say something like "Not interested" and end)

If opener is good, respond with an early objection from the list.""",
            
            "early_objection": f"""
Give ONE early objection from this list:
{', '.join(self.early_objections[:10])}...
Be natural and realistic. Don't make it too easy.""",
            
            "pitch_response": f"""
Respond to their pitch with one of these prompts:
{', '.join(self.pitch_prompts[:5])}...""",
            
            "pitch_and_objections": f"""
Mix questions and objections. Use post-pitch objections:
{', '.join(self.post_pitch_objections[:8])}...
Be challenging but not impossible."""
        }
        
        return instructions.get(stage, "Continue the natural conversation flow as the prospect.")

    def _evaluate_user_input(self, user_input: str, conversation_history: List[Dict], 
                           roleplay_config: Dict) -> Dict[str, Any]:
        """Evaluate user's performance and determine next action"""
        try:
            # This is a simplified evaluation - you could make this more sophisticated
            evaluation_prompt = f"""
Evaluate this SDR response for a cold call:
"{user_input}"

Rate on a scale of 1-5:
1. Opener quality (if applicable)
2. Objection handling 
3. Natural English flow
4. Professional tone

Return JSON with scores and brief feedback.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": evaluation_prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            # For now, return basic evaluation
            return {
                'should_continue': True,
                'next_stage': 'in_progress',
                'quality_score': 3,  # Default score
                'feedback': 'Continue the conversation'
            }
            
        except Exception as e:
            logger.error(f"Error evaluating user input: {e}")
            return {
                'should_continue': True,
                'next_stage': 'in_progress',
                'quality_score': 3,
                'feedback': 'Continue'
            }

    def generate_coaching_feedback(self, session_data: Dict, user_context: Dict) -> Dict[str, Any]:
        """Generate coaching feedback after roleplay session"""
        try:
            conversation = session_data.get('conversation_history', [])
            roleplay_id = session_data.get('roleplay_id', 1)
            mode = session_data.get('mode', 'practice')
            
            # Build coaching prompt
            coaching_prompt = f"""
Analyze this cold calling roleplay session and provide coaching feedback.

## SESSION INFO
- Roleplay: {self._get_roleplay_name(roleplay_id)}
- Mode: {mode}
- Prospect: {user_context.get('prospect_job_title')} in {user_context.get('prospect_industry')}

## CONVERSATION
{self._format_conversation_for_coaching(conversation)}

## COACHING REQUIREMENTS
Provide feedback in exactly these categories (A2 level English for Spanish speakers):

1. **Sales Coaching**: Techniques, effectiveness, sales skills
2. **Grammar Coaching**: Spanish→English interference patterns  
3. **Vocabulary Coaching**: Unnatural word choices
4. **Pronunciation Coaching**: Words that may be unclear
5. **Rapport & Assertiveness**: Tone and confidence

For each category, provide:
- One specific observation (what they did well OR what to improve)
- One actionable tip (simple English)

Maximum 2 sentences per category. Focus on the most impactful improvements.
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": coaching_prompt}],
                temperature=0.5,
                max_tokens=600
            )
            
            coaching_text = response.choices[0].message.content.strip()
            
            # Parse coaching into categories (simplified)
            coaching_feedback = self._parse_coaching_feedback(coaching_text)
            
            return {
                'success': True,
                'coaching': coaching_feedback,
                'overall_score': self._calculate_overall_score(conversation),
                'raw_feedback': coaching_text
            }
            
        except Exception as e:
            logger.error(f"Error generating coaching feedback: {e}")
            return {
                'success': False,
                'error': str(e),
                'coaching': {}
            }

    def _format_conversation_history(self, conversation: List[Dict]) -> str:
        """Format conversation for prompt"""
        formatted = []
        for msg in conversation[-10:]:  # Last 10 messages
            role = "SDR" if msg.get('role') == 'user' else "Prospect"
            content = msg.get('content', '')
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)

    def _format_conversation_for_coaching(self, conversation: List[Dict]) -> str:
        """Format conversation for coaching analysis"""
        formatted = []
        for i, msg in enumerate(conversation):
            role = "SDR" if msg.get('role') == 'user' else "Prospect"
            content = msg.get('content', '')
            formatted.append(f"{i+1}. {role}: {content}")
        return "\n".join(formatted)

    def _parse_coaching_feedback(self, coaching_text: str) -> Dict[str, str]:
        """Parse coaching feedback into categories"""
        # Simplified parsing - you could make this more sophisticated
        categories = {
            'sales_coaching': 'Good conversation flow. Focus on asking more discovery questions.',
            'grammar_coaching': 'Grammar was clear. Watch out for direct Spanish translations.',
            'vocabulary_coaching': 'Good word choices. Try using more natural English phrases.',
            'pronunciation_coaching': 'Speech was clear. Practice key sales terms.',
            'rapport_assertiveness': 'Confident tone. Build more rapport with casual language.'
        }
        
        # TODO: Parse the actual coaching_text into these categories
        return categories

    def _calculate_overall_score(self, conversation: List[Dict]) -> int:
        """Calculate overall performance score (1-10)"""
        # Simplified scoring based on conversation length and participation
        user_messages = [msg for msg in conversation if msg.get('role') == 'user']
        
        if len(user_messages) >= 3:
            return 7  # Good participation
        elif len(user_messages) >= 2:
            return 5  # Moderate participation
        else:
            return 3  # Limited participation

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

    def get_random_objection(self, objection_type: str = 'early') -> str:
        """Get random objection for roleplay"""
        if objection_type == 'early':
            return random.choice(self.early_objections)
        elif objection_type == 'post_pitch':
            return random.choice(self.post_pitch_objections)
        else:
            return random.choice(self.early_objections + self.post_pitch_objections)

    def get_random_pitch_prompt(self) -> str:
        """Get random pitch prompt"""
        return random.choice(self.pitch_prompts)

    def get_impatience_phrase(self) -> str:
        """Get random impatience phrase for silence handling"""
        return random.choice(self.impatience_phrases)
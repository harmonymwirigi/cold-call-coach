# ===== services/roleplay/roleplay_3.py =====
# Warm-up Challenge - 25 rapid-fire questions

import random
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from .base_roleplay import BaseRoleplay
from .configs.roleplay_3_config import Roleplay3Config

logger = logging.getLogger(__name__)

class Roleplay3(BaseRoleplay):
    """
    Roleplay 3 - Warm-up Challenge
    25 rapid-fire questions to sharpen cold calling skills
    """
    
    def __init__(self, openai_service=None):
        super().__init__(openai_service)
        self.config = Roleplay3Config()
        self.roleplay_id = self.config.ROLEPLAY_ID

    def get_roleplay_info(self) -> Dict[str, Any]:
        return {
            'id': self.config.ROLEPLAY_ID,
            'name': self.config.NAME,
            'description': self.config.DESCRIPTION,
            'type': 'challenge',
            'features': {
                'ai_evaluation': self.is_openai_available(),
                'rapid_fire': True,
                'skill_sharpening': True,
                'time_pressure': True,
                'always_available': True,
                'total_questions': self.config.TOTAL_QUESTIONS
            }
        }

    def create_session(self, user_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Creates a warm-up challenge session"""
        session_id = f"{user_id}_{self.config.ROLEPLAY_ID}_{mode}_{int(datetime.now().timestamp())}"
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'roleplay_id': self.config.ROLEPLAY_ID,
            'mode': 'challenge',
            'started_at': datetime.now(timezone.utc).isoformat(),
            'user_context': user_context,
            'session_active': True,
            
            # Challenge-specific state
            'conversation_history': [],
            'current_stage': 'challenge_active',
            'turn_count': 0,
            'questions_completed': 0,
            'questions_correct': 0,
            'current_question_index': 0,
            'total_questions': self.config.TOTAL_QUESTIONS,
            
            # Question management
            'question_queue': self._generate_question_queue(),
            'current_question': None,
            'question_start_time': None,
            'response_times': [],
            'question_scores': [],
            
            # Performance tracking
            'streak_count': 0,
            'longest_streak': 0,
            'categories_covered': set(),
            'difficulty_progression': [],
            
            # Challenge state
            'challenge_complete': False,
            'overall_performance': 0
        }
        
        self.active_sessions[session_id] = session_data
        
        # Start with first question
        first_question = self._get_next_question(session_data)
        
        session_data['conversation_history'].append({
            'role': 'assistant',
            'content': first_question,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'challenge_active',
            'question_number': 1
        })
        
        logger.info(f"Warm-up challenge session {session_id} created for user {user_id}")
        return {
            'success': True,
            'session_id': session_id,
            'initial_response': first_question,
            'roleplay_info': self.get_roleplay_info(),
            'challenge_info': {
                'total_questions': self.config.TOTAL_QUESTIONS,
                'current_question': 1,
                'questions_remaining': self.config.TOTAL_QUESTIONS - 1
            }
        }

    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user response to rapid-fire questions"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            
            if not session.get('session_active'):
                raise ValueError("Session not active")
            
            # Skip if challenge is complete
            if session.get('challenge_complete'):
                return self._handle_challenge_completion(session)
            
            # Increment counters
            session['turn_count'] += 1
            session['questions_completed'] += 1
            
            # Record response time
            if session.get('question_start_time'):
                response_time = datetime.now(timezone.utc).timestamp() - session['question_start_time']
                session['response_times'].append(response_time)
            
            # Add user input to conversation
            session['conversation_history'].append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': 'challenge_active',
                'question_number': session['questions_completed']
            })
            
            logger.info(f"Challenge Q#{session['questions_completed']}: Processing '{user_input[:50]}...'")
            
            # Evaluate response
            evaluation = self._evaluate_challenge_response(session, user_input)
            
            # Update performance tracking
            self._update_challenge_performance(session, evaluation)
            
            # Check if challenge is complete
            if session['questions_completed'] >= self.config.TOTAL_QUESTIONS:
                session['challenge_complete'] = True
                return self._handle_challenge_completion(session)
            
            # Get next question
            next_question = self._get_next_question(session)
            
            # Add AI response to conversation
            session['conversation_history'].append({
                'role': 'assistant',
                'content': next_question,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'stage': 'challenge_active',
                'question_number': session['questions_completed'] + 1
            })
            
            return {
                'success': True,
                'ai_response': next_question,
                'call_continues': True,
                'evaluation': evaluation,
                'challenge_info': {
                    'current_question': session['questions_completed'] + 1,
                    'questions_remaining': self.config.TOTAL_QUESTIONS - session['questions_completed'],
                    'questions_correct': session['questions_correct'],
                    'current_streak': session['streak_count'],
                    'accuracy': (session['questions_correct'] / session['questions_completed']) * 100
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing challenge input: {e}")
            return {'success': False, 'error': str(e), 'call_continues': False}

    def _generate_question_queue(self) -> list:
        """Generate randomized queue of 25 questions"""
        all_questions = []
        
        # Get questions from different categories
        for category, questions in self.config.QUESTION_CATEGORIES.items():
            # Take a portion from each category
            category_size = min(len(questions), 8)  # Max 8 per category
            selected = random.sample(questions, category_size)
            for q in selected:
                all_questions.append({
                    'question': q,
                    'category': category,
                    'difficulty': self._get_question_difficulty(q, category)
                })
        
        # Shuffle and take exactly 25
        random.shuffle(all_questions)
        return all_questions[:self.config.TOTAL_QUESTIONS]

    def _get_question_difficulty(self, question: str, category: str) -> str:
        """Determine question difficulty based on content and category"""
        difficulty_indicators = {
            'easy': ['what', 'who', 'name', 'introduce'],
            'medium': ['how', 'why', 'explain', 'handle'],
            'hard': ['complex', 'multiple', 'challenging', 'advanced']
        }
        
        question_lower = question.lower()
        
        for difficulty, indicators in difficulty_indicators.items():
            if any(indicator in question_lower for indicator in indicators):
                return difficulty
        
        # Default based on category
        category_defaults = {
            'openers': 'easy',
            'objections': 'medium',
            'qualification': 'medium',
            'closing': 'hard'
        }
        
        return category_defaults.get(category, 'medium')

    def _get_next_question(self, session: Dict) -> str:
        """Get the next question in sequence"""
        question_index = session['current_question_index']
        question_queue = session['question_queue']
        
        if question_index >= len(question_queue):
            return "Challenge complete! Great job!"
        
        question_data = question_queue[question_index]
        session['current_question'] = question_data
        session['current_question_index'] += 1
        session['question_start_time'] = datetime.now(timezone.utc).timestamp()
        
        # Add category to tracking
        session['categories_covered'].add(question_data['category'])
        session['difficulty_progression'].append(question_data['difficulty'])
        
        # Format question with number
        question_num = session['questions_completed'] + 1
        return f"Question {question_num}/25: {question_data['question']}"

    def _evaluate_challenge_response(self, session: Dict, user_input: str) -> Dict[str, Any]:
        """Evaluate user response to challenge question"""
        current_question = session.get('current_question')
        if not current_question:
            return {'score': 0, 'passed': False}
        
        # Use AI evaluation if available
        if self.is_openai_available():
            try:
                return self.openai_service.evaluate_user_input(
                    user_input,
                    [{'role': 'assistant', 'content': current_question['question']}],
                    'challenge_response'
                )
            except Exception as e:
                logger.error(f"AI evaluation error: {e}")
        
        # Fallback evaluation
        return self._basic_challenge_evaluation(user_input, current_question)

    def _basic_challenge_evaluation(self, user_input: str, question_data: Dict) -> Dict[str, Any]:
        """Basic evaluation for challenge responses"""
        words = user_input.split()
        score = 0
        criteria_met = []
        
        # Length check - should be reasonably detailed
        if len(words) >= 3:
            score += 1
            criteria_met.append('adequate_length')
        
        # Category-specific evaluation
        category = question_data['category']
        question_text = question_data['question'].lower()
        user_lower = user_input.lower()
        
        if category == 'openers':
            # Check for introduction elements
            if any(word in user_lower for word in ['hi', 'hello', 'calling from', 'my name']):
                score += 1
                criteria_met.append('proper_introduction')
        
        elif category == 'objections':
            # Check for acknowledgment and response
            if any(word in user_lower for word in ['understand', 'appreciate', 'get that']):
                score += 1
                criteria_met.append('acknowledges_objection')
        
        elif category == 'qualification':
            # Check for discovery questions
            if '?' in user_input or any(word in user_lower for word in ['how', 'what', 'when']):
                score += 1
                criteria_met.append('asks_questions')
        
        elif category == 'closing':
            # Check for clear action or next steps
            if any(word in user_lower for word in ['meeting', 'call', 'follow up', 'next step']):
                score += 1
                criteria_met.append('clear_next_step')
        
        # Communication quality
        if any(word in user_lower for word in ["i'm", "we're", "don't", "can't"]):
            score += 0.5
            criteria_met.append('natural_language')
        
        # Difficulty bonus
        difficulty = question_data['difficulty']
        if difficulty == 'hard' and score >= 2:
            score += 0.5
        
        final_score = min(4, score)
        passed = final_score >= 2
        
        return {
            'score': int(final_score),
            'passed': passed,
            'criteria_met': criteria_met,
            'category': category,
            'difficulty': difficulty,
            'feedback': f'Challenge response: {len(criteria_met)} criteria met'
        }

    def _update_challenge_performance(self, session: Dict, evaluation: Dict):
        """Update challenge performance metrics"""
        # Record score
        session['question_scores'].append(evaluation.get('score', 0))
        
        # Update correct count
        if evaluation.get('passed', False):
            session['questions_correct'] += 1
            session['streak_count'] += 1
            session['longest_streak'] = max(session['longest_streak'], session['streak_count'])
        else:
            session['streak_count'] = 0
        
        # Update overall performance
        if session['questions_completed'] > 0:
            session['overall_performance'] = (session['questions_correct'] / session['questions_completed']) * 100

    def _handle_challenge_completion(self, session: Dict) -> Dict[str, Any]:
        """Handle completion of the warm-up challenge"""
        session['session_active'] = False
        session['challenge_complete'] = True
        
        # Calculate final metrics
        total_questions = session['questions_completed']
        correct_answers = session['questions_correct']
        accuracy = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Calculate average response time
        response_times = session.get('response_times', [])
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        completion_message = f"🎯 Challenge Complete! {correct_answers}/{total_questions} correct ({accuracy:.1f}%)"
        
        session['conversation_history'].append({
            'role': 'assistant',
            'content': completion_message,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'stage': 'challenge_complete',
            'final_results': True
        })
        
        return {
            'success': True,
            'ai_response': completion_message,
            'call_continues': False,
            'challenge_complete': True,
            'final_results': {
                'total_questions': total_questions,
                'correct_answers': correct_answers,
                'accuracy': accuracy,
                'longest_streak': session['longest_streak'],
                'avg_response_time': avg_response_time,
                'categories_covered': len(session['categories_covered']),
                'difficulty_distribution': self._analyze_difficulty_distribution(session)
            }
        }

    def _analyze_difficulty_distribution(self, session: Dict) -> Dict[str, int]:
        """Analyze distribution of difficulty levels attempted"""
        difficulty_count = {'easy': 0, 'medium': 0, 'hard': 0}
        for difficulty in session.get('difficulty_progression', []):
            difficulty_count[difficulty] = difficulty_count.get(difficulty, 0) + 1
        return difficulty_count

    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End warm-up challenge session"""
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
            
            # Calculate final score
            questions_completed = session.get('questions_completed', 0)
            questions_correct = session.get('questions_correct', 0)
            
            if questions_completed > 0:
                accuracy = (questions_correct / questions_completed) * 100
                overall_score = min(100, max(20, int(accuracy + (session.get('longest_streak', 0) * 2))))
            else:
                accuracy = 0
                overall_score = 20
            
            # Determine success
            session_success = accuracy >= 60  # 60% accuracy to pass
            
            # Generate coaching
            coaching = self._generate_challenge_coaching(session)
            
            result = {
                'success': True,
                'duration_minutes': duration_minutes,
                'session_success': session_success,
                'coaching': coaching,
                'overall_score': overall_score,
                'session_data': session,
                'roleplay_type': 'challenge',
                'challenge_results': {
                    'questions_completed': questions_completed,
                    'questions_correct': questions_correct,
                    'accuracy': accuracy,
                    'longest_streak': session.get('longest_streak', 0),
                    'categories_covered': len(session.get('categories_covered', set())),
                    'avg_response_time': sum(session.get('response_times', [])) / max(len(session.get('response_times', [])), 1),
                    'difficulty_distribution': self._analyze_difficulty_distribution(session)
                }
            }
            
            # Clean up session
            del self.active_sessions[session_id]
            
            logger.info(f"Challenge session {session_id} ended. Success: {session_success}, Score: {overall_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error ending challenge session: {e}")
            return {'success': False, 'error': str(e)}

    def _generate_challenge_coaching(self, session: Dict) -> Dict[str, str]:
        """Generate coaching for challenge performance"""
        coaching = {}
        
        questions_completed = session.get('questions_completed', 0)
        questions_correct = session.get('questions_correct', 0)
        accuracy = (questions_correct / questions_completed) * 100 if questions_completed > 0 else 0
        longest_streak = session.get('longest_streak', 0)
        
        # Overall performance
        if accuracy >= 80:
            coaching['overall'] = f"Excellent challenge performance! {accuracy:.1f}% accuracy shows strong fundamentals."
        elif accuracy >= 60:
            coaching['overall'] = f"Good work on the challenge! {accuracy:.1f}% accuracy shows solid understanding."
        else:
            coaching['overall'] = f"Challenge completed! Focus on fundamentals to improve from {accuracy:.1f}% accuracy."
        
        # Streak performance
        if longest_streak >= 10:
            coaching['consistency'] = "Outstanding consistency! Your longest streak shows excellent focus."
        elif longest_streak >= 5:
            coaching['consistency'] = "Good consistency with your streak. Keep building that momentum."
        else:
            coaching['consistency'] = "Work on consistency. Try to maintain focus across multiple questions."
        
        # Speed vs accuracy
        response_times = session.get('response_times', [])
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            if avg_time < 5:
                coaching['timing'] = "Great response speed! Make sure to maintain accuracy with quick thinking."
            elif avg_time > 15:
                coaching['timing'] = "Take time to think, but try to be more decisive in your responses."
        
        # Category performance
        categories_covered = len(session.get('categories_covered', set()))
        if categories_covered >= 3:
            coaching['versatility'] = "Excellent! You handled questions across multiple skill areas."
        else:
            coaching['versatility'] = "Continue practicing different types of cold calling scenarios."
        
        return coaching
# ===== services/roleplay/configs/roleplay_3_config.py =====

class Roleplay3Config:
    """
    Configuration for Roleplay 3 - Warm-up Challenge
    25 rapid-fire questions to sharpen cold calling skills
    """
    
    # Basic Info
    ROLEPLAY_ID = "3"
    NAME = "Warm-up Challenge"
    DESCRIPTION = "25 rapid-fire questions to sharpen your cold calling skills"
    TYPE = "challenge"
    
    # Challenge Settings
    TOTAL_QUESTIONS = 25
    PASS_THRESHOLD = 60  # 60% accuracy to pass
    TIME_PRESSURE = True
    
    # ===== QUESTION CATEGORIES =====
    
    QUESTION_CATEGORIES = {
        'openers': [
            "How do you introduce yourself on a cold call?",
            "What's the first thing you say after 'Hello'?",
            "How do you get someone's attention in the first 10 seconds?",
            "What makes a strong opening line?",
            "How do you state your name and company clearly?",
            "What's the purpose of your opening statement?",
            "How do you show respect for their time upfront?",
            "What should you avoid saying in your opener?",
            "How do you transition from greeting to purpose?",
            "What tone should you use when opening a call?"
        ],
        
        'objections': [
            "How do you respond to 'I'm not interested'?",
            "What do you say when they say 'I'm too busy'?",
            "How do you handle 'We already have a vendor'?",
            "What's your response to 'Send me information'?",
            "How do you address 'It's too expensive'?",
            "What do you say to 'Call me back later'?",
            "How do you handle 'I'm not the decision maker'?",
            "What's your response to 'We don't have budget'?",
            "How do you address 'I'm in a meeting'?",
            "What do you say when they ask 'How did you get my number'?",
            "How do you respond to 'Remove me from your list'?",
            "What's your approach to 'We're happy with our current solution'?",
            "How do you handle 'Can you call back next month'?",
            "What do you say to 'I don't take cold calls'?"
        ],
        
        'qualification': [
            "What questions help you qualify a prospect?",
            "How do you determine if they're a good fit?",
            "What should you ask about their current situation?",
            "How do you identify their pain points?",
            "What questions reveal their decision-making process?",
            "How do you qualify their budget?",
            "What do you ask about timing?",
            "How do you determine their authority level?",
            "What questions help understand their needs?",
            "How do you ask about their current challenges?",
            "What's the best way to ask about their goals?",
            "How do you inquire about their current tools?"
        ],
        
        'closing': [
            "How do you ask for a meeting?",
            "What's the best way to propose next steps?",
            "How do you handle objections to meeting requests?",
            "What should you say to confirm a meeting?",
            "How do you end a call professionally?",
            "What's your approach to setting expectations?",
            "How do you ask for their calendar availability?",
            "What do you say to create urgency?",
            "How do you confirm contact information?",
            "What's the best way to summarize next steps?",
            "How do you ask for referrals?",
            "What should you say before hanging up?"
        ],
        
        'rapport': [
            "How do you build rapport quickly?",
            "What questions help you connect personally?",
            "How do you show genuine interest?",
            "What's your approach to active listening?",
            "How do you mirror their communication style?",
            "What makes someone feel heard?",
            "How do you find common ground?",
            "What builds trust in a conversation?",
            "How do you show empathy on a call?",
            "What questions demonstrate understanding?"
        ],
        
        'discovery': [
            "What's your best discovery question?",
            "How do you dig deeper into their answers?",
            "What questions reveal business impact?",
            "How do you ask about their priorities?",
            "What's the best way to understand their process?",
            "How do you ask about previous solutions they've tried?",
            "What questions help quantify their problem?",
            "How do you ask about their success metrics?",
            "What's your approach to understanding their industry?",
            "How do you ask about their team structure?"
        ],
        
        'value_proposition': [
            "How do you explain your value in one sentence?",
            "What's your elevator pitch?",
            "How do you connect features to benefits?",
            "What makes your solution unique?",
            "How do you demonstrate ROI quickly?",
            "What's your strongest value statement?",
            "How do you tailor your pitch to their industry?",
            "What proof points support your claims?",
            "How do you make abstract benefits concrete?",
            "What's the most compelling reason to choose you?"
        ],
        
        'handling_gatekeepers': [
            "How do you get past a receptionist?",
            "What do you say to an assistant?",
            "How do you build rapport with gatekeepers?",
            "What's your approach to getting transferred?",
            "How do you ask for the decision maker?",
            "What information should you give a gatekeeper?",
            "How do you handle screening questions?",
            "What's the best way to be memorable to gatekeepers?",
            "How do you ask about the best time to call back?",
            "What builds credibility with assistants?"
        ]
    }
    
    # ===== SCORING SYSTEM =====
    
    SCORING_CRITERIA = {
        'accuracy_weight': 0.70,      # 70% based on correct answers
        'streak_weight': 0.15,        # 15% based on longest streak
        'speed_weight': 0.10,         # 10% based on response speed
        'coverage_weight': 0.05       # 5% based on category coverage
    }
    
    PERFORMANCE_THRESHOLDS = {
        'excellent': 85,    # 85%+ = Excellent
        'good': 70,         # 70-84% = Good
        'fair': 55,         # 55-69% = Fair
        'needs_work': 0     # Below 55% = Needs Work
    }
    
    STREAK_BONUSES = {
        15: 10,   # 15+ streak = 10 bonus points
        10: 5,    # 10+ streak = 5 bonus points
        5: 2      # 5+ streak = 2 bonus points
    }
    
    # ===== TIME MANAGEMENT =====
    
    TIME_LIMITS = {
        'recommended_per_question': 20,  # 20 seconds recommended
        'maximum_per_question': 60,      # 60 seconds maximum
        'total_session_target': 8        # 8 minutes total target
    }
    
    # ===== COACHING TEMPLATES =====
    
    COACHING_TEMPLATES = {
        'accuracy': {
            'excellent': "Outstanding accuracy! You clearly understand cold calling fundamentals.",
            'good': "Good accuracy! Your fundamentals are solid with room for refinement.",
            'fair': "Fair performance. Review the basics to improve your accuracy.",
            'needs_work': "Focus on fundamentals. Practice core concepts to build confidence."
        },
        
        'speed': {
            'fast': "Great response speed! You think quickly under pressure.",
            'moderate': "Good pace. Balance speed with thoughtful responses.",
            'slow': "Take time to think, but try to be more decisive in real calls."
        },
        
        'consistency': {
            'high_streak': "Excellent consistency! Your focus stayed strong throughout.",
            'medium_streak': "Good consistency. Work on maintaining focus across more questions.",
            'low_streak': "Practice consistency. Try to maintain momentum between questions."
        },
        
        'coverage': {
            'comprehensive': "Excellent! You handled questions across all skill areas.",
            'broad': "Good coverage of different cold calling scenarios.",
            'narrow': "Continue practicing different types of situations."
        }
    }
    
    # ===== DIFFICULTY PROGRESSION =====
    
    DIFFICULTY_DISTRIBUTION = {
        'easy': 0.40,      # 40% easy questions
        'medium': 0.45,    # 45% medium questions  
        'hard': 0.15       # 15% hard questions
    }
    
    CATEGORY_PRIORITIES = {
        'openers': 'high',           # Always include opener questions
        'objections': 'high',        # Always include objection questions
        'qualification': 'medium',   # Usually include qualification
        'closing': 'medium',         # Usually include closing
        'rapport': 'low',           # Sometimes include rapport
        'discovery': 'medium',       # Usually include discovery
        'value_proposition': 'low',  # Sometimes include value prop
        'handling_gatekeepers': 'low' # Sometimes include gatekeepers
    }
    
    # ===== SUCCESS MESSAGES =====
    
    SUCCESS_MESSAGES = {
        'completion': [
            "🎯 Challenge Complete! Great warm-up session!",
            "🔥 Warm-up finished! You're ready for more training!",
            "✅ Challenge done! Your skills are getting sharper!",
            "🚀 Excellent warm-up! Ready for the next level!"
        ],
        
        'high_performance': [
            "Outstanding performance! You're mastering the fundamentals!",
            "Incredible accuracy! Your cold calling skills are excellent!",
            "Perfect warm-up! You're ready for advanced training!"
        ],
        
        'encouraging': [
            "Good work! Keep practicing to build your skills!",
            "Nice effort! Every challenge makes you stronger!",
            "Great practice! You're building valuable experience!"
        ]
    }
    
    # ===== FEEDBACK CATEGORIES =====
    
    FEEDBACK_CATEGORIES = {
        'openers': {
            'strength_indicators': ['clear introduction', 'respect for time', 'confident tone'],
            'improvement_areas': ['more specific purpose', 'stronger hook', 'better timing']
        },
        
        'objections': {
            'strength_indicators': ['acknowledges concern', 'stays calm', 'redirects well'],
            'improvement_areas': ['more empathy', 'stronger response', 'better reframe']
        },
        
        'qualification': {
            'strength_indicators': ['good questions', 'listens well', 'digs deeper'],
            'improvement_areas': ['more specific questions', 'better follow-up', 'clearer focus']
        },
        
        'closing': {
            'strength_indicators': ['clear ask', 'specific next steps', 'confident tone'],
            'improvement_areas': ['more urgency', 'better options', 'stronger close']
        }
    }
    
    # ===== IMPLEMENTATION NOTES =====
    """
    ROLEPLAY 3 KEY FEATURES:
    
    1. RAPID-FIRE FORMAT:
       - 25 questions total
       - Mixed categories for comprehensive coverage
       - Time pressure to simulate real call pace
       - Immediate progression (no detailed feedback per question)
    
    2. SKILL SHARPENING:
       - Covers all core cold calling areas
       - Reinforces quick thinking
       - Builds confidence through repetition
       - Identifies knowledge gaps
    
    3. ALWAYS AVAILABLE:
       - No unlock requirements
       - Perfect for daily warm-up
       - Quick 5-10 minute sessions
       - Good for skill maintenance
    
    4. PERFORMANCE TRACKING:
       - Accuracy percentage
       - Response time averages
       - Streak tracking for consistency
       - Category coverage analysis
    
    5. ADAPTIVE DIFFICULTY:
       - Mix of easy/medium/hard questions
       - Progression based on performance
       - Balanced across categories
       - Builds confidence gradually
    
    USAGE SCENARIOS:
    - Daily warm-up before calls
    - Quick skill assessment
    - Break between longer training
    - Confidence building
    - Knowledge gap identification
    
    SUCCESS METRICS:
    - 60%+ accuracy to pass
    - Improved response times
    - Higher streak counts
    - Broader category coverage
    """
# ===== API/UTILS/CONSTANTS.PY =====

# Job titles (alphabetically sorted)
JOB_TITLES = [
    "Brand/Communications Manager",
    "CEO (Chief Executive Officer)", 
    "CFO (Chief Financial Officer)",
    "CIO (Chief Information Officer)",
    "COO (Chief Operating Officer)",
    "Content Marketing Manager",
    "CTO (Chief Technology Officer)",
    "Demand Generation Manager",
    "Digital Marketing Manager",
    "Engineering Manager",
    "Finance Director",
    "Founder / Owner / Managing Director (MD)",
    "Head of Product",
    "Purchasing Manager",
    "R&D/Product Development Manager",
    "Sales Manager",
    "Sales Operations Manager",
    "Social Media Manager",
    "UX/UI Design Lead",
    "VP of Finance",
    "VP of HR",
    "VP of IT/Engineering", 
    "VP of Marketing",
    "VP of Sales",
    "Other (Please specify)"
]

# Industries
INDUSTRIES = [
    "Education & e-Learning",
    "Energy & Utilities", 
    "Finance & Banking",
    "Government & Public Sector",
    "Healthcare & Life Sciences",
    "Hospitality & Travel",
    "Information Technology & Services",
    "Logistics, Transportation & Supply Chain",
    "Manufacturing & Industrial",
    "Media & Entertainment",
    "Non-Profit & Associations", 
    "Professional Services (Legal, Accounting, Consulting)",
    "Real Estate & Property Management",
    "Retail & e-Commerce",
    "Telecommunications",
    "Other (Please specify)"
]

# Early objections (29 total) - used in Roleplay 1
EARLY_OBJECTIONS = [
    "What's this about?",
    "I'm not interested",
    "We don't take cold calls", 
    "Now is not a good time",
    "I have a meeting",
    "Can you call me later?",
    "I'm about to go into a meeting",
    "Send me an email",
    "Can you send me the information?",
    "Can you message me on WhatsApp?",
    "Who gave you this number?",
    "This is my personal number",
    "Where did you get my number?",
    "What are you trying to sell me?",
    "Is this a sales call?",
    "Is this a cold call?",
    "Are you trying to sell me something?",
    "We are ok for the moment",
    "We are all good / all set",
    "We're not looking for anything right now",
    "We are not changing anything",
    "How long is this going to take?",
    "Is this going to take long?",
    "What company are you calling from?",
    "Who are you again?",
    "Where are you calling from?",
    "I never heard of you",
    "Not interested right now",
    "Just send me the details"
]

# Post-pitch objections (24 total) - used in Roleplay 2
POST_PITCH_OBJECTIONS = [
    "It's too expensive for us",
    "We have no budget for this right now",
    "Your competitor is cheaper",
    "Can you give us a discount?", 
    "This isn't a good time",
    "We've already set this year's budget",
    "Call me back next quarter",
    "We're busy with other projects right now",
    "We already use [competitor] and we're happy",
    "We built something similar ourselves",
    "How exactly are you better than [competitor]?",
    "Switching providers seems like a lot of work",
    "I've never heard of your company",
    "Who else like us have you worked with?",
    "Can you send customer testimonials?",
    "How do I know this will really work?",
    "I'm not the decision-maker",
    "I need approval from my team first",
    "Can you send details so I can forward them?",
    "We'll need buy-in from other departments",
    "How long does this take to implement?",
    "We don't have time to learn a new system",
    "I'm concerned this won't integrate with our existing tools",
    "What happens if this doesn't work as promised?"
]

# AI pitch prompts (10 total) - used in Roleplay 2
PITCH_PROMPTS = [
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

# Impatience phrases for silence handling
IMPATIENCE_PHRASES = [
    "Hello? Are you still with me?",
    "Can you hear me?",
    "Just checking you're there…",
    "Still on the line?",
    "I don't have much time for this.",
    "Sounds like you are gone.",
    "Are you an idiot.",
    "What is going on.",
    "Are you okay to continue?",
    "I am afraid I have to go"
]

# Warm-up challenge questions (54 total) - used in Roleplay 3
WARMUP_QUESTIONS = [
    # Opener questions (3)
    "Give your opener",
    "What's your pitch in one sentence?", 
    "Ask me for a meeting",
    
    # Early objection responses (29) 
    "What's this about?",
    "I'm not interested",
    "We don't take cold calls",
    "Now is not a good time", 
    "I have a meeting",
    "Can you call me later?",
    "I'm about to go into a meeting",
    "Send me an email",
    "Can you send me the information?",
    "Can you message me on WhatsApp?",
    "Who gave you this number?",
    "This is my personal number",
    "Where did you get my number?",
    "What are you trying to sell me?",
    "Is this a sales call?",
    "Is this a cold call?",
    "Are you trying to sell me something?",
    "We are ok for the moment",
    "We are all good / all set",
    "We're not looking for anything right now",
    "We are not changing anything",
    "How long is this going to take?",
    "Is this going to take long?",
    "What company are you calling from?",
    "Who are you again?",
    "Where are you calling from?",
    "I never heard of you",
    "Not interested right now",
    "Just send me the details",
    
    # Post-pitch objection responses (22 remaining to make 54 total)
    "It's too expensive for us",
    "We have no budget right now",
    "Your competitor is cheaper",
    "Can you give us a discount?",
    "This isn't a good time",
    "We've already set this year's budget",
    "Call me back next quarter",
    "We're busy with other projects right now",
    "We already use [competitor] and we're happy",
    "We built something similar ourselves",
    "How exactly are you better than [competitor]?",
    "Switching providers seems like a lot of work",
    "I've never heard of your company",
    "Who else like us have you worked with?",
    "Can you send customer testimonials?",
    "How do I know this will really work?",
    "I'm not the decision-maker",
    "I need approval from my team first",
    "Can you send details so I can forward them?",
    "We'll need buy-in from other departments",
    "How long does this take to implement?",
    "We don't have time to learn a new system"
]

# Roleplay configuration
ROLEPLAY_CONFIG = {
    1: {
        "name": "Opener + Early Objections",
        "description": "Practice call opening, handling early objections, and delivering mini-pitch",
        "unlock_condition": "Always available",
        "modes": ["practice", "marathon", "legend"],
        "unlock_target": 2,  # Unlocks roleplay 2
        "marathon_threshold": 6,  # Need 6/10 to pass
        "legend_threshold": 6,  # Need 6/6 to pass
        "includes_hang_ups": True,
        "hang_up_chance": 0.25  # 25% chance of hang up after poor opener
    },
    2: {
        "name": "Pitch + Objections + Close", 
        "description": "Practice post-pitch conversation, objection handling, and meeting closing",
        "unlock_condition": "Complete Marathon 1 (6/10 calls)",
        "modes": ["practice", "marathon", "legend"],
        "unlock_target": 3,  # Unlocks roleplay 3
        "marathon_threshold": 6,
        "legend_threshold": 6,
        "includes_hang_ups": False,
        "requires_qualification": True,  # Must get company-fit admission
        "requires_meeting_ask": True     # Must ask for meeting with time slot
    },
    3: {
        "name": "Warm-up Challenge",
        "description": "25 random questions from master list (18/25 to pass)",
        "unlock_condition": "Complete Marathon 2 (6/10 calls)",
        "modes": ["challenge"],  # No marathon/legend mode
        "unlock_target": 4,
        "pass_threshold": 18,  # Need 18/25 correct
        "total_questions": 25,
        "time_limit_seconds": 5,  # >5 seconds = "too slow" warning
        "skip_allowed": True
    },
    4: {
        "name": "Full Cold Call Simulation",
        "description": "Complete call flow: opener → objection → pitch → objections → meeting ask",
        "unlock_condition": "Pass Warm-up Challenge (18/25)", 
        "modes": ["simulation"],  # No marathon/legend mode
        "unlock_target": 5,
        "success_criteria": "Successfully book a meeting",
        "includes_hang_ups": True,
        "hang_up_chance": 0.25,
        "requires_all_stages": True
    },
    5: {
        "name": "Power Hour Challenge",
        "description": "10 consecutive full cold calls - book as many meetings as possible",
        "unlock_condition": "Complete Full Cold Call Simulation",
        "modes": ["power_hour"],
        "unlock_target": None,  # Final roleplay
        "total_calls": 10,
        "success_metric": "meetings_booked",  # Track booking rate
        "no_pass_fail": True  # Focus on performance metrics
    }
}

# Pass criteria for different elements
PASS_CRITERIA = {
    "opener": {
        "required_count": 3,
        "total_criteria": 4,
        "criteria": [
            "Clear cold call opener (pattern interrupt, permission-based, or value-first)",
            "Casual, confident tone (contractions, short phrases)", 
            "Demonstrates empathy ('I know this is out of the blue...', 'You don't know me...')",
            "Ends with soft question ('Can I tell you why I'm calling?')"
        ]
    },
    "objection_handling": {
        "required_count": 3,
        "total_criteria": 4,
        "criteria": [
            "Acknowledges calmly ('Fair enough', 'Totally get that')",
            "Doesn't argue or pitch immediately",
            "Reframes or buys time in 1 sentence",
            "Ends with forward-moving question"
        ]
    },
    "mini_pitch": {
        "required_count": 3,
        "total_criteria": 4,
        "criteria": [
            "Short (1-2 sentences)",
            "Focuses on problem solved or outcome delivered",
            "Simple English, no jargon",
            "Sounds natural, not robotic"
        ]
    },
    "qualification": {
        "required": True,
        "criteria": "SDR secures explicit company-fit admission"
    },
    "meeting_ask": {
        "required_count": 1,
        "criteria": [
            "Clear meeting request",
            "Offers ≥1 concrete day/time slot", 
            "Handles push-back confidently"
        ]
    }
}

# Success messages for different achievements
SUCCESS_MESSAGES = {
    "marathon_pass": "Nice work—you passed {score} out of 10! You've unlocked the next modules and earned one shot at Legend Mode.",
    "marathon_fail": "You completed all 10 calls and scored {score}/10. Keep practising—the more reps you get, the easier it becomes.",
    "legend_success": "Wow—six for six! That's legendary. Very few reps pull this off, so enjoy the bragging rights!",
    "legend_fail": "Legend attempt over this time. To earn another shot, just pass Marathon again.",
    "warmup_pass": "Great job! You got {score}/25 correct. You've unlocked the Full Cold Call Simulation!",
    "warmup_fail": "You scored {score}/25. You need 18/25 to pass. Keep practicing and try again!",
    "simulation_success": "Excellent! You successfully booked a meeting. You've unlocked the Power Hour Challenge!",
    "simulation_fail": "Good effort! Keep practicing the full call flow and try again.",
    "power_hour_complete": "Power Hour complete! You booked {meetings} meetings out of 10 calls. Success rate: {rate}%"
}

# Access level configurations
ACCESS_LEVELS = {
    "limited_trial": {
        "name": "Limited Trial",
        "limits": {
            "total_hours": 3,      # 3 hours lifetime
            "days_limit": 7,       # 7 days from signup
            "monthly_hours": None
        },
        "unlocks": "permanent",     # Unlocks are permanent for trial users
        "features": ["all_roleplays", "coaching", "progress_tracking"]
    },
    "unlimited_basic": {
        "name": "Unlimited Basic", 
        "limits": {
            "total_hours": None,
            "days_limit": None,
            "monthly_hours": 50     # 50 hours per month
        },
        "unlocks": "24_hours",      # Unlocks expire after 24 hours
        "features": ["all_roleplays", "coaching", "progress_tracking", "priority_support"]
    },
    "unlimited_pro": {
        "name": "Unlimited Pro",
        "limits": {
            "total_hours": None,
            "days_limit": None, 
            "monthly_hours": 50     # 50 hours per month
        },
        "unlocks": "permanent",     # All roleplays unlocked immediately 
        "features": ["all_roleplays", "coaching", "progress_tracking", "priority_support", "advanced_analytics"]
    }
}

# Coaching categories
COACHING_CATEGORIES = [
    {
        "name": "Sales Coaching",
        "focus": ["opener_effectiveness", "objection_handling", "pitch_clarity", "qualification", "meeting_ask", "closing"],
        "examples": ["Opener effectiveness and empathy", "Objection handling techniques", "Pitch clarity and value focus"]
    },
    {
        "name": "Grammar Coaching",
        "focus": ["spanish_interference", "verb_tenses", "article_usage", "word_order"],
        "examples": ["You said: 'We can assist the meeting.' Say: 'We can attend the meeting.' Because 'assist' in Spanish means 'attend', but in English it means 'help'."]
    },
    {
        "name": "Vocabulary Coaching", 
        "focus": ["unnatural_choices", "false_friends", "register_appropriateness"],
        "examples": ["You said: 'win a meeting.' Say: 'book a meeting.' Because 'win' is not natural here."]
    },
    {
        "name": "Pronunciation Coaching",
        "focus": ["unclear_words", "asr_confidence", "stress_patterns"],
        "examples": ["Word mispronounced: 'schedule' Say it like: 'sked-jool'"]
    },
    {
        "name": "Rapport & Assertiveness",
        "focus": ["tone_confidence", "conversation_flow", "professional_warmth"],
        "examples": ["Tone and confidence levels", "Natural conversation flow", "Professional warmth"]
    }
]

# Default prospect avatars (placeholder paths)
PROSPECT_AVATARS = {
    "default": "/static/images/prospect-avatars/default.jpg",
    "male_ceo": "/static/images/prospect-avatars/male_ceo.jpg",
    "female_ceo": "/static/images/prospect-avatars/female_ceo.jpg", 
    "male_manager": "/static/images/prospect-avatars/male_manager.jpg",
    "female_manager": "/static/images/prospect-avatars/female_manager.jpg",
    "male_technical": "/static/images/prospect-avatars/male_technical.jpg",
    "female_technical": "/static/images/prospect-avatars/female_technical.jpg"
}

# Voice settings presets based on prospect types
VOICE_PRESETS = {
    "executive": {
        "stability": 0.85,
        "similarity_boost": 0.80,
        "style": 0.1,
        "description": "Authoritative, confident executive voice"
    },
    "manager": {
        "stability": 0.75,
        "similarity_boost": 0.75, 
        "style": 0.05,
        "description": "Professional, balanced manager voice"
    },
    "technical": {
        "stability": 0.80,
        "similarity_boost": 0.70,
        "style": 0.0,
        "description": "Analytical, neutral technical voice"
    },
    "friendly": {
        "stability": 0.70,
        "similarity_boost": 0.80,
        "style": 0.15,
        "description": "Warm, approachable voice"
    },
    "skeptical": {
        "stability": 0.80,
        "similarity_boost": 0.75,
        "style": 0.05,
        "description": "Cautious, questioning voice"
    }
}

# Voice settings for different prospect types
VOICE_SETTINGS = {
    'CEO': {
        'tone': 'authoritative',
        'pace': 'measured',
        'style': 'professional'
    },
    'CTO': {
        'tone': 'analytical',
        'pace': 'moderate',
        'style': 'technical'
    },
    'VP of Sales': {
        'tone': 'direct',
        'pace': 'fast',
        'style': 'results-oriented'
    },
    'Director': {
        'tone': 'friendly',
        'pace': 'moderate',
        'style': 'collaborative'
    }
}

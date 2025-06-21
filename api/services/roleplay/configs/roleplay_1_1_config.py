# ===== services/roleplay/configs/roleplay_1_1_config.py =====
# THIS IS WHERE YOU PUT YOUR ROLEPLAY INSTRUCTIONS

class Roleplay11Config:
    """Configuration for Roleplay 1.1 - Practice Mode
    
    PUT ALL YOUR ROLEPLAY INSTRUCTIONS AND RULES HERE!
    """
    
    # Basic Info
    ROLEPLAY_ID = "1.1"
    NAME = "Practice Mode"
    DESCRIPTION = "Single call with detailed coaching and feedback"
    
    # ===== YOUR CUSTOM INSTRUCTIONS GO HERE =====
    
    # Stage Flow (defines the conversation progression)
    STAGE_FLOW = {
        'phone_pickup': 'opener_evaluation',      # AI answers phone -> User gives opener
        'opener_evaluation': 'early_objection',   # AI evaluates opener -> Gives objection
        'early_objection': 'objection_handling',  # User handles objection
        'objection_handling': 'mini_pitch',       # User gives mini pitch
        'mini_pitch': 'soft_discovery',           # User asks discovery question
        'soft_discovery': 'extended_conversation', # Continue conversation
        'extended_conversation': 'call_ended'     # Natural end
    }
    
    # Evaluation Criteria for Each Stage
    EVALUATION_CRITERIA = {
        'opener': {
            'description': 'Evaluate opening statement',
            'criteria': [
                {
                    'name': 'clear_opener',
                    'description': 'Mentions reason for calling or company name',
                    'examples': ['calling from TechCorp', 'calling about your marketing'],
                    'keywords': ['calling from', 'calling about', 'reach out about']
                },
                {
                    'name': 'casual_tone',
                    'description': 'Uses contractions for natural speech',
                    'examples': ["I'm calling", "don't want to", "we're helping"],
                    'keywords': ["i'm", "don't", "can't", "we're", "you're"]
                },
                {
                    'name': 'shows_empathy',
                    'description': 'Acknowledges interrupting their day',
                    'examples': ['know this is out of the blue', 'know you don\'t know me'],
                    'keywords': ['out of the blue', 'interrupting', 'don\'t know me', 'unexpected']
                },
                {
                    'name': 'ends_with_question',
                    'description': 'Ends with engaging question',
                    'examples': ['Can I tell you why I\'m calling?', 'Mind if I explain?'],
                    'pattern': r'\?$'  # Ends with question mark
                }
            ],
            'pass_threshold': 3,  # Need 3 out of 4 criteria
            'coaching_tips': {
                'good': 'Excellent opener! You showed empathy and were direct.',
                'needs_work': 'Try adding more empathy: "I know this is out of the blue, but..."'
            }
        },
        
        'objection_handling': {
            'description': 'How user responds to early objections',
            'criteria': [
                {
                    'name': 'acknowledges_calmly',
                    'description': 'Acknowledges objection without arguing',
                    'examples': ['Fair enough', 'I understand', 'I get that'],
                    'keywords': ['fair enough', 'understand', 'get that', 'totally fair']
                },
                {
                    'name': 'no_arguing',
                    'description': 'Doesn\'t get defensive or argue',
                    'negative_keywords': ['but you should', 'you need to', 'you have to'],
                    'positive_examples': ['I hear you', 'That makes sense']
                },
                {
                    'name': 'brief_reframe',
                    'description': 'Briefly explains why calling in 1 sentence',
                    'examples': ['The reason I called is...', 'Quick reason for my call...'],
                    'max_words': 20
                },
                {
                    'name': 'forward_question',
                    'description': 'Moves conversation forward with question',
                    'examples': ['Can I get 30 seconds?', 'Fair to ask why?'],
                    'keywords': ['30 seconds', 'quick question', 'fair to ask']
                }
            ],
            'pass_threshold': 3,
            'coaching_tips': {
                'good': 'Great objection handling! You stayed calm and moved forward.',
                'needs_work': 'Don\'t argue back. Try: "Fair enough. Quick reason for my call..."'
            }
        },
        
        'mini_pitch': {
            'description': 'Short, outcome-focused pitch',
            'criteria': [
                {
                    'name': 'short_pitch',
                    'description': 'Under 30 words total',
                    'max_words': 30
                },
                {
                    'name': 'outcome_focused',
                    'description': 'Mentions benefits/results, not features',
                    'positive_keywords': ['save', 'increase', 'improve', 'reduce', 'help'],
                    'negative_keywords': ['features', 'platform', 'software', 'tool']
                },
                {
                    'name': 'simple_language',
                    'description': 'No jargon or buzzwords',
                    'negative_keywords': ['synergies', 'optimize', 'leverage', 'streamline'],
                    'positive_style': 'conversational'
                },
                {
                    'name': 'natural_tone',
                    'description': 'Sounds conversational, not robotic',
                    'check_contractions': True,
                    'avoid_corporate_speak': True
                }
            ],
            'pass_threshold': 3,
            'coaching_tips': {
                'good': 'Perfect pitch! Short, benefit-focused, and natural.',
                'needs_work': 'Keep it shorter and focus on outcomes: "We help companies save 30% on..."'
            }
        },
        
        'soft_discovery': {
            'description': 'Asking discovery questions',
            'criteria': [
                {
                    'name': 'tied_to_pitch',
                    'description': 'Question relates to the pitch given',
                    'check_relevance': True
                },
                {
                    'name': 'open_question',
                    'description': 'Uses "How", "What", not yes/no questions',
                    'question_starters': ['how', 'what', 'when', 'where', 'why'],
                    'avoid_yes_no': True
                },
                {
                    'name': 'soft_tone',
                    'description': 'Curious, not pushy',
                    'soft_phrases': ['curious', 'wondering', 'mind me asking'],
                    'avoid_aggressive': ['need to know', 'have to tell me']
                }
            ],
            'pass_threshold': 2,  # Easier threshold
            'coaching_tips': {
                'good': 'Great discovery question! You were curious and open-ended.',
                'needs_work': 'Try open questions: "How are you currently handling..."'
            }
        }
    }
    
    # Pass Thresholds (how many criteria needed to pass each stage)
    PASS_THRESHOLDS = {
        'opener': 3,
        'objection_handling': 3,
        'mini_pitch': 3,
        'soft_discovery': 2
    }
    
    # AI Prospect Behavior Instructions
    PROSPECT_BEHAVIOR = {
        'personality': 'Busy but professional executive',
        'initial_resistance': 'Moderate - willing to listen if approached right',
        'objection_style': 'Direct but not rude',
        'responses': {
            'good_opener': [
                "Alright, what's this about?",
                "I'm listening. Go ahead.",
                "You have 30 seconds."
            ],
            'poor_opener': [
                "What's this about?",
                "I'm not interested.",
                "Now is not a good time."
            ],
            'good_objection_handling': [
                "Okay, you have my attention.",
                "Fair enough. What do you do?",
                "Alright, I'm listening."
            ],
            'poor_objection_handling': [
                "I already told you I'm not interested.",
                "You're not listening to me.",
                "This is exactly why I hate cold calls."
            ]
        }
    }
    
    # Conversation Limits
    MAX_TOTAL_TURNS = 12  # Maximum conversation length
    MIN_TURNS_FOR_SUCCESS = 6  # Minimum turns to be considered successful
    
    # Scoring Weights
    SCORING_WEIGHTS = {
        'opener_score': 0.3,           # 30% weight
        'objection_handling_score': 0.3, # 30% weight  
        'pitch_score': 0.25,           # 25% weight
        'discovery_score': 0.15,       # 15% weight
        'overall_flow': 0.1            # 10% bonus for good flow
    }
    
    # Success Criteria
    SUCCESS_CRITERIA = {
        'minimum_score': 70,           # Need 70+ to pass
        'required_stages': ['opener_evaluation', 'objection_handling', 'mini_pitch'],
        'bonus_stages': ['soft_discovery'],  # Extra points for reaching these
    }
    
    # Coaching Feedback Templates
    COACHING_TEMPLATES = {
        'excellent': {
            'opener': 'Outstanding opener! You nailed the empathy and clarity.',
            'objection': 'Perfect objection handling - calm and forward-moving.',
            'pitch': 'Excellent pitch - short, benefit-focused, and natural.',
            'discovery': 'Great discovery question - curious and open-ended.'
        },
        'good': {
            'opener': 'Good opener! Consider adding more empathy next time.',
            'objection': 'Nice objection handling. Stay calm and acknowledge first.',
            'pitch': 'Solid pitch! Keep it short and focus on outcomes.',
            'discovery': 'Good question! Try making it more open-ended.'
        },
        'needs_work': {
            'opener': 'Work on your opener. Try: "I know this is out of the blue, but..."',
            'objection': 'Don\'t argue back. Try: "Fair enough. Quick reason for my call..."',
            'pitch': 'Keep your pitch under 20 words and focus on benefits.',
            'discovery': 'Ask "How" or "What" questions instead of yes/no questions.'
        }
    }
    
    # Custom Hang-up Triggers (when AI should hang up)
    HANGUP_TRIGGERS = {
        'poor_opener': 0.4,           # 40% chance if opener scores 0-1
        'repeated_objections': 0.6,    # 60% chance if user keeps arguing
        'too_long_pitch': 0.3,         # 30% chance if pitch is over 50 words
        'no_empathy': 0.5,             # 50% chance if user shows no empathy
        'silence_15_seconds': 1.0      # 100% chance after 15 seconds silence
    }

# ===== EXAMPLE: How to Add Your Own Custom Instructions =====

class CustomInstructions:
    """
    ADD YOUR SPECIFIC ROLEPLAY INSTRUCTIONS HERE!
    
    Examples of what you can customize:
    """
    
    # 1. CUSTOM EVALUATION CRITERIA
    YOUR_CUSTOM_CRITERIA = {
        'opener': {
            'must_mention_company': {
                'name': 'mentions_company_name',
                'description': 'Must mention the company name clearly',
                'required_keywords': ['TechCorp', 'our company', 'we at'],
                'weight': 2  # Double weight for this criterion
            },
            'no_weak_words': {
                'name': 'avoid_weak_language',
                'description': 'Avoid weak words like "maybe", "possibly"',
                'forbidden_words': ['maybe', 'possibly', 'perhaps', 'might'],
                'penalty': -1  # Subtract points for using these
            }
        }
    }
    
    # 2. CUSTOM AI BEHAVIOR
    YOUR_PROSPECT_PERSONALITY = {
        'industry': 'healthcare',  # Change AI behavior based on industry
        'personality_type': 'skeptical_but_fair',
        'pain_points': ['compliance', 'patient_safety', 'cost_reduction'],
        'hot_buttons': ['improve_patient_outcomes', 'reduce_errors'],
        'objection_style': 'asks_detailed_questions'
    }
    
    # 3. CUSTOM SCORING RULES
    YOUR_SCORING_RULES = {
        'perfect_score_requirements': [
            'mentions_company_name',
            'shows_empathy', 
            'asks_permission',
            'ends_with_question'
        ],
        'auto_fail_conditions': [
            'argues_with_prospect',
            'pitch_over_40_words',
            'uses_jargon'
        ],
        'bonus_points': {
            'uses_prospect_name': 5,    # +5 points for personalization
            'references_company_news': 10,  # +10 for good research
            'perfect_objection_handling': 15  # +15 for flawless objection response
        }
    }
    
    # 4. INDUSTRY-SPECIFIC INSTRUCTIONS
    HEALTHCARE_SPECIFIC = {
        'required_compliance_mention': True,
        'must_mention_hipaa': False,
        'avoid_medical_claims': True,
        'focus_on_efficiency': True
    }
    
    # 5. DIFFICULTY LEVELS
    DIFFICULTY_SETTINGS = {
        'beginner': {
            'ai_patience': 'high',
            'objection_intensity': 'low',
            'pass_threshold': 2  # Only need 2/4 criteria
        },
        'intermediate': {
            'ai_patience': 'medium',
            'objection_intensity': 'medium', 
            'pass_threshold': 3  # Need 3/4 criteria
        },
        'expert': {
            'ai_patience': 'low',
            'objection_intensity': 'high',
            'pass_threshold': 4,  # Need all 4 criteria
            'random_curveballs': True
        }
    }

# ===== HOW TO USE THESE INSTRUCTIONS =====
"""
TO ADD YOUR OWN ROLEPLAY INSTRUCTIONS:

1. MODIFY THE CONFIG ABOVE:
   - Change EVALUATION_CRITERIA to match your requirements
   - Update PROSPECT_BEHAVIOR for your industry/scenario
   - Adjust SCORING_WEIGHTS based on what's most important
   - Customize COACHING_TEMPLATES for your style

2. THE ROLEPLAY ENGINE READS THIS CONFIG:
   - services/roleplay/roleplay_1_1.py uses this config
   - The AI evaluation system follows these rules
   - Scoring is calculated based on your criteria

3. FRONTEND AUTOMATICALLY UPDATES:
   - No changes needed in JavaScript
   - UI will reflect your new scoring system
   - Coaching feedback will use your templates

4. EXAMPLE CUSTOMIZATION:
   If you want to focus on healthcare cold calls:
   - Add medical terminology to required keywords
   - Include HIPAA compliance in evaluation criteria
   - Adjust AI personality to be more cautious
   - Update coaching tips for healthcare context

5. TESTING YOUR CHANGES:
   - Start a practice call in mode 1.1
   - The system will use your new criteria
   - Check that scoring matches your expectations
   - Adjust weights and thresholds as needed
"""
# ===== ENHANCED: services/roleplay/configs/roleplay_1_2_config.py =====

class Roleplay12Config:
    """
    Enhanced Configuration for Roleplay 1.2 - Marathon Mode
    Adapted from successful Roleplay 1.1 with marathon-specific features
    """
    
    # Basic Info
    ROLEPLAY_ID = "1.2"
    NAME = "Marathon Mode"
    DESCRIPTION = "10 calls, extended repetition. Pass 6 out of 10 to complete."
    
    # Marathon Settings
    TOTAL_CALLS = 10
    CALLS_TO_PASS = 6
    RANDOM_HANGUP_CHANCE = 0.25  # 25% chance of random hang-up in marathon
    
    # ===== ENHANCED STAGE FLOW (adapted from 1.1) =====
    
    STAGE_FLOW = {
        'phone_pickup': 'opener_evaluation',      # AI answers phone -> User gives opener
        'opener_evaluation': 'early_objection',   # AI evaluates opener -> Gives objection
        'early_objection': 'objection_handling',  # User handles objection
        'objection_handling': 'mini_pitch',       # User gives mini pitch
        'mini_pitch': 'soft_discovery',           # User asks discovery question
        'soft_discovery': 'call_ended'            # Natural end or continue
    }
    
    # ===== EVALUATION CRITERIA (same as 1.1 but more lenient) =====
    
    EVALUATION_CRITERIA = {
        'opener': {
            'description': 'Evaluate opening statement - Marathon mode (more lenient)',
            'criteria': [
                {
                    'name': 'clear_introduction',
                    'description': 'Clearly states name and company/reason for calling',
                    'examples': ['Hi, this is John from TechCorp', 'calling from SalesCorp about your marketing'],
                    'keywords': ['calling from', 'this is', 'my name is', 'calling about'],
                    'weight': 1.5
                },
                {
                    'name': 'shows_empathy',
                    'description': 'Acknowledges interrupting their day or shows understanding',
                    'examples': ['know this is out of the blue', 'know you don\'t know me', 'unexpected call'],
                    'keywords': ['out of the blue', 'interrupting', 'don\'t know me', 'unexpected', 'busy'],
                    'weight': 1.8  # Slightly less weight than practice mode
                },
                {
                    'name': 'natural_tone',
                    'description': 'Uses contractions and conversational language',
                    'examples': ["I'm calling", "don't want to", "we're helping", "can't take long"],
                    'keywords': ["i'm", "don't", "can't", "we're", "you're", "won't", "isn't"],
                    'weight': 1.0
                },
                {
                    'name': 'engaging_close',
                    'description': 'Ends with permission-seeking question',
                    'examples': ['Can I tell you why I\'m calling?', 'Mind if I explain?', 'Fair to ask why?'],
                    'patterns': [r'\?$', r'can i', r'mind if', r'fair to'],
                    'weight': 1.2  # Slightly less critical in marathon
                }
            ],
            'pass_threshold': 4.0,  # More lenient than practice mode (was 5.0)
            'coaching_tips': {
                'excellent': 'Great opener! Perfect for marathon mode.',
                'good': 'Good opener! You\'re building momentum.',
                'needs_work': 'Keep it simple for marathon: empathy + brief reason + question.'
            }
        },
        
        'objection_handling': {
            'description': 'How user responds to early objections - Marathon mode',
            'criteria': [
                {
                    'name': 'acknowledges_gracefully',
                    'description': 'Acknowledges objection without being defensive',
                    'examples': ['Fair enough', 'I understand', 'I get that', 'That makes sense'],
                    'keywords': ['fair enough', 'understand', 'get that', 'totally fair', 'makes sense'],
                    'negative_indicators': ['but you', 'you need', 'you should'],
                    'weight': 1.8  # Slightly less weight than practice
                },
                {
                    'name': 'stays_calm',
                    'description': 'Doesn\'t argue or get defensive',
                    'evaluation': 'no_defensive_language',
                    'negative_keywords': ['but you should', 'you need to understand', 'actually you do'],
                    'positive_tone': ['calm', 'understanding', 'respectful'],
                    'weight': 1.5
                },
                {
                    'name': 'brief_reason',
                    'description': 'Gives brief, compelling reason for calling (under 25 words)',
                    'examples': ['Quick reason I called...', 'The reason I reached out...'],
                    'max_words': 25,  # More lenient than practice mode
                    'keywords': ['reason i called', 'why i reached out', 'quick reason'],
                    'weight': 1.5
                },
                {
                    'name': 'moves_forward',
                    'description': 'Asks for permission to continue or small commitment',
                    'examples': ['Can I get 30 seconds?', 'Fair to ask why?', 'Mind if I explain?'],
                    'keywords': ['30 seconds', 'quick question', 'fair to ask', 'mind if'],
                    'weight': 1.8
                }
            ],
            'pass_threshold': 4.5,  # More lenient than practice mode
            'coaching_tips': {
                'excellent': 'Perfect objection handling for marathon mode!',
                'good': 'Good handling. Keep the momentum going.',
                'needs_work': 'Marathon tip: Acknowledge + brief reason + move forward.'
            }
        },
        
        'mini_pitch': {
            'description': 'Short, compelling pitch - Marathon optimized',
            'criteria': [
                {
                    'name': 'concise_length',
                    'description': 'Under 30 words total',  # More lenient than practice
                    'max_words': 30,
                    'weight': 1.0
                },
                {
                    'name': 'outcome_focused',
                    'description': 'Mentions benefits/results, not just features',
                    'positive_keywords': ['save', 'increase', 'improve', 'reduce', 'help companies', 'results'],
                    'negative_keywords': ['platform', 'software features', 'our tool', 'technology'],
                    'examples': ['help companies save 30%', 'increase revenue by', 'reduce costs'],
                    'weight': 2.0  # Still important but less critical than practice
                },
                {
                    'name': 'specific_benefit',
                    'description': 'Includes specific numbers or concrete outcomes',
                    'examples': ['save 30%', 'increase by 50%', 'reduce time by 2 hours'],
                    'patterns': [r'\d+%', r'\$\d+', r'\d+\s*(hours|minutes|days)'],
                    'weight': 1.5  # Less critical in marathon mode
                },
                {
                    'name': 'conversational_tone',
                    'description': 'Sounds natural, not robotic or scripted',
                    'check_contractions': True,
                    'avoid_jargon': ['synergies', 'optimize', 'leverage', 'streamline', 'solution'],
                    'weight': 1.5
                }
            ],
            'pass_threshold': 4.0,  # More lenient than practice mode
            'coaching_tips': {
                'excellent': 'Perfect marathon pitch! Short and powerful.',
                'good': 'Good pitch! Keep it simple for marathon mode.',
                'needs_work': 'Marathon pitches: under 25 words, focus on specific outcomes.'
            }
        },
        
        'soft_discovery': {
            'description': 'Asking discovery questions naturally - Marathon mode',
            'criteria': [
                {
                    'name': 'relevant_to_pitch',
                    'description': 'Question relates directly to the pitch given',
                    'check_relevance': True,
                    'weight': 1.8  # Less critical in marathon
                },
                {
                    'name': 'open_ended',
                    'description': 'Uses "How", "What", "When" - not yes/no questions',
                    'question_starters': ['how', 'what', 'when', 'where', 'why', 'tell me'],
                    'avoid_yes_no': True,
                    'examples': ['How are you currently handling...', 'What\'s your process for...'],
                    'weight': 1.5
                },
                {
                    'name': 'curious_tone',
                    'description': 'Sounds genuinely curious, not pushy',
                    'soft_phrases': ['curious', 'wondering', 'mind me asking', 'interested to know'],
                    'avoid_aggressive': ['need to know', 'have to tell me', 'you must'],
                    'weight': 1.2
                }
            ],
            'pass_threshold': 3.0,  # More lenient than practice mode
            'coaching_tips': {
                'excellent': 'Great discovery question for marathon!',
                'good': 'Good question! Keep the conversation flowing.',
                'needs_work': 'Simple discovery: "How are you currently handling [area from pitch]?"'
            }
        }
    }
    
    # ===== MARATHON-SPECIFIC AI BEHAVIOR =====
    
    PROSPECT_BEHAVIOR = {
        'personality_traits': {
            'base_personality': 'Busy but professional executive',
            'initial_resistance': 'Moderate - marathon mode is slightly more forgiving',
            'empathy_sensitivity': 'High - responds well to empathy and respect',
            'time_consciousness': 'High - values brevity and directness',
            'decision_style': 'Analytical but practical',
            'marathon_patience': 'Slightly higher patience for learning'
        },
        
        'response_patterns': {
            'excellent_opener': [
                "Alright, what's this about?",
                "I'm listening. You have my attention.",
                "You have 30 seconds. Go ahead.",
                "Fair enough. What do you do?",
                "Okay, I'll hear you out."
            ],
            'good_opener': [
                "What's this regarding?",
                "I'm busy, but go ahead.",
                "Make it quick.",
                "I'm listening.",
                "Go on."
            ],
            'poor_opener': [
                "I'm not interested.",
                "We don't take cold calls.",
                "How did you get this number?",
                "Remove me from your list.",
                "This is a waste of time."
            ],
            'excellent_objection_handling': [
                "Okay, you have my attention.",
                "Fair enough. What exactly do you do?",
                "Alright, I'm listening.",
                "That's reasonable. Continue.",
                "You've got 30 seconds."
            ],
            'good_objection_handling': [
                "Go on.",
                "I'm listening.",
                "What do you mean?",
                "Continue.",
                "Okay."
            ],
            'poor_objection_handling': [
                "I already told you I'm not interested.",
                "You're not listening to me.",
                "This is exactly why I hate cold calls.",
                "I'm hanging up now.",
                "Goodbye."
            ],
            'excellent_pitch': [
                "That sounds interesting. How does that work?",
                "Tell me more about that.",
                "What kind of results do you typically see?",
                "That could be relevant. Continue.",
                "I'm intrigued. Go on."
            ],
            'good_pitch': [
                "Okay, I'm following.",
                "That's intriguing.",
                "Go on.",
                "I see.",
                "Continue."
            ],
            'poor_pitch': [
                "That's too vague.",
                "I don't understand what you're saying.",
                "Sounds like every other vendor.",
                "We're all set, thanks.",
                "Not interested."
            ]
        }
    }
    
    # ===== CONVERSATION LIMITS (Marathon Optimized) =====
    
    CONVERSATION_LIMITS = {
        'max_total_turns': 12,          # Shorter than practice mode for efficiency
        'min_turns_for_success': 4,    # Lower minimum for marathon
        'optimal_turn_range': (6, 10), # Slightly shorter optimal range
        'max_stage_turns': {
            'opener_evaluation': 2,
            'objection_handling': 2,     # Faster progression
            'mini_pitch': 2,
            'soft_discovery': 3,
            'call_ended': 1
        }
    }
    
    # ===== MARATHON-SPECIFIC SCORING =====
    
    SCORING_WEIGHTS = {
        'opener_score': 0.35,           # Slightly higher weight on opener
        'objection_handling_score': 0.35, # High weight on objection handling
        'pitch_score': 0.20,            # Reduced pitch weight for marathon
        'discovery_score': 0.10,        # Lower discovery weight
        'conversation_flow_bonus': 0.05, # Small flow bonus
        'marathon_efficiency_bonus': 0.05 # New: bonus for efficient calls
    }
    
    SUCCESS_CRITERIA = {
        'minimum_score': 60,            # Lower than practice mode
        'excellent_threshold': 80,      # Lower excellent threshold
        'required_stages': ['opener_evaluation', 'objection_handling'],
        'bonus_stages': ['mini_pitch', 'soft_discovery'],
        'marathon_pass_threshold': 6,   # Need 6 out of 10 calls
        'critical_failures': {
            'no_empathy': -5,           # Reduced penalties for marathon
            'too_pushy': -10,
            'too_vague': -5,
            'argues_with_prospect': -15
        }
    }
    
    # ===== MARATHON HANG-UP TRIGGERS (More Forgiving) =====
    
    HANGUP_TRIGGERS = {
        'immediate_hangup': {
            'no_empathy_opener': 0.4,       # Reduced from 0.6
            'aggressive_response': 0.6,      # Reduced from 0.8
            'pushy_after_objection': 0.5     # Reduced from 0.7
        },
        'gradual_hangup': {
            'poor_opener': 0.2,              # Reduced from 0.3
            'repeated_objections': 0.3,       # Reduced from 0.5
            'too_long_pitch': 0.2,           # Reduced from 0.4
            'no_questions': 0.1               # Reduced from 0.3
        },
        'random_hangup': {
            'marathon_only': True,
            'opener_stage_chance': 0.25,     # 25% chance after successful opener
            'applies_to_stages': ['opener_evaluation']
        },
        'silence_hangup': {
            'silence_15_seconds': 1.0        # Same as practice mode
        }
    }
    
    # ===== MARATHON COACHING TEMPLATES =====
    
    COACHING_TEMPLATES = {
        'marathon_completion': {
            'passed': {
                'message': 'Excellent! You passed {calls_passed} out of {total_calls} calls. Marathon completed successfully!',
                'next_steps': 'You\'ve unlocked Legend Mode! Your consistency is impressive.'
            },
            'failed': {
                'message': 'You completed all {total_calls} calls and passed {calls_passed}. Keep practicing - marathon mode builds consistency!',
                'next_steps': 'Each marathon run improves your skills. Try again when you\'re ready.'
            }
        },
        
        'opener_feedback': {
            'excellent': {
                'message': 'Perfect opener for marathon mode! You\'re building great momentum.',
                'next_steps': 'Keep this energy and approach for the remaining calls.'
            },
            'good': {
                'message': 'Good opener! Marathon is about consistency - you\'re on track.',
                'next_steps': 'Try adding a bit more empathy: "I know this is out of the blue, but..."'
            },
            'needs_work': {
                'message': 'Marathon tip: Keep openers simple and empathetic.',
                'next_steps': 'Formula: Empathy + Brief reason + Permission question.'
            }
        },
        
        'objection_feedback': {
            'excellent': {
                'message': 'Excellent objection handling! You\'re mastering the marathon rhythm.',
                'next_steps': 'This approach works - keep using it consistently.'
            },
            'good': {
                'message': 'Good objection handling. Marathon success comes from consistency.',
                'next_steps': 'Remember: Acknowledge + Brief reason + Move forward.'
            },
            'needs_work': {
                'message': 'Marathon objection tip: Stay calm and redirect quickly.',
                'next_steps': 'Try: "Fair enough. Quick reason I called is [X]. Can I get 30 seconds?"'
            }
        },
        
        'pitch_feedback': {
            'excellent': {
                'message': 'Perfect marathon pitch! Short, specific, and compelling.',
                'next_steps': 'This is exactly the right length and focus for marathon mode.'
            },
            'good': {
                'message': 'Good pitch! Marathon efficiency is key.',
                'next_steps': 'Keep it under 25 words and focus on specific outcomes.'
            },
            'needs_work': {
                'message': 'Marathon pitches need to be shorter and more specific.',
                'next_steps': 'Formula: "We help [specific type] companies [specific outcome with number]."'
            }
        }
    }
    
    # ===== MARATHON PROGRESSION RULES =====
    
    PROGRESSION_RULES = {
        'unlock_legend_mode': {
            'requirement': 'marathon_passed',
            'description': 'Pass Marathon Mode to unlock Legend Mode (1.3)',
            'benefits': [
                'Unlocks Legend Mode (1.3)',
                'Unlocks Module 2 access for 24 hours',
                'Resets Legend attempt flag'
            ]
        },
        'marathon_streak_bonuses': {
            '2_marathons': 'Consistency Badge',
            '5_marathons': 'Marathon Master Badge',
            '10_marathons': 'Endurance Expert Badge'
        }
    }
    
    # ===== IMPLEMENTATION NOTES =====
    """
    MARATHON MODE KEY DIFFERENCES FROM PRACTICE MODE:
    
    1. MORE FORGIVING EVALUATION:
       - Lower pass thresholds across all rubrics
       - Reduced hang-up probabilities
       - Higher minimum scores for early attempts
    
    2. MARATHON-SPECIFIC FEATURES:
       - Random hang-ups at opener stage (25% chance)
       - Progress tracking across 10 calls
       - Efficiency bonuses for quick, effective calls
       - Streak tracking and momentum building
    
    3. OPTIMIZED FOR REPETITION:
       - Shorter optimal conversation length
       - Faster stage progression
       - Focus on consistency over perfection
       - Encouraging coaching messages
    
    4. UNLOCKS AND PROGRESSION:
       - Passing marathon unlocks Legend Mode
       - Temporary access to advanced modules
       - Achievement badges for multiple completions
    
    TO USE THIS CONFIG:
    1. Replace existing roleplay_1_2_config.py
    2. Restart roleplay service
    3. Test marathon flow with multiple calls
    4. Monitor for appropriate difficulty and progression
    
    EXPECTED IMPROVEMENTS:
    - More consistent call completion rates
    - Better user engagement through achievable goals
    - Natural progression to advanced modes
    - Maintains challenge while encouraging practice
    """
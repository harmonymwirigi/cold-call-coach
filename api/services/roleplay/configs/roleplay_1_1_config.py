# ===== ENHANCED: services/roleplay/configs/roleplay_1_1_config.py =====

class Roleplay11Config:
    """Enhanced Configuration for Roleplay 1.1 - Practice Mode
    
    OPTIMIZED FOR LOGICAL CONVERSATION FLOW AND ACCURATE SCORING
    """
    
    # Basic Info
    ROLEPLAY_ID = "1.1"
    NAME = "Practice Mode"
    DESCRIPTION = "Single call with detailed coaching and feedback"
    
    # ===== ENHANCED STAGE FLOW =====
    
    STAGE_FLOW = {
        'phone_pickup': 'opener_evaluation',      # AI answers phone -> User gives opener
        'opener_evaluation': 'early_objection',   # AI evaluates opener -> Gives objection
        'early_objection': 'objection_handling',  # User handles objection
        'objection_handling': 'mini_pitch',       # User gives mini pitch
        'mini_pitch': 'soft_discovery',           # User asks discovery question
        'soft_discovery': 'extended_conversation', # Continue natural conversation
        'extended_conversation': 'call_ended'     # Natural end
    }
    
    # ===== ENHANCED EVALUATION CRITERIA =====
    
    EVALUATION_CRITERIA = {
        'opener': {
            'description': 'Evaluate opening statement for empathy, clarity, and engagement',
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
                    'weight': 2.0  # Higher weight for empathy
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
                    'weight': 1.5
                }
            ],
            'pass_threshold': 5.0,  # Out of 7 possible points (weighted)
            'coaching_tips': {
                'excellent': 'Outstanding opener! Perfect empathy, clarity, and natural tone.',
                'good': 'Good opener! Consider adding more empathy: "I know this is out of the blue, but..."',
                'needs_work': 'Focus on empathy first, then briefly state why you\'re calling. Try: "I know this is unexpected, but I\'m calling from [Company] because..."'
            }
        },
        
        'objection_handling': {
            'description': 'How user responds to early objections with grace and forward momentum',
            'criteria': [
                {
                    'name': 'acknowledges_gracefully',
                    'description': 'Acknowledges objection without being defensive',
                    'examples': ['Fair enough', 'I understand', 'I get that', 'That makes sense'],
                    'keywords': ['fair enough', 'understand', 'get that', 'totally fair', 'makes sense'],
                    'negative_indicators': ['but you', 'you need', 'you should'],
                    'weight': 2.0
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
                    'description': 'Gives brief, compelling reason for calling (under 20 words)',
                    'examples': ['Quick reason I called...', 'The reason I reached out...'],
                    'max_words': 20,
                    'keywords': ['reason i called', 'why i reached out', 'quick reason'],
                    'weight': 1.5
                },
                {
                    'name': 'moves_forward',
                    'description': 'Asks for permission to continue or small commitment',
                    'examples': ['Can I get 30 seconds?', 'Fair to ask why?', 'Mind if I explain?'],
                    'keywords': ['30 seconds', 'quick question', 'fair to ask', 'mind if'],
                    'weight': 2.0
                }
            ],
            'pass_threshold': 5.0,
            'coaching_tips': {
                'excellent': 'Perfect objection handling! You stayed calm and moved the conversation forward.',
                'good': 'Good objection handling. Remember to acknowledge first, then briefly explain.',
                'needs_work': 'Don\'t argue back. Try: "Fair enough. Quick reason I called is... Can I get 30 seconds?"'
            }
        },
        
        'mini_pitch': {
            'description': 'Short, compelling pitch focused on outcomes',
            'criteria': [
                {
                    'name': 'concise_length',
                    'description': 'Under 25 words total',
                    'max_words': 25,
                    'weight': 1.0
                },
                {
                    'name': 'outcome_focused',
                    'description': 'Mentions benefits/results, not just features',
                    'positive_keywords': ['save', 'increase', 'improve', 'reduce', 'help companies', 'results'],
                    'negative_keywords': ['platform', 'software features', 'our tool', 'technology'],
                    'examples': ['help companies save 30%', 'increase revenue by', 'reduce costs'],
                    'weight': 2.5  # Most important for pitch
                },
                {
                    'name': 'specific_benefit',
                    'description': 'Includes specific numbers or concrete outcomes',
                    'examples': ['save 30%', 'increase by 50%', 'reduce time by 2 hours'],
                    'patterns': [r'\d+%', r'\$\d+', r'\d+\s*(hours|minutes|days)'],
                    'weight': 2.0
                },
                {
                    'name': 'conversational_tone',
                    'description': 'Sounds natural, not robotic or scripted',
                    'check_contractions': True,
                    'avoid_jargon': ['synergies', 'optimize', 'leverage', 'streamline', 'solution'],
                    'weight': 1.5
                }
            ],
            'pass_threshold': 5.0,
            'coaching_tips': {
                'excellent': 'Perfect pitch! Short, specific, and outcome-focused.',
                'good': 'Good pitch! Make it even shorter and more specific about results.',
                'needs_work': 'Keep it under 20 words and focus on specific outcomes: "We help [type] companies save [X]% on [specific thing]."'
            }
        },
        
        'soft_discovery': {
            'description': 'Asking discovery questions naturally',
            'criteria': [
                {
                    'name': 'relevant_to_pitch',
                    'description': 'Question relates directly to the pitch given',
                    'check_relevance': True,
                    'weight': 2.0
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
                    'weight': 1.5
                }
            ],
            'pass_threshold': 3.5,
            'coaching_tips': {
                'excellent': 'Great discovery question! Curious, relevant, and open-ended.',
                'good': 'Good question! Make sure it ties directly to your pitch.',
                'needs_work': 'Try open questions tied to your pitch: "How are you currently handling [specific area from pitch]?"'
            }
        }
    }
    
    # ===== ENHANCED AI PROSPECT BEHAVIOR =====
    
    PROSPECT_BEHAVIOR = {
        'personality_traits': {
            'base_personality': 'Busy but professional executive',
            'initial_resistance': 'Moderate - willing to listen if approached right',
            'empathy_sensitivity': 'High - responds well to empathy and respect',
            'time_consciousness': 'Very high - values brevity and directness',
            'decision_style': 'Analytical but practical'
        },
        
        'response_patterns': {
            'excellent_opener': [
                "Alright, what's this about?",
                "I'm listening. You have my attention.",
                "You have 30 seconds. Go ahead.",
                "Fair enough. What do you do?"
            ],
            'good_opener': [
                "What's this regarding?",
                "I'm busy, but go ahead.",
                "Make it quick."
            ],
            'poor_opener': [
                "I'm not interested.",
                "We don't take cold calls.",
                "How did you get this number?",
                "Remove me from your list."
            ],
            'excellent_objection_handling': [
                "Okay, you have my attention.",
                "Fair enough. What exactly do you do?",
                "Alright, I'm listening.",
                "That's reasonable. Continue."
            ],
            'good_objection_handling': [
                "Go on.",
                "I'm listening.",
                "What do you mean?"
            ],
            'poor_objection_handling': [
                "I already told you I'm not interested.",
                "You're not listening to me.",
                "This is exactly why I hate cold calls.",
                "Goodbye."
            ],
            'excellent_pitch': [
                "That sounds interesting. How does that work?",
                "Tell me more about that.",
                "What kind of results do you typically see?",
                "That could be relevant. Continue."
            ],
            'good_pitch': [
                "Okay, I'm following.",
                "That's intriguing.",
                "Go on."
            ],
            'poor_pitch': [
                "That's too vague.",
                "I don't understand what you're saying.",
                "Sounds like every other vendor.",
                "We're all set, thanks."
            ]
        },
        
        'conversation_progression': {
            'warmup_threshold': 3,  # Number of good responses needed to warm up
            'interest_indicators': ['specific questions', 'asking for details', 'time investment'],
            'disengagement_signals': ['short responses', 'looking to end', 'skeptical tone']
        }
    }
    
    # ===== ENHANCED CONVERSATION LIMITS =====
    
    CONVERSATION_LIMITS = {
        'max_total_turns': 14,          # Increased for natural conversation
        'min_turns_for_success': 6,    # Minimum for meaningful conversation
        'optimal_turn_range': (8, 12), # Sweet spot for practice mode
        'max_stage_turns': {
            'opener_evaluation': 2,
            'objection_handling': 3,
            'mini_pitch': 2,
            'soft_discovery': 4,
            'extended_conversation': 6
        }
    }
    
    # ===== ENHANCED SCORING SYSTEM =====
    
    SCORING_WEIGHTS = {
        'opener_score': 0.30,           # 30% - Critical first impression
        'objection_handling_score': 0.30, # 30% - Shows sales skill
        'pitch_score': 0.25,            # 25% - Core value proposition
        'discovery_score': 0.15,        # 15% - Shows curiosity
        'conversation_flow_bonus': 0.10, # 10% - Natural progression
        'empathy_bonus': 0.05,          # 5% - Extra for showing empathy
        'specificity_bonus': 0.05       # 5% - Extra for specific benefits
    }
    
    SUCCESS_CRITERIA = {
        'minimum_score': 70,            # Need 70+ to pass
        'excellent_threshold': 85,      # Excellent performance
        'required_stages': ['opener_evaluation', 'objection_handling', 'mini_pitch'],
        'bonus_stages': ['soft_discovery', 'extended_conversation'],
        'critical_failures': {
            'no_empathy': -10,          # Penalty for no empathy
            'too_pushy': -15,           # Penalty for being pushy
            'too_vague': -10,           # Penalty for vague pitch
            'argues_with_prospect': -20  # Major penalty for arguing
        }
    }
    
    # ===== ENHANCED COACHING TEMPLATES =====
    
    COACHING_TEMPLATES = {
        'opener_feedback': {
            'excellent': {
                'message': 'Outstanding opener! You showed genuine empathy, were clear about why you were calling, and sounded completely natural. This is exactly how cold calls should start.',
                'next_steps': 'Keep using this approach - it builds immediate trust and rapport.'
            },
            'good': {
                'message': 'Good opener! You covered most of the basics well. Consider adding more empathy right at the start.',
                'next_steps': 'Try: "I know this is completely out of the blue, but I\'m calling from [Company] because..."'
            },
            'needs_work': {
                'message': 'Your opener needs more empathy and clarity. Start by acknowledging you\'re interrupting their day.',
                'next_steps': 'Structure: Empathy → Brief reason → Permission. Example: "I know this is unexpected, but I\'m calling because we help companies like yours save 30% on [specific area]. Mind if I explain?"'
            }
        },
        
        'objection_feedback': {
            'excellent': {
                'message': 'Perfect objection handling! You stayed calm, acknowledged their concern, and smoothly moved the conversation forward.',
                'next_steps': 'This is the gold standard - keep using this approach.'
            },
            'good': {
                'message': 'Good objection handling. You stayed calm and professional.',
                'next_steps': 'Remember the formula: Acknowledge → Brief reason → Ask permission. "Fair enough. Quick reason I called is [X]. Can I get 30 seconds?"'
            },
            'needs_work': {
                'message': 'Don\'t argue with objections. Instead, acknowledge and redirect.',
                'next_steps': 'Try: "I totally understand. The reason I called is [brief, specific reason]. Fair to ask why?" Never say "but you should" or argue back.'
            }
        },
        
        'pitch_feedback': {
            'excellent': {
                'message': 'Excellent pitch! Short, specific, and focused on concrete outcomes. This is how you capture attention.',
                'next_steps': 'Perfect approach - specific benefits resonate much better than features.'
            },
            'good': {
                'message': 'Good pitch! You kept it concise and benefit-focused.',
                'next_steps': 'Make it even more specific with numbers: "We help [type] companies save [X]% on [specific thing]."'
            },
            'needs_work': {
                'message': 'Your pitch needs to be shorter and more outcome-focused.',
                'next_steps': 'Under 20 words. Formula: "We help [specific type] companies [specific outcome with number] on [specific area]." Avoid feature lists.'
            }
        },
        
        'discovery_feedback': {
            'excellent': {
                'message': 'Great discovery question! Open-ended, relevant to your pitch, and shows genuine curiosity.',
                'next_steps': 'This shows you\'re consultative, not just pitching. Keep asking questions that relate to your value proposition.'
            },
            'good': {
                'message': 'Good discovery approach. Your question was open-ended and relevant.',
                'next_steps': 'Make sure every question ties directly back to the specific area you mentioned in your pitch.'
            },
            'needs_work': {
                'message': 'Use open-ended questions that relate to your pitch.',
                'next_steps': 'Try: "How are you currently handling [specific area from your pitch]?" or "What\'s your process for [relevant area]?"'
            }
        }
    }
    
    # ===== CONVERSATION QUALITY INDICATORS =====
    
    QUALITY_INDICATORS = {
        'excellent_conversation': {
            'prospect_engagement': ['asks questions', 'provides details', 'shows interest'],
            'user_performance': ['natural flow', 'good listening', 'relevant responses'],
            'overall_feel': 'Natural, consultative, professional'
        },
        'good_conversation': {
            'prospect_engagement': ['stays on call', 'responds appropriately'],
            'user_performance': ['follows structure', 'mostly natural'],
            'overall_feel': 'Professional, somewhat engaging'
        },
        'needs_improvement': {
            'prospect_engagement': ['short responses', 'trying to end call'],
            'user_performance': ['rigid script', 'not listening', 'pushy'],
            'overall_feel': 'Awkward, one-sided, unnatural'
        }
    }
    
    # ===== HANG-UP TRIGGERS (ENHANCED) =====
    
    HANGUP_TRIGGERS = {
        'immediate_hangup': {
            'no_empathy_opener': 0.6,       # 60% chance if opener shows no empathy
            'aggressive_response': 0.8,      # 80% chance if user argues aggressively
            'pushy_after_objection': 0.7     # 70% chance if pushy after clear objection
        },
        'gradual_hangup': {
            'poor_opener': 0.3,              # 30% chance if opener scores 0-1
            'repeated_objections': 0.5,       # 50% chance if user ignores objections
            'too_long_pitch': 0.4,           # 40% chance if pitch over 40 words
            'no_questions': 0.3               # 30% chance if no discovery questions
        },
        'silence_hangup': {
            'silence_15_seconds': 1.0        # 100% chance after 15 seconds silence
        }
    }
    
    # ===== DYNAMIC DIFFICULTY ADJUSTMENT =====
    
    DIFFICULTY_LEVELS = {
        'beginner_mode': {
            'prospect_patience': 'high',
            'objection_intensity': 'low',
            'hang_up_probability': 0.5,      # Reduce all hang-up chances by 50%
            'coaching_detail': 'high'
        },
        'standard_mode': {
            'prospect_patience': 'medium',
            'objection_intensity': 'medium',
            'hang_up_probability': 1.0,      # Normal hang-up chances
            'coaching_detail': 'medium'
        },
        'expert_mode': {
            'prospect_patience': 'low',
            'objection_intensity': 'high',
            'hang_up_probability': 1.5,      # Increase hang-up chances by 50%
            'coaching_detail': 'low'
        }
    }

# ===== IMPLEMENTATION NOTES =====
"""
CRITICAL IMPROVEMENTS IN THIS VERSION:

1. WEIGHTED SCORING SYSTEM:
   - Different criteria have different weights based on importance
   - Empathy gets highest weight in opener evaluation
   - Outcome-focus gets highest weight in pitch evaluation

2. ENHANCED PROSPECT BEHAVIOR:
   - More nuanced responses based on user performance
   - Gradual warming up based on good performance
   - Realistic conversation progression

3. BETTER CONVERSATION FLOW:
   - Natural stage transitions
   - Extended conversation phase for practice
   - Quality indicators for overall conversation assessment

4. COMPREHENSIVE COACHING:
   - Specific feedback for each performance level
   - Actionable next steps for improvement
   - Templates that address exact issues

5. LOGICAL HANG-UP SYSTEM:
   - Multiple trigger types (immediate, gradual, silence)
   - Realistic probability based on actual poor performance
   - Weighted by conversation quality

TO USE THIS CONFIG:
1. Replace the existing roleplay_1_1_config.py with this version
2. Restart the roleplay service
3. Test with various conversation styles to validate scoring
4. Monitor for logical conversation flow and appropriate AI responses

EXPECTED IMPROVEMENTS:
- More accurate scoring based on actual sales effectiveness
- More logical and natural AI responses
- Better coaching that helps users improve specific skills
- Reduced false hang-ups while maintaining realism
"""
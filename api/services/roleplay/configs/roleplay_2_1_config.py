# ===== services/roleplay/configs/roleplay_2_1_config.py =====

class Roleplay21Config:
    """
    Configuration for Roleplay 2.1 - Post-Pitch Practice Mode
    Based on the specification for advanced pitch, objections, qualification, and meeting ask
    """
    
    # Basic Info
    ROLEPLAY_ID = "2.1"
    NAME = "Post-Pitch Practice"
    DESCRIPTION = "Advanced practice: Pitch → Objections/Questions → Qualification → Meeting Ask"
    TYPE = "advanced_practice"
    
    # Stage Flow
    STAGE_FLOW = {
        'pitch_prompt': 'objections_questions',
        'objections_questions': 'qualification',
        'qualification': 'meeting_ask',
        'meeting_ask': 'wrap_up',
        'wrap_up': 'call_ended'
    }
    
    # ===== AI PITCH PROMPTS (10 variants) =====
    PITCH_PROMPTS = [
        "Alright, tell me what you do.",
        "Okay, I'm listening. What's this about?",
        "Go ahead, you have my attention.",
        "Fair enough. What exactly do you do?",
        "You mentioned you could help. How?",
        "I'm curious - what's your solution?",
        "Explain what you're offering.",
        "Tell me more about what you do.",
        "What's your pitch?",
        "How exactly do you help companies?"
    ]
    
    # ===== POST-PITCH OBJECTIONS (24 items) =====
    POST_PITCH_OBJECTIONS = [
        # Budget/Cost objections
        "That sounds expensive.",
        "We don't have budget for that right now.",
        "How much does this cost?",
        "We're cutting costs, not adding expenses.",
        "I'd need to see ROI numbers first.",
        "That's outside our budget range.",
        
        # Timing objections
        "This isn't a priority right now.",
        "We're too busy to implement anything new.",
        "Maybe next quarter.",
        "We just implemented a new system.",
        "Not the right time for us.",
        "Call me back in six months.",
        
        # Authority objections
        "I'm not the decision maker.",
        "I'd have to talk to my team first.",
        "That's not my department.",
        "You'd need to speak with my boss.",
        "I don't make those decisions.",
        "The CEO handles all vendor relationships.",
        
        # Need objections
        "We're doing fine without it.",
        "We already have something similar.",
        "That's not really a problem for us.",
        "We handle that internally.",
        "We're not looking for new vendors.",
        "We have other priorities right now.",
        
        # Trust/Skepticism objections
        "I've heard that before.",
        "How do I know this actually works?"
    ]
    
    # ===== EVALUATION CRITERIA =====
    
    EVALUATION_CRITERIA = {
        'mini_pitch': {
            'description': 'Short, outcome-focused pitch with natural delivery',
            'pass_requirements': 3,  # Must meet 3 of 4 criteria
            'criteria': [
                {
                    'name': 'appropriate_length',
                    'description': 'Short (1-2 sentences, 10-30 words)',
                    'weight': 1.0
                },
                {
                    'name': 'outcome_focused',
                    'description': 'Focuses on problem solved or outcome delivered',
                    'keywords': ['save', 'increase', 'reduce', 'improve', 'help', 'results', 'growth'],
                    'weight': 1.5
                },
                {
                    'name': 'natural_delivery',
                    'description': 'Sounds natural, not robotic or memorized',
                    'contractions_expected': True,
                    'avoid_jargon': ['synergies', 'leverage', 'optimize', 'streamline'],
                    'weight': 1.0
                },
                {
                    'name': 'soft_discovery',
                    'description': 'Ends with open, curious question',
                    'question_required': True,
                    'examples': ['How are you handling that now?', 'What\'s your current process?'],
                    'weight': 1.2
                }
            ],
            'fail_triggers': [
                'too_long_detailed',
                'feature_focused',
                'vague_unclear',
                'sounds_scripted'
            ]
        },
        
        'objection_handling': {
            'description': 'Calm, clear response to objections without defensiveness',
            'pass_requirements': 3,  # Must meet 3 of 4 criteria
            'criteria': [
                {
                    'name': 'calm_acknowledgment',
                    'description': 'Acknowledges objection calmly',
                    'positive_phrases': ['understand', 'fair enough', 'get that', 'makes sense'],
                    'weight': 1.5
                },
                {
                    'name': 'not_defensive',
                    'description': 'Doesn\'t panic or argue',
                    'negative_phrases': ['but you should', 'you need to understand', 'actually you do'],
                    'weight': 1.5
                },
                {
                    'name': 'clear_response',
                    'description': 'Gives clear, short answer or effective reframe',
                    'max_words': 40,
                    'weight': 1.0
                },
                {
                    'name': 'maintains_flow',
                    'description': 'Keeps conversation flowing naturally',
                    'weight': 1.0
                }
            ],
            'fail_triggers': [
                'gets_flustered',
                'defensive_aggressive',
                'avoids_dodges',
                'rambles_off_track'
            ]
        },
        
        'qualification': {
            'description': 'Secures company-fit admission (mandatory for pass)',
            'mandatory': True,
            'criteria': [
                {
                    'name': 'company_fit_secured',
                    'description': 'SDR gets prospect to admit solution might help',
                    'required_phrases': [
                        'might help', 'could work', 'sounds relevant', 'worth exploring',
                        'makes sense', 'could be useful', 'relevant to us', 'fits our needs'
                    ],
                    'weight': 3.0,
                    'mandatory': True
                },
                {
                    'name': 'decision_maker_confirmed',
                    'description': 'Confirms decision-making authority (coachable if missed)',
                    'phrases': ['decision maker', 'make decisions', 'i decide', 'my call'],
                    'weight': 1.0,
                    'mandatory': False,
                    'coaching_if_missed': True
                }
            ],
            'fail_triggers': [
                'no_qualification_attempt',
                'only_small_talk',
                'launches_full_discovery'
            ]
        },
        
        'meeting_ask': {
            'description': 'Clear meeting request with concrete time options',
            'pass_requirements': 'all',  # Must meet all criteria
            'criteria': [
                {
                    'name': 'clear_meeting_ask',
                    'description': 'Explicitly asks for a meeting',
                    'keywords': ['meeting', 'call', 'chat', 'discuss', 'talk', 'demo'],
                    'weight': 2.0,
                    'mandatory': True
                },
                {
                    'name': 'concrete_time_slots',
                    'description': 'Offers at least 1 specific day/time option',
                    'time_indicators': [
                        'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                        'morning', 'afternoon', 'am', 'pm', 'o\'clock'
                    ],
                    'minimum_slots': 1,
                    'optimal_slots': 2,
                    'weight': 2.0,
                    'mandatory': True
                },
                {
                    'name': 'confident_tone',
                    'description': 'Sounds confident and human',
                    'weight': 1.0
                },
                {
                    'name': 'handles_pushback',
                    'description': 'Re-asks after pushback',
                    'weight': 1.0
                }
            ],
            'coaching_notes': {
                'single_slot': 'Good meeting ask! Next time offer 2-3 options for better response rates.',
                'multiple_slots': 'Perfect! Multiple time options show professionalism.'
            },
            'fail_triggers': [
                'never_asks',
                'too_vague',
                'no_concrete_time',
                'doesnt_handle_objections'
            ]
        }
    }
    
    # ===== CONVERSATION LIMITS =====
    CONVERSATION_LIMITS = {
        'max_total_turns': 15,
        'min_turns_for_success': 6,
        'max_objections_questions': 6,  # 1-3 objections + 1-3 questions
        'qualification_attempts': 2,
        'meeting_ask_attempts': 2,
        'silence_threshold': {
            'impatience': 10,  # 10 seconds
            'hangup': 15       # 15 seconds
        }
    }
    
    # ===== SCORING SYSTEM =====
    SCORING_WEIGHTS = {
        'pitch_delivery': 0.25,
        'objection_handling': 0.25,
        'qualification': 0.30,     # Higher weight - mandatory
        'meeting_ask': 0.20,
        'conversation_flow': 0.05,
        'stage_completion_bonus': 0.10
    }
    
    SUCCESS_CRITERIA = {
        'minimum_score': 70,
        'excellent_threshold': 85,
        'required_stages': ['pitch_prompt', 'qualification', 'meeting_ask'],
        'mandatory_elements': [
            'company_fit_qualified',
            'meeting_asked',
            'concrete_time_offered'
        ]
    }
    
    # ===== AI BEHAVIOR PATTERNS =====
    PROSPECT_BEHAVIOR = {
        'personality': 'Busy executive, moderately skeptical but professional',
        'objection_style': 'Direct but not hostile',
        'question_style': 'Practical and business-focused',
        'qualification_resistance': 'Medium - needs convincing but reasonable',
        'meeting_receptivity': 'High if properly qualified',
        
        'response_patterns': {
            'excellent_pitch': [
                "That's interesting. Tell me more.",
                "Okay, I'm following. How does that work?",
                "That could be relevant. Continue.",
                "I see the potential. What's involved?"
            ],
            'poor_pitch': [
                "That's pretty vague.",
                "I don't understand what you're saying.",
                "Sounds like every other vendor.",
                "That doesn't tell me anything."
            ],
            'qualification_success': [
                "Yes, that could definitely help us.",
                "That sounds like something we need.",
                "I can see how that would be useful.",
                "That addresses a real challenge we have."
            ],
            'meeting_agreement': [
                "Let me check my calendar. Tuesday works.",
                "Thursday afternoon is better for me.",
                "Either time works. Let's go with the earlier one.",
                "Sounds good. Send me the invite."
            ]
        }
    }
    
    # ===== COACHING TEMPLATES =====
    COACHING_TEMPLATES = {
        'pitch_coaching': {
            'excellent': 'Perfect pitch! Concise, outcome-focused, and ended with a great question.',
            'good': 'Good pitch structure. Keep it brief and focus on specific outcomes.',
            'needs_work': 'Work on being more concise and outcome-focused. Avoid features, focus on results.'
        },
        
        'objection_coaching': {
            'excellent': 'Excellent objection handling! You stayed calm and gave a clear response.',
            'good': 'Good approach to objections. Remember to acknowledge before responding.',
            'needs_work': 'Stay calm with objections. Acknowledge their concern, then give a brief, clear response.'
        },
        
        'qualification_coaching': {
            'excellent': 'Perfect! You secured clear company-fit confirmation.',
            'good': 'Good qualification. Make sure they explicitly say it could help them.',
            'needs_work': 'You must qualify company fit. Ask directly: "Does this sound like something that could help your team?"'
        },
        
        'meeting_coaching': {
            'excellent': 'Outstanding meeting ask! Clear request with specific time options.',
            'good': 'Good meeting ask. Offering 2-3 time slots gets better response rates.',
            'needs_work': 'Always ask clearly for a meeting and offer specific day/time options.'
        }
    }
    
    # ===== PRONUNCIATION COACHING =====
    PRONUNCIATION_TARGETS = {
        # Common mispronunciations for Spanish speakers
        'schedule': 'sked-jool',
        'focus': 'foh-kus', 
        'process': 'prah-ses',
        'productivity': 'pro-duk-tiv-ih-tee',
        'efficiency': 'ih-fish-uhn-see',
        'opportunity': 'ah-per-toon-ih-tee',
        'valuable': 'val-yoo-uh-buhl',
        'implementation': 'im-pluh-muhn-tay-shuhn'
    }
    
    # ===== SILENCE HANDLING =====
    SILENCE_RESPONSES = {
        'impatience': [
            "Hello? Are you still there?",
            "Can you hear me?", 
            "Just checking you're still on the line...",
            "Are we still connected?"
        ],
        'hangup_reasons': [
            "15 seconds of silence - prospect hung up",
            "Lost connection due to silence",
            "Prospect became unresponsive"
        ]
    }
    
    # ===== SUCCESS MESSAGES =====
    SUCCESS_MESSAGES = {
        'call_completion': [
            "Perfect! I'll send you that calendar invite. Talk soon!",
            "Great, I'll get that meeting set up. Thanks for your time!",
            "Excellent! You'll receive the calendar invite shortly. Have a great day!",
            "Sounds good! I'll send the details over. Looking forward to it!"
        ],
        'coaching_completion': "Excellent advanced practice! You successfully navigated a complete post-pitch conversation."
    }
    
    # ===== FAILURE MESSAGES =====
    FAILURE_MESSAGES = {
        'abrupt_hangup': [
            "I don't think this is going to work. Thanks anyway.",
            "This isn't what I'm looking for. Goodbye.",
            "I'm not interested. Please don't call again.",
            "This is a waste of time. I'm hanging up.",
            "No thanks. *click*"
        ]
    }
    
    # ===== IMPLEMENTATION NOTES =====
    """
    ROLEPLAY 2.1 KEY FEATURES:
    
    1. POST-PITCH FOCUS:
       - Starts with AI pitch prompt (not phone pickup)
       - User must deliver mini-pitch + soft discovery
       - More advanced than basic opener practice
    
    2. DUAL OBJECTION/QUESTION HANDLING:
       - AI randomly injects 1-3 objections AND 1-3 questions
       - Can happen in any order, any time during call
       - Tests adaptability and conversation management
    
    3. MANDATORY QUALIFICATION:
       - Must secure company-fit admission
       - Decision-maker check is coachable but not mandatory
       - Critical for call success
    
    4. ADVANCED MEETING ASK:
       - Must offer concrete day/time options
       - Coach for 2+ slots (better response rates)
       - Handle pushback professionally
    
    5. COACHING SOPHISTICATION:
       - CEFR A2 level for coaching (simple English)
       - CEFR C2 level for prospect (advanced)
       - Up to 6 coaching lines, ranked by severity
       - Pronunciation coaching for ASR < 0.70
    
    6. PASS/FAIL CONDITIONS:
       - Pass: All mandatory stages + company-fit + meeting ask
       - Fail: Any critical mistake → immediate AI hangup
       - More demanding than Roleplay 1.x series
    
    PROGRESSION:
    - Unlocked by completing Roleplay 1.2 (Marathon Mode)
    - Prepares for Roleplay 2.2 (Advanced Marathon)
    - Gateway to Module 2 advanced content
    """
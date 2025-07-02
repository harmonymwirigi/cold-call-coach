# ===== services/roleplay/configs/roleplay_4_config.py =====

class Roleplay4Config:
    """
    Configuration for Roleplay 4 - Full Cold Call Simulation
    Complete end-to-end cold call practice with realistic scenarios
    """
    
    # Basic Info
    ROLEPLAY_ID = "4"
    NAME = "Full Cold Call Simulation"
    DESCRIPTION = "Complete end-to-end cold call from phone pickup to close"
    TYPE = "simulation"
    
    # Simulation Settings
    EXTENDED_CONVERSATION = True
    REALISTIC_SCENARIOS = True
    PERSONALITY_DRIVEN = True
    
    # ===== COMPREHENSIVE STAGE FLOW =====
    
    STAGE_FLOW = {
        'phone_pickup': 'opener_evaluation',
        'opener_evaluation': 'objection_handling', 
        'objection_handling': 'discovery',
        'discovery': 'value_proposition',
        'value_proposition': 'qualification',
        'qualification': 'next_steps',
        'next_steps': 'call_ended'
    }
    
    # ===== PROSPECT PERSONALITIES =====
    
    PROSPECT_PERSONALITIES = {
        'analytical': {
            'traits': ['data-driven', 'skeptical', 'thorough', 'logical'],
            'communication_style': 'formal',
            'decision_speed': 'slow',
            'objection_style': 'detailed_questions',
            'trust_building': 'proof_required',
            'preferred_pace': 'methodical',
            'information_needs': 'high',
            'risk_tolerance': 'low',
            'typical_responses': {
                'interested': [
                    "I need to see the data on that.",
                    "What are your success metrics?",
                    "Can you send me case studies?",
                    "I'd like to review the documentation."
                ],
                'skeptical': [
                    "How do I know this actually works?",
                    "What evidence do you have?",
                    "I've heard similar claims before.",
                    "I need proof of ROI."
                ],
                'objections': [
                    "I need more time to analyze this.",
                    "The data doesn't convince me yet.",
                    "I have concerns about the implementation.",
                    "This needs thorough evaluation."
                ]
            }
        },
        
        'driver': {
            'traits': ['results-focused', 'impatient', 'direct', 'decisive'],
            'communication_style': 'concise',
            'decision_speed': 'fast',
            'objection_style': 'blunt_objections',
            'trust_building': 'credibility_focused',
            'preferred_pace': 'fast',
            'information_needs': 'low',
            'risk_tolerance': 'high',
            'typical_responses': {
                'interested': [
                    "Get to the point. What's the bottom line?",
                    "How much and how fast?",
                    "What's the ROI?",
                    "Can we start next week?"
                ],
                'skeptical': [
                    "Sounds like marketing fluff.",
                    "I don't have time for this.",
                    "What makes you different?",
                    "Prove it works."
                ],
                'objections': [
                    "Too expensive.",
                    "Takes too long.",
                    "We don't need it.",
                    "Not a priority."
                ]
            }
        },
        
        'expressive': {
            'traits': ['relationship-oriented', 'enthusiastic', 'collaborative', 'optimistic'],
            'communication_style': 'friendly',
            'decision_speed': 'medium',
            'objection_style': 'concerns_sharing',
            'trust_building': 'rapport_based',
            'preferred_pace': 'conversational',
            'information_needs': 'medium',
            'risk_tolerance': 'medium',
            'typical_responses': {
                'interested': [
                    "That sounds really exciting!",
                    "I love innovative solutions!",
                    "This could be perfect for our team!",
                    "How does this help us collaborate better?"
                ],
                'skeptical': [
                    "I'm not sure our team would adopt this.",
                    "We've tried similar things before.",
                    "Change is always challenging for us.",
                    "I'd need to get everyone on board."
                ],
                'objections': [
                    "The team might resist change.",
                    "We're very collaborative in our decisions.",
                    "I'd need to see how this fits our culture.",
                    "What if people don't like it?"
                ]
            }
        },
        
        'amiable': {
            'traits': ['supportive', 'cautious', 'consensus-seeking', 'patient'],
            'communication_style': 'polite',
            'decision_speed': 'slow',
            'objection_style': 'gentle_pushback',
            'trust_building': 'relationship_first',
            'preferred_pace': 'relaxed',
            'information_needs': 'medium',
            'risk_tolerance': 'low',
            'typical_responses': {
                'interested': [
                    "That sounds like it could be helpful.",
                    "I'd like to learn more about this.",
                    "This seems like it could work for us.",
                    "I appreciate you sharing this with me."
                ],
                'skeptical': [
                    "I'm not sure we're ready for this.",
                    "We usually move pretty slowly on decisions.",
                    "I'd need to think about this more.",
                    "Change makes me a bit nervous."
                ],
                'objections': [
                    "I'd need to discuss this with the team.",
                    "We prefer to take our time with decisions.",
                    "I'm not the only one involved in this.",
                    "Can you give us some time to consider?"
                ]
            }
        }
    }
    
    # ===== COMPANY SCENARIOS =====
    
    COMPANY_SCENARIOS = {
        'technology': {
            'common_challenges': [
                'scaling_engineering_teams',
                'technical_debt_management', 
                'cloud_migration',
                'security_compliance',
                'development_velocity'
            ],
            'decision_makers': ['CTO', 'VP Engineering', 'Head of DevOps'],
            'budget_cycles': 'quarterly',
            'urgency_drivers': ['security_threats', 'scalability_issues', 'competitive_pressure']
        },
        
        'healthcare': {
            'common_challenges': [
                'patient_data_management',
                'regulatory_compliance',
                'cost_reduction',
                'patient_experience',
                'operational_efficiency'
            ],
            'decision_makers': ['CMO', 'CFO', 'Head of Operations'],
            'budget_cycles': 'annual',
            'urgency_drivers': ['regulatory_changes', 'patient_safety', 'cost_pressures']
        },
        
        'finance': {
            'common_challenges': [
                'risk_management',
                'regulatory_reporting',
                'digital_transformation',
                'customer_experience',
                'operational_efficiency'
            ],
            'decision_makers': ['CFO', 'CRO', 'Head of Operations'],
            'budget_cycles': 'annual',
            'urgency_drivers': ['regulatory_deadlines', 'competitive_threats', 'risk_exposure']
        },
        
        'manufacturing': {
            'common_challenges': [
                'supply_chain_optimization',
                'quality_control',
                'predictive_maintenance',
                'cost_reduction',
                'sustainability'
            ],
            'decision_makers': ['COO', 'Plant Manager', 'Head of Operations'],
            'budget_cycles': 'annual',
            'urgency_drivers': ['equipment_failures', 'quality_issues', 'cost_pressures']
        },
        
        'retail': {
            'common_challenges': [
                'customer_experience',
                'inventory_management',
                'omnichannel_strategy',
                'data_analytics',
                'cost_optimization'
            ],
            'decision_makers': ['CMO', 'Head of Digital', 'VP Operations'],
            'budget_cycles': 'quarterly',
            'urgency_drivers': ['seasonal_demands', 'competitive_pressure', 'customer_expectations']
        }
    }
    
    # ===== EVALUATION CRITERIA =====
    
    EVALUATION_CRITERIA = {
        'opener': {
            'description': 'Professional opening with empathy and clear purpose',
            'weight': 1.0,
            'criteria': [
                {
                    'name': 'clear_introduction',
                    'description': 'States name, company, and reason for calling',
                    'weight': 1.2
                },
                {
                    'name': 'shows_empathy',
                    'description': 'Acknowledges interrupting their day',
                    'weight': 1.5
                },
                {
                    'name': 'establishes_credibility',
                    'description': 'Mentions relevant experience or social proof',
                    'weight': 1.3
                },
                {
                    'name': 'asks_permission',
                    'description': 'Seeks permission to continue',
                    'weight': 1.2
                }
            ]
        },
        
        'discovery': {
            'description': 'Effective questioning to understand needs and challenges',
            'weight': 1.5,
            'criteria': [
                {
                    'name': 'open_ended_questions',
                    'description': 'Uses how, what, when, why questions',
                    'weight': 1.4
                },
                {
                    'name': 'listens_actively',
                    'description': 'Acknowledges and builds on responses',
                    'weight': 1.6
                },
                {
                    'name': 'uncovers_pain_points',
                    'description': 'Identifies specific challenges or problems',
                    'weight': 1.8
                },
                {
                    'name': 'quantifies_impact',
                    'description': 'Explores business impact of challenges',
                    'weight': 1.5
                }
            ]
        },
        
        'value_proposition': {
            'description': 'Compelling value statement tied to discovered needs',
            'weight': 1.4,
            'criteria': [
                {
                    'name': 'tailored_to_needs',
                    'description': 'Directly addresses identified challenges',
                    'weight': 1.8
                },
                {
                    'name': 'specific_benefits',
                    'description': 'Mentions concrete outcomes and results',
                    'weight': 1.6
                },
                {
                    'name': 'differentiated',
                    'description': 'Explains unique value or approach',
                    'weight': 1.3
                },
                {
                    'name': 'credible',
                    'description': 'Supported by proof points or examples',
                    'weight': 1.4
                }
            ]
        },
        
        'qualification': {
            'description': 'Thorough qualification of fit, authority, need, timeline',
            'weight': 1.3,
            'criteria': [
                {
                    'name': 'confirms_fit',
                    'description': 'Validates solution relevance to their situation',
                    'weight': 1.7
                },
                {
                    'name': 'identifies_decision_process',
                    'description': 'Understands who is involved in decisions',
                    'weight': 1.5
                },
                {
                    'name': 'explores_timeline',
                    'description': 'Discovers urgency and implementation timeline',
                    'weight': 1.4
                },
                {
                    'name': 'discusses_investment',
                    'description': 'Addresses budget or investment considerations',
                    'weight': 1.3
                }
            ]
        },
        
        'relationship_building': {
            'description': 'Building rapport and trust throughout conversation',
            'weight': 1.2,
            'criteria': [
                {
                    'name': 'adapts_to_style',
                    'description': 'Matches prospect communication preferences',
                    'weight': 1.5
                },
                {
                    'name': 'shows_genuine_interest',
                    'description': 'Demonstrates care for their success',
                    'weight': 1.6
                },
                {
                    'name': 'builds_credibility',
                    'description': 'Establishes expertise and trustworthiness',
                    'weight': 1.4
                },
                {
                    'name': 'maintains_professionalism',
                    'description': 'Appropriate tone and demeanor throughout',
                    'weight': 1.2
                }
            ]
        }
    }
    
    # ===== CONVERSATION LIMITS =====
    
    CONVERSATION_LIMITS = {
        'max_total_turns': 20,           # Extended for full simulation
        'min_turns_for_success': 8,     # Minimum meaningful conversation
        'optimal_turn_range': (12, 18), # Sweet spot for engagement
        'max_stage_turns': {
            'opener_evaluation': 3,
            'objection_handling': 4,
            'discovery': 6,              # More time for discovery
            'value_proposition': 4,
            'qualification': 5,          # Thorough qualification
            'next_steps': 3
        }
    }
    
    # ===== SCORING SYSTEM =====
    
    SCORING_WEIGHTS = {
        'relationship_building': 0.25,   # High weight on relationship
        'discovery_effectiveness': 0.25, # High weight on discovery
        'value_communication': 0.20,    # Strong value proposition
        'qualification_thoroughness': 0.15, # Proper qualification
        'conversation_flow': 0.10,      # Natural progression
        'closing_effectiveness': 0.05   # Appropriate next steps
    }
    
    SUCCESS_CRITERIA = {
        'minimum_score': 70,            # Higher bar for simulation
        'excellent_threshold': 85,
        'required_stages': ['opener_evaluation', 'discovery', 'value_proposition', 'qualification'],
        'mandatory_elements': [
            'pain_points_identified',
            'value_proposition_given',
            'qualification_attempted',
            'next_steps_discussed'
        ],
        'relationship_thresholds': {
            'trust_level': 5,           # Minimum trust level
            'interest_level': 4,        # Minimum interest level
            'conversation_depth': 6     # Minimum conversation depth
        }
    }
    
    # ===== HANG-UP TRIGGERS (REALISTIC) =====
    
    HANGUP_TRIGGERS = {
        'personality_based': {
            'driver': {
                'impatience_threshold': 0.4,
                'value_threshold': 0.6,
                'time_pressure': 'high'
            },
            'analytical': {
                'logic_threshold': 0.3,
                'proof_threshold': 0.5,
                'time_pressure': 'low'
            },
            'expressive': {
                'enthusiasm_threshold': 0.2,
                'relationship_threshold': 0.4,
                'time_pressure': 'medium'
            },
            'amiable': {
                'pressure_threshold': 0.1,
                'comfort_threshold': 0.3,
                'time_pressure': 'low'
            }
        },
        
        'universal_triggers': {
            'poor_opener': 0.3,
            'pushy_behavior': 0.7,
            'irrelevant_pitch': 0.5,
            'no_value_demonstrated': 0.4
        }
    }
    
    # ===== COACHING TEMPLATES =====
    
    COACHING_TEMPLATES = {
        'relationship_building': {
            'excellent': 'Outstanding relationship building! You adapted perfectly to their communication style.',
            'good': 'Good rapport building. Continue focusing on their preferred pace and style.',
            'needs_work': 'Work on reading their personality and adapting your approach accordingly.'
        },
        
        'discovery': {
            'excellent': 'Excellent discovery! You uncovered key challenges and quantified their impact.',
            'good': 'Good questioning technique. Try to dig deeper into business impact.',
            'needs_work': 'Ask more open-ended questions to understand their specific challenges.'
        },
        
        'value_proposition': {
            'excellent': 'Perfect value proposition! Directly addressed their specific needs.',
            'good': 'Good value communication. Make it even more specific to their situation.',
            'needs_work': 'Tailor your value proposition more closely to their discovered needs.'
        },
        
        'qualification': {
            'excellent': 'Thorough qualification! You understand their decision process and timeline.',
            'good': 'Good qualification questions. Explore decision-making process more.',
            'needs_work': 'Ask more about who\'s involved in decisions and their timeline.'
        }
    }
    
    # ===== SIMULATION SCENARIOS =====
    
    SIMULATION_SCENARIOS = {
        'standard': {
            'complexity': 'medium',
            'objections': 2,
            'decision_makers': 1,
            'timeline': 'normal'
        },
        'challenging': {
            'complexity': 'high',
            'objections': 3,
            'decision_makers': 2,
            'timeline': 'urgent'
        },
        'expert': {
            'complexity': 'very_high',
            'objections': 4,
            'decision_makers': 3,
            'timeline': 'complex'
        }
    }
    
    # ===== SUCCESS MESSAGES =====
    
    SUCCESS_MESSAGES = {
        'call_success': [
            "This sounds very promising! Let's set up a follow-up call to discuss this further.",
            "I'm definitely interested. Can you send me more information and we'll schedule a demo?",
            "Great conversation! I'd like to involve my team. When can we meet?",
            "This could be exactly what we need. What are the next steps?"
        ],
        
        'high_performance': [
            "Excellent simulation! You conducted a professional, consultative conversation.",
            "Outstanding work! You built strong rapport and identified clear next steps.",
            "Perfect execution! You demonstrated all the key skills of effective cold calling."
        ]
    }
    
    # ===== IMPLEMENTATION NOTES =====
    """
    ROLEPLAY 4 KEY FEATURES:
    
    1. COMPLETE SIMULATION:
       - Full conversation flow from pickup to close
       - Realistic prospect personalities and company scenarios
       - Extended conversations (12-20 turns)
       - Comprehensive skill assessment
    
    2. PERSONALITY-DRIVEN:
       - Four distinct prospect personalities (Driver, Analytical, Expressive, Amiable)
       - Personality affects responses, objections, and hang-up probability
       - Requires adaptation to communication style
    
    3. SCENARIO-BASED:
       - Industry-specific challenges and contexts
       - Realistic company sizes and decision processes
       - Contextual objections and interests
    
    4. RELATIONSHIP FOCUS:
       - Trust and interest levels tracked throughout
       - Relationship building weighted heavily in scoring
       - Long-term success mindset vs. quick close
    
    5. COMPREHENSIVE EVALUATION:
       - All major cold calling skills assessed
       - Weighted scoring based on conversation quality
       - Detailed coaching across multiple dimensions
    
    UNLOCK REQUIREMENTS:
    - Complete Post-Pitch Practice (Roleplay 2.1) with 70+ score
    - Demonstrates readiness for complete conversations
    
    SUCCESS METRICS:
    - 70+ overall score
    - Completion of all required stages
    - Appropriate relationship building
    - Clear next steps defined
    
    COACHING FOCUS:
    - Personality adaptation
    - Discovery effectiveness  
    - Value proposition alignment
    - Professional relationship building
    """
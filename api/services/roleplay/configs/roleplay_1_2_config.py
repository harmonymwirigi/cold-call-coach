# services/roleplay/configs/roleplay_1_2_config.py
class Roleplay12Config:
    """Configuration for Roleplay 1.2 - Marathon Mode"""
    
    ROLEPLAY_ID = "1.2"
    NAME = "Marathon Mode"
    DESCRIPTION = "10 calls, need 6 to pass"
    
    # Marathon specific settings
    TOTAL_CALLS = 10
    CALLS_TO_PASS = 6
    RANDOM_HANGUP_CHANCE = 0.25  # 20-30% as specified
    
    # Stage flow (simpler than 1.1)
    STAGE_FLOW = {
        'phone_pickup': 'opener_evaluation',
        'opener_evaluation': 'early_objection',
        'early_objection': 'objection_handling',
        'objection_handling': 'mini_pitch',
        'mini_pitch': 'soft_discovery',
        'soft_discovery': 'call_ended'
    }
    
    # Silence thresholds (same as 1.1)
    IMPATIENCE_THRESHOLD = 10000
    HANGUP_THRESHOLD = 15000
    
    # Pass thresholds (same rubrics as 1.1)
    PASS_THRESHOLDS = {
        'opener': 3,
        'objection_handling': 3,
        'mini_pitch': 3,
        'soft_discovery': 2
    }
    
    # Objection list (29 items as specified)
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
    
    # Impatience phrases
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
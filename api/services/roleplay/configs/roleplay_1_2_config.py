# services/roleplay/configs/roleplay_1_2_config.py
class Roleplay12Config:
    """Configuration for Roleplay 1.2 - Marathon Mode"""
    
    ROLEPLAY_ID = "1.2"
    NAME = "Marathon Mode"
    DESCRIPTION = "10 calls, need 6 to pass"
    
    # Marathon specific settings
    TOTAL_CALLS = 10
    CALLS_TO_PASS = 6
    RANDOM_HANGUP_CHANCE = 0.25  # 20-30% range, we'll use 25%
    
    # Stage flow is simpler, as each call ends after the mini-pitch
    STAGE_FLOW = {
        'phone_pickup': 'opener_evaluation',
        'opener_evaluation': 'early_objection',
        'early_objection': 'objection_handling',
        'objection_handling': 'mini_pitch',
        'mini_pitch': 'call_ended' # A successful call ends here
    }
    
    # Silence thresholds from the spec
    IMPATIENCE_THRESHOLD = 10000 # 10 seconds
    HANGUP_THRESHOLD = 15000     # 15 seconds
    
    # Pass thresholds for each rubric (3 of 4 for all stages)
    PASS_THRESHOLDS = {
        'opener': 3,
        'objection_handling': 3,
        'mini_pitch': 3
    }
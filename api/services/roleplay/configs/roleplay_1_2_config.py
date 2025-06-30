# ===== services/roleplay/configs/roleplay_1_2_config.py =====

class Roleplay12Config:
    """
    Configuration for Roleplay 1.2 - Marathon Mode.
    Based on the provided specification document.
    """
    
    ROLEPLAY_ID = "1.2"
    NAME = "Marathon Mode"
    DESCRIPTION = "10 calls, extended repetition. Pass 6 out of 10 to complete."
    
    # Marathon specific settings
    TOTAL_CALLS = 10
    CALLS_TO_PASS = 6
    RANDOM_HANGUP_CHANCE = 0.25  # 20-30% range, we'll use a fixed 25% for simplicity
    
    # Stage flow for a single call within the marathon
    STAGE_FLOW = {
        'phone_pickup': 'opener_evaluation',
        'opener_evaluation': 'early_objection',
        'early_objection': 'objection_handling',
        'objection_handling': 'mini_pitch',
        'mini_pitch': 'call_ended' # A successful call ends after the mini-pitch
    }
    
    # Silence thresholds from the spec
    IMPATIENCE_THRESHOLD_S = 10
    HANGUP_THRESHOLD_S = 15
    
    # Pass thresholds for each rubric (3 of 4 for opener and objection, etc.)
    # This will be used by the evaluation logic.
    PASS_THRESHOLDS = {
        'opener': 3,
        'objection_handling': 3,
        'mini_pitch': 3,
        'uncovering_pain': 2 # Though not used in this flow, good to have
    }
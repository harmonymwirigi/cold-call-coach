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
    
    # --- STAGE FLOW UPDATED FOR NATURAL CONVERSATION ---
    # This now mirrors the practice mode flow, allowing for a real conversation.
    STAGE_FLOW = {
        'phone_pickup': 'opener_evaluation',
        'opener_evaluation': 'early_objection',
        'early_objection': 'objection_handling',
        'objection_handling': 'mini_pitch',
        'mini_pitch': 'extended_conversation', # Allows for a short natural conversation
        'extended_conversation': 'call_ended' # Ends the individual call
    }
    
    # --- NEW: CONVERSATION LIMITS FOR EACH CALL ---
    CONVERSATION_LIMITS = {
        'max_total_turns': 8,  # Each marathon call is shorter than practice
        'min_turns_for_success': 4, # A call needs at least 4 user turns to be successful
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
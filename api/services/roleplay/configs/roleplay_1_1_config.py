# services/roleplay/configs/roleplay_1_1_config.py
class Roleplay11Config:
    """Configuration for Roleplay 1.1 - Practice Mode"""
    
    ROLEPLAY_ID = "1.1"
    NAME = "Practice Mode"
    DESCRIPTION = "Single call with detailed CEFR A2 coaching"
    
    # Stage flow
    STAGE_FLOW = {
        'phone_pickup': 'opener_evaluation',
        'opener_evaluation': 'early_objection',
        'early_objection': 'objection_handling', 
        'objection_handling': 'mini_pitch',
        'mini_pitch': 'soft_discovery',
        'soft_discovery': 'extended_conversation',
        'extended_conversation': 'call_ended'
    }
    
    # Limits
    MAX_TURNS_PER_STAGE = 5
    MAX_TOTAL_TURNS = 25
    
    # Silence thresholds
    IMPATIENCE_THRESHOLD = 10000  # 10 seconds
    HANGUP_THRESHOLD = 15000      # 15 seconds
    
    # Scoring thresholds
    PASS_THRESHOLDS = {
        'opener': 3,
        'objection_handling': 3,
        'mini_pitch': 3,
        'soft_discovery': 2
    }
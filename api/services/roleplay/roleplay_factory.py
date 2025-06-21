# ===== services/roleplay/roleplay_factory.py (SIMPLIFIED) =====

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class RoleplayFactory:
    """Simplified factory for creating roleplay instances"""
    
    @staticmethod
    def get_available_roleplays():
        """Get list of available roleplay IDs"""
        return ['1.1', '1.2', '1.3', '2.1', '2.2', '3', '4', '5']
    
    @staticmethod
    def create_roleplay(roleplay_id: str, openai_service=None):
        """Create appropriate roleplay instance - SIMPLIFIED"""
        try:
            logger.info(f"Creating SIMPLE roleplay instance for ID: {roleplay_id}")
            
            # Import the base roleplay class
            from services.roleplay.base_roleplay import BaseRoleplay
            
            # Create a simple roleplay instance for any ID
            roleplay = BaseRoleplay(openai_service)
            roleplay.roleplay_id = roleplay_id
            
            logger.info(f"✅ Created simple roleplay instance for {roleplay_id}")
            return roleplay
                
        except Exception as e:
            logger.error(f"❌ Error creating roleplay {roleplay_id}: {e}")
            # Last resort fallback
            from services.roleplay.base_roleplay import BaseRoleplay
            fallback = BaseRoleplay(openai_service)
            fallback.roleplay_id = roleplay_id
            return fallback
    
    @staticmethod
    def get_roleplay_info(roleplay_id: str) -> Dict[str, Any]:
        """Get roleplay configuration information"""
        roleplay_configs = {
            '1.1': {
                'id': '1.1',
                'name': 'Practice Mode',
                'description': 'Single call with detailed coaching',
                'icon': 'user-graduate',
                'difficulty': 'Beginner',
                'available': True
            },
            '1.2': {
                'id': '1.2',
                'name': 'Marathon Mode',
                'description': '10 calls, need 6 to pass',
                'icon': 'running',
                'difficulty': 'Intermediate',
                'available': True
            },
            '1.3': {
                'id': '1.3',
                'name': 'Legend Mode',
                'description': '6 perfect calls in a row',
                'icon': 'crown',
                'difficulty': 'Expert',
                'available': False
            },
            '2.1': {
                'id': '2.1',
                'name': 'Pitch Practice',
                'description': 'Advanced pitch training',
                'icon': 'bullhorn',
                'difficulty': 'Advanced',
                'available': False
            },
            '2.2': {
                'id': '2.2',
                'name': 'Pitch Marathon',
                'description': '10 advanced calls',
                'icon': 'running',
                'difficulty': 'Expert',
                'available': False
            },
            '3': {
                'id': '3',
                'name': 'Warm-up Challenge',
                'description': '25 rapid-fire questions',
                'icon': 'fire',
                'difficulty': 'All Levels',
                'available': True
            },
            '4': {
                'id': '4',
                'name': 'Full Cold Call',
                'description': 'Complete simulation',
                'icon': 'headset',
                'difficulty': 'Advanced',
                'available': True
            },
            '5': {
                'id': '5',
                'name': 'Power Hour',
                'description': '10 consecutive calls',
                'icon': 'bolt',
                'difficulty': 'Expert',
                'available': True
            }
        }
        
        if roleplay_id not in roleplay_configs:
            logger.warning(f"No config found for roleplay {roleplay_id}")
            return {
                'id': roleplay_id,
                'name': f'Roleplay {roleplay_id}',
                'description': 'Roleplay training',
                'icon': 'phone',
                'difficulty': 'Unknown',
                'available': True
            }
        
        return roleplay_configs[roleplay_id]
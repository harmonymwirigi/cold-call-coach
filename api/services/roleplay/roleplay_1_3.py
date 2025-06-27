# ===== services/roleplay/roleplay_1_3.py =====

from .base_roleplay import BaseRoleplay

class Roleplay13(BaseRoleplay):
    """
    Placeholder for Roleplay 1.3 - Legend Mode.
    The logic for this mode is very strict and will be implemented next.
    For now, it will behave like the base roleplay.
    """
    def __init__(self, openai_service=None):
        super().__init__(openai_service)
        self.roleplay_id = "1.3"

    def get_roleplay_info(self) -> dict:
        return {
            'id': self.roleplay_id,
            'name': "Legend Mode",
            'description': "6 perfect calls in a row - the ultimate challenge.",
            'type': 'legend'
        }
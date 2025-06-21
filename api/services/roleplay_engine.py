# ===== services/roleplay_engine.py (Updated Main Engine) =====

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class RoleplayEngine:
    """Main engine that delegates to specific roleplay implementations"""
    
    def __init__(self):
        try:
            from services.openai_service import OpenAIService
            self.openai_service = OpenAIService()
            logger.info(f"OpenAI service initialized: {self.openai_service.is_available()}")
        except Exception as e:
            logger.error(f"Failed to import OpenAI service: {e}")
            self.openai_service = None
        
        self.roleplay_instances = {}
        
        # Import factory here to avoid circular imports
        try:
            from services.roleplay.roleplay_factory import RoleplayFactory
            self.factory = RoleplayFactory
            logger.info("Roleplay factory initialized successfully")
        except Exception as e:
            logger.error(f"Failed to import roleplay factory: {e}")
            self.factory = None
    
    def is_openai_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.openai_service and self.openai_service.is_available()
    
    def get_available_roleplays(self) -> List[str]:
        """Get list of available roleplay types"""
        return ["1.1", "1.2", "1.3", "2.1", "2.2", "3", "4", "5"]
    
    def get_roleplay_instance(self, roleplay_id: str):
        """Get or create roleplay instance"""
        if not self.factory:
            logger.error("Roleplay factory not available")
            raise Exception("Roleplay system not properly initialized")
        
        if roleplay_id not in self.roleplay_instances:
            try:
                self.roleplay_instances[roleplay_id] = self.factory.create_roleplay(
                    roleplay_id, self.openai_service
                )
                logger.info(f"Created roleplay instance: {roleplay_id}")
            except Exception as e:
                logger.error(f"Failed to create roleplay instance {roleplay_id}: {e}")
                raise
        
        return self.roleplay_instances[roleplay_id]
    
    def get_roleplay_info(self, roleplay_id: str) -> Dict[str, Any]:
        """Get roleplay configuration info"""
        try:
            roleplay = self.get_roleplay_instance(roleplay_id)
            return roleplay.get_roleplay_info()
        except Exception as e:
            logger.error(f"Error getting roleplay info for {roleplay_id}: {e}")
            return {
                'id': roleplay_id,
                'name': f'Roleplay {roleplay_id}',
                'description': 'Roleplay training',
                'error': str(e)
            }
    
    def create_session(self, user_id: str, roleplay_id: str, mode: str, user_context: Dict) -> Dict[str, Any]:
        """Create session using appropriate roleplay implementation"""
        try:
            logger.info(f"Creating session: user={user_id}, roleplay={roleplay_id}, mode={mode}")
            roleplay = self.get_roleplay_instance(roleplay_id)
            result = roleplay.create_session(user_id, mode, user_context)
            
            if result.get('success'):
                logger.info(f"Session created successfully: {result.get('session_id')}")
            else:
                logger.error(f"Session creation failed: {result.get('error')}")
            
            return result
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process input using appropriate roleplay implementation"""
        try:
            roleplay_id = self._extract_roleplay_id_from_session(session_id)
            logger.info(f"Processing input for {roleplay_id}: '{user_input[:50]}...'")
            
            roleplay = self.get_roleplay_instance(roleplay_id)
            result = roleplay.process_user_input(session_id, user_input)
            
            return result
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            return {'success': False, 'error': str(e), 'call_continues': False}
    
    def end_session(self, session_id: str, forced_end: bool = False) -> Dict[str, Any]:
        """End session using appropriate roleplay implementation"""
        try:
            roleplay_id = self._extract_roleplay_id_from_session(session_id)
            logger.info(f"Ending session for {roleplay_id}: {session_id}")
            
            roleplay = self.get_roleplay_instance(roleplay_id)
            result = roleplay.end_session(session_id, forced_end)
            
            return result
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session status using appropriate roleplay implementation"""
        try:
            roleplay_id = self._extract_roleplay_id_from_session(session_id)
            roleplay = self.get_roleplay_instance(roleplay_id)
            return roleplay.get_session_status(session_id)
        except Exception as e:
            logger.error(f"Error getting session status: {e}")
            return None
    
    def cleanup_expired_sessions(self):
        """Clean up old sessions across all roleplay types"""
        try:
            for roleplay_instance in self.roleplay_instances.values():
                if hasattr(roleplay_instance, 'cleanup_expired_sessions'):
                    roleplay_instance.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        total_sessions = 0
        roleplay_statuses = {}
        
        for roleplay_id, instance in self.roleplay_instances.items():
            session_count = len(getattr(instance, 'active_sessions', {}))
            total_sessions += session_count
            roleplay_statuses[roleplay_id] = {
                'active_sessions': session_count,
                'instance_created': True
            }
        
        return {
            'active_sessions': total_sessions,
            'openai_available': self.is_openai_available(),
            'engine_status': 'running',
            'available_roleplays': self.get_available_roleplays(),
            'roleplay_instances': roleplay_statuses,
            'openai_status': self.openai_service.get_status() if self.openai_service else None
        }
    
    def _extract_roleplay_id_from_session(self, session_id: str) -> str:
        """Extract roleplay ID from session ID"""
        # Format: user_roleplayid_mode_timestamp
        parts = session_id.split('_')
        if len(parts) >= 2:
            return parts[1]  # roleplay ID
        return "1.1"  # default fallback
# ===== UPDATED API/SERVICES/SUPABASE_CLIENT.PY (FIXED) =====
# ===== UPDATED API/SERVICES/SUPABASE_CLIENT.PY (FIXED) =====
from supabase import create_client, Client
import os
from typing import Optional, Dict, Any, List, Union
import logging
import json

logger = logging.getLogger(__name__)

class SupabaseService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.url = os.getenv('REACT_APP_SUPABASE_URL')
            self.anon_key = os.getenv('REACT_APP_SUPABASE_ANON_KEY')
            self.service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if not self.url or not self.anon_key:
                raise ValueError("Supabase URL and anon key must be provided")
            
            self.client: Client = create_client(self.url, self.anon_key)
            
            if self.service_key:
                self.service_client: Client = create_client(self.url, self.service_key)
            else:
                logger.warning("Service role key not provided - using anon key for all operations")
                self.service_client = self.client
            
            self._initialized = True
    
    def get_client(self) -> Client:
        return self.client
    
    def get_service_client(self) -> Client:
        return self.service_client
    
    def authenticate_user(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            user = self.client.auth.get_user(token)
            return user.user if user else None
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return None
    def get_user_profile_by_service(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.service_client.table('user_profiles').select('*').eq('id', user_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting user profile for {user_id}: {e}")
            return None
            
    
    def get_user_profile(self, user_id: str, access_token: str = None) -> Optional[Dict[str, Any]]:
        """Get user profile by ID with enhanced error handling"""
        try:
            # If we have an access token, create an authenticated client
            if access_token:
                try:
                    # Create a new client instance with the user's token
                    auth_client = create_client(self.url, self.anon_key)
                    auth_client.auth.set_session(access_token, "")
                    response = auth_client.table('user_profiles').select('*').eq('id', user_id).execute()
                except Exception as auth_error:
                    logger.warning(f"Failed to use authenticated client: {auth_error}, falling back to service client")
                    # Fall back to service client if auth client fails
                    response = self.service_client.table('user_profiles').select('*').eq('id', user_id).execute()
            else:
                # Use service client for non-authenticated requests
                response = self.service_client.table('user_profiles').select('*').eq('id', user_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            else:
                logger.warning(f"No profile found for user_id: {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user profile for {user_id}: {e}")
            return None
    
    
    def create_user_profile(self, profile_data: Dict[str, Any]) -> bool:
        try:
            response = self.service_client.table('user_profiles').insert(profile_data).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            return False

    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        try:
            updates['updated_at'] = 'NOW()'
            response = self.client.table('user_profiles').update(updates).eq('id', user_id).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False
    
    def get_user_progress(self, user_id: str) -> list:
        """Get all user progress records from the correct stats table."""
        try:
            # FIX: This was pointing to the old 'user_progress' table.
            # It should query 'user_roleplay_stats' to get the summary data.
            response = self.client.table('user_roleplay_stats').select('*').eq('user_id', user_id).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting user progress from user_roleplay_stats: {e}")
            return []
    
    def update_user_progress(self, user_id: str, roleplay_id: int, updates: Dict[str, Any]) -> bool:
        """Update or create user progress for specific roleplay"""
        try:
            client_to_use = self.service_client
            
            # This function is likely legacy now, but we'll keep it pointed to the old table
            # in case it's used elsewhere. The primary flow uses the UserProgressService.
            response = client_to_use.table('user_progress').update(updates).eq('user_id', user_id).eq('roleplay_id', roleplay_id).execute()
            
            if not response.data:
                progress_data = {
                    'user_id': user_id,
                    'roleplay_id': roleplay_id,
                    **updates
                }
                response = client_to_use.table('user_progress').insert(progress_data).execute()
            
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error updating legacy user progress: {e}")
            return False
    
    def create_verification_code(self, email: str, code: str) -> bool:
        """Create verification code (legacy method)"""
        return self.create_verification_code_with_data(email, code, {})
    
    def create_verification_code_with_data(self, email: str, code: str, user_data: Dict[str, Any]) -> bool:
        try:
            data = {'email': email, 'code': code, 'user_data': json.dumps(user_data)}
            response = self.service_client.table('verification_codes').insert(data).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error creating verification code: {e}")
            return False

    def verify_code_and_get_data(self, email: str, code: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.service_client.table('verification_codes').select('*').eq('email', email).eq('code', code).eq('used', False).gt('expires_at', 'NOW()').execute()
            if not response.data: return None
            
            verification_record = response.data[0]
            self.service_client.table('verification_codes').update({'used': True}).eq('id', verification_record['id']).execute()
            return json.loads(verification_record.get('user_data', '{}'))
        except Exception as e:
            logger.error(f"Error verifying code: {e}")
            return None


    def verify_code_and_get_data(self, email: str, code: str) -> Optional[Dict[str, Any]]:
        """Verify email code and return associated user data"""
        try:
            # Check if code exists and is not expired (using service client to ensure access)
            response = self.service_client.table('verification_codes')\
                .select('*')\
                .eq('email', email)\
                .eq('code', code)\
                .eq('used', False)\
                .gt('expires_at', 'NOW()')\
                .execute()
            
            if response.data:
                verification_record = response.data[0]
                
                # Mark code as used
                self.service_client.table('verification_codes')\
                    .update({'used': True})\
                    .eq('id', verification_record['id'])\
                    .execute()
                
                # Extract user data
                user_data_json = verification_record.get('user_data', '{}')
                try:
                    user_data = json.loads(user_data_json) if user_data_json else {}
                    logger.info(f"Verification code verified for {email}")
                    return user_data
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse user_data JSON: {user_data_json}")
                    return {}
            
            logger.warning(f"Invalid or expired verification code for {email}")
            return None
            
        except Exception as e:
            logger.error(f"Error verifying code: {e}")
            return None
    
    def verify_code(self, email: str, code: str) -> bool:
        """Verify email code (legacy method)"""
        user_data = self.verify_code_and_get_data(email, code)
        return user_data is not None
    
    
        
    def upsert_data(self, table_name: str, data: Union[Dict, List[Dict]]) -> Optional[List[Dict]]:
        """Upsert data into a table using the service client."""
        try:
            response = self.service_client.table(table_name).upsert(data).execute()
            # FIX: Check if response.data is not empty before returning
            if response.data:
                logger.info(f"Upsert successful for table '{table_name}'")
                return response.data
            else:
                logger.error(f"Upsert to '{table_name}' failed. Response: {response}")
                return None
        except Exception as e:
            logger.error(f"Exception during upsert to '{table_name}': {e}", exc_info=True)
            return None

    def get_data_with_filter(self, table_name: str, filter_column: str, filter_value: Any, additional_filters: Dict = None, limit: int = None, order_by: str = None, ascending: bool = True) -> List[Dict[str, Any]]:
        """Get data from a table with filters using the service client."""
        try:
            query = self.service_client.table(table_name).select('*').eq(filter_column, filter_value)
            if additional_filters:
                for col, val in additional_filters.items():
                    query = query.eq(col, val)
            if order_by:
                query = query.order(order_by, desc=not ascending)
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting data from '{table_name}': {e}")
            return []

    def insert_data(self, table_name: str, data: Dict) -> Optional[Dict[str, Any]]:
        """Insert a single record into a table using the service client."""
        try:
            response = self.service_client.table(table_name).insert(data).execute()
            # FIX: Check if response.data is not empty before accessing the first element
            if response.data:
                logger.info(f"Insert successful for table '{table_name}'")
                return response.data[0]
            else:
                # Log the failure reason if available from Supabase/PostgREST
                logger.error(f"Insert failed for table '{table_name}'. Response: {response}")
                return None
        except Exception as e:
            logger.error(f"Exception during insert into '{table_name}': {e}", exc_info=True)
            return None

    def update_data_by_id(self, table_name: str, id_filter: Dict, updates: Dict) -> bool:
        """Update data in a table based on a filter using the service client."""
        try:
            query = self.service_client.table(table_name).update(updates)
            for col, val in id_filter.items():
                query = query.eq(col, val)
            response = query.execute()
            # FIX: Check if response.data exists and has content
            if response.data:
                logger.info(f"Update successful for table '{table_name}' with filter {id_filter}")
                return True
            else:
                logger.warning(f"Update for table '{table_name}' with filter {id_filter} affected 0 rows. Response: {response}")
                return False
        except Exception as e:
            logger.error(f"Exception during update in '{table_name}': {e}", exc_info=True)
            return False
    def get_user_sessions(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get user's voice sessions (LEGACY)"""
        try:
            response = self.service_client.table('voice_sessions')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []

    def get_session_count(self, user_id: str) -> int:
        """Get total session count for user (LEGACY)"""
        try:
            response = self.service_client.table('voice_sessions')\
                .select('id', count='exact')\
                .eq('user_id', user_id)\
                .execute()
            return response.count or 0
        except Exception as e:
            logger.error(f"Error getting session count: {e}")
            return 0

    def update_user_profile_by_service(self, user_id: str, updates: Dict[str, Any]) -> bool:
        from datetime import datetime, timezone
        updates['updated_at'] = datetime.now(timezone.utc).isoformat()
        try:
            response = self.service_client.table('user_profiles').update(updates).eq('id', user_id).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error updating user profile by service: {e}")
            return False
    def get_user_completions(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        try:
            response = self.service_client.table('roleplay_completions').select('*').eq('user_id', user_id).order('completed_at', desc=True).range(offset, offset + limit - 1).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting user completions: {e}")
            return []

    def get_completion_count(self, user_id: str) -> int:
        try:
            response = self.service_client.table('roleplay_completions').select('id', count='exact').eq('user_id', user_id).execute()
            return response.count or 0
        except Exception as e:
            logger.error(f"Error getting completion count: {e}")
            return 0
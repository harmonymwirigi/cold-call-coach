# ===== FIXED: services/supabase_client.py =====
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
            temp_client = create_client(self.url, self.anon_key)
            response = temp_client.auth.get_user(token)
            return response.user.dict() if response and response.user else None
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return None

    def get_user_profile_by_service(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.service_client.table('user_profiles').select('*').eq('id', user_id).execute()
            if response.data:
                logger.info(f"Profile found for user_id: {user_id}")
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

    def update_user_profile_by_service(self, user_id: str, updates: Dict[str, Any]) -> bool:
        try:
            from datetime import datetime, timezone
            updates['updated_at'] = datetime.now(timezone.utc).isoformat()
            response = self.service_client.table('user_profiles').update(updates).eq('id', user_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error updating user profile by service: {e}")
            return False

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
            if response.data:
                record = response.data[0]
                self.service_client.table('verification_codes').update({'used': True}).eq('id', record['id']).execute()
                return json.loads(record.get('user_data', '{}'))
            return None
        except Exception as e:
            logger.error(f"Error verifying code: {e}")
            return None

    # ===== NEW GENERIC DATA ACCESS METHODS =====

    def upsert_data(self, table_name: str, data: Union[Dict, List[Dict]]) -> Optional[List[Dict]]:
        """Upsert data into a table using the service client."""
        try:
            response = self.service_client.table(table_name).upsert(data).execute()
            if response.data:
                logger.info(f"Upsert successful for table '{table_name}'")
                return response.data
            else:
                logger.warning(f"Upsert to '{table_name}' returned no data.")
                return None
        except Exception as e:
            logger.error(f"Error upserting data to '{table_name}': {e}")
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
            if response.data:
                logger.info(f"Insert successful for table '{table_name}'")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error inserting data into '{table_name}': {e}")
            return None

    def update_data_by_id(self, table_name: str, id_filter: Dict, updates: Dict) -> bool:
        """Update data in a table based on a filter using the service client."""
        try:
            query = self.service_client.table(table_name).update(updates)
            for col, val in id_filter.items():
                query = query.eq(col, val)
            response = query.execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error updating data in '{table_name}': {e}")
            return False
"""
Supabase Configuration and Utilities
"""
import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SupabaseConfig:
    """Supabase configuration class"""
    
    def __init__(self):
        self.url: str = os.getenv("SUPABASE_URL", "")
        self.key: str = os.getenv("SUPABASE_ANON_KEY", "")
        self.service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
    
    def get_client(self, use_service_key: bool = False) -> Client:
        """Create and return Supabase client"""
        key = self.service_key if use_service_key and self.service_key else self.key
        return create_client(self.url, key)

# Global Supabase client instances
_config: Optional[SupabaseConfig] = None
_client: Optional[Client] = None
_service_client: Optional[Client] = None

def get_supabase_config() -> SupabaseConfig:
    """Get Supabase configuration singleton"""
    global _config
    if _config is None:
        _config = SupabaseConfig()
    return _config

def get_supabase_client() -> Client:
    """Get Supabase client for regular operations"""
    global _client
    if _client is None:
        config = get_supabase_config()
        _client = config.get_client()
    return _client

def get_supabase_service_client() -> Client:
    """Get Supabase client with service key for admin operations"""
    global _service_client
    if _service_client is None:
        config = get_supabase_config()
        _service_client = config.get_client(use_service_key=True)
    return _service_client

def test_connection() -> bool:
    """Test Supabase connection"""
    try:
        client = get_supabase_client()
        # Try to fetch from auth table or any accessible endpoint
        result = client.auth.get_session()
        print("✅ Supabase connection successful")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

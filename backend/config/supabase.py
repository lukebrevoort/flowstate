"""
Supabase Configuration and Utilities
"""
import os
import httpx
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simple HTTP client for Supabase API calls
class SimpleSupabaseClient:
    """Simplified Supabase client to avoid version conflicts"""
    
    def __init__(self, url: str, key: str, user_token: Optional[str] = None):
        self.url = url.rstrip('/')
        self.key = key
        self.user_token = user_token
        
        # Use user token for auth if provided, otherwise use service key
        auth_token = user_token if user_token else key
        
        self.headers = {
            'apikey': key,  # Always include API key
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
    
    def set_user_token(self, user_token: str):
        """Set user authentication token for RLS"""
        self.user_token = user_token
        self.headers['Authorization'] = f'Bearer {user_token}'
    
    async def query(self, table: str, method: str = 'GET', data: Optional[Dict] = None, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a query on Supabase table"""
        url = f"{self.url}/rest/v1/{table}"
        
        # Add filters as query parameters
        if filters:
            query_params = []
            for key, value in filters.items():
                query_params.append(f"{key}=eq.{value}")
            if query_params:
                url += "?" + "&".join(query_params)
        
        async with httpx.AsyncClient() as client:
            if method == 'GET':
                response = await client.get(url, headers=self.headers)
            elif method == 'POST':
                response = await client.post(url, headers=self.headers, json=data)
            elif method == 'PATCH':
                response = await client.patch(url, headers=self.headers, json=data)
            elif method == 'DELETE':
                response = await client.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code >= 400:
                raise Exception(f"Supabase API error {response.status_code}: {response.text}")
            
            return response.json() if response.text else {}
    
    async def auth_signup(self, email: str, password: str, user_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Sign up a new user"""
        url = f"{self.url}/auth/v1/signup"
        data = {
            'email': email,
            'password': password
        }
        if user_metadata:
            data['data'] = user_metadata
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=data)
            
            if response.status_code >= 400:
                raise Exception(f"Supabase auth error {response.status_code}: {response.text}")
            
            return response.json()
    
    async def auth_signin(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in a user"""
        url = f"{self.url}/auth/v1/token?grant_type=password"
        data = {
            'email': email,
            'password': password
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=data)
            
            if response.status_code >= 400:
                raise Exception(f"Supabase auth error {response.status_code}: {response.text}")
            
            return response.json()

class SupabaseConfig:
    """Supabase configuration class"""
    
    def __init__(self):
        self.url: str = os.getenv("SUPABASE_URL", "")
        self.key: str = os.getenv("SUPABASE_ANON_KEY", "")
        self.service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
    
    def get_client(self, use_service_key: bool = False) -> SimpleSupabaseClient:
        """Create and return Supabase client"""
        key = self.service_key if use_service_key and self.service_key else self.key
        return SimpleSupabaseClient(self.url, key)

# Global Supabase client instances
_config: Optional[SupabaseConfig] = None
_client: Optional[SimpleSupabaseClient] = None
_service_client: Optional[SimpleSupabaseClient] = None

def get_supabase_config() -> SupabaseConfig:
    """Get Supabase configuration singleton"""
    global _config
    if _config is None:
        _config = SupabaseConfig()
    return _config

def get_supabase_client() -> SimpleSupabaseClient:
    """Get Supabase client for regular operations"""
    global _client
    if _client is None:
        config = get_supabase_config()
        _client = config.get_client()
    return _client

def get_supabase_service_client() -> SimpleSupabaseClient:
    """Get Supabase client with service key for admin operations"""
    global _service_client
    if _service_client is None:
        config = get_supabase_config()
        if not config.service_key:
            raise ValueError("SUPABASE_SERVICE_KEY must be set for service operations")
        _service_client = SimpleSupabaseClient(config.url, config.service_key)
    return _service_client

async def test_connection() -> bool:
    """Test Supabase connection"""
    try:
        if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
            print("❌ Supabase credentials not configured")
            return False
        
        client = get_supabase_client()
        # Try a simple query to test connection - just get the first few rows without filters
        result = await client.query("profiles", "GET")
        print("✅ Supabase connection successful")
        print(f"   Found {len(result) if isinstance(result, list) else 'unknown'} profiles in database")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

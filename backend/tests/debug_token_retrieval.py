"""
Debug the token retrieval process
"""
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.user_tokens import UserTokenService
from config.supabase import get_supabase_service_client

async def debug_token_retrieval():
    """Debug why token retrieval is failing"""
    
    user_id = "79ba6a8b-7aa7-498b-a9ed-a772d1dc34ef"
    print(f"Debugging token retrieval for user: {user_id}")
    
    try:
        # Test the UserTokenService
        print("\n1. Testing UserTokenService...")
        token = await UserTokenService.get_user_notion_token(user_id)
        print(f"UserTokenService result: {token[:20]}..." if token else "No token found")
        
        # Test direct query with the same filters
        print("\n2. Testing direct query...")
        supabase = get_supabase_service_client()
        
        result = await supabase.query(
            "user_integrations",
            "GET",
            filters={
                "user_id": user_id,
                "integration_type": "notion",
                "is_active": True
            }
        )
        
        print(f"Direct query result: {len(result) if result else 0} rows")
        if result:
            for integration in result:
                print(f"  - Integration: {integration}")
        
        # Test without the is_active filter
        print("\n3. Testing without is_active filter...")
        result2 = await supabase.query(
            "user_integrations",
            "GET",
            filters={
                "user_id": user_id,
                "integration_type": "notion"
            }
        )
        
        print(f"Query without is_active: {len(result2) if result2 else 0} rows")
        if result2:
            for integration in result2:
                print(f"  - Integration: {integration}")
                
    except Exception as e:
        print(f"Error in debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_token_retrieval())
# Debug script to check OAuth token retrieval
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

import asyncio
from backend.services.user_tokens import UserTokenService
from backend.config.supabase import get_supabase_service_client

async def debug_oauth_token():
    user_id = "99d11141-76eb-460f-8741-f2f5e767ba0f"
    
    print(f"Debugging OAuth token for user: {user_id}")
    
    # Test direct database access
    try:
        supabase = get_supabase_service_client()
        print("✓ Supabase client initialized")
        
        # Check if user exists in user_integrations table
        result = await supabase.query(
            "user_integrations",
            "GET",
            filters={
                "user_id": user_id,
            },
        )
        
        print(f"All integrations for user: {result}")
        
        # Check specifically for Notion integration
        notion_result = await supabase.query(
            "user_integrations",
            "GET",
            filters={
                "user_id": user_id,
                "integration_type": "notion",
            },
        )
        
        print(f"Notion integrations: {notion_result}")
        
        # Try the service method
        token = await UserTokenService.get_user_notion_token(user_id)
        print(f"UserTokenService result: {token}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_oauth_token())
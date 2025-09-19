## 🔧 OAuth User ID Issue - Solutions

The error you're experiencing is because the user ID `93f2ef33-aa8e-421f-934c-f1b964786bc4` doesn't exist in the `profiles` table when trying to store Notion OAuth tokens.

### Root Cause

The OAuth flow is trying to store integration data for a user that doesn't have a profile record in Supabase.

### Solutions Applied

#### 1. **Enhanced Token Storage (IMPLEMENTED)**

Modified `store_user_tokens()` to:

- Check if user profile exists before storing tokens
- Create a basic profile if missing
- Use service role key for all operations

#### 2. **RLS Policy Fix (NEEDS TO BE APPLIED)**

Run this SQL in your Supabase dashboard:

```sql
-- Drop existing conflicting policies if they exist
DROP POLICY IF EXISTS "Service role can manage integrations" ON public.user_integrations;
DROP POLICY IF EXISTS "Service role can manage profiles" ON public.profiles;

-- Add comprehensive service role policies
CREATE POLICY "Service role bypass for integrations" ON public.user_integrations
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Service role bypass for profiles" ON public.profiles
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);
```

#### 3. **Recommended OAuth Flow Fix**

The OAuth callback should get the user ID from the authenticated session, not the state parameter:

```python
@app.get("/api/oauth/notion/callback")
async def notion_callback(
    code: str,
    state: str,
    current_user = Depends(get_current_user_dependency)  # ADD THIS
):
    """Handle Notion OAuth callback"""
    try:
        oauth_service = NotionOAuthService()

        # Use authenticated user ID instead of state
        user_id = current_user["id"]  # More secure

        # Exchange code for token
        token_data = await oauth_service.exchange_code_for_token(code, state)

        # Store tokens
        success = await oauth_service.store_user_tokens(user_id, token_data)

        # ... rest of the function
```

### Immediate Steps to Fix

1. **Apply RLS Policy** - Run the SQL above in Supabase dashboard
2. **Restart Backend** - Restart your FastAPI server to pick up config changes
3. **Test Again** - Try the OAuth flow again

### Verification

Run this test to verify the fix:

```bash
cd backend
python test_oauth_storage.py
```

The enhanced token storage function will now handle missing user profiles gracefully.

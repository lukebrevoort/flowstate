# Notion OAuth Setup Guide for Flowstate

## Overview
This guide will help you set up Notion OAuth integration for your Flowstate application, allowing users to connect their personal Notion workspaces.

## Step 1: Create a Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "Create new integration"
3. Fill in the details:
   - **Name**: `Flowstate`
   - **Associated workspace**: Select your workspace
   - **Type**: Choose "Public integration"
4. Click "Submit"
5. Note down the following values:
   - **OAuth client ID**: This will be your `NOTION_OAUTH_CLIENT_ID`
   - **OAuth client secret**: This will be your `NOTION_OAUTH_CLIENT_SECRET`

## Step 2: Configure OAuth Settings

1. In your Notion integration settings, go to the "OAuth Domain & URIs" section
2. Add the following redirect URIs:
   - For development: `http://localhost:3000/api/oauth/notion/callback`
   - For production: `https://your-domain.com/api/oauth/notion/callback`

## Step 3: Set Capabilities

In the integration settings, make sure you have the following capabilities enabled:
- **Read content**: ✅
- **Update content**: ✅
- **Insert content**: ✅
- **Read user information including email addresses**: ✅

## Step 4: Update Environment Variables

Add these to your `/Users/lbrevoort/Desktop/flowstate/backend/.env` file:

```env
# Replace with your actual values from Notion
NOTION_OAUTH_CLIENT_ID=your_notion_oauth_client_id_here
NOTION_OAUTH_CLIENT_SECRET=your_notion_oauth_client_secret_here
NOTION_OAUTH_REDIRECT_URI=http://localhost:3000/api/oauth/notion/callback
```

## Step 5: Update Frontend Environment Variables

Add this to your `/Users/lbrevoort/Desktop/flowstate/frontend/flowstate/.env.local` file:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## Step 6: Test the OAuth Flow

1. Start your backend server:
   ```bash
   cd /Users/lbrevoort/Desktop/flowstate/backend
   python app.py
   ```

2. Start your frontend server:
   ```bash
   cd /Users/lbrevoort/Desktop/flowstate/frontend/flowstate
   npm run dev
   ```

3. Navigate to `http://localhost:3000/OAuth`
4. Click "Connect Notion"
5. You should be redirected to Notion's authorization page
6. After authorizing, you should be redirected back with a success message

## Step 7: Verify Database Storage

After successful OAuth, check your Supabase database:

1. Go to your Supabase dashboard
2. Navigate to the "Table Editor"
3. Check the `user_integrations` table
4. You should see a new row with:
   - `integration_type`: "notion"
   - `access_token`: Your Notion access token
   - `is_active`: true

## Step 8: Test Agent Integration

Once OAuth is working, test that your agents can use the user's Notion token:

```python
# Test script to verify user token access
from services.user_tokens import UserTokenService
import asyncio

async def test_user_notion_access(user_id):
    token = await UserTokenService.get_user_notion_token(user_id)
    if token:
        print(f"✅ User {user_id} has Notion token")
        from notion_api import NotionAPI
        api = NotionAPI(user_id=user_id)
        print(f"✅ NotionAPI initialized with user token")
    else:
        print(f"❌ No Notion token found for user {user_id}")

# Replace with actual user ID from your database
asyncio.run(test_user_notion_access("your-user-id-here"))
```

## Troubleshooting

### Common Issues:

1. **"Invalid redirect URI"**
   - Make sure the redirect URI in Notion matches exactly with `NOTION_OAUTH_REDIRECT_URI`
   - Check for trailing slashes or protocol mismatches

2. **"Authorization header required"**
   - Make sure users are logged in before attempting OAuth
   - Check that the frontend is sending the authorization header

3. **"Failed to store Notion tokens"**
   - Verify Supabase connection is working
   - Check that the `user_integrations` table exists
   - Verify RLS policies allow the user to insert their own records

4. **"No Notion token available"**
   - Make sure the OAuth flow completed successfully
   - Check that tokens are being stored in the database
   - Verify the `user_id` parameter is being passed correctly

### Debug Mode:

To enable debug logging, add this to your backend:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

1. **Never expose client secrets**: Keep `NOTION_OAUTH_CLIENT_SECRET` server-side only
2. **Validate state parameters**: The OAuth flow includes CSRF protection via state parameters
3. **Token storage**: Access tokens are stored encrypted in Supabase with RLS policies
4. **Token refresh**: Notion tokens don't expire, but implement refresh logic if needed

## Production Deployment

When deploying to production:

1. Update redirect URIs in Notion integration settings
2. Update `NOTION_OAUTH_REDIRECT_URI` environment variable
3. Update `NEXT_PUBLIC_BACKEND_URL` to your production backend URL
4. Ensure HTTPS is used for all OAuth URLs
5. Set up proper domain verification in Notion integration settings

## Next Steps

Once Notion OAuth is working:

1. Implement Google Calendar OAuth using similar patterns
2. Add token refresh mechanisms
3. Add integration status indicators in the UI
4. Implement integration management (disconnect, reconnect)
5. Add error handling for expired or invalid tokens

# Supabase Integration for FlowState

This guide explains how to set up and use Supabase as your database backend for the FlowState project.

## What is Supabase?

Supabase is an open-source Firebase alternative that provides:

- PostgreSQL database
- Built-in authentication
- Real-time subscriptions
- Row Level Security (RLS)
- Auto-generated APIs

## Why Supabase?

✅ **Free Tier**: 500MB database storage, perfect for getting started
✅ **PostgreSQL**: Full-featured relational database
✅ **Built-in Auth**: User authentication handled automatically
✅ **Scalable**: Easy to upgrade as your app grows
✅ **Real-time**: Live updates for collaborative features

## Setup Instructions

### 1. Create a Supabase Project

1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Sign up for a free account
3. Click "New Project"
4. Fill in your project details:
   - Name: `flowstate-app`
   - Database Password: Choose a strong password
   - Region: Select closest to your users

### 2. Get Your Project Keys

1. In your Supabase dashboard, go to "Settings" → "API"
2. Copy these values:
   - **Project URL** (looks like `https://xxxxx.supabase.co`)
   - **anon/public key** (starts with `eyJhbGciOi...`)
   - **service_role key** (starts with `eyJhbGciOi...`, optional but recommended)

### 3. Configure Your Environment

1. Copy the environment template:

   ```bash
   cp .env.example .env
   ```

2. Update your `.env` file:
   ```env
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=your-anon-key-here
   SUPABASE_SERVICE_KEY=your-service-role-key-here
   ```

### 4. Install Dependencies

Run the setup script:

```bash
python scripts/setup_supabase.py
```

Or install manually:

```bash
pip install supabase>=2.4.0 postgrest-py>=0.13.0
```

### 5. Set Up Database Schema

1. In your Supabase dashboard, go to "SQL Editor"
2. Create a new query
3. Copy and paste the contents of `database/supabase_schema.sql`
4. Click "Run" to execute the schema

This will create:

- `profiles` table for user data
- `user_tasks` table for task management
- `user_sessions` table for chat history
- `user_integrations` table for third-party connections
- Row Level Security policies
- Automatic triggers for timestamps

### 6. Test the Connection

```bash
python -c "from config.supabase import test_connection; test_connection()"
```

You should see: `✅ Supabase connection successful`

### 7. Start Your Application

```bash
python app.py
```

## How It Works

### Database Service Layer

The `services/database.py` file provides a unified interface that can work with both:

- **Supabase** (when configured)
- **SQLAlchemy** (as fallback)

This means your app will automatically:

1. Try to use Supabase if configured
2. Fall back to SQLAlchemy/SQLite if Supabase is not available
3. Work seamlessly in both modes

### Authentication Flow

1. **Signup**: Creates user in Supabase Auth + profiles table
2. **Login**: Authenticates with Supabase + returns JWT token
3. **Protected Routes**: Use JWT tokens for authentication

### User Data Storage

- **Auth**: Handled by Supabase Auth (built-in)
- **Profile Data**: Stored in `profiles` table
- **Tasks**: Stored in `user_tasks` table
- **Chat History**: Stored in `user_sessions` table
- **Integrations**: Stored in `user_integrations` table

## Database Schema

### profiles

- User profile information
- Connected service flags
- User preferences and settings

### user_tasks

- Task management
- Priority, status, due dates
- Integration with Notion/Calendar

### user_sessions

- Chat conversation history
- Session context and metadata

### user_integrations

- OAuth tokens for third-party services
- Integration configuration

## Security Features

### Row Level Security (RLS)

All tables have RLS policies ensuring users can only access their own data.

### JWT Authentication

Uses standard JWT tokens compatible with your existing auth system.

### API Keys

- **anon key**: For client-side operations (limited permissions)
- **service key**: For server-side operations (full permissions)

## Free Tier Limits

Supabase free tier includes:

- 500MB database storage
- 2GB bandwidth
- 50MB file storage
- Up to 50,000 monthly active users
- Unlimited API requests

Perfect for development and small production deployments!

## Upgrading

When you need more resources:

1. Go to your Supabase dashboard
2. Click "Settings" → "Billing"
3. Choose a paid plan starting at $25/month

## Troubleshooting

### Connection Issues

- Check your `.env` file has correct URL and keys
- Verify your Supabase project is active
- Test connection with the test script

### Schema Issues

- Make sure you ran the complete schema from `database/supabase_schema.sql`
- Check the SQL Editor for any error messages
- Verify tables were created in the "Table Editor"

### Authentication Issues

- Check your JWT secret matches
- Verify RLS policies are enabled
- Test with the debug endpoints

## Support

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Community](https://github.com/supabase/supabase/discussions)
- FlowState project issues on GitHub

## Cost Comparison

| Service     | Free Tier | Paid Start |
| ----------- | --------- | ---------- |
| Supabase    | 500MB DB  | $25/month  |
| Render DB   | 1GB DB    | $7/month   |
| PlanetScale | 5GB DB    | $29/month  |
| AWS RDS     | None      | ~$15/month |

Supabase provides the best balance of features, free tier, and pricing for this project!

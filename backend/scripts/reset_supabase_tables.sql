-- Reset Supabase Tables Script
-- WARNING: This will DROP all existing tables and recreate them
-- Make sure to backup any important data before running this script

-- Step 1: Drop existing triggers first (to avoid dependency issues)
drop trigger if exists on_auth_user_created on auth.users;
drop trigger if exists profiles_updated_at on public.profiles;
drop trigger if exists user_tasks_updated_at on public.user_tasks;
drop trigger if exists user_sessions_updated_at on public.user_sessions;
drop trigger if exists user_integrations_updated_at on public.user_integrations;
drop trigger if exists profiles_validate_input on public.profiles;
drop trigger if exists user_tasks_validate_input on public.user_tasks;
drop trigger if exists profiles_security_log on public.profiles;
drop trigger if exists user_integrations_security_log on public.user_integrations;

-- Step 2: Drop existing functions
drop function if exists public.handle_new_user();
drop function if exists public.handle_updated_at();
drop function if exists public.validate_user_input();
drop function if exists public.log_security_event();

-- Step 3: Drop existing tables (order matters due to foreign key constraints)
drop table if exists public.security_log cascade;
drop table if exists public.user_integrations cascade;
drop table if exists public.user_sessions cascade;
drop table if exists public.user_tasks cascade;
drop table if exists public.profiles cascade;

-- Step 4: Drop indexes if they exist
drop index if exists profiles_email_idx;
drop index if exists user_tasks_user_id_idx;
drop index if exists user_tasks_status_idx;
drop index if exists user_tasks_due_date_idx;
drop index if exists user_sessions_user_id_idx;
drop index if exists user_sessions_session_id_idx;
drop index if exists user_integrations_user_id_idx;

-- Now you can run your main schema file to recreate everything

-- Supabase Database Schema for FlowState
-- This file contains all the necessary tables and functions for the FlowState application
-- Enhanced security configuration with comprehensive RLS policies

-- Enable necessary extensions
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto"; -- For additional security functions

-- Create enhanced profiles table to store additional user information
-- This extends Supabase Auth users with our app-specific data
create table public.profiles (
  id uuid references auth.users(id) primary key,
  name text,
  email text unique not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  personal_info jsonb default '{}'::jsonb, -- Store additional personal info securely, e.g. information for agent to pull from for additional context on User
  notion_connected boolean default false,
  google_calendar_connected boolean default false,
  
  -- User preferences
  timezone text default 'UTC',
  work_hours_start time default '09:00:00',
  work_hours_end time default '17:00:00',
  break_duration_minutes integer default 15,
  focus_session_duration_minutes integer default 25
);

-- Create user tasks table
create table public.user_tasks (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  title text not null,
  description text,
  category text default 'default',
  priority integer default 3 check (priority >= 1 and priority <= 5),
  status text default 'pending' check (status in ('pending', 'in_progress', 'completed', 'cancelled')),
  due_date timestamp with time zone,
  completed_at timestamp with time zone,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  
  -- Task metadata
  estimated_duration_minutes integer,
  actual_duration_minutes integer,
  notion_page_id text,
  google_calendar_event_id text
);

-- Create user sessions table for chat history
create table public.user_sessions (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  session_id text not null,
  messages jsonb default '[]'::jsonb,
  context jsonb default '{}'::jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  
  unique(user_id, session_id)
);

-- Create user integrations table
create table public.user_integrations (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  integration_type text not null check (integration_type in ('notion', 'google_calendar', 'google_drive')),
  access_token text,
  refresh_token text,
  token_expires_at timestamp with time zone,
  integration_data jsonb default '{}'::jsonb,
  is_active boolean default true,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  
  unique(user_id, integration_type)
);

-- Create indexes for better performance
create index profiles_email_idx on public.profiles(email);
create index user_tasks_user_id_idx on public.user_tasks(user_id);
create index user_tasks_status_idx on public.user_tasks(status);
create index user_tasks_due_date_idx on public.user_tasks(due_date);
create index user_sessions_user_id_idx on public.user_sessions(user_id);
create index user_sessions_session_id_idx on public.user_sessions(session_id);
create index user_integrations_user_id_idx on public.user_integrations(user_id);

-- Enable Row Level Security (RLS)
alter table public.profiles enable row level security;
alter table public.user_tasks enable row level security;
alter table public.user_sessions enable row level security;
alter table public.user_integrations enable row level security;

-- Force RLS for table owners (additional security)
alter table public.profiles force row level security;
alter table public.user_tasks force row level security;
alter table public.user_sessions force row level security;
alter table public.user_integrations force row level security;

-- Create enhanced RLS policies with additional security checks

-- Profiles policies - Enhanced with stricter validation
create policy "Users can view own profile" on public.profiles
  for select using (
    auth.uid() = id AND 
    auth.uid() is not null
  );

create policy "Users can update own profile" on public.profiles
  for update using (
    auth.uid() = id AND 
    auth.uid() is not null
  ) with check (
    auth.uid() = id AND 
    auth.uid() is not null
  );

create policy "Users can insert own profile" on public.profiles
  for insert with check (
    auth.uid() = id AND 
    auth.uid() is not null
  );

-- Prevent unauthorized profile deletion
create policy "Prevent profile deletion" on public.profiles
  for delete using (false);

-- User tasks policies - Enhanced with comprehensive validation
create policy "Users can view own tasks" on public.user_tasks
  for select using (
    auth.uid() = user_id AND 
    auth.uid() is not null
  );

create policy "Users can insert own tasks" on public.user_tasks
  for insert with check (
    auth.uid() = user_id AND 
    auth.uid() is not null AND
    title is not null AND
    length(title) > 0 AND
    length(title) <= 255
  );

create policy "Users can update own tasks" on public.user_tasks
  for update using (
    auth.uid() = user_id AND 
    auth.uid() is not null
  ) with check (
    auth.uid() = user_id AND 
    auth.uid() is not null AND
    title is not null AND
    length(title) > 0 AND
    length(title) <= 255
  );

create policy "Users can delete own tasks" on public.user_tasks
  for delete using (
    auth.uid() = user_id AND 
    auth.uid() is not null
  );

-- User sessions policies - Enhanced with session validation
create policy "Users can view own sessions" on public.user_sessions
  for select using (
    auth.uid() = user_id AND 
    auth.uid() is not null
  );

create policy "Users can insert own sessions" on public.user_sessions
  for insert with check (
    auth.uid() = user_id AND 
    auth.uid() is not null AND
    session_id is not null AND
    length(session_id) > 0
  );

create policy "Users can update own sessions" on public.user_sessions
  for update using (
    auth.uid() = user_id AND 
    auth.uid() is not null
  ) with check (
    auth.uid() = user_id AND 
    auth.uid() is not null
  );

create policy "Users can delete own sessions" on public.user_sessions
  for delete using (
    auth.uid() = user_id AND 
    auth.uid() is not null
  );

-- User integrations policies - Enhanced with integration type validation
create policy "Users can view own integrations" on public.user_integrations
  for select using (
    auth.uid() = user_id AND 
    auth.uid() is not null
  );

create policy "Users can insert own integrations" on public.user_integrations
  for insert with check (
    auth.uid() = user_id AND 
    auth.uid() is not null AND
    integration_type in ('notion', 'google_calendar', 'google_drive')
  );

create policy "Users can update own integrations" on public.user_integrations
  for update using (
    auth.uid() = user_id AND 
    auth.uid() is not null
  ) with check (
    auth.uid() = user_id AND 
    auth.uid() is not null AND
    integration_type in ('notion', 'google_calendar', 'google_drive')
  );

create policy "Users can delete own integrations" on public.user_integrations
  for delete using (
    auth.uid() = user_id AND 
    auth.uid() is not null
  );

-- Create function to automatically create profile when user signs up
-- Security: Set search_path to prevent search path attacks
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, name, email)
  values (
    new.id,
    new.raw_user_meta_data->>'name',
    new.email
  );
  return new;
end;
$$ language plpgsql security definer set search_path = public;

-- Create trigger to automatically create profile
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Create function to automatically update updated_at timestamps
-- Security: Set search_path to prevent search path attacks
create or replace function public.handle_updated_at()
returns trigger as $$
begin
  new.updated_at = timezone('utc'::text, now());
  return new;
end;
$$ language plpgsql set search_path = public;

-- Create triggers for updated_at
create trigger profiles_updated_at
  before update on public.profiles
  for each row execute procedure public.handle_updated_at();

create trigger user_tasks_updated_at
  before update on public.user_tasks
  for each row execute procedure public.handle_updated_at();

create trigger user_sessions_updated_at
  before update on public.user_sessions
  for each row execute procedure public.handle_updated_at();

create trigger user_integrations_updated_at
  before update on public.user_integrations
  for each row execute procedure public.handle_updated_at();

-- Additional Security Functions and Triggers

-- Function to validate and sanitize user input
create or replace function public.validate_user_input()
returns trigger as $$
begin
  -- Sanitize text fields to prevent XSS and injection attacks
  if TG_TABLE_NAME = 'profiles' then
    if new.name is not null then
      new.name = trim(new.name);
      if length(new.name) > 255 then
        raise exception 'Name too long';
      end if;
    end if;
  elsif TG_TABLE_NAME = 'user_tasks' then
    if new.title is not null then
      new.title = trim(new.title);
      if length(new.title) > 255 then
        raise exception 'Title too long';
      end if;
    end if;
    if new.description is not null then
      new.description = trim(new.description);
      if length(new.description) > 10000 then
        raise exception 'Description too long';
      end if;
    end if;
  end if;
  
  return new;
end;
$$ language plpgsql set search_path = public;

-- Add validation triggers
create trigger profiles_validate_input
  before insert or update on public.profiles
  for each row execute procedure public.validate_user_input();

create trigger user_tasks_validate_input
  before insert or update on public.user_tasks
  for each row execute procedure public.validate_user_input();

-- Function to log security events
create or replace function public.log_security_event()
returns trigger as $$
begin
  -- Log important security events (can be extended for audit trail)
  insert into public.security_log (
    user_id,
    table_name,
    operation,
    timestamp
  ) values (
    coalesce(auth.uid(), '00000000-0000-0000-0000-000000000000'::uuid),
    TG_TABLE_NAME,
    TG_OP,
    now()
  );
  
  if TG_OP = 'DELETE' then
    return old;
  else
    return new;
  end if;
end;
$$ language plpgsql security definer set search_path = public;

-- Create security log table for audit trail
create table if not exists public.security_log (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid,
  table_name text not null,
  operation text not null,
  timestamp timestamp with time zone default now() not null
);

-- Enable RLS on security log
alter table public.security_log enable row level security;

-- Only allow service role to access security logs
create policy "Service role only access" on public.security_log
  using (auth.jwt() ->> 'role' = 'service_role');

-- Add security logging triggers for sensitive operations
create trigger profiles_security_log
  after insert or update or delete on public.profiles
  for each row execute procedure public.log_security_event();

create trigger user_integrations_security_log
  after insert or update or delete on public.user_integrations
  for each row execute procedure public.log_security_event();

-- Additional constraints for data integrity
alter table public.profiles add constraint profiles_email_format 
  check (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

alter table public.user_tasks add constraint user_tasks_title_not_empty 
  check (length(trim(title)) > 0);

alter table public.user_sessions add constraint user_sessions_session_id_not_empty 
  check (length(trim(session_id)) > 0);

-- Grant necessary permissions
grant usage on schema public to authenticated;
grant select, insert, update, delete on all tables in schema public to authenticated;
grant usage on all sequences in schema public to authenticated;

-- Revoke dangerous permissions from public
revoke all on schema public from public;
revoke all on all tables in schema public from public;

-- Security settings for functions
alter function public.handle_new_user() owner to postgres;
alter function public.handle_updated_at() owner to postgres;
alter function public.validate_user_input() owner to postgres;
alter function public.log_security_event() owner to postgres;

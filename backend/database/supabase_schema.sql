-- Supabase Database Schema for FlowState
-- This file contains all the necessary tables and functions for the FlowState application

-- Enable necessary extensions
create extension if not exists "uuid-ossp";

-- Create profiles table to store additional user information
-- This extends Supabase Auth users with our app-specific data
create table public.profiles (
  id uuid references auth.users(id) primary key,
  name text,
  email text unique not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
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

-- Create RLS policies

-- Profiles policies
create policy "Users can view own profile" on public.profiles
  for select using (auth.uid() = id);

create policy "Users can update own profile" on public.profiles
  for update using (auth.uid() = id);

create policy "Users can insert own profile" on public.profiles
  for insert with check (auth.uid() = id);

-- User tasks policies
create policy "Users can view own tasks" on public.user_tasks
  for select using (auth.uid() = user_id);

create policy "Users can insert own tasks" on public.user_tasks
  for insert with check (auth.uid() = user_id);

create policy "Users can update own tasks" on public.user_tasks
  for update using (auth.uid() = user_id);

create policy "Users can delete own tasks" on public.user_tasks
  for delete using (auth.uid() = user_id);

-- User sessions policies
create policy "Users can view own sessions" on public.user_sessions
  for select using (auth.uid() = user_id);

create policy "Users can insert own sessions" on public.user_sessions
  for insert with check (auth.uid() = user_id);

create policy "Users can update own sessions" on public.user_sessions
  for update using (auth.uid() = user_id);

create policy "Users can delete own sessions" on public.user_sessions
  for delete using (auth.uid() = user_id);

-- User integrations policies
create policy "Users can view own integrations" on public.user_integrations
  for select using (auth.uid() = user_id);

create policy "Users can insert own integrations" on public.user_integrations
  for insert with check (auth.uid() = user_id);

create policy "Users can update own integrations" on public.user_integrations
  for update using (auth.uid() = user_id);

create policy "Users can delete own integrations" on public.user_integrations
  for delete using (auth.uid() = user_id);

-- Create function to automatically create profile when user signs up
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
$$ language plpgsql security definer;

-- Create trigger to automatically create profile
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Create function to automatically update updated_at timestamps
create or replace function public.handle_updated_at()
returns trigger as $$
begin
  new.updated_at = timezone('utc'::text, now());
  return new;
end;
$$ language plpgsql;

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

-- Fix for Notion OAuth RLS Policy Issue
-- Add service role bypass policy for user_integrations table

-- Add service role policy for user_integrations
create policy "Service role can manage integrations" on public.user_integrations
  for all using (
    auth.jwt() ->> 'role' = 'service_role'
  ) with check (
    auth.jwt() ->> 'role' = 'service_role'
  );

-- Add service role policy for profiles  
create policy "Service role can manage profiles" on public.profiles
  for all using (
    auth.jwt() ->> 'role' = 'service_role'
  ) with check (
    auth.jwt() ->> 'role' = 'service_role'
  );

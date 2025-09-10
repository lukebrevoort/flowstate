-- Enhanced RLS fix for OAuth operations
-- This addresses the service role authentication issue

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

-- Also ensure anon role can't access these tables directly
CREATE POLICY "Block anon access to integrations" ON public.user_integrations
  FOR ALL
  TO anon
  USING (false)
  WITH CHECK (false);

-- Allow authenticated users to manage their own data (keep existing functionality)
-- The existing user policies should remain for authenticated users

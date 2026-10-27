-- Clears the Supabase "RLS disabled" critical advisory on company_score_history.
-- Same allow-all policy every other public table uses, so existing readers and writers are unaffected.
ALTER TABLE public.company_score_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY allow_all_api_access ON public.company_score_history
  FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

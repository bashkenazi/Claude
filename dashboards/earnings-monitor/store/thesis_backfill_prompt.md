Build "Thesis - Revised" pages for Bobby Ashkenazi's (SRS Investment Management) Tier 1–2 names that don't have one yet,
10 names per run, end to end without stopping for confirmation. Bobby approved this on 2026-11-03: he will not confirm
tenets one by one, so proposed tenets are auto-confirmed and he edits them in Notion afterwards.

1. Pick the names. From the Notion Companies DB (collection://54e1fc28-0c99-43cf-9d42-a6aa7de55d87), take the Tier 1
   and Tier 2 rows. Skip any company that already has a child page titled "<TICKER> Thesis - Revised" (or
   "<TICKER> Thesis Revised — <date>", "<Company> Thesis - Revised") under its company or thesis page. Take the next 10
   in this order: Tier 1 first, then Semis, Hardware, Power & DC infra, Software, Internet, IT Services.

2. For each name (one subagent per name, at most 5 at a time), run the thesis-builder skill end to end:
   - Step 2 deviation: propose the 3–6 tenets and proceed without stopping. Put this line at the top of the Thesis
     section: "Tenets auto-confirmed on <date> (Bobby: no time to approve); edit here and Tech Daily follows."
   - Publish deviation: create the page as a CHILD of the company's thesis page, titled "<TICKER> Thesis - Revised",
     instead of under Anthropic Output. Never edit the source thesis page's own content.
   - If the thesis page has a "Thesis Tenet Tracker (rolling)" toggle from an earnings review, replace only the tenet
     names in it with the new tenets (the revised page is the single source); leave every other block alone.
   - CUSTOMER RULE (Bobby, 2026-11-03): for every customer that is, or recently was, 10%+ of revenue (from
     10-K/10-Q/20-F concentration disclosures, transcripts, or broker estimates), include a customer sub-toggle under
     the relevant tenet and a "Customers" block in Business Description with: % of revenue by year/quarter as
     disclosed (broker estimates labelled), what the company sells them, contract/LTA terms and duration, share of
     that customer's wallet vs competitors, ramp or loss timing, and the latest dated, sourced datapoints on that
     customer. If there is no 10%+ customer, say so in one line.
   - Read-only on Supabase. Do not run the analyst-day skill (it publishes elsewhere); read the transcript instead.
   - Each subagent works only in its own scratch folder.

3. Finish with a short summary: each name with its page URL, overall conviction and per-tenet convictions; names
   skipped and why; and the measured token count per name and in total.

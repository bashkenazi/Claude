# Backfill rules for workers (coordinator additions to worker-brief.md; these take precedence where they differ)
This is Bobby's approved 90-day backfill; calls are older than today.
1. GenSearch pacing: exactly ONE alphasense_genai ask in flight at a time — never send asks in parallel. Wait ~15 s between asks.
2. Errors: on `alphasense_unavailable` or `vendor_rejected` with no conversation_id, `sleep 60` then ask the same call again; at most 2 such retries per call, then mark `failed`. On a timeout with no conversation_id, do NOT re-ask; mark `failed` with note "timeout-no-conv-id".
3. Comparisons ("What changed vs last check", Summary): use only evidence dated BEFORE the call's `released` date. Ignore later rows and later Expert Calls toggles.
4. Thesis page ordering: insert each call toggle in date order so the Expert Calls section stays newest-first (directly before the first existing toggle with an older date, or at the section end).
5. Full template always. If a toggle is too large for one update_content, file it in two updates: first the toggle containing Summary through Thesis impact, then a second update_content inserting the remaining sections and the Q&A toggle just before that toggle's closing tag. Never drop sections ("lean form" is not allowed).
6. Files: write ONLY `calls/<doc_id>.json` for doc_ids in YOUR batch, your own summaries/context files, and `workers/worker-<your id>.json`. Never loop over, rewrite or delete other files in calls/ or anywhere else. Only cp the exact file path named in a tool result; never glob the shared tool-results directory.
7. A GenSearch answer whose document_ids don't match the call you asked about belongs to another call: don't use it for this one.

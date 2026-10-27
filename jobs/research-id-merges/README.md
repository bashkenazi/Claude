# research_id merges

One-off fixes that move `research_evidence` rows from a duplicate (alias) `research` ID to the company's
canonical ID. Each file records the exact rows moved and an undo statement. Only `research_evidence.research_id`
changes; `model_forecasts`, scores and the alias `research` rows are left as they are.

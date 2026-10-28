# Working rules for this repo

- **Datapoint rules live in Notion.** When Bobby changes or adds a datapoint or extraction rule, write it straight
  into the OpenClaw Agent Feedback page (`33aa883333de817c853ef25feefea41d`): the calibration "Datapoint Filter"
  reference toggles and, where it changes the standard, the "🧩 SKILL: datapoint-filter — master text" toggle
  (bump its version line). Do this without asking first, then tell him what changed. Do not edit the installed
  datapoint-filter skill; offer a repackaged zip through a download page instead.
- New pipelines that load to Supabase under the filter's Auto-load policy are added to the master text's Auto-load
  scope list.

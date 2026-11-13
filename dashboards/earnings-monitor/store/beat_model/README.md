# Revenue-beat model (2026-11-13)

Question: what predicts the size of a company's revenue surprise vs final FactSet consensus?

Data (FactSet, 142 coverage names, 3,547 quarterly prints, 2019Q3-2026Q4):
- `surprise` SALES QTR (consensus before, actual after) -> sales_surprise.json
- `guidance` SALES QTR rel 1, AQ snapshots -> guidance.json
- `consensus_rolling` SALES QTR rel 1, monthly -> cons_fq1.json (mean, std, high/low, up/down, count)
- monthly prices (USD) -> prices_m.json
- Supabase research_evidence + Insider Score (2025-05+ subset) via ../../scratchpad panel.py loaders

Scripts: panel_rb.py (point-in-time event panel) -> ic_rb.py (univariate rank ICs, quintiles, halves)
-> fm_rb.py (Fama-MacBeth multivariate + OOS) -> model_rb.py (% model, fit <=2023 / test 2024+) -> score_next.py.

Model (% surprise): 0.76 + 0.30*median beat last 8 + 0.21*last beat + 0.29*consensus revision since last print
+ 0.32*guided + 0.048*(guide vs consensus at guide, %) + 0.15*(3m price move/10) + 0.08*(easy comp/10) + 0.14*(peer beats vs norm this season).
OOS 2024-26: top quintile median beat +4.4% (93% beat), bottom +0.4% (57% beat, 28% miss >1%).
Live check on 51 Nov 1-13 prints: rank corr 0.26; top third median +4.4% vs bottom third +0.9%.

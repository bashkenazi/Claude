# Signal score (Stocks page)

Backtested stock score (Bobby, 2026-11-13). Weekly, point-in-time, Tier 1-2 names with prices.

Inputs (pull into the working folder, then run panel.py → ic.py → final.py → snapshot.py):
- companies.json: stocks.companies from the live page (t, bbg, rids, sector, subs, tier) plus fs = FactSet id.
- prices_w.json: FactSet GlobalPrices, data_type prices, frequency W, USD, fields price+turnover, 50 ids per call, from 52 weeks back.
- est_w.json: FactSet EstimatesConsensus consensus_rolling NTMA EPS and SALES, relativeFiscal 1, frequency W, USD, ~37 ids per call.
- pt.json: PRICE_TGT consensus_rolling 0/0, frequency AM. surprise.json: surprise QTR SALES and EPS.
- insiders.json: Insider Score get_insider_transactions, Buy+Sell, CEO/CFO/OFF/DIR, use_disclosure_date, 3-month windows (US only).
- evidence.json: Supabase research_evidence for the companies' research ids (id|rid|event_date|field_key|impact|confidence|source_type|primary_source|created).

Method: forward 4- and 12-week returns minus beta (26-week, vs equal-weight universe) x universe return; weekly Spearman IC per input;
t-stats divide by sqrt(overlap). Weights in final.py were chosen from inputs with the same sign in both halves and both horizons.
Walk-forward (walk.py) out-of-sample IC ~0.00 for 2026-07-24..2026-10-16: re-test monthly and keep weights small.
snapshot.py writes stock_scores_latest.json → page db stock_scores/latest (the Stocks page reads it live).

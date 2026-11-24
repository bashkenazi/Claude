-- Markets tab (Bobby Tech Daily): macro & technical indicator store.
-- Project hftouzahniiwigcchvje, schema public. Adds four tables; touches no existing table.

create table public.macro_series (
  series_id      text primary key,          -- e.g. UST10Y, ISM_MFG, INIT_CLAIMS, PX_XLY
  name           text not null,
  category       text not null,             -- Growth, Labor, Inflation, Rates & policy, Credit & liquidity, Housing, Sentiment, Valuation, Markets
  units          text,
  frequency      text not null default 'M', -- storage frequency (M = month-end / monthly average)
  sources        text,                      -- e.g. 'Bloomberg NAPMPMI Index to 2018-07; FactSet US.LMUEMPR after'
  notes          text,
  first_month    date,
  last_month     date,
  updated_at     timestamptz not null default now()
);

create table public.macro_observations (
  series_id      text not null references public.macro_series (series_id),
  obs_month      date not null,             -- month-end date
  value          double precision not null,
  source         text not null,             -- 'bloomberg_csv' | 'factset' | 'derived'
  loaded_at      timestamptz not null default now(),
  primary key (series_id, obs_month)
);
create index macro_observations_month_idx on public.macro_observations (obs_month);

-- Weekly readings of each signal on the scorecard, so state changes can be tracked over time.
create table public.market_signal_snapshots (
  asof           date not null,             -- run date (weekly)
  signal_key     text not null,             -- e.g. curve, claims, trend10, ism_chg
  data_month     date,                      -- month of the latest underlying data
  value          double precision,
  state          text check (state in ('bull', 'bear')),
  pct            double precision,          -- percentile vs full history
  stale          boolean,
  payload        jsonb,
  primary key (asof, signal_key)
);

-- One row per weekly run: composite scores and the written call-outs.
create table public.market_regime_snapshots (
  asof           date primary key,
  mkt_score      double precision,          -- -1 (all bearish) .. +1 (all bullish)
  rot_score      double precision,          -- -1 favour defensives .. +1 favour cyclicals
  headline       text,
  callouts       jsonb,
  run_notes      jsonb,
  created_at     timestamptz not null default now()
);

-- Only the connector's privileged role uses these tables; no API access.
alter table public.macro_series enable row level security;
alter table public.macro_observations enable row level security;
alter table public.market_signal_snapshots enable row level security;
alter table public.market_regime_snapshots enable row level security;

-- Sell-Side Daily Research Extractor: run log and per-file ledger.
-- Project hftouzahniiwigcchvje, schema public. Adds two tables; touches no existing table.

create table public.sellside_runs (
  id               bigserial primary key,
  started_at       timestamptz not null default now(),
  finished_at      timestamptz,
  mode             text not null default 'live'
                   check (mode in ('live', 'dry_run')),
  trigger          text check (trigger in ('scheduled', 'manual')),
  status           text not null default 'running'
                   check (status in ('running', 'completed', 'partial', 'blocked_source', 'failed')),
  rules_version    text,          -- datapoint-filter version or Notion master date
  files_listed     int,
  files_new        int,
  files_processed  int,
  files_pending    int,
  rows_loaded      int,
  rows_held        int,
  dups_skipped     int,
  failures         int,
  notion_url       text,
  notes            jsonb
);

create table public.sellside_file_ledger (
  drive_item_id    text primary key,
  drive_id         text not null,
  folder_path      text not null,  -- e.g. 'Daily Research/10.26.26' or '.../10.26.26/AI Files'
  folder_date      date,           -- parsed from the M.D.YY date folder
  file_name        text not null,
  size_bytes       bigint,
  last_modified    timestamptz,
  page_count       int,
  status           text not null default 'pending'
                   check (status in ('pending', 'extracting', 'extracted', 'loaded', 'held_only',
                                     'no_datapoints', 'failed', 'skipped')),
  attempts         int not null default 0,
  last_run_id      bigint references public.sellside_runs (id),
  duplicate_of     text,           -- drive_item_id of the original when skipped as a re-filed copy
  evidence_ids     bigint[],
  kept             int,
  held             int,
  cut              int,
  hold_reasons     jsonb,
  last_error       text,
  first_seen_at    timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

create index sellside_file_ledger_status_idx on public.sellside_file_ledger (status);
create index sellside_file_ledger_folder_date_idx on public.sellside_file_ledger (folder_date);
create index sellside_file_ledger_file_name_idx on public.sellside_file_ledger (file_name);

-- Only the connector's privileged role uses these tables; no API access.
alter table public.sellside_runs enable row level security;
alter table public.sellside_file_ledger enable row level security;

-- ============================================================
-- Clinexa — Migration 001: Initial Schema
-- Apply this in your Supabase SQL editor or via psql.
-- ============================================================

-- Enable the pgvector extension (required for document_chunks.embedding)
create extension if not exists vector;

-- ============================================================
-- profiles
-- Extends Supabase auth.users with app-level profile data.
-- ============================================================
create table if not exists profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  preferred_language text default 'en',
  created_at timestamptz default now()
);

alter table profiles enable row level security;

create policy "profiles: own row" on profiles
  for all using (auth.uid() = id);

-- Auto-create profile on user signup
create or replace function handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into profiles (id, full_name)
  values (new.id, new.raw_user_meta_data ->> 'full_name')
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure handle_new_user();

-- ============================================================
-- reports
-- ============================================================
create table if not exists reports (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  file_name text not null,
  file_path text not null,
  report_type text,
  status text default 'processing' check (status in ('processing', 'ready', 'failed')),
  uploaded_at timestamptz default now(),
  processed_at timestamptz
);

alter table reports enable row level security;

create policy "reports: own rows" on reports
  for all using (auth.uid() = user_id);

-- ============================================================
-- report_pages
-- ============================================================
create table if not exists report_pages (
  id uuid primary key default gen_random_uuid(),
  report_id uuid not null references reports(id) on delete cascade,
  page_number int not null,
  raw_text text,
  used_ocr boolean default false
);

alter table report_pages enable row level security;

-- Access via report ownership
create policy "report_pages: own rows" on report_pages
  for all using (
    exists (
      select 1 from reports r
      where r.id = report_pages.report_id
        and r.user_id = auth.uid()
    )
  );

-- ============================================================
-- health_parameters
-- ============================================================
create table if not exists health_parameters (
  id uuid primary key default gen_random_uuid(),
  report_id uuid not null references reports(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  parameter text not null,
  value numeric,
  unit text,
  ref_min numeric,
  ref_max numeric,
  status text check (status in ('NORMAL', 'HIGH', 'LOW', 'UNKNOWN')),
  page_number int,
  extracted_at timestamptz default now()
);

alter table health_parameters enable row level security;

create policy "health_parameters: own rows" on health_parameters
  for all using (auth.uid() = user_id);

create index if not exists idx_health_parameters_user_id on health_parameters(user_id);
create index if not exists idx_health_parameters_report_id on health_parameters(report_id);
create index if not exists idx_health_parameters_parameter on health_parameters(parameter);

-- ============================================================
-- document_chunks
-- ============================================================
create table if not exists document_chunks (
  id uuid primary key default gen_random_uuid(),
  report_id uuid not null references reports(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  page_number int,
  content text not null,
  embedding vector(384)
);

alter table document_chunks enable row level security;

create policy "document_chunks: own rows" on document_chunks
  for all using (auth.uid() = user_id);

-- IVFFlat index for approximate nearest-neighbor search
create index if not exists idx_document_chunks_embedding
  on document_chunks using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- Full-text search index
alter table document_chunks
  add column if not exists content_tsvector tsvector
    generated always as (to_tsvector('english', content)) stored;

create index if not exists idx_document_chunks_fts
  on document_chunks using gin(content_tsvector);

-- ============================================================
-- chat_sessions
-- ============================================================
create table if not exists chat_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text,
  created_at timestamptz default now()
);

alter table chat_sessions enable row level security;

create policy "chat_sessions: own rows" on chat_sessions
  for all using (auth.uid() = user_id);

-- ============================================================
-- chat_messages
-- ============================================================
create table if not exists chat_messages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references chat_sessions(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  citations jsonb,
  risk_level text check (risk_level in ('low', 'medium', 'high')),
  created_at timestamptz default now()
);

alter table chat_messages enable row level security;

create policy "chat_messages: own rows" on chat_messages
  for all using (
    exists (
      select 1 from chat_sessions cs
      where cs.id = chat_messages.session_id
        and cs.user_id = auth.uid()
    )
  );

create index if not exists idx_chat_messages_session_id on chat_messages(session_id);

-- ============================================================
-- health_trends
-- ============================================================
create table if not exists health_trends (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  parameter text not null,
  data_points jsonb not null default '[]',
  direction text check (direction in ('increasing', 'decreasing', 'stable')),
  updated_at timestamptz default now(),
  unique(user_id, parameter)
);

alter table health_trends enable row level security;

create policy "health_trends: own rows" on health_trends
  for all using (auth.uid() = user_id);

create index if not exists idx_health_trends_user_parameter on health_trends(user_id, parameter);

-- ============================================================
-- request_logs (for observability — Phase 11)
-- ============================================================
create table if not exists request_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete set null,
  endpoint text,
  total_latency_ms int,
  rag_latency_ms int,
  llm_latency_ms int,
  safety_latency_ms int,
  input_tokens int,
  output_tokens int,
  estimated_cost_usd numeric(10,6),
  error_code text,
  created_at timestamptz default now()
);

alter table request_logs enable row level security;

-- Only admins can query logs; service role bypasses RLS
create policy "request_logs: deny all non-service" on request_logs
  for all using (false);

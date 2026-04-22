-- NutriDécrypte , initial schema
-- 2026-04-22

-- =============================
-- Analytics tracker (règle STACK-2026)
-- =============================
create table if not exists public.page_views (
  id bigserial primary key,
  created_at timestamptz not null default now(),
  path text not null,
  locale text,
  referrer text,
  user_agent text,
  is_bot boolean not null default false,
  country_code text,
  session_id text,
  event_type text not null default 'page_view',
  event_data jsonb
);
create index if not exists page_views_created_at_idx on public.page_views (created_at desc);
create index if not exists page_views_path_idx on public.page_views (path);
create index if not exists page_views_is_bot_idx on public.page_views (is_bot);

-- =============================
-- Brands
-- =============================
create table if not exists public.brands (
  id bigserial primary key,
  slug text not null unique,
  name text not null,
  country text,
  parent_company text,
  website text,
  description text,
  description_fr text,
  average_grade text,
  average_score numeric(5,2),
  product_count integer not null default 0,
  logo_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists brands_average_grade_idx on public.brands (average_grade);

-- =============================
-- Categories (magnésium, vitamine D, oméga 3, céréales, yaourts, etc.)
-- =============================
create table if not exists public.categories (
  id bigserial primary key,
  slug text not null unique,
  name_en text not null,
  name_fr text not null,
  parent_slug text,
  description_en text,
  description_fr text,
  type text not null default 'food',
  product_count integer not null default 0,
  created_at timestamptz not null default now()
);
create index if not exists categories_parent_idx on public.categories (parent_slug);
create index if not exists categories_type_idx on public.categories (type);

-- =============================
-- Products (issus d'Open Food Facts + scoring NutriDécrypte)
-- =============================
create table if not exists public.products (
  id bigserial primary key,
  slug text not null unique,
  barcode text unique,
  name text not null,
  brand_slug text references public.brands(slug) on delete set null,
  categories text[] not null default '{}',
  countries text[] not null default '{}',

  -- raw Open Food Facts data
  off_data jsonb,
  ingredients_text text,
  nutrition_grade text,
  nova_group integer,
  additives_tags text[] not null default '{}',
  allergens_tags text[] not null default '{}',
  labels_tags text[] not null default '{}',

  -- NutriDécrypte Score (5 axes pondérés)
  score_nutri integer,
  score_nova integer,
  score_additives integer,
  score_claims integer,
  score_density integer,
  score_overall integer,
  grade text,
  verdict_en text,
  verdict_fr text,
  warnings jsonb,

  image_url text,
  image_small_url text,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  last_scored_at timestamptz
);
create index if not exists products_brand_idx on public.products (brand_slug);
create index if not exists products_grade_idx on public.products (grade);
create index if not exists products_categories_gin on public.products using gin (categories);
create index if not exists products_countries_gin on public.products using gin (countries);

-- =============================
-- Additives dictionary (E-numbers, référentiel EFSA)
-- =============================
create table if not exists public.additives (
  id bigserial primary key,
  e_number text not null unique,
  slug text not null unique,
  name_en text not null,
  name_fr text,
  category text,
  risk_level text not null default 'unknown',
  controversy boolean not null default false,
  banned_in text[] not null default '{}',
  anses_opinion text,
  efsa_opinion_url text,
  last_reviewed_at date,
  summary_en text,
  summary_fr text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists additives_risk_idx on public.additives (risk_level);

-- =============================
-- Scores history (pour voir l'évolution si recettes changent)
-- =============================
create table if not exists public.scores_history (
  id bigserial primary key,
  product_id bigint not null references public.products(id) on delete cascade,
  score_overall integer not null,
  grade text not null,
  algorithm_version text not null default 'v1',
  captured_at timestamptz not null default now(),
  snapshot jsonb
);
create index if not exists scores_history_product_idx on public.scores_history (product_id, captured_at desc);

-- =============================
-- Newsletter subscribers (Phase 2)
-- =============================
create table if not exists public.subscribers (
  id bigserial primary key,
  email text not null unique,
  locale text not null default 'fr',
  source text,
  status text not null default 'active',
  confirmed boolean not null default false,
  confirmed_at timestamptz,
  unsubscribed_at timestamptz,
  created_at timestamptz not null default now()
);

-- =============================
-- Row Level Security , permissive en lecture publique
-- =============================
alter table public.page_views enable row level security;
alter table public.brands enable row level security;
alter table public.categories enable row level security;
alter table public.products enable row level security;
alter table public.additives enable row level security;
alter table public.scores_history enable row level security;
alter table public.subscribers enable row level security;

-- anon peut insérer un page_view et un subscriber, le reste est service_role only pour écriture
create policy "anon_insert_page_view" on public.page_views
  for insert to anon
  with check (true);

create policy "anon_insert_subscriber" on public.subscribers
  for insert to anon
  with check (true);

-- Lecture publique des catalogues
create policy "public_read_brands" on public.brands for select to anon, authenticated using (true);
create policy "public_read_categories" on public.categories for select to anon, authenticated using (true);
create policy "public_read_products" on public.products for select to anon, authenticated using (true);
create policy "public_read_additives" on public.additives for select to anon, authenticated using (true);

-- service_role peut tout
create policy "service_all_page_views" on public.page_views for all to service_role using (true) with check (true);
create policy "service_all_brands" on public.brands for all to service_role using (true) with check (true);
create policy "service_all_categories" on public.categories for all to service_role using (true) with check (true);
create policy "service_all_products" on public.products for all to service_role using (true) with check (true);
create policy "service_all_additives" on public.additives for all to service_role using (true) with check (true);
create policy "service_all_scores_history" on public.scores_history for all to service_role using (true) with check (true);
create policy "service_all_subscribers" on public.subscribers for all to service_role using (true) with check (true);

-- NutriDecrypte · affiliate clicks tracking
-- 2026-05-27 · Phase 3 Amazon Partenaires launch (tag nutridecrypte-21)

create table if not exists public.affiliate_clicks (
  id uuid primary key default gen_random_uuid(),
  occurred_at timestamptz not null default now(),
  slug text not null,
  merchant text not null check (merchant in ('amazon')),
  destination_url text not null,
  referrer text,
  country text,
  ua_hash text,
  is_bot boolean not null default false
);

create index if not exists affiliate_clicks_occurred_at_idx
  on public.affiliate_clicks (occurred_at desc);
create index if not exists affiliate_clicks_slug_idx
  on public.affiliate_clicks (slug, occurred_at desc);
create index if not exists affiliate_clicks_not_bot_idx
  on public.affiliate_clicks (occurred_at desc) where is_bot = false;

alter table public.affiliate_clicks enable row level security;

drop policy if exists "anon_insert_affiliate_click" on public.affiliate_clicks;
create policy "anon_insert_affiliate_click" on public.affiliate_clicks
  for insert to anon, authenticated
  with check (true);

drop policy if exists "service_all_affiliate_clicks" on public.affiliate_clicks;
create policy "service_all_affiliate_clicks" on public.affiliate_clicks
  for all to service_role using (true) with check (true);

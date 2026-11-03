-- Перá — известия на телефона (Release C, част 2). Пусни веднъж в Supabase → SQL Editor → Run. Безопасно е да се пусне повторно.
-- 1. pg_net: базата може сама да „почука“ на помощника push (така работят и Database Webhooks).
do $$ begin
  if not exists (select 1 from pg_extension where extname = 'pg_net') then
    begin create extension pg_net with schema extensions; exception when others then create extension pg_net; end;
  end if;
end $$;

-- 2. Телефоните, които са приели известия: по един ред на телефон и човек. Всеки вижда и пипа само своите редове.
create table if not exists public.push_subs (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null default auth.uid() references auth.users(id) on delete cascade,
  endpoint   text not null check (length(endpoint) <= 1000),
  p256dh     text not null check (length(p256dh) <= 200),
  auth       text not null check (length(auth) <= 100),
  kinds      text[] not null default '{ask,idp,inv,comment}',
  updated_at timestamptz not null default now(),
  unique (user_id, endpoint)
);
alter table public.push_subs enable row level security;
drop policy if exists "push_subs: own" on public.push_subs;
create policy "push_subs: own" on public.push_subs for all to authenticated
  using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
grant select, insert, update, delete on public.push_subs to authenticated;

-- 3. Ключовете на помощника (правят се сами) и какво вече е известено за всеки дневник — само за служебния ключ (без правила = никой друг).
create table if not exists public.push_keys (
  id int primary key default 1 check (id = 1), pub text not null, priv text not null, created_at timestamptz not null default now());
alter table public.push_keys enable row level security;
create table if not exists public.push_state (
  owner uuid primary key references auth.users(id) on delete cascade, seen jsonb not null default '{}', updated_at timestamptz not null default now());
alter table public.push_state enable row level security;

-- 4. Подписът на дневника: отворените въпроси, приетите определения и поканите. Променен ли е — има какво да се извести.
create or replace function public.push_sig(d jsonb) returns jsonb language sql immutable set search_path = '' as $$
  select jsonb_build_object(
    'ask', coalesce((select jsonb_agg(o->>'id' order by o->>'id') from jsonb_array_elements(coalesce(d->'obs', '[]'::jsonb)) o
                     where jsonb_typeof(o) = 'object' and o ? 'ask' and not (o ? 'askOk')), '[]'::jsonb),
    'ok',  coalesce((select jsonb_agg((o->>'id') || ':' || (o->'askOk'->>'by') order by o->>'id') from jsonb_array_elements(coalesce(d->'obs', '[]'::jsonb)) o
                     where jsonb_typeof(o) = 'object' and o ? 'askOk'), '[]'::jsonb),
    'inv', coalesce((select jsonb_agg(x order by x) from (select (s->>'id') || ':' || k.key || ':' || k.value::text as x
                     from jsonb_array_elements(coalesce(d->'outs', '[]'::jsonb)) s, jsonb_each(case when jsonb_typeof(s->'inv') = 'object' then s->'inv' else '{}'::jsonb end) k) q), '[]'::jsonb));
$$;

-- 5. Почукването: само номер или човек, без съдържание. Грешка тук никога не спира записа (известията са екстра).
--    Носи публичния ключ на проекта (apikey) — Supabase вече го иска при всяко повикване на помощник.
-- (полетата на NEW се четат в отделни клонове: social няма user_id, а journals няма id)
create or replace function public.push_ping() returns trigger language plpgsql security definer set search_path = '' as $$
declare b jsonb;
begin
  if TG_TABLE_NAME = 'social' then
    b := jsonb_build_object('table', 'social', 'id', NEW.id);
  else
    if TG_OP = 'UPDATE' and public.push_sig(NEW.data) = public.push_sig(OLD.data) then return NEW; end if;
    b := jsonb_build_object('table', 'journals', 'owner', NEW.user_id);
  end if;
  begin
    perform net.http_post(url := 'https://szyituwdlbwpqkfuklxq.supabase.co/functions/v1/push', body := b,
      headers := '{"Content-Type": "application/json", "apikey": "sb_publishable_B74aN3lH5shn4ECtrTYsTw_I4OAhL4M"}'::jsonb, timeout_milliseconds := 5000);
  exception when others then null;
  end;
  return NEW;
end $$;
drop trigger if exists push_social on public.social;
create trigger push_social after insert on public.social for each row execute function public.push_ping();
drop trigger if exists push_journals on public.journals;
create trigger push_journals after insert or update on public.journals for each row execute function public.push_ping();

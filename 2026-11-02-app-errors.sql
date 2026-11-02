-- Пусни веднъж: Supabase → SQL Editor → New query → постави → Run. Безопасно е и да се пусне повторно.
-- 9. Грешките на приложението (издание A, 2026-11-02): записват се автоматично — версия, телефон, екран, съобщение.
--    Без записи и без места. Добавят се и без профил (user_id празно); никой не ги чете през приложението —
--    гледат се в Supabase → Table Editor → app_errors.
create table if not exists public.app_errors (
  id      bigint generated always as identity primary key,
  at      timestamptz not null default now(),
  user_id uuid references auth.users(id) on delete set null,
  ver     text check (ver is null or length(ver) <= 40),
  ua      text check (ua is null or length(ua) <= 300),
  view    text check (view is null or length(view) <= 60),
  msg     text check (msg is null or length(msg) <= 600),
  src     text check (src is null or length(src) <= 400)
);
alter table public.app_errors enable row level security;
drop policy if exists "app_errors: add own" on public.app_errors;
create policy "app_errors: add own" on public.app_errors for insert to authenticated
  with check (user_id is null or user_id = (select auth.uid()));
drop policy if exists "app_errors: add anonymous" on public.app_errors;
create policy "app_errors: add anonymous" on public.app_errors for insert to anon
  with check (user_id is null);
grant insert on public.app_errors to anon, authenticated;

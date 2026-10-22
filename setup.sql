-- Птичи дневник — споделяне между приятели (Supabase)
-- Пусни целия файл веднъж: SQL Editor → New query → постави → Run.
-- Може да се пуска и повторно — нищо не се дублира и нищо не се трие.
--
-- Модел: всеки има свой дневник (един ред с всички записи, излети и етикети) и папка със снимки.
-- Кодът ти позволява на някого да ГЛЕДА твоя дневник; той не може да го променя.
-- За да се виждате взаимно, двамата си разменяте кодовете.

-- 1. Профил: име и код за приятели (12 знака, случайни)
create table if not exists public.profiles (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  name       text not null default '',
  code       text not null unique default upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 12)),
  created_at timestamptz not null default now()
);

-- 2. Кой кого гледа: owner позволява на viewer да чете дневника и снимките му
create table if not exists public.viewers (
  owner      uuid not null references auth.users(id) on delete cascade,
  viewer     uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (owner, viewer),
  check (owner <> viewer)
);

-- 3. Дневникът: един ред на човек, целият дневник като JSON ({v, obs, beh, outs})
create table if not exists public.journals (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  data       jsonb not null,
  updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;
alter table public.viewers  enable row level security;
alter table public.journals enable row level security;

-- Помощни функции (security definer, за да не се въртят политиките една в друга)
create or replace function public.can_view(who uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select who = (select auth.uid())
      or exists (select 1 from public.viewers v where v.owner = who and v.viewer = (select auth.uid()));
$$;

create or replace function public.can_view_folder(folder text) returns boolean
language sql stable security definer set search_path = '' as $$
  select folder = (select auth.uid())::text
      or exists (select 1 from public.viewers v where v.owner::text = folder and v.viewer = (select auth.uid()));
$$;

-- Ставаш зрител на чужд дневник, като въведеш кода му. Връща id-то на собственика.
create or replace function public.follow(friend_code text) returns uuid
language plpgsql security definer set search_path = '' as $$
declare
  me uuid := auth.uid();
  o  uuid;
begin
  if me is null then raise exception 'not signed in'; end if;
  select p.user_id into o from public.profiles p
   where p.code = upper(regexp_replace(coalesce(friend_code, ''), '[^0-9A-Za-z]', '', 'g'));
  if o is null then raise exception 'unknown code'; end if;
  if o = me then raise exception 'own code'; end if;
  insert into public.viewers(owner, viewer) values (o, me) on conflict do nothing;
  return o;
end $$;

-- Собственият код се чете и сменя само през тези две функции — иначе приятел, който те следва,
-- можеше да прочете твоя код и да те последва, без да си му го дал.
create or replace function public.my_code() returns text
language sql stable security definer set search_path = '' as $$
  select p.code from public.profiles p where p.user_id = (select auth.uid());
$$;
create or replace function public.new_code() returns text
language sql volatile security definer set search_path = '' as $$
  update public.profiles set code = upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 12))
   where user_id = (select auth.uid()) returning code;
$$;

-- Сървърът слага часа на всяко записване
create or replace function public.touch_updated() returns trigger
language plpgsql set search_path = '' as $$
begin new.updated_at := now(); return new; end $$;
drop trigger if exists journals_touch on public.journals;
create trigger journals_touch before insert or update on public.journals
  for each row execute function public.touch_updated();

-- За незадължителното „будене": заявка веднъж дневно пречи на безплатния проект да заспи
create or replace function public.ping() returns timestamptz
language sql stable set search_path = '' as $$ select now(); $$;

-- 4. Правила за достъп
drop policy if exists "profiles: read" on public.profiles;
create policy "profiles: read" on public.profiles for select to authenticated
  using (public.can_view(user_id)
         or exists (select 1 from public.viewers v where v.viewer = profiles.user_id and v.owner = (select auth.uid())));
drop policy if exists "profiles: create own" on public.profiles;
create policy "profiles: create own" on public.profiles for insert to authenticated
  with check (user_id = (select auth.uid()));
drop policy if exists "profiles: edit own" on public.profiles;
create policy "profiles: edit own" on public.profiles for update to authenticated
  using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));

drop policy if exists "viewers: see own links" on public.viewers;
create policy "viewers: see own links" on public.viewers for select to authenticated
  using (owner = (select auth.uid()) or viewer = (select auth.uid()));
drop policy if exists "viewers: remove own links" on public.viewers;
create policy "viewers: remove own links" on public.viewers for delete to authenticated
  using (owner = (select auth.uid()) or viewer = (select auth.uid()));
-- нови връзки има само през follow()

drop policy if exists "journals: read own or followed" on public.journals;
create policy "journals: read own or followed" on public.journals for select to authenticated
  using (public.can_view(user_id));
drop policy if exists "journals: create own" on public.journals;
create policy "journals: create own" on public.journals for insert to authenticated
  with check (user_id = (select auth.uid()));
drop policy if exists "journals: edit own" on public.journals;
create policy "journals: edit own" on public.journals for update to authenticated
  using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
drop policy if exists "journals: delete own" on public.journals;
create policy "journals: delete own" on public.journals for delete to authenticated
  using (user_id = (select auth.uid()));

-- 5. Изрични разрешения (от 30.10.2026 Supabase не ги дава сам на нови таблици и функции)
revoke all on public.profiles, public.viewers, public.journals from anon;
revoke all on public.profiles from authenticated;                  -- колоната code не се вижда отвън
grant select (user_id, name, created_at) on public.profiles to authenticated;
grant insert (user_id, name)             on public.profiles to authenticated;
grant update (name)                      on public.profiles to authenticated;
grant select, delete                 on public.viewers  to authenticated;
grant select, insert, update, delete on public.journals to authenticated;
revoke execute on function public.can_view(uuid), public.can_view_folder(text), public.follow(text), public.my_code(), public.new_code() from public, anon;
grant  execute on function public.can_view(uuid), public.can_view_folder(text), public.follow(text), public.my_code(), public.new_code() to authenticated;
grant  execute on function public.ping() to anon, authenticated;

-- 6. Снимки: частна кофа, папка на човек (<user_id>/<снимка>.jpg), само JPEG до 3 MB
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('photos', 'photos', false, 3145728, array['image/jpeg'])
on conflict (id) do nothing;

drop policy if exists "photos: read own or followed" on storage.objects;
create policy "photos: read own or followed" on storage.objects for select to authenticated
  using (bucket_id = 'photos' and public.can_view_folder((storage.foldername(name))[1]));
drop policy if exists "photos: upload own" on storage.objects;
create policy "photos: upload own" on storage.objects for insert to authenticated
  with check (bucket_id = 'photos' and (storage.foldername(name))[1] = (select auth.uid())::text);
drop policy if exists "photos: replace own" on storage.objects;
create policy "photos: replace own" on storage.objects for update to authenticated
  using (bucket_id = 'photos' and (storage.foldername(name))[1] = (select auth.uid())::text);
drop policy if exists "photos: delete own" on storage.objects;
create policy "photos: delete own" on storage.objects for delete to authenticated
  using (bucket_id = 'photos' and (storage.foldername(name))[1] = (select auth.uid())::text);

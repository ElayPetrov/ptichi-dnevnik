# Перá — phone notifications: one-time setup (about 15 minutes)

You do this once, in the Supabase dashboard. Nothing here needs a password or key from you:
the helper makes its own keys the first time it runs and keeps them in the database.

## 1. The database (2 minutes)
1. Supabase → **SQL Editor** → **New query**.
2. Open `2026-11-03-push.sql` from the release, copy all of it, paste, **Run**.
3. Expected: "Success. No rows returned". (It is safe to run again.)

It adds the table of phones that accepted notifications (each person sees only their own), two private tables for the
helper (its keys, and what it has already announced), and two small triggers. The triggers only "knock" with a number or a
person's id — never content — and a failed knock can never stop a journal from saving.

## 2. The helper „push“ (5 minutes)
1. Supabase → **Edge Functions** → **Deploy a new function** → **Via Editor**.
2. Name it exactly `push`.
3. In the **Code** tab, delete **all** of the example code (it starts with `// Setup type definitions…` and uses
   `withSupabase`), paste the whole of `supabase/functions/push/index.ts`, press **Deploy updates**.
   Line 1 must now read `// push — известията на Перá към телефоните (Web Push).`
4. In the function's **Settings** tab: turn **off** "Enforce JWT verification" (the same as for `xc`) → Save.
   The helper trusts no message: it re-reads everything from the database itself before announcing anything.

## 3. Check it (1 minute)
Open in the browser: https://szyituwdlbwpqkfuklxq.supabase.co/functions/v1/push?key=1
You should see `{"key":"B…"}` — a long code. The first call creates the keys; later calls show the same code.
- „MISSING_CREDENTIALS“ with „publishable“, „secret“ → the editor's example code is still deployed: redo step 2.3.
- A message about a JWT → „Enforce JWT verification“ is still on: redo step 2.4.

(Перá and the database also send the project's public key with every call, so they keep working even if Supabase
starts asking for one.)

## 4. The app
Upload the release to GitHub as usual (including `sw.js` and the folder `supabase/functions/push`). Then on each phone:
open Перá → your profile → **Известия на този телефон** → **Включи известията** → allow → **Изпрати пробно**.

- **iPhone:** notifications only arrive if Перá was added to the Home Screen (Safari → Share → „Добави към началния
  екран“) and opened from there; iOS 16.4 or newer. The app says so on an iPhone in Safari.
- **Android:** works in Chrome, installed or not.

What arrives (each switchable on that phone): a friend asks what a bird is · a suggestion on your question, or your
suggestion accepted · an outing invitation · comments and replies · „Браво“ (off at first).

## If something doesn't arrive
- „Изпрати пробно“ says it didn't reach the phone → switch notifications off and on again on that phone.
- Test arrives but real ones don't → check step 1 ran (Database → Triggers should list `push_social` and `push_journals`).
  If you ran an earlier copy of the SQL, run this one again (it now sends the project key with each knock).
- Supabase → Edge Functions → push → **Logs** shows every call and any error.

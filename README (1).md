# Птичи дневник

A bird field-observation journal: one HTML file with a Bulgarian interface. It installs on a phone, works offline, and can share and sync journals between friends through Supabase.

## What's where

- `site/`: the app exactly as Netlify serves it. `index.html` is the whole app; `sw.js` keeps it working offline; `manifest.webmanifest` and the icons make it installable.
- `supabase/setup.sql`: the database setup for sharing and sync. Safe to re-run in the Supabase SQL editor.
- `tests/`: 204 automated checks and a sunrise check, built to run in a Claude sandbox. See `tests/README.md`.
- `netlify.toml`: tells Netlify to publish `site/` with no build step.

The Supabase key in `site/index.html` is the publishable key, meant to sit in a browser. What each person can read or change is enforced by the database rules in `supabase/setup.sql`.

## Releasing a new version

1. Bump `VER` in `site/index.html`. The app shows it at the bottom as „версия …“.
2. Run the tests. Every suite must end with `FAILURES: 0`.
3. If `supabase/setup.sql` changed, run it in Supabase first.
4. Commit the changed files to `main`. Netlify deploys every commit within a minute or two.
5. Open the app once with signal on each device so it picks up the new version.

Change the cache name `V` in `sw.js` only when `sw.js` itself changes.

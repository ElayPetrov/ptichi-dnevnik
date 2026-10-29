# Птичи дневник

A bird field-observation journal: one HTML file with a Bulgarian interface. It installs on a phone, works offline, and can share and sync journals between friends through Supabase.

## What's here

Everything sits in this one folder, and GitHub Pages publishes it as it is from `main` at https://elaypetrov.github.io/ptichi-dnevnik/ (Settings → Pages; no build step). `netlify.toml` is left over from the earlier Netlify hosting and does nothing now.

- The app: `index.html` is the whole app, `sw.js` keeps it working offline, and `manifest.webmanifest` with the three icons makes it installable.
- The database: `setup.sql` sets up sharing and sync. Safe to re-run in the Supabase SQL editor.
- The species list: built into `index.html` (`SPL`). 268 species from BSPB's Определител (Bulgarian and Latin names), with the Latin name checked against Wikipedia's „List of birds of Bulgaria“ (IOC 9.2), which also gives the English name and the family. It suggests names, fills empty fields, and links names that belong to one species when counting; it never changes a record. `species.csv` is the same list as a spreadsheet, with BSPB's older Latin names where they differ.
- The tests: `prepare.sh`, `setup.sh`, `run_all.sh`, `sbstack.py`, `sun.js`, `sun_check.py`, `tap_test.py`, the `test_*.py` files and two test photos. 488 automated checks and a sunrise check, built to run in a Claude sandbox; see `TESTS.md`.

The Supabase key in `index.html` is the publishable key, meant to sit in a browser. What each person can read or change is enforced by the database rules in `setup.sql`.

## Releasing a new version

1. Bump `VER` in `index.html`. The app shows it at the bottom as „версия …“.
2. Run the tests. Every suite must end with `FAILURES: 0`.
3. If `setup.sql` changed, run it in Supabase first.
4. On the repo's main page, Add file → Upload files, and drop the changed files. A file with the same name replaces the old one. GitHub Pages publishes every commit to `main` within a minute or two (Actions → „pages build and deployment“).
5. Open the app once with signal on each device so it picks up the new version.

Change the cache name `V` in `sw.js` only when `sw.js` itself changes.

Province outlines for the eBird export come from Apache Superset's country map of Bulgaria (Apache License 2.0), simplified.

# Птичи дневник — tests

254 automated checks plus a sunrise cross-check, written for a Claude sandbox (Ubuntu, Python 3, Node).

## Run

1. Clone this repo to `/home/claude/repo` and run `bash /home/claude/repo/prepare.sh`. It copies the tests, the app and `setup.sql` into `/home/claude`, where the tests expect them. Run the next two steps there.
2. `bash setup.sh` — Python packages, Postgres, PostgREST 12.2.12, supabase-js 2.117.3 from npm.
3. `bash run_all.sh` — every suite should end with `FAILURES: 0`.

Postgres stops between sandbox sessions; `run_all.sh` starts it again.
The sandbox can't reach supabase.co, so sharing is tested against a stand-in (`sbstack.py`):
real Postgres and PostgREST running the real `supabase-setup.sql`, the real supabase-js bundle,
and imitation sign-in and file storage that enforce the same storage policies.

## Suites

| File | Checks | Covers |
| --- | --- | --- |
| test_autofill.py | 19 | name and place autofill, never overwriting typed values |
| test_fixes.py | 25 | species merging, outing banner, stale outing prompt, photo staging |
| test_modes.py | 13 | live versus write-up outing defaults |
| test_pwa.py | 23 | installability, offline opening, updates, backups, arrivals, install hints |
| test_outings.py | 25 | unsure records, outings as events, backups v4/v5/v6 |
| test_views.py | 14 | sun times, species page, year curve, share cards |
| test_sql.py | 24 | database access rules, as three users |
| test_share.py | 24 | two people end to end: sign-up, codes, sync, comparison, offline, second phone |
| test_twoway.py | 14 | one account on phone and laptop: merges, deletions, outings, photos, a write race |
| test_guard.py | 7 | a friend's two devices; someone signing in on another person's browser; the message when sign-ups are off |
| test_sil.py | 6 | family silhouettes in the life list, species page and share card |
| test_season.py | 7 | the seasonal header: months to seasons, each season's details, theme switch, season-coloured cards |
| test_map.py | 8 | close points merge on the map, nothing lost, the merged point's list, its photos load, re-merging on zoom |
| test_photos.py | 9 | missing or unreadable photos say so; an unreadable pick (e.g. HEIC) warns at once; normal photos still show; Запиши waits for a photo in progress; a failed save says why |
| test_days.py | 9 | Дневник days fold: newest open, counts, photos load on opening, remembered, search opens matches, saving opens the day |
| test_species.py | 14 | the built-in list fills new species, finds BSPB's older Latin and second Bulgarian names, never overrides your own names or records; names it links count as one species, also against a friend's journal |
| test_pick.py | 9 | coordinates under Място, the map pin: where it opens, tapping, Готово, the place not moving the pin, saving, no signal |
| tap_test.py | 4 | Запиши never misses a tap after a blur-time layout change |
| sun_check.py | 7 dates | sunrise formula against the astral library for Kazanlak |

## Files

In `/home/claude`, `prepare.sh` puts the app at `ptichi-dnevnik.html` and in `netlify/` (copies of `index.html` and its files), and the database setup at `supabase-setup.sql`.
After changing the app there, copy `ptichi-dnevnik.html` back to `index.html` in the repo.
`a.jpg` and `b.jpg` are plain generated test photos.

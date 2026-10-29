# Птичи дневник — tests

507 automated checks plus a sunrise cross-check, written for a Claude sandbox (Ubuntu, Python 3, Node).

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
| test_map.py | 10 | close points merge on the map, nothing lost, the merged point's list, its photos load, re-merging on zoom |
| test_photos.py | 9 | missing or unreadable photos say so; an unreadable pick (e.g. HEIC) warns at once; normal photos still show; Запиши waits for a photo in progress; a failed save says why |
| test_days.py | 9 | Дневник days fold: newest open, counts, photos load on opening, remembered, search opens matches, saving opens the day |
| test_species.py | 14 | the built-in list fills new species, finds BSPB's older Latin and second Bulgarian names, never overrides your own names or records; names it links count as one species, also against a friend's journal |
| test_pick.py | 10 | the form's field order (count and name first, the usually pre-filled date, time, place and coordinates lower), the map pin: where it opens, tapping, Готово, the place not moving the pin, saving, no signal |
| test_yay.py | 12 | „Честито, нов вид!“: only for a species new to the journal (not repeats, not unsure), its number and round numbers, silhouette or photo, hides by itself or on a tap, opens the share card, never blocks typing during an outing |
| test_treats.py | 17 | first meeting of the year (with last year's date), badges (pop-up once, the strip in Моите видове), „СТО!“ at 100, the end-of-outing summary and its card, „На днешна дата“, the sky through the day (night: stars, moon phase, owl, dark hills) |
| test_outedit.py | 15 | outings inside their day in Дневник (placed by time, foldable), „+ птица“ for forgotten birds, moving records in and out with the form's Излет field, one editor from Дневник and Излети, moving an outing's date, live outings, search, Фенология and Карта fitting a 360 px phone |
| test_layout.py | 12 | tab order and all eight tabs on a 360 px phone, the Значки tab, Места (named first, unnamed points by coordinates, opening with a mini map and every record), Карта's style row under „Истинска карта“, every photo of a map point in a swipe strip, Приятели with friends first |
| test_places.py | 9 | renaming a place or naming an unnamed point in Места: confirmation with the count, all records (unsure too) and outings updated, joining an existing place, „без място и координати“ left alone |
| test_more.py | 14 | icon filters (no „Тази година“) fitting a 360 px phone, months and years folding in Дневник, an outing card's little map and photos, Фенология's order and its month grid fitting a phone with every name in full; the app uses its own address for sign-up emails and the shared code |
| test_invite.py | 13 | outing invitations through the database stand-in: inviting someone who sees your journal, the banner and checklist, copying without photos or notes into „с …“, answers syncing, later edits staying separate, inviting again for forgotten birds, declining |
| test_alt.py | 14 | „Може да е и“ for unsure records: hidden until unsure, same-genus suggestions from the list, adding and removing, saving, „или …“ in Дневник, no merging or counting, search, editing, dropped once sure; a long name never runs under the record's buttons |
| test_feed.py | 16 | the Приятели feed with three accounts on the stand-in: cards for outings and days, opening read-only records, Браво, comments, who sees what, the database refusing outsiders, „Бях там“ with the owner's approval, and the joint-outing comparison; the 2-minute refresh downloads only changed journals and lights the dot on any tab |
| test_notify.py | 14 | the bird on the account button; orange dots on Приятели (a friend's new records, others' Браво or comments on yours) and Значки (a new badge); new cards first and marked „ново“ until you leave the tab |
| test_badges.py | 18 | the 31 badges in three levels: honest counting, places (~1 km) and patch (~500 m), the best 365 days, big outing and big day, one winter, careful counts, notes, group thresholds, scientific families, social badges, the one-time summary after the update, a new level while logging and its highlight in the feed, the Значки tab |
| test_ranks.py | 11 | how well you know each species: bronze „Познат“ 10, silver „Приятел“ 50, gold „Познавач“ 150 days, counted by days not records, species outside the list too, sure records only, the legend, the species page, crowns (not rings) in the bird's corner; badge cards with progress and description apart |
| test_store.py | 7 | the journal, outings, friends' copies and reactions moving from localStorage to IndexedDB on first opening (localStorage freed only after a successful write), new records stored there, reload, and a 40,000-record journal far beyond the old ~5 MB limit |
| test_back.py | 5 | „назад“ from a species page returns Моите видове to where you were, and back from a friend's journal returns the feed to where you were |
| test_merge.py | 6 | the sixth box „дни на терен“ (days with sure records in the last 365 days) and the six boxes in two rows; Места under the map in Карта, opening a place without redrawing the map |
| test_goals.py | 13 | Цели: only the targets you add, from the list or the group's new species; a new species needs all three names and then fills the form; a friend's last sighting with day, place and distance; „и … го търси“; the dot for a nearby sighting; „Цел постигната!“; removed targets stay removed through sync |
| test_ebird.py | 11 | „Към eBird“: eBird Record Format (Extended) with 19 columns and no header; one list per outing (Traveling or Stationary with duration, distance in miles, completeness, observers), incidental lists for other records, one row per species, cleaned text, province from the outlines, unsure records left out |
| test_checklist.py | 18 | „Списък“: open any time, counting only in an outing; suggestions from where you are, added only on tap; adding by name; a tap logs +1 with time and GPS; a new record beyond ~300 m; minus and undo; heard mode; the new-species card; long press opens the current batch with its count, describing closes it and new taps start a second batch; heard and seen kept apart; form records never added to; no keyboard on opening; the list stays |
| test_sesslist.py | 7 | the green outing banner opens and closes a plain list of the outing's records, newest first, unsure marked, each with a pencil (edit) and × (delete) |
| test_onboard.py | 17 | first steps: four welcome cards (with the profile's why and how), „Направи профил сега“, the data buttons moved into the profile with „Как се ползва“, calm empty screens, each tip once, the outing tip after three records, examples marked „напр.“, and nothing for people who already use the app |
| tap_test.py | 4 | Запиши never misses a tap after a blur-time layout change |
| sun_check.py | 7 dates | sunrise formula against the astral library for Kazanlak |

## Files

In `/home/claude`, `prepare.sh` puts the app at `ptichi-dnevnik.html` and in `netlify/` (copies of `index.html` and its files), and the database setup at `supabase-setup.sql`.
After changing the app there, copy `ptichi-dnevnik.html` back to `index.html` in the repo.
`a.jpg` and `b.jpg` are plain generated test photos.

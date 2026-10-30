#!/bin/bash
# Runs every suite. Each prints PASS/FAIL lines; this shows the last line of each (FAILURES: 0 = all good).
cd "$(dirname "$0")"
CL=$(pg_lsclusters -h | awk 'NR==1{print $1" "$2}'); pg_ctlcluster $CL status >/dev/null 2>&1 || { pg_ctlcluster $CL start; sleep 2; }
for pid in $(pgrep -f '^/home/claude/sb/postgrest'); do kill $pid; done
cp ptichi-dnevnik.html netlify/index.html
run(){ printf '%-9s ' "$1"; shift; "$@" 2>&1 | tail -1; }
run autofill python3 test_autofill.py 8941
run fixes    python3 test_fixes.py 8942
run modes    python3 test_modes.py 8943
run pwa      python3 test_pwa.py 8944
run outings  python3 test_outings.py 8945
run views    python3 test_views.py 8946
run sql      python3 test_sql.py
run share    timeout 300 python3 test_share.py 8947
run twoway   timeout 400 python3 test_twoway.py 8948
run guard    timeout 300 python3 test_guard.py 8949
run sil      python3 test_sil.py 8951
run season   python3 test_season.py 8952
run map      python3 test_map.py 8953
run photos   python3 test_photos.py 8954
run days     python3 test_days.py 8956
run species  python3 test_species.py 8957
run pick     python3 test_pick.py 8958
run yay      python3 test_yay.py 8959
run treats   python3 test_treats.py 8960
run outedit  python3 test_outedit.py 8962
run layout   python3 test_layout.py 8963
run places   python3 test_places.py 8964
run more     python3 test_more.py 8965
run invite   timeout 600 python3 test_invite.py 8966
run alt      python3 test_alt.py 8967
run feed     timeout 700 python3 test_feed.py 8968
run notify   python3 test_notify.py 8969
run badges   python3 test_badges.py 8970
run ranks    python3 test_ranks.py 8971
run store    python3 test_store.py 8972
run back     python3 test_back.py 8973
run merge    python3 test_merge.py 8974
run goals    python3 test_goals.py 8975
run ebird    python3 test_ebird.py 8976
run list     python3 test_checklist.py 8977
run banner   python3 test_sesslist.py 8978
run welcome  python3 test_onboard.py 8979
run idlinks  python3 test_idlinks.py 8980
run refphoto python3 test_refphoto.py 8981
run sounds   python3 test_sounds.py 8982
run spnav    python3 test_spnav.py 8983
run names    python3 test_names.py 8984
run xcfn     sh -c 'cp supabase/functions/xc/index.ts /tmp/xcfn.mjs && node test_xcfn.mjs'
printf '%-9s %s of 4 save taps landed\n' tap "$(python3 tap_test.py 8950 ptichi-dnevnik.html | grep -c "'saved'")"
printf '%-9s ' sun; python3 sun_check.py | tail -1

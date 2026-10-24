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
printf '%-9s %s of 4 save taps landed\n' tap "$(python3 tap_test.py 8950 ptichi-dnevnik.html | grep -c "'saved'")"
printf '%-9s ' sun; python3 sun_check.py | tail -1

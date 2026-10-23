#!/bin/bash
# Prepares a Claude sandbox (Ubuntu, Python 3, Node) for the Птичи дневник tests.
# Run it in /home/claude (prepare.sh puts everything there): the tests use paths under /home/claude.
set -e
cd "$(dirname "$0")"
pip install -q --break-system-packages psycopg2-binary astral pillow >/dev/null 2>&1 || true
python3 -c "import playwright" 2>/dev/null || pip install -q --break-system-packages playwright
command -v psql >/dev/null || { apt-get update -q >/dev/null; apt-get install -y -q postgresql >/dev/null; }
CL=$(pg_lsclusters -h | awk 'NR==1{print $1" "$2}'); pg_ctlcluster $CL start 2>/dev/null || true; sleep 2
cat > /tmp/role.sql <<'SQL'
do $$ begin if not exists (select from pg_roles where rolname='tester') then create role tester login superuser password 't'; end if; end $$;
SQL
chmod 644 /tmp/role.sql && su postgres -c "psql -q -f /tmp/role.sql"
mkdir -p sb && cd sb
[ -x postgrest ] || { curl -sSL -o pg.tar.xz https://github.com/PostgREST/postgrest/releases/download/v12.2.12/postgrest-v12.2.12-linux-static-x86-64.tar.xz && tar xJf pg.tar.xz; }
[ -f package/dist/umd/supabase.js ] || { npm pack @supabase/supabase-js@2.117.3 >/dev/null 2>&1 && tar xzf supabase-supabase-js-2.117.3.tgz; }
[ -f leaflet/leaflet.js ] || { mkdir -p leaflet && cd leaflet && npm pack leaflet@1.9.4 >/dev/null 2>&1 && tar xzf leaflet-1.9.4.tgz && cp package/dist/leaflet.js . && cd ..; }   # the map tests serve this in place of cdnjs
echo "ready: run bash run_all.sh"

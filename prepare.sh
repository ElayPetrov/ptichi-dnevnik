#!/bin/bash
# Copies the tests and the current app from this repo into /home/claude, where the tests expect them.
# In a Claude sandbox:
#   git clone <this repo's URL> /home/claude/repo && bash /home/claude/repo/tests/prepare.sh
#   cd /home/claude && bash setup.sh && bash run_all.sh
set -e
R="$(cd "$(dirname "$0")/.." && pwd)"; H=/home/claude
cp "$R"/tests/* "$H"/
cp "$R/site/index.html" "$H/ptichi-dnevnik.html"
mkdir -p "$H/netlify" && cp "$R"/site/* "$H/netlify/"
cp "$R/supabase/setup.sql" "$H/supabase-setup.sql"
echo "copied into $H; now: cd $H && bash setup.sh && bash run_all.sh"

#!/bin/bash
# Copies the tests and the current app from this repo into /home/claude, where the tests expect them.
# In a Claude sandbox:
#   git clone https://github.com/ElayPetrov/ptichi-dnevnik /home/claude/repo && bash /home/claude/repo/prepare.sh
#   cd /home/claude && bash setup.sh && bash run_all.sh
set -e
R="$(cd "$(dirname "$0")" && pwd)"; H=/home/claude
cd "$R"
cp *.py *.sh sun.js a.jpg b.jpg "$H"/
cp index.html "$H/ptichi-dnevnik.html"
mkdir -p "$H/netlify" && cp index.html sw.js manifest.webmanifest icon-192.png icon-512.png apple-touch-icon.png "$H/netlify/"
cp setup.sql "$H/supabase-setup.sql"
echo "copied into $H; now: cd $H && bash setup.sh && bash run_all.sh"

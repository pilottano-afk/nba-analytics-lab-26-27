#!/usr/bin/env bash
set -euo pipefail
# Run on a machine with Python/pip and network access.
REPO_DIR="${BASKETBALLSCRAPER_REPO_DIR:-./vendor/BasketballScrapeR}"
SEASON="${1:-2026-2027}"
OUT_DIR="${BASKETBALLSCRAPER_DATA_DIR:-./data/basketballscraper/${SEASON}}"
if [[ ! -d "$REPO_DIR/.git" ]]; then
  mkdir -p "$(dirname "$REPO_DIR")"
  git clone https://github.com/francescoolivo/BasketballScrapeR.git "$REPO_DIR"
fi
mkdir -p "$OUT_DIR"
python -m pip install -r "$REPO_DIR/requirements.txt" 2>/dev/null || true
# The upstream repository documents run.py -l LBA -s YYYY-YYYY -o directory.
python "$REPO_DIR/run.py" -l LBA -s "$SEASON" -o "$OUT_DIR"
echo "CSV scraper salvati in: $OUT_DIR"
echo "Nota: l’import è isolato per stagione; il progetto non esegue backfill storico."
echo "Imposta BASKETBALLSCRAPER_DATA_DIR=$OUT_DIR per l'API."

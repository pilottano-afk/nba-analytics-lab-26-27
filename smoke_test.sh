#!/usr/bin/env bash
# Quick post-start smoke test for NBA/LBA API endpoints.
set -uo pipefail
BASE_URL="${BASE_URL:-http://localhost:8000}"
failures=0

check_endpoint() {
  local path="$1" description="$2" expected="$3"
  local tmp status
  tmp="$(mktemp)"
  status="$(curl -sS -L --max-time 15 -o "$tmp" -w '%{http_code}' "$BASE_URL$path" 2>/dev/null || true)"
  if [[ "$status" != "200" ]]; then
    printf 'FAIL  %-28s HTTP %s\n' "$description" "${status:-no response}"
    failures=$((failures + 1))
  elif ! grep -q "$expected" "$tmp"; then
    printf 'FAIL  %-28s response missing expected marker: %s\n' "$description" "$expected"
    failures=$((failures + 1))
  else
    printf 'PASS  %s\n' "$description"
  fi
  rm -f "$tmp"
}

printf 'Basketball Analytics smoke test\nAPI: %s\n\n' "$BASE_URL"
check_endpoint '/health' 'API health' 'ok'
check_endpoint '/api/v1/live/nba/scoreboard' 'NBA scoreboard endpoint' 'data_status'
check_endpoint '/api/v1/refresh/status' 'Refresh status endpoint' 'nba'
check_endpoint '/api/v1/live/lba/standings' 'LBA standings endpoint' 'data_status'

if (( failures > 0 )); then
  printf '\nResult: %s check(s) failed. Inspect: docker compose logs --tail=100 api worker beat\n' "$failures"
  exit 1
fi
printf '\nAll endpoint smoke checks passed. Note: HTTP 200 does not prove that the returned data are current/live; inspect data_status and checked_at.\n'

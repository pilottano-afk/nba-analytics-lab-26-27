# Pipeline status — v5

## Completed
- Competition-isolated EuroLeague adapter boundary.
- Immutable raw staging with SHA-256 canonical checksum.
- Two-team checksum validation and quarantine.
- Circuit breaker after three consecutive failures.
- Candidate snapshot and promotion contract.
- PostgreSQL repository boundary with lazy psycopg import.
- Analytical snapshot and team-game analytics tables.
- Deterministic FIBA fallback possession formula and core shooting metrics.

## Next
1. Persist verified games and analytics into PostgreSQL.
2. Add Redis versioned snapshot/cache promotion.
3. Replace demo adapter with a real EuroLeague upstream adapter after validating the permitted source/API contract.
4. Expose database-backed analytics through FastAPI.
5. Connect dashboard to the verified snapshot.


## v6 — Pipeline → PostgreSQL → API
- Added checksum column to raw payload persistence contract.
- Added snapshot persistence and current-snapshot query repository methods.
- Added `/api/v1/snapshots/current`.
- API falls back explicitly to DEMO_FALLBACK when PostgreSQL is unavailable.
- Added DB contract test without requiring a live database.


## v11.4 — aggiornamento stagione in corso
- Import LBA di default: `2026-2027`, in cartella dedicata.
- Analytics LBA: supporta box-score CSV con colonne riconoscibili e identificatore partita/data.
- Le statistiche aggregate a granularità non verificata non vengono convertite in medie.
- Nessun risultato ufficiale LBA è incluso nel pacchetto senza import effettivo della fonte.

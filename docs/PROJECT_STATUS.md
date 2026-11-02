# Stato progetto — 2 novembre 2026

Obiettivo: NBA Analytics Lab 26/27, solo stagione corrente, dati reali e aggiornamento quotidiano alle 08:00 Europe/Rome.

## Contenuto del pacchetto v13 disponibile
- Frontend Next.js 15 / React 19 e API FastAPI.
- PostgreSQL, Redis, Celery worker e Celery Beat tramite Docker Compose.
- Adattatore ESPN per scoreboard e box score NBA.
- Metriche individuali avanzate aggregate dai box score realmente acquisiti.
- Scheduler configurato alle 08:00 Europe/Rome.
- Il pacchetto dichiara 61 test backend superati.

## Limiti ancora aperti
- Backfill iniziale delle partite 2026/27 già concluse.
- Team ORtg, DRtg, Pace e Four Factors da completare.
- Lineup Lab e shot charts non ancora alimentati da dati NBA reali.
- Build Next.js, avvio Docker end-to-end e acquisizione live nell'ambiente ospitato non ancora verificati.
- Il refresh automatico richiede un host persistente con API, Redis, worker e Beat attivi.

## Prossimi passi
1. Importare i sorgenti applicativi del pacchetto v13, escludendo cache e dati runtime.
2. Eseguire test backend e build frontend in CI.
3. Correggere eventuali errori e verificare lo smoke test Docker.
4. Implementare backfill e completare le metriche di squadra e quintetti.
5. Distribuire i servizi persistenti e verificare il refresh giornaliero.

Regola: nessuna statistica demo deve essere presentata come dato reale; distinguere sempre LIVE, SNAPSHOT e DEMO.

# Smoke test post-avvio (Chromebook/Linux)

Questa verifica controlla che i servizi API rispondano. Non sostituisce i test unitari e non certifica da sola che i dati siano aggiornati.

1. Avvia il progetto con `docker compose up --build -d` dalla cartella che contiene `docker-compose.yml`.
2. Esegui `./scripts/smoke_test.sh`.
3. Se un controllo fallisce, consulta `docker compose logs --tail=100 api worker beat`.
4. Apri `http://localhost:8000/api/v1/live/nba/scoreboard` e verifica `data_status`:
   - `LIVE_SOURCE`: risposta appena ricevuta dalla fonte ESPN;
   - `CACHED_SNAPSHOT`: risposta recuperata da una copia locale, potenzialmente non aggiornata;
   - `SOURCE_UNAVAILABLE`: nessuna risposta live o snapshot utilizzabile.
5. Per il refresh programmato, apri `http://localhost:8000/api/v1/refresh/status`. Un campo `SUCCESS` indica che l'ultimo tentativo è riuscito; `FAILED` richiede di leggere il messaggio d'errore.

Per fermare i servizi: `docker compose down`.

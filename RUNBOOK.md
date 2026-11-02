# Runbook — Linux su Chromebook

1. Scarica ed estrai lo ZIP del progetto.
2. Apri il terminale Linux nella cartella che contiene `docker-compose.yml`.
3. Esegui `docker compose config`. Se non segnala errori, avvia `docker compose up --build`.
4. Apri `http://localhost:3000` per la dashboard e `http://localhost:8000/health` per verificare l'API.
5. La documentazione interattiva dell'API è su `http://localhost:8000/docs`.
6. Per controllare le fonti ufficiali, usa il pulsante in dashboard oppure visita `http://localhost:8000/api/v1/sources/check`.
7. Per i log del worker: `docker compose logs -f worker beat`.
8. Per fermare i servizi: `Ctrl+C`, poi `docker compose down`.

## Stato dei dati
La UI usa fixture sintetiche chiaramente etichettate. Il task schedulato controlla solo se i calendari ufficiali rispondono via HTTP; non importa ancora statistiche reali. Non cancellare il volume PostgreSQL per risolvere problemi senza prima salvare i dati.

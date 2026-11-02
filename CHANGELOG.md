# Changelog

## v11 — NBA + LBA live data adapters
- Added ESPN NBA scoreboard adapter and API endpoint.
- Added BasketballScrapeR CSV import endpoint and import helper script.
- Added provider status endpoint and mocked adapter tests.
- Kept demo analytics clearly labelled; real-data normalization remains a follow-up.

# Changelog

## v10 — Italian Basketball Analytics (2026-10-11)
- Refocused the existing Euro Basketball Stats Hub codebase on Serie A LBA and Serie A2 Old Wild West.
- Added competition switcher and separate synthetic leaderboard fixtures.
- Added official LBA/LNP source directory and an HTTP reachability check API/UI.
- Replaced the scheduled EuroLeague synthetic ingestion task with an Italian source-reachability-only task, so it will not persist fake games as live data.
- Added PostgreSQL seed and idempotent migration for LBA/A2 reference rows.
- Added tests for competition scoping, source metadata, source check behavior, and invalid competition IDs.
- Backend verification: 29 tests passing.
- Frontend build and Docker Compose runtime could not be verified in the build environment (npm install timed out; Docker CLI is unavailable).

## v11.2
- LBA CSV import inventory endpoint and dashboard panel.
- Added test for real-file inventory and explicit raw-data semantics.
- Backend tests: 34 passed.

## v11.3 — aggiornamento automatico stagione corrente
- Dashboard con aggiornamento manuale e polling automatico: NBA ogni 60 secondi, controllo import LBA ogni 5 minuti.
- I dati NBA riportano ora timestamp del controllo e stagione 2026/27.
- Nessun backfill storico: il flusso si concentra su calendario/risultati correnti. Le statistiche avanzate restano demo finché non sono normalizzati box score verificati.


## v11.4 — stagione corrente e analytics LBA
- Default import stagione LBA aggiornato a 2026-2027 e isolato in una sottocartella stagionale.
- Aggiunto endpoint analytics LBA con mapping conservativo di statistiche giocatore per partita e deduplicazione degli stessi game/player tra CSV.
- Esclusione dei file esplicitamente appartenenti a stagioni precedenti.
- La dashboard espone le medie reali solo quando la granularità è verificabile.


## v11.6 — compatibilità con il vero export BasketballScrapeR
- Riconosciuto il formato `Pbox.csv` realmente prodotto dallo scraper: i dati sono aggregati per giocatore e contengono `GP`, `PTS`, `P2M/P2A`, `P3M/P3A`, `OREB/DREB`, `AST`, `TOV`, `STL`, `BLK` e `PM`.
- Calcolate medie per partita da totali stagione / `GP` solo per questo schema noto; gli schemi ambigui restano non verificati.
- L'inventario CSV ora include le sottocartelle `LBA/2627/` create dallo scraper.
- Aggiunti test per Pbox, esclusione della stagione precedente e inventario annidato.


## v11.6 — tabellini NBA e pannello LBA pronto per verifica
- Nuovo adapter `GET /api/v1/live/nba/boxscore/{event_id}` per leggere dal riepilogo ESPN il tabellino giocatore della partita selezionata. Errori fonte e tabellini non disponibili sono stati separati dai dati reali; nessun fallback sintetico.
- La dashboard consente di selezionare una partita NBA e visualizzare MIN, PTS, REB, AST, STL, BLK e palle perse, quando forniti dalla fonte.
- Lo stato connettori conta anche i CSV nelle sottocartelle stagionali.
- Test backend: 43 superati; compilazione Python verificata.
- Limite: il collegamento esterno non è stato provato end-to-end perché la rete di questo ambiente non risolve i domini; build frontend non verificata perché `node_modules` non è presente.

## v11.7 — verifica import LBA
- Aggiunto `scripts/validate_lba_import.py`: controlla inventario CSV, dati riconosciuti per la stagione 2026/27 e granularità delle statistiche.
- Produce un report JSON leggibile da persone e automazioni, con prossima azione consigliata.
- Exit code `0` quando sono riconosciuti dati statistici correnti; `2` quando mancano dati o lo schema non è riconosciuto.
- Il report mantiene `publication_ready: false`: dati riconosciuti non equivalgono automaticamente a dati verificati contro una fonte ufficiale.
- Aggiunti due test automatizzati per import valido e cartella vuota.

## v11.8 — risultati LBA e classifica calcolata

- Aggiunto snapshot dei 24 risultati conclusi delle prime tre giornate LBA 2026/27, con URL e tipo di fonte su ogni partita.
- Distinte le fonti secondarie (giornate 1–2) dalla pagina LBA (giornata 3); il pacchetto dichiara esplicitamente che lo snapshot non è un feed live.
- Nuovi endpoint `GET /api/v1/live/lba/results` e `GET /api/v1/live/lba/standings`.
- La classifica è calcolata dai risultati importati: vittorie, sconfitte, punti segnati/subiti, differenza e punti in classifica.
- La dashboard LBA mostra la classifica calcolata separatamente dalle statistiche giocatore, che restano in attesa di box score verificati.
- Il preflight JSON ora include anche conteggio partite/giornate e prime tre squadre.
- Test aggiunti per completezza 24 gare/16 squadre, calcolo classifica, righe invalide, file mancante e API.

## v11.9 — pipeline di aggiornamento dati più affidabile
- Il worker NBA aggiorna sia la data corrente sia quella precedente nel fuso `America/New_York`, così le partite serali USA non vengono perse quando la data UTC è già cambiata.
- Corretto il volume Docker del worker: i risultati LBA aggiornati vengono scritti nel medesimo `data/lba/results_2026-27.csv` letto dall'API, non in un filesystem isolato del container.
- Esplicitato `LBA_RESULTS_CSV` nel worker per mantenere un percorso condiviso e configurabile.
- Aggiunti test per refresh NBA su due date, sostituzione atomica dello snapshot LBA e conservazione dei dati precedenti se la fonte restituisce dati incompleti.
- Test backend: 57 superati.
- Limite ancora presente: il parser LBA non è stato verificato contro una risposta live dall'ambiente di sviluppo; la compilazione frontend e Docker Compose vanno ancora eseguiti su un host con Docker e accesso alla rete.

## v12.0 — NBA snapshot fallback (2026-10-21)
- Successful NBA scoreboard responses are saved atomically to a local JSON snapshot.
- If ESPN is unreachable, the API attempts to serve today's saved snapshot (then yesterday's) instead of returning an empty list.
- Cached results are explicitly marked `CACHED_SNAPSHOT`, include a stale-data warning, and are not mislabeled as live.
- Dashboard status now distinguishes live data, cached data, and source/API failures.
- Validation: backend test suite passes (58 tests). Frontend production build not run in this environment because web dependencies are not installed and network access is unavailable.

## v13.0 — NBA Analytics Lab 26/27 (2026-10-31)
- NBA-first dashboard and advanced current-season player leaderboard.
- ESPN box score normalization now derives eFG%, TS%, AST/TO and points/minute at game level.
- Completed game box scores are persisted atomically under `data/nba/boxscores/2026-27`.
- New season aggregation endpoint: `/api/v1/live/nba/players/advanced`.
- NBA data refresh scheduled daily at 08:00 Europe/Rome and now archives final box scores from the checked scoreboard days.
- Backend tests: 61 passing.
- Frontend build and Docker Compose smoke test remain unverified because Node dependencies are not installed and Docker is unavailable in the build environment.

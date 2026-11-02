# Stato implementazione — v10 Italian Basketball Analytics

## Implementato
- Dashboard web italiana responsive con selezione LBA / Serie A2.
- Leaderboard filtrate per competizione, profili giocatore e Shot Selection Studio.
- Dati di esempio esplicitamente marcati come sintetici.
- Collegamenti a calendari/fonti ufficiali LBA e LNP.
- Endpoint API per elenco fonti e verifica di raggiungibilità HTTP.
- Worker Celery notturno che verifica le fonti senza pubblicare dati fittizi come dati reali.
- Seed PostgreSQL per le due competizioni e club dimostrativi.
- Test API aggiunti per separazione competizioni, marcatura demo, fonti e competizioni non valide.

## Da completare per dati live reali
1. Verificare condizioni d'uso e accesso automatizzabile delle fonti.
2. Implementare un adapter LBA per calendario/tabellini e mappatura verso lo schema canonico.
3. Implementare un adapter LNP per Serie A2, gestendo differenze di formato.
4. Aggiungere test con fixture reali anonimizzate e controlli su duplicati, rinvii e statistiche mancanti.
5. Attivare import pianificato solo dopo validazione e test di integrazione.

## Limiti attuali
La dashboard non va considerata un feed statistico live. Tutti i numeri dei giocatori e i tiri sono sintetici. Il controllo fonti verifica la risposta HTTP, non garantisce che i dati siano scaricabili o riutilizzabili.

## v11.2 — aggiornamento
- Endpoint diagnostico per inventario dei CSV LBA (file, righe, colonne).
- Dashboard LBA mostra stato dell'import senza spacciare righe grezze per statistiche normalizzate.
- Suite backend: 34 test superati.
- Da completare: normalizzazione dei CSV BasketballScrapeR, box score/statistiche individuali NBA, build frontend e test end-to-end Docker.

## v11.3 update policy
- Frontend refreshes NBA live scoreboard every 60 seconds and supports manual refresh.
- Frontend refreshes LBA CSV import inventory every 5 minutes; this is an inventory check, not yet a verified statistical ingestion.
- NBA live payload exposes season `2026/27` and UTC `checked_at`. Historical backfill is out of scope.
- NBA box scores/player stats and canonical LBA game/player normalization remain incomplete.


## v11.6 — compatibilità Pbox LBA
- Backend: normalizzazione del formato aggregato `Pbox.csv` di BasketballScrapeR e calcolo di medie basate su GP.
- Backend: inventario ricorsivo dei CSV annidati nelle cartelle stagionali.
- Test: 41 test backend attesi superati dopo questa modifica.
- Limite residuo: serve eseguire l'importazione reale via rete per confermare i tre turni della stagione 2026/27 in questo ambiente; non sono stati inseriti risultati manuali o sintetici.


## v11.6 — tabellini NBA
- Aggiunto adapter box score ESPN per evento NBA, con normalizzazione delle principali statistiche individuali.
- Dashboard: cliccando una partita NBA si apre il pannello tabellino, aggiornabile manualmente.
- Suite backend: 43 test superati.
- Da verificare con rete reale: risposta effettiva dell'endpoint ESPN e build Next.js; la rete di build non ha risolto i domini e non sono disponibili le dipendenze frontend locali.

## v11.7 — LBA import preflight
- Added `scripts/validate_lba_import.py` for a repeatable import check.
- JSON report includes CSV inventory, recognized player count, stat-grain counts, publication safety flag and next action.
- Exit status distinguishes usable recognized stats (0) from missing/unrecognized data (2).
- Test suite: 45 backend tests passing.
- Still not complete: no real BasketballScrapeR CSVs were downloaded in this environment; current LBA data are not yet promoted into verified results/standings.

## v12.0 — snapshot risultati LBA e classifica

- Inseriti 24 risultati conclusi delle giornate 1–3 della stagione 2026/27, con fonte per riga e distinzione `official`/`secondary`.
- Aggiunto `app.lba_results` con validazione CSV, esclusione dei risultati non conclusi, quarantena delle righe non valide e calcolo classifica.
- API: `/api/v1/live/lba/results` e `/api/v1/live/lba/standings`.
- Dashboard: tabella classifica LBA reale derivata dallo snapshot, distinta dalle statistiche individuali demo.
- Stato trasparente: è un import statico curato, non un aggiornamento live. Le giornate 1–2 hanno fonte secondaria; la giornata 3 è collegata alla pagina LBA.
- Non verificato in questo ambiente: build Next.js completa e aggiornamento automatico direttamente dai siti fonte. I dati individuali e shot chart restano demo/da verificare.

## v12.0 — dati automatici
- [x] Refresh NBA per data corrente e precedente (fuso America/New_York)
- [x] Snapshot risultati LBA condiviso tra worker e API tramite volume Docker
- [x] Validazione e sostituzione atomica dello snapshot LBA
- [x] Test regressione refresh: 57 test backend superati
- [ ] Verifica live del parser LBA su risposta reale
- [ ] Smoke test end-to-end con Docker Compose e frontend nel browser
- [ ] Conferma del refresh programmato in ambiente ospitato


## v12.1 — verifica post-avvio
- Aggiunto `scripts/smoke_test.sh` per controllare health, scoreboard NBA, stato refresh e classifica LBA dopo l'avvio Docker.
- Aggiunta guida `SMOKE_TEST.md` con interpretazione di `LIVE_SOURCE`, `CACHED_SNAPSHOT` e `SOURCE_UNAVAILABLE`.
- Verificato in ambiente di lavoro: suite backend 58/58 test superati; archivio ZIP integro.
- Non verificato qui: build Next.js, avvio Docker completo e chiamata live a ESPN dall'applicazione.


## NBA Analytics Lab 26/27 — avanzamento 2026-10-31

- Dashboard predefinita sulla sezione NBA e copy riallineato al prodotto NBA Analytics Lab.
- Box score ESPN: normalizzazione di FGM/FGA, 3PM/3PA, FTM/FTA e metriche di partita eFG%, TS%, AST/TO e punti/minuto.
- Nuovo endpoint `GET /api/v1/live/nba/players/advanced`: aggrega medie e metriche avanzate esclusivamente dai box score reali salvati nella cartella `data/nba/boxscores/2026-27`. Nessun dato demo viene promosso.
- Refresh NBA: oltre agli scoreboard di oggi/ieri in Eastern Time, salva atomicamente i box score delle partite concluse; i tabellini già acquisiti non vengono riscaricati.
- Frontend: leaderboard avanzata di stagione con copertura esplicita (numero partite) e metriche PTS/REB/AST, eFG%, TS%, AST/TO e PTS/36.
- Scheduler Celery impostato su `Europe/Rome`, ogni giorno alle 08:00. Il refresh manuale/periodico della dashboard resta separato dall'acquisizione pianificata.
- Test backend: 61/61 superati. Build Next.js e smoke test Docker non ancora eseguiti in questo ambiente.

### Limiti ancora aperti
- L'aggregazione stagionale cresce dalle partite che il job riesce a salvare; per una stagione già iniziata serve un backfill una tantum delle partite precedenti non ancora archiviate.
- Team ratings completi (ORtg/DRtg/Pace/Four Factors) richiedono team box score e calcolo per gara.
- Lineup Lab e shot charts non sono ancora alimentati da dati NBA reali; le schermate demo devono rimanere etichettate come tali finché non arriva una fonte verificata.
- Il job delle 08:00 diventa automatico solo quando il progetto viene avviato su un host persistente con worker, Redis e Celery Beat attivi.

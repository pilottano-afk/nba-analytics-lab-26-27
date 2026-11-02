# LBA risultati — stagione 2026/27

`results_2026-27.csv` contiene i 24 risultati conclusi delle prime tre giornate disponibili al 13 ottobre 2026.

- Giornata 1 e 2: riepiloghi giornalistici di PianetaBasket (URL memorizzato su ogni riga).
- Giornata 3: calendario/risultati LBA (URL memorizzato su ogni riga).
- Ogni record conserva il collegamento alla fonte e `source_type` per distinguere fonte ufficiale e secondaria.
- I risultati sono stati inseriti in uno snapshot CSV verificabile, non recuperati automaticamente dalla fonte durante l'esecuzione.
- L'API calcola la classifica solo da questi record conclusi e validati; partite senza risultato, pareggi o righe malformate sono escluse/segnalate.
- Prima della pubblicazione definitiva occorre un confronto indipendente con la fonte LBA e predisporre un processo di aggiornamento automatico.

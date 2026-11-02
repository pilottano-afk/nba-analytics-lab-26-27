#!/usr/bin/env python3
"""Validate current-season LBA CSV imports and emit a machine-readable report.

This is a preflight tool, not a scraper: it never downloads or fabricates statistics.
Exit codes: 0 = usable recognized stats, 2 = missing/unrecognized current-season data.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1] / "apps" / "api"
sys.path.insert(0, str(API_DIR))
from app.providers import lba_csv_summary, lba_current_analytics  # noqa: E402
from app.lba_results import lba_standings  # noqa: E402


def build_report(data_dir: str | Path) -> dict:
    root = Path(data_dir).expanduser().resolve()
    inventory = lba_csv_summary(root)
    analytics = lba_current_analytics(root)
    standings = lba_standings()
    grains: dict[str, int] = {}
    for player in analytics.get("players", []):
        grain = player.get("stat_grain", "unknown")
        grains[grain] = grains.get(grain, 0) + 1
    recognized = analytics.get("recognized_files", [])
    status = analytics.get("data_status", "NO_IMPORTED_DATA")
    if standings.get("game_count", 0) > 0 and analytics.get("player_count", 0) == 0:
        next_action = "Risultati LBA importati per il calendario corrente; importare e verificare anche i box score giocatore per attivare le statistiche individuali."
        exit_code = 2
    elif status == "LIVE_SOURCE" and analytics.get("player_count", 0) > 0:
        next_action = "Dati riconosciuti: controllare la stagione e confrontare alcuni record con la fonte originale prima di pubblicarli."
        exit_code = 0
    elif inventory.get("files_found", 0) > 0:
        next_action = "CSV presenti ma statistiche correnti non riconosciute: controllare colonne e cartella stagione (2026-2027 / 2627)."
        exit_code = 2
    else:
        next_action = "Nessun CSV trovato: eseguire scripts_import_basketballscraper.sh 2026-2027 su una macchina con rete."
        exit_code = 2
    return {
        "league": "LBA",
        "season": "2026/27",
        "data_dir": str(root),
        "status": status,
        "inventory": {
            "files_found": inventory.get("files_found", 0),
            "total_rows": inventory.get("total_rows", 0),
            "files": inventory.get("files", []),
        },
        "analytics": {
            "player_count": analytics.get("player_count", 0),
            "recognized_files": recognized,
            "stat_grains": grains,
            "message": analytics.get("message"),
        },
        "results_import": {
            "data_status": standings.get("data_status"),
            "games": standings.get("game_count", 0),
            "teams": standings.get("team_count", 0),
            "rounds_covered": standings.get("rounds_covered", []),
            "source_types": standings.get("source_types", []),
            "top_three": [{"rank": row["rank"], "team": row["team"], "wins": row["wins"], "losses": row["losses"], "league_points": row["league_points"]} for row in standings.get("standings", [])[:3]],
            "note": standings.get("note"),
        },
        "publication_ready": False,
        "publication_note": "Il riconoscimento automatico non sostituisce la verifica contro una fonte ufficiale; risultati e classifica non vengono generati da questo report.",
        "next_action": next_action,
        "exit_code": exit_code,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=os.getenv("BASKETBALLSCRAPER_DATA_DIR", "./data/basketballscraper"),
                        help="Cartella contenente i CSV BasketballScrapeR (default: BASKETBALLSCRAPER_DATA_DIR o ./data/basketballscraper)")
    parser.add_argument("--output", help="Salva anche il report JSON in questo percorso")
    args = parser.parse_args()
    report = build_report(args.data_dir)
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    print(serialized)
    if args.output:
        output = Path(args.output).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized + "\n", encoding="utf-8")
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())

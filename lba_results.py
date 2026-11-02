"""Season-scoped LBA completed-game import and standings calculator."""
from __future__ import annotations
import csv
import os
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone

DEFAULT_RESULTS = Path(__file__).resolve().parents[3] / "data" / "lba" / "results_2026-27.csv"
REQUIRED = {"season", "round", "date", "home_team", "away_team", "home_score", "away_score", "status", "source_url", "source_type"}


def load_lba_results(data_file: str | Path | None = None) -> dict:
    path = Path(data_file or os.getenv("LBA_RESULTS_CSV", str(DEFAULT_RESULTS))).expanduser()
    games, errors, seen = [], [], set()
    if not path.is_file():
        return {"league": "LBA", "season": "2026/27", "data_status": "NO_IMPORTED_DATA", "source_file": str(path), "games": [], "game_count": 0, "errors": ["RESULTS_FILE_NOT_FOUND"], "checked_at": datetime.now(timezone.utc).isoformat()}
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            columns = set(reader.fieldnames or [])
            missing = sorted(REQUIRED - columns)
            if missing:
                return {"league": "LBA", "season": "2026/27", "data_status": "INVALID_SCHEMA", "source_file": str(path), "games": [], "game_count": 0, "errors": ["MISSING_COLUMNS:" + ",".join(missing)], "checked_at": datetime.now(timezone.utc).isoformat()}
            for line, raw in enumerate(reader, start=2):
                row = {k: (v or "").strip() for k, v in raw.items() if k}
                if row["season"] != "2026/27":
                    continue
                if row["status"].lower() not in {"final", "completed", "conclusa"}:
                    continue
                try:
                    date = datetime.strptime(row["date"], "%Y-%m-%d").date().isoformat()
                    rnd = int(row["round"])
                    hs, aws = int(row["home_score"]), int(row["away_score"])
                    if rnd < 1 or hs < 0 or aws < 0 or hs == aws:
                        raise ValueError("invalid round or score")
                    if not row["home_team"] or not row["away_team"] or row["home_team"] == row["away_team"] or not row["source_url"]:
                        raise ValueError("missing team or source")
                except (ValueError, TypeError):
                    errors.append(f"INVALID_ROW:{line}")
                    continue
                key = (date, row["home_team"], row["away_team"])
                if key in seen:
                    errors.append(f"DUPLICATE_GAME:{line}")
                    continue
                seen.add(key)
                games.append({"season": row["season"], "round": rnd, "date": date, "home_team": row["home_team"], "away_team": row["away_team"], "home_score": hs, "away_score": aws, "status": "final", "source_url": row["source_url"], "source_type": row["source_type"] or "unspecified"})
    except (OSError, UnicodeError, csv.Error):
        errors.append("CSV_READ_ERROR")
    games.sort(key=lambda g: (g["round"], g["date"], g["home_team"]))
    return {"league": "LBA", "season": "2026/27", "data_status": "IMPORTED_SNAPSHOT" if games and not errors else "PARTIAL_IMPORT" if games else "INVALID_DATA" if errors else "NO_IMPORTED_DATA", "source_file": str(path), "games": games, "game_count": len(games), "errors": errors, "rounds_covered": sorted({g["round"] for g in games}), "source_types": sorted({g["source_type"] for g in games}), "checked_at": datetime.now(timezone.utc).isoformat(), "note": "Snapshot iniziale compilato manualmente da fonti pubblicate; non è un feed live e l’aggiornamento automatico non è ancora attivo."}


def lba_standings(data_file: str | Path | None = None) -> dict:
    result = load_lba_results(data_file)
    stats = defaultdict(lambda: {"team": "", "games_played": 0, "wins": 0, "losses": 0, "points_for": 0, "points_against": 0, "league_points": 0})
    for g in result["games"]:
        h, a = g["home_team"], g["away_team"]
        for name, pf, pa in ((h, g["home_score"], g["away_score"]), (a, g["away_score"], g["home_score"])):
            s = stats[name]; s["team"] = name; s["games_played"] += 1; s["points_for"] += pf; s["points_against"] += pa
            if pf > pa: s["wins"] += 1; s["league_points"] += 2
            else: s["losses"] += 1
    rows = []
    for s in stats.values():
        s["point_difference"] = s["points_for"] - s["points_against"]
        s["win_pct"] = round(s["wins"] / s["games_played"], 3) if s["games_played"] else 0
        rows.append(s)
    rows.sort(key=lambda x: (-x["league_points"], -x["point_difference"], -x["points_for"], x["team"].casefold()))
    for i, row in enumerate(rows, start=1): row["rank"] = i
    result.pop("games", None)
    return {**result, "standings": rows, "team_count": len(rows), "standings_basis": "2 punti per vittoria; ordinamento per punti, differenza punti, punti segnati", "note": "La classifica è calcolata esclusivamente dai risultati presenti nel CSV; fonti secondarie sono indicate partita per partita."}

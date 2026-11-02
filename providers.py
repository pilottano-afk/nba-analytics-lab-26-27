"""Live basketball data adapters. Never silently label demo fixtures as live data."""
from __future__ import annotations
import csv
import os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
import json
from typing import Any
import httpx

ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"


def nba_scoreboard(date: str | None = None, client: Any = httpx) -> dict:
    params = {"dates": date} if date else {}
    try:
        response = client.get(ESPN_SCOREBOARD, params=params, timeout=12.0,
                              headers={"User-Agent": "BasketballAnalytics/1.0"})
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        # Serve the last known-good scoreboard when ESPN is temporarily unreachable.
        # Cached data is explicitly labeled and never presented as live.
        cache_dir = Path(os.getenv("NBA_SNAPSHOT_DIR", str(Path(__file__).resolve().parents[3] / "data" / "nba")))
        requested_day = date or datetime.now(ZoneInfo("America/New_York")).strftime("%Y%m%d")
        candidates = [requested_day]
        try:
            candidates.append((datetime.strptime(requested_day, "%Y%m%d").date() - timedelta(days=1)).strftime("%Y%m%d"))
        except ValueError:
            pass
        for day in candidates:
            cached_file = cache_dir / f"scoreboard_{day}.json"
            try:
                cached = json.loads(cached_file.read_text(encoding="utf-8"))
                if isinstance(cached.get("games"), list):
                    cached["data_status"] = "CACHED_SNAPSHOT"
                    cached["cache_used"] = True
                    cached["source_error"] = type(exc).__name__
                    cached["message"] = "Fonte live non disponibile: visualizzati gli ultimi dati salvati, che potrebbero non essere aggiornati."
                    return cached
            except (OSError, ValueError, TypeError):
                continue
        return {"league": "NBA", "data_status": "SOURCE_UNAVAILABLE", "source": ESPN_SCOREBOARD,
                "games": [], "error": type(exc).__name__, "cache_used": False}
    games = []
    for event in payload.get("events", []):
        comp = (event.get("competitions") or [{}])[0]
        competitors = comp.get("competitors", [])
        home = next((x for x in competitors if x.get("homeAway") == "home"), {})
        away = next((x for x in competitors if x.get("homeAway") == "away"), {})
        status = event.get("status", {}).get("type", {})
        games.append({"id": event.get("id"), "date": event.get("date"),
          "status": status.get("description", "Unknown"), "state": status.get("state"),
          "home_team": (home.get("team") or {}).get("displayName"),
          "home_abbreviation": (home.get("team") or {}).get("abbreviation"),
          "home_score": int(home["score"]) if str(home.get("score", "")).isdigit() else None,
          "away_team": (away.get("team") or {}).get("displayName"),
          "away_abbreviation": (away.get("team") or {}).get("abbreviation"),
          "away_score": int(away["score"]) if str(away.get("score", "")).isdigit() else None,
          "venue": (comp.get("venue") or {}).get("fullName")})
    result = {"league": "NBA", "season": "2026/27", "data_status": "LIVE_SOURCE", "source": ESPN_SCOREBOARD,
            "source_date": payload.get("day", {}).get("date"),
            "checked_at": datetime.now(timezone.utc).isoformat(), "games": games}
    # Persist each successful response atomically so later outages do not blank the dashboard.
    cache_dir = Path(os.getenv("NBA_SNAPSHOT_DIR", str(Path(__file__).resolve().parents[3] / "data" / "nba")))
    cache_day = date or result["source_date"] or datetime.now(ZoneInfo("America/New_York")).strftime("%Y%m%d")
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        destination = cache_dir / f"scoreboard_{cache_day}.json"
        temporary = destination.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(destination)
    except OSError:
        # Cache failure must not invalidate a successful live response.
        pass
    return result


def nba_boxscore(event_id: str, client: Any = httpx) -> dict:
    """Fetch and normalize an ESPN NBA event box score by event ID.

    The endpoint is public but unofficial. A source failure is returned explicitly;
    no demo values are substituted.
    """
    if not event_id or not str(event_id).strip() or not str(event_id).isalnum():
        return {"league": "NBA", "event_id": event_id, "data_status": "INVALID_EVENT_ID", "teams": [], "players": [], "player_count": 0}
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"
    try:
        response = client.get(url, params={"event": str(event_id)}, timeout=12.0,
                              headers={"User-Agent": "BasketballAnalytics/1.0"})
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        return {"league": "NBA", "event_id": event_id, "data_status": "SOURCE_UNAVAILABLE",
                "source": url, "teams": [], "players": [], "error": type(exc).__name__,
                "checked_at": datetime.now(timezone.utc).isoformat()}

    boxscore = payload.get("boxscore") or {}
    teams, players = [], []
    for team_block in boxscore.get("players", []) or []:
        team = team_block.get("team") or {}
        team_name = team.get("displayName") or team.get("name")
        team_abbr = team.get("abbreviation")
        teams.append({"name": team_name, "abbreviation": team_abbr})
        for stat_block in team_block.get("statistics", []) or []:
            labels = stat_block.get("names") or stat_block.get("labels") or []
            for athlete_row in stat_block.get("athletes", []) or []:
                athlete = athlete_row.get("athlete") or {}
                raw_stats = athlete_row.get("stats") or []
                stat_map = {str(label).upper(): value for label, value in zip(labels, raw_stats)}
                def val(*names):
                    for name in names:
                        value = stat_map.get(name)
                        if value not in (None, "", "--", "-"):
                            try:
                                return float(str(value).replace("%", ""))
                            except ValueError:
                                return value
                    return None
                def made_attempted(*names):
                    raw = next((stat_map.get(name) for name in names if stat_map.get(name) not in (None, "", "--", "-")), None)
                    if isinstance(raw, str) and "-" in raw:
                        try:
                            made, attempted = raw.split("-", 1)
                            return float(made), float(attempted)
                        except ValueError:
                            return None, None
                    return None, None
                fgm, fga = made_attempted("FG")
                three_pm, three_pa = made_attempted("3PT", "3P")
                ftm, fta = made_attempted("FT")
                minutes = val("MIN", "MP")
                points = val("PTS")
                rebounds = val("REB", "TRB")
                assists = val("AST")
                turnovers = val("TO", "TOV")
                efg = ((fgm + 0.5 * three_pm) / fga) if fga and fga > 0 and three_pm is not None else None
                ts_denom = 2 * (fga + 0.44 * fta) if fga is not None and fta is not None else None
                ts = (points / ts_denom) if ts_denom and ts_denom > 0 and points is not None else None
                ast_to = (assists / turnovers) if assists is not None and turnovers is not None and turnovers > 0 else None
                players.append({
                    "player_id": str(athlete.get("id") or ""),
                    "player": athlete.get("displayName") or athlete.get("fullName"),
                    "team": team_name, "team_abbreviation": team_abbr,
                    "minutes": minutes, "field_goals": val("FG"), "fgm": fgm, "fga": fga,
                    "three_pointers": val("3PT", "3P"), "three_pm": three_pm, "three_pa": three_pa,
                    "free_throws": val("FT"), "ftm": ftm, "fta": fta,
                    "offensive_rebounds": val("OREB", "OR"), "defensive_rebounds": val("DREB", "DR"),
                    "rebounds": rebounds, "assists": assists, "steals": val("STL"),
                    "blocks": val("BLK"), "turnovers": turnovers, "fouls": val("PF"),
                    "points": points, "raw_stats": stat_map,
                    "advanced": {"efg_pct": round(efg, 4) if efg is not None else None,
                                 "ts_pct": round(ts, 4) if ts is not None else None,
                                 "ast_to": round(ast_to, 3) if ast_to is not None else None,
                                 "points_per_minute": round(points / minutes, 3) if points is not None and minutes and minutes > 0 else None},
                })
    event = payload.get("header") or {}
    competition = ((event.get("competitions") or [{}])[0])
    return {"league": "NBA", "event_id": str(event_id), "data_status": "LIVE_SOURCE" if players else "NO_BOX_SCORE",
            "source": url, "event_name": event.get("name"), "date": competition.get("date"),
            "teams": teams, "players": players, "player_count": len(players),
            "analytics_status": "GAME_LEVEL_ADVANCED_DERIVED" if players else "NOT_AVAILABLE",
            "analytics_note": "eFG%, TS%, AST/TO e punti/minuto sono calcolati dal box score della singola partita; non sono ancora medie di stagione né dati di lineup.",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "message": None if players else "La fonte non ha restituito statistiche giocatore per questo evento."}


def nba_season_player_analytics(data_dir: str | Path | None = None) -> dict:
    """Aggregate only persisted, real ESPN box scores for the current NBA season."""
    root = Path(data_dir or os.getenv("NBA_SNAPSHOT_DIR", str(Path(__file__).resolve().parents[3] / "data" / "nba")))
    season_dir = root / "boxscores" / "2026-27"
    aggregates: dict[tuple[str, str], dict[str, Any]] = {}
    game_count = 0
    errors = []
    for path in sorted(season_dir.glob("*.json")) if season_dir.exists() else []:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("data_status") != "LIVE_SOURCE" or not payload.get("players"):
                continue
            game_count += 1
            for player in payload["players"]:
                pid = str(player.get("player_id") or "")
                name = player.get("player")
                team = player.get("team")
                if not pid or not name or not team:
                    continue
                key = (pid, team)
                row = aggregates.setdefault(key, {"player_id": pid, "player": name, "team": team,
                    "games_played": 0, "minutes": 0.0, "points": 0.0, "rebounds": 0.0,
                    "assists": 0.0, "steals": 0.0, "blocks": 0.0, "turnovers": 0.0,
                    "fgm": 0.0, "fga": 0.0, "three_pm": 0.0, "fta": 0.0,
                    "game_ids": []})
                row["games_played"] += 1
                row["game_ids"].append(str(payload.get("event_id") or path.stem))
                for field in ("minutes", "points", "rebounds", "assists", "steals", "blocks", "turnovers", "fgm", "fga", "three_pm", "fta"):
                    value = player.get(field)
                    if isinstance(value, (int, float)):
                        row[field] += float(value)
        except (OSError, ValueError, TypeError) as exc:
            errors.append({"file": path.name, "error": type(exc).__name__})
    players = []
    for row in aggregates.values():
        gp = row["games_played"]
        fga, fta = row["fga"], row["fta"]
        ts_denom = 2 * (fga + 0.44 * fta)
        row["per_game"] = {field: round(row[field] / gp, 2) for field in
            ("minutes", "points", "rebounds", "assists", "steals", "blocks", "turnovers")}
        row["advanced"] = {
            "efg_pct": round((row["fgm"] + 0.5 * row["three_pm"]) / fga, 4) if fga > 0 else None,
            "ts_pct": round(row["points"] / ts_denom, 4) if ts_denom > 0 else None,
            "ast_to": round(row["assists"] / row["turnovers"], 3) if row["turnovers"] > 0 else None,
            "points_per_36": round(row["points"] * 36 / row["minutes"], 2) if row["minutes"] > 0 else None,
        }
        row["game_ids"] = sorted(set(row["game_ids"]))
        players.append(row)
    players.sort(key=lambda x: x["per_game"]["points"], reverse=True)
    return {"league": "NBA", "season": "2026/27", "data_status": "LIVE_SOURCE" if players else "NO_IMPORTED_BOXSCORES",
        "source": "ESPN public event summary box scores", "games_aggregated": game_count,
        "player_count": len(players), "players": players, "errors": errors,
        "message": None if players else "Nessun tabellino NBA verificato salvato per la stagione 2026/27."}


def lba_csv_games(data_dir: str | Path | None = None) -> dict:
    """Read real CSV exports produced by BasketballScrapeR; no synthetic fallback."""
    root = Path(data_dir or os.getenv("BASKETBALLSCRAPER_DATA_DIR", "./data/basketballscraper"))
    files = sorted(root.rglob("*.csv")) if root.exists() else []
    rows = []
    for path in files:
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    normalized = {str(k).strip().lower(): (v.strip() if isinstance(v, str) else v)
                                  for k, v in row.items() if k is not None}
                    # Keep source columns intact because BasketballScrapeR CSV schemas vary by export.
                    rows.append({"source_file": path.name, "source_row": normalized})
        except (OSError, UnicodeError, csv.Error):
            continue
    return {"league": "LBA", "data_status": "LIVE_SOURCE" if rows else "NO_IMPORTED_DATA",
            "source": "BasketballScrapeR CSV export", "data_dir": str(root),
            "files_found": len(files), "rows": rows,
            "message": None if rows else "Nessun CSV trovato. Esegui lo scraper e configura BASKETBALLSCRAPER_DATA_DIR."}


def lba_csv_summary(data_dir: str | Path | None = None) -> dict:
    """Return an import inventory for real BasketballScrapeR CSV files, without guessing their schema."""
    root = Path(data_dir or os.getenv("BASKETBALLSCRAPER_DATA_DIR", "./data/basketballscraper"))
    files = []
    total_rows = 0
    for path in sorted(root.rglob("*.csv")) if root.exists() else []:
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                columns = [str(c).strip() for c in (reader.fieldnames or [])]
                row_count = sum(1 for _ in reader)
            files.append({"name": str(path.relative_to(root)), "rows": row_count, "columns": columns})
            total_rows += row_count
        except (OSError, UnicodeError, csv.Error):
            files.append({"name": str(path.relative_to(root)), "rows": 0, "columns": [], "error": "CSV_READ_ERROR"})
    return {
        "league": "LBA",
        "data_status": "LIVE_SOURCE" if total_rows else "NO_IMPORTED_DATA",
        "source": "BasketballScrapeR CSV export",
        "data_dir": str(root),
        "files_found": len(files),
        "total_rows": total_rows,
        "files": files,
        "message": None if total_rows else "Nessun record CSV leggibile. Esegui lo scraper e controlla il percorso dati."
    }


# Canonical stat aliases are intentionally conservative: a column is mapped only when
# its name clearly identifies the metric. Unknown CSV layouts remain raw data.
_STAT_ALIASES = {
    "player": ("player", "player_name", "playername", "personname", "name"),
    "team": ("team", "team_name", "teamname", "team_abbreviation", "teamtricode", "club"),
    "games": ("games", "games_played", "gp", "g"),
    "points": ("points", "pts", "point"),
    "rebounds": ("rebounds", "reb", "trb", "total_rebounds"),
    "offensive_rebounds": ("oreb", "offensive_rebounds", "offensiverebounds"),
    "defensive_rebounds": ("dreb", "defensive_rebounds", "defensiverebounds"),
    "two_made": ("p2m", "2pm", "twopointersmade"),
    "two_attempted": ("p2a", "2pa", "twopointersattempted"),
    "two_pct": ("p2p", "2pp", "twopointerspercentage"),
    "three_pct": ("p3p", "3pp", "threepointerspercentage"),
    "ft_pct": ("ftp", "free_throw_percentage", "freethrowpercentage"),
    "assists": ("assists", "ast"),
    "steals": ("steals", "stl"),
    "blocks": ("blocks", "blk"),
    "turnovers": ("turnovers", "tov", "to"),
    "minutes": ("minutes", "min", "mp"),
    "fg_made": ("fgm", "field_goals_made", "fieldgoalsmade"),
    "fg_attempted": ("fga", "field_goals_attempted", "fieldgoalsattempted"),
    "three_made": ("p3m", "3pm", "fg3m", "three_pointers_made", "threepointersmade"),
    "three_attempted": ("p3a", "3pa", "fg3a", "three_pointers_attempted", "threepointersattempted"),
    "ft_made": ("ftm", "free_throws_made", "freethrowsmade"),
    "ft_attempted": ("fta", "free_throws_attempted", "freethrowsattempted"),
}

def _key(value: Any) -> str:
    return "".join(ch for ch in str(value or "").strip().lower() if ch.isalnum())

def _number(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() in {"", "-", "—", "nan", "None"}:
            return None
        return float(str(value).strip().replace(",", "."))
    except (ValueError, TypeError):
        return None

def _map_stats(row: dict[str, Any]) -> dict[str, Any]:
    keyed = {_key(k): v for k, v in row.items()}
    mapped: dict[str, Any] = {}
    for canonical, aliases in _STAT_ALIASES.items():
        for alias in aliases:
            if _key(alias) in keyed:
                value = keyed[_key(alias)]
                mapped[canonical] = value.strip() if isinstance(value, str) else value
                break
    return mapped

def lba_current_analytics(data_dir: str | Path | None = None) -> dict:
    """Normalize recognizable current-season player box-score rows from CSV exports.

    Supports both explicit per-game box-score rows and BasketballScrapeR's Pbox season aggregates.
    BasketballScrapeR Pbox is known to contain totals plus GP; those totals can safely be divided by GP.
    """
    root = Path(data_dir or os.getenv("BASKETBALLSCRAPER_DATA_DIR", "./data/basketballscraper"))
    files = sorted(root.rglob("*.csv")) if root.exists() else []
    game_players: dict[tuple[str, str], dict[str, Any]] = {}
    season_players: dict[tuple[str, str], dict[str, Any]] = {}
    recognized_files: list[str] = []
    current_season_tokens = ("2026-2027", "2026/2027", "2026-27", "2026/27", "2026_2027", "2026_27", "2627")
    older_tokens = ("2024-2025", "2024/2025", "2024-25", "2024/25", "2025-2026", "2025/2026", "2025-26", "2025/26", "2023-2024", "2023/2024", "2023-24", "2526", "2425", "2324")
    for path in files:
        location = str(path.relative_to(root)).lower().replace("\\", "/")
        if any(token in location for token in older_tokens) and not any(token in location for token in current_season_tokens):
            continue
        # BasketballScrapeR names season folders with compact codes such as 2627, 2526.
        compact_season_dirs = [part for part in location.split("/") if len(part) == 4 and part.isdigit()]
        if compact_season_dirs and any(part != "2627" for part in compact_season_dirs) and not any(token in location for token in current_season_tokens):
            continue
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames:
                    continue
                columns = {_key(c) for c in reader.fieldnames}
                if not (any(_key(x) in columns for x in _STAT_ALIASES["player"]) and
                        any(_key(x) in columns for x in _STAT_ALIASES["team"]) and
                        any(_key(x) in columns for x in _STAT_ALIASES["points"])):
                    continue
                # BasketballScrapeR Pbox exports aggregated season totals, not one row per game.
                # Its upstream summarize_players_df groups by Team/Player and computes GP from MIN.
                is_basketballscraper_pbox = (
                    "gp" in columns and "pts" in columns and
                    ("p2m" in columns or "p3m" in columns) and
                    ("oreb" in columns or "dreb" in columns)
                )
                game_key = next((c for c in reader.fieldnames if _key(c) in {"gameid", "matchid", "gamecode"}), None)
                date_key = next((c for c in reader.fieldnames if _key(c) in {"gamedate", "date", "matchdate"}), None)
                season_col = next((c for c in reader.fieldnames if _key(c) in {"season", "seasonname", "seasonyear"}), None)
                for raw in reader:
                    if season_col and raw.get(season_col):
                        season_value = str(raw[season_col]).strip().lower().replace(" ", "")
                        if any(token in season_value for token in older_tokens):
                            continue
                        if any(ch.isdigit() for ch in season_value) and not any(token in season_value for token in current_season_tokens) and "2026" not in location:
                            continue
                    mapped = _map_stats(raw)
                    name, team = str(mapped.get("player") or "").strip(), str(mapped.get("team") or "").strip()
                    if not name or not team:
                        continue
                    key = (name.casefold(), team.casefold())
                    if game_key or date_key:
                        game_id = str((raw.get(game_key) if game_key else raw.get(date_key)) or "").strip()
                        if not game_id:
                            continue
                        item = game_players.setdefault(key, {"player": name, "team": team, "games": {}, "source_files": set()})
                        # One row per player per game is the expected grain. Duplicate exports for the same
                        # player/game are ignored so files copied twice cannot inflate season averages.
                        if game_id not in item["games"]:
                            item["games"][game_id] = {metric: _number(mapped.get(metric)) for metric in
                                ("points", "rebounds", "assists", "steals", "blocks", "turnovers", "minutes")}
                        item["source_files"].add(path.name)
                    else:
                        # Preserve unknown season-level schemas as raw values. For the documented
                        # BasketballScrapeR Pbox schema, GP and all box-score columns are season totals.
                        item = season_players.setdefault(key, {"player": name, "team": team, "source_values": {}, "source_files": set(), "source_rows": 0, "known_aggregate": False})
                        item["source_values"] = {k: mapped[k] for k in ("games", "points", "rebounds", "offensive_rebounds", "defensive_rebounds", "assists", "steals", "blocks", "turnovers", "minutes", "two_made", "two_attempted", "three_made", "three_attempted", "ft_made", "ft_attempted") if k in mapped}
                        if is_basketballscraper_pbox:
                            gp = _number(mapped.get("games"))
                            values = item["source_values"]
                            oreb, dreb = _number(mapped.get("offensive_rebounds")), _number(mapped.get("defensive_rebounds"))
                            if oreb is not None or dreb is not None:
                                values["rebounds"] = (oreb or 0) + (dreb or 0)
                            item["known_aggregate"] = gp is not None and gp > 0
                        item["source_files"].add(path.name)
                        item["source_rows"] += 1
                recognized_files.append(str(path.relative_to(root)))
        except (OSError, UnicodeError, csv.Error):
            continue
    rows = []
    for item in game_players.values():
        game_values = list(item["games"].values())
        gp = len(game_values)
        totals = {metric: round(sum((g[metric] or 0) for g in game_values), 2) for metric in
                  ("points", "rebounds", "assists", "steals", "blocks", "turnovers", "minutes")}
        per_game = {metric: round(totals[metric] / gp, 2) if gp else None for metric in totals}
        rows.append({"player": item["player"], "team": item["team"], "games_played": gp, "totals": totals,
                     "per_game": per_game, "stat_grain": "game_rows", "source_rows": gp,
                     "source_files": sorted(item["source_files"])})
    for key, item in season_players.items():
        if key in game_players:
            continue
        source_values = item["source_values"]
        gp = _number(source_values.get("games"))
        if item.get("known_aggregate") and gp:
            metrics = ("points", "rebounds", "assists", "steals", "blocks", "turnovers", "minutes")
            totals = {metric: round(_number(source_values.get(metric)) or 0, 2) for metric in metrics}
            per_game = {metric: round(totals[metric] / gp, 2) for metric in metrics}
            # BasketballScrapeR publishes shooting makes/attempts as season totals.
            shooting = {}
            for label, made_key, att_key in (("fg_pct", "two_made", "two_attempted"), ("three_pct", "three_made", "three_attempted"), ("ft_pct", "ft_made", "ft_attempted")):
                made = _number(source_values.get(made_key)); attempted = _number(source_values.get(att_key))
                if label == "fg_pct":
                    made3, att3 = _number(source_values.get("three_made")), _number(source_values.get("three_attempted"))
                    made = (made or 0) + (made3 or 0)
                    attempted = (attempted or 0) + (att3 or 0)
                if attempted is not None and attempted > 0 and made is not None:
                    shooting[label] = round(made / attempted, 4)
            rows.append({"player": item["player"], "team": item["team"], "games_played": int(gp),
                         "totals": totals, "per_game": per_game, "shooting": shooting,
                         "source_values": source_values, "stat_grain": "season_aggregate",
                         "source_rows": item["source_rows"], "source_files": sorted(item["source_files"])})
        else:
            rows.append({"player": item["player"], "team": item["team"], "games_played": int(gp) if gp is not None else None,
                         "source_values": source_values, "per_game": None, "stat_grain": "season_row_unverified",
                         "source_rows": item["source_rows"], "source_files": sorted(item["source_files"])})
    rows.sort(key=lambda x: (-(x.get("per_game") or {}).get("points", 0) if x.get("per_game") else 0, x["player"].casefold()))
    game_level_rows = sum(1 for x in rows if x["stat_grain"] in {"game_rows", "season_aggregate"})
    return {"league": "LBA", "season": "2026/27", "data_status": "LIVE_SOURCE" if game_level_rows else "RAW_DATA_ONLY" if files else "NO_IMPORTED_DATA",
        "source": "BasketballScrapeR CSV export", "files_scanned": len(files), "recognized_files": sorted(set(recognized_files)),
        "player_count": len(rows), "players": rows, "checked_at": datetime.now(timezone.utc).isoformat(),
        "message": None if game_level_rows else "Nessun box score o aggregato stagione riconosciuto per la stagione corrente. I file possono avere uno schema non supportato."}

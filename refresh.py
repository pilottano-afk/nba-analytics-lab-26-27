"""Scheduled current-season data refresh with atomic promotion and explicit status."""
from __future__ import annotations
import json, os, shutil, subprocess, sys, tempfile
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any

API_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = API_ROOT.parent.parent if API_ROOT.name == "api" else API_ROOT
STATUS_FILE = Path(os.getenv("BASKETBALL_REFRESH_STATUS", str(PROJECT_ROOT / "data" / "refresh" / "status.json")))
SEASON = os.getenv("BASKETBALL_SEASON", "2026-2027")
LBA_DATA_DIR = Path(os.getenv("BASKETBALLSCRAPER_DATA_DIR", str(PROJECT_ROOT / "data" / "basketballscraper")))
SCRAPER_REPO = Path(os.getenv("BASKETBALLSCRAPER_REPO_DIR", str(PROJECT_ROOT / "vendor" / "BasketballScrapeR")))
SCRAPER_URL = "https://github.com/francescoolivo/BasketballScrapeR.git"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_status() -> dict[str, Any]:
    try:
        return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"updated_at": None, "nba": {"status": "NOT_RUN"}, "lba": {"status": "NOT_RUN"}}


def _write_status(status: dict[str, Any]) -> None:
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATUS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STATUS_FILE)


def refresh_nba_scoreboard(date: str | None = None, fetcher=None) -> dict[str, Any]:
    """Fetch the ESPN public scoreboard and persist only successful source responses."""
    from .providers import nba_scoreboard
    day = date or datetime.now(timezone.utc).strftime("%Y%m%d")
    payload = (fetcher or nba_scoreboard)(date=day)
    if payload.get("data_status") != "LIVE_SOURCE":
        result = {"status": "FAILED", "checked_at": utc_now(), "error": payload.get("error", payload.get("data_status", "SOURCE_UNAVAILABLE")), "source": payload.get("source")}
    else:
        out_dir = Path(os.getenv("NBA_SNAPSHOT_DIR", str(PROJECT_ROOT / "data" / "nba")))
        out_dir.mkdir(parents=True, exist_ok=True)
        destination = out_dir / f"scoreboard_{day}.json"
        tmp = destination.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(destination)
        result = {"status": "SUCCESS", "checked_at": utc_now(), "date": day, "games": len(payload.get("games", [])), "file": str(destination), "source": payload.get("source")}
    status = _read_status(); status["updated_at"] = utc_now(); status["nba"] = result; _write_status(status)
    return result


def refresh_nba_boxscores(days: list[str] | None = None, fetcher=None) -> dict[str, Any]:
    """Persist completed-game box scores atomically for current-season aggregation."""
    from .providers import nba_boxscore
    snapshot_dir = Path(os.getenv("NBA_SNAPSHOT_DIR", str(PROJECT_ROOT / "data" / "nba")))
    requested_days = days or [datetime.now(ZoneInfo("America/New_York")).strftime("%Y%m%d")]
    stored = 0
    skipped = 0
    failed = []
    for day in requested_days:
        scoreboard_file = snapshot_dir / f"scoreboard_{day}.json"
        try:
            scoreboard = json.loads(scoreboard_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            skipped += 1
            continue
        for game in scoreboard.get("games", []):
            if game.get("state") != "post" and str(game.get("status", "")).lower() not in {"final", "game over"}:
                continue
            event_id = str(game.get("id") or "")
            if not event_id or not event_id.isalnum():
                skipped += 1
                continue
            season_dir = snapshot_dir / "boxscores" / "2026-27"
            destination = season_dir / f"{event_id}.json"
            if destination.exists():
                continue
            try:
                payload = (fetcher or nba_boxscore)(event_id=event_id)
                if payload.get("data_status") != "LIVE_SOURCE" or not payload.get("players"):
                    failed.append({"event_id": event_id, "status": payload.get("data_status", "UNKNOWN")})
                    continue
                season_dir.mkdir(parents=True, exist_ok=True)
                temporary = destination.with_suffix(".json.tmp")
                temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                temporary.replace(destination)
                stored += 1
            except Exception as exc:
                failed.append({"event_id": event_id, "error": type(exc).__name__})
    return {"status": "SUCCESS" if not failed else "PARTIAL", "stored": stored, "skipped": skipped,
            "failed": failed, "season": "2026/27", "directory": str(snapshot_dir / "boxscores" / "2026-27")}


def refresh_nba_scoreboards(fetcher=None) -> dict[str, Any]:
    """Refresh today and yesterday in US Eastern time to catch late-night NBA games."""
    eastern_today = datetime.now(ZoneInfo("America/New_York")).date()
    days = [(eastern_today - timedelta(days=1)).strftime("%Y%m%d"), eastern_today.strftime("%Y%m%d")]
    results = [refresh_nba_scoreboard(day, fetcher=fetcher) for day in days]
    successful = [item for item in results if item.get("status") == "SUCCESS"]
    boxscore_result = refresh_nba_boxscores(days=days)
    aggregate = {
        "status": "SUCCESS" if successful else "FAILED",
        "checked_at": utc_now(),
        "timezone": "America/New_York",
        "days_checked": days,
        "successful_days": len(successful),
        "results": results,
        "boxscores": boxscore_result,
        "source": "ESPN public scoreboard JSON + event box scores",
    }
    status = _read_status()
    status["updated_at"] = utc_now()
    status["nba"] = aggregate
    _write_status(status)
    return aggregate


def _ensure_scraper() -> None:
    if not (SCRAPER_REPO / ".git").exists():
        SCRAPER_REPO.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", SCRAPER_URL, str(SCRAPER_REPO)], check=True, timeout=180, capture_output=True, text=True)
    if not (SCRAPER_REPO / "run.py").is_file():
        raise RuntimeError("BasketballScrapeR run.py non trovato nel repository configurato")
    # Install only once per container/repo checkout; failures stop the refresh and preserve prior data.
    marker = SCRAPER_REPO / ".deps-installed"
    if not marker.exists():
        requirements = SCRAPER_REPO / "requirements.txt"
        if requirements.is_file():
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements)], check=True, timeout=300, capture_output=True, text=True)
        marker.write_text(utc_now(), encoding="utf-8")


def refresh_lba_boxscores() -> dict[str, Any]:
    """Run BasketballScrapeR into staging, validate outputs, then promote without wiping last good data."""
    started = utc_now()
    try:
        _ensure_scraper()
        LBA_DATA_DIR.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix="lba-staging-", dir=str(LBA_DATA_DIR.parent)))
        try:
            cmd = [sys.executable, str(SCRAPER_REPO / "run.py"), "-l", "LBA", "-s", SEASON, "-o", str(staging), "--ignore_pbp"]
            completed = subprocess.run(cmd, check=True, timeout=int(os.getenv("LBA_REFRESH_TIMEOUT_SECONDS", "1200")), capture_output=True, text=True)
            csvs = sorted(staging.rglob("*.csv"))
            if not csvs:
                raise RuntimeError("Lo scraper è terminato senza produrre CSV: snapshot precedente conservato")
            summary = []
            for file in csvs:
                # Basic validation: CSV must be non-empty and have a header plus at least one record.
                lines = file.read_text(encoding="utf-8-sig", errors="replace").splitlines()
                if len(lines) < 2 or not lines[0].strip():
                    continue
                summary.append({"name": str(file.relative_to(staging)), "rows": len(lines) - 1, "bytes": file.stat().st_size})
            if not summary:
                raise RuntimeError("CSV prodotti ma nessuno contiene righe dati; snapshot precedente conservato")
            LBA_DATA_DIR.mkdir(parents=True, exist_ok=True)
            promoted = []
            for file in csvs:
                if file.stat().st_size == 0:
                    continue
                relative = file.relative_to(staging)
                target = LBA_DATA_DIR / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                temp_target = target.with_suffix(target.suffix + ".tmp")
                shutil.copy2(file, temp_target)
                temp_target.replace(target)
                promoted.append(str(relative))
            result = {"status": "SUCCESS", "started_at": started, "checked_at": utc_now(), "season": SEASON, "files": summary, "promoted_files": promoted, "source": SCRAPER_URL, "note": "Box score/CSV import aggiornato. I risultati e la classifica derivati da questo output non vengono promossi automaticamente finché lo schema game-level non è verificato."}
            if completed.stderr.strip(): result["scraper_stderr_tail"] = completed.stderr[-1000:]
        finally:
            shutil.rmtree(staging, ignore_errors=True)
    except Exception as exc:
        result = {"status": "FAILED", "started_at": started, "checked_at": utc_now(), "season": SEASON, "error": type(exc).__name__, "message": str(exc)[:500], "note": "Dati già importati non cancellati."}
    status = _read_status(); status["updated_at"] = utc_now(); status["lba"] = result; _write_status(status)
    return result


def refresh_status() -> dict[str, Any]:
    return _read_status()


def refresh_lba_results(fetcher=None) -> dict[str, Any]:
    """Refresh game-level results from LBA's public calendar endpoints and atomically replace CSV."""
    started = utc_now()
    target = Path(os.getenv("LBA_RESULTS_CSV", str(PROJECT_ROOT / "data" / "lba" / "results_2026-27.csv")))
    try:
        from .lba_official import fetch_official_lba_results
        payload = (fetcher or fetch_official_lba_results)()
        games = payload.get("games", [])
        if len(games) < 8 or payload.get("data_status") != "LIVE_SOURCE":
            raise ValueError("Risposta ufficiale incompleta; snapshot precedente conservato")
        import csv
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        fields = ["season", "round", "date", "home_team", "away_team", "home_score", "away_score", "status", "source_url", "source_type"]
        with tmp.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for game in games:
                writer.writerow({key: game[key] for key in fields})
        # Validate the staged file before replacing the last known-good snapshot.
        from .lba_results import load_lba_results
        check = load_lba_results(tmp)
        if check.get("game_count") != len(games) or check.get("errors"):
            tmp.unlink(missing_ok=True)
            raise ValueError("CSV ufficiale non supera la validazione; snapshot precedente conservato")
        tmp.replace(target)
        result = {"status": "SUCCESS", "started_at": started, "checked_at": utc_now(), "season": "2026/27",
                  "games": len(games), "rounds_covered": payload.get("rounds_covered", []), "file": str(target),
                  "source": "https://www.legabasket.it/competizioni", "source_type": "official_lba",
                  "note": "Risultati e classifica possono essere ricalcolati dal CSV verificato."}
    except Exception as exc:
        result = {"status": "FAILED", "started_at": started, "checked_at": utc_now(), "season": "2026/27",
                  "error": type(exc).__name__, "message": str(exc)[:500], "note": "Snapshot risultati precedente conservato."}
    status = _read_status(); status["updated_at"] = utc_now(); status["lba_results"] = result; _write_status(status)
    return result

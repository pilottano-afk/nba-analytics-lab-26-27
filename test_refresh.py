import json
from pathlib import Path
from app import refresh


def test_nba_refresh_persists_only_live_source(monkeypatch, tmp_path):
    monkeypatch.setattr(refresh, "STATUS_FILE", tmp_path / "status.json")
    monkeypatch.setenv("NBA_SNAPSHOT_DIR", str(tmp_path / "nba"))
    def fake_fetcher(date=None):
        return {"league":"NBA", "data_status":"LIVE_SOURCE", "source":"https://example.test/scoreboard", "games":[{"id":"1"}]}
    result = refresh.refresh_nba_scoreboard("20261020", fetcher=fake_fetcher)
    assert result["status"] == "SUCCESS"
    saved = json.loads((tmp_path / "nba" / "scoreboard_20261020.json").read_text())
    assert saved["games"][0]["id"] == "1"
    assert json.loads((tmp_path / "status.json").read_text())["nba"]["status"] == "SUCCESS"


def test_nba_refresh_does_not_persist_source_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(refresh, "STATUS_FILE", tmp_path / "status.json")
    monkeypatch.setenv("NBA_SNAPSHOT_DIR", str(tmp_path / "nba"))
    result = refresh.refresh_nba_scoreboard("20261020", fetcher=lambda date=None: {"data_status":"SOURCE_UNAVAILABLE", "error":"ConnectError"})
    assert result["status"] == "FAILED"
    assert not (tmp_path / "nba" / "scoreboard_20261020.json").exists()


def test_refresh_status_has_explicit_not_run_defaults(monkeypatch, tmp_path):
    monkeypatch.setattr(refresh, "STATUS_FILE", tmp_path / "missing.json")
    status = refresh.refresh_status()
    assert status["nba"]["status"] == "NOT_RUN"
    assert status["lba"]["status"] == "NOT_RUN"


def test_failed_lba_refresh_preserves_existing_snapshot(monkeypatch, tmp_path):
    data_dir = tmp_path / "basketballscraper"
    data_dir.mkdir()
    existing = data_dir / "Pbox.csv"
    existing.write_text("player,points\nPlayer,10\n")
    monkeypatch.setattr(refresh, "STATUS_FILE", tmp_path / "status.json")
    monkeypatch.setattr(refresh, "LBA_DATA_DIR", data_dir)
    monkeypatch.setattr(refresh, "_ensure_scraper", lambda: (_ for _ in ()).throw(RuntimeError("network unavailable")))
    result = refresh.refresh_lba_boxscores()
    assert result["status"] == "FAILED"
    assert "Player,10" in existing.read_text()
    assert json.loads((tmp_path / "status.json").read_text())["lba"]["status"] == "FAILED"


def test_nba_refresh_checks_yesterday_and_today_in_eastern_time(monkeypatch, tmp_path):
    monkeypatch.setattr(refresh, "STATUS_FILE", tmp_path / "status.json")
    monkeypatch.setenv("NBA_SNAPSHOT_DIR", str(tmp_path / "nba"))
    seen = []
    def fake_fetcher(date=None):
        seen.append(date)
        return {"league": "NBA", "data_status": "LIVE_SOURCE", "source": "https://example.test/scoreboard", "games": []}
    result = refresh.refresh_nba_scoreboards(fetcher=fake_fetcher)
    assert len(seen) == 2
    assert seen == result["days_checked"]
    assert result["successful_days"] == 2
    saved = json.loads((tmp_path / "status.json").read_text())
    assert saved["nba"]["status"] == "SUCCESS"
    assert len(saved["nba"]["results"]) == 2


def test_lba_results_refresh_atomically_replaces_snapshot(monkeypatch, tmp_path):
    target = tmp_path / "results.csv"
    target.write_text("old snapshot", encoding="utf-8")
    monkeypatch.setattr(refresh, "STATUS_FILE", tmp_path / "status.json")
    monkeypatch.setenv("LBA_RESULTS_CSV", str(target))
    games = []
    for i in range(8):
        games.append({"season":"2026/27", "round":1, "date":f"2026-10-{10+i:02d}",
          "home_team":f"Home {i}", "away_team":f"Away {i}", "home_score":80+i,
          "away_score":70, "status":"final", "source_url":"https://example.test/game/"+str(i),
          "source_type":"official_lba", "game_id":str(i)})
    result = refresh.refresh_lba_results(fetcher=lambda: {"data_status":"LIVE_SOURCE", "games":games, "rounds_covered":[1]})
    assert result["status"] == "SUCCESS"
    from app.lba_results import load_lba_results
    imported = load_lba_results(target)
    assert imported["game_count"] == 8
    assert imported["data_status"] == "IMPORTED_SNAPSHOT"
    assert "old snapshot" not in target.read_text(encoding="utf-8")


def test_lba_results_refresh_preserves_snapshot_when_source_incomplete(monkeypatch, tmp_path):
    target = tmp_path / "results.csv"
    target.write_text("existing good data", encoding="utf-8")
    monkeypatch.setattr(refresh, "STATUS_FILE", tmp_path / "status.json")
    monkeypatch.setenv("LBA_RESULTS_CSV", str(target))
    result = refresh.refresh_lba_results(fetcher=lambda: {"data_status":"LIVE_SOURCE", "games":[{}]})
    assert result["status"] == "FAILED"
    assert target.read_text(encoding="utf-8") == "existing good data"
    status = json.loads((tmp_path / "status.json").read_text())
    assert status["lba_results"]["status"] == "FAILED"

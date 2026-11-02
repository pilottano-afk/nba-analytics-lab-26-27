from app.providers import nba_scoreboard, lba_csv_games

class FakeResponse:
    def raise_for_status(self): pass
    def json(self):
        return {"day":{"date":"2026-10-12"},"events":[{"id":"g1","date":"2026-10-12T23:00Z",
          "status":{"type":{"description":"Final","state":"post"}},
          "competitions":[{"venue":{"fullName":"Arena"},"competitors":[
            {"homeAway":"home","score":"101","team":{"displayName":"Boston Celtics","abbreviation":"BOS"}},
            {"homeAway":"away","score":"99","team":{"displayName":"New York Knicks","abbreviation":"NYK"}}]}]}]}
class FakeClient:
    @staticmethod
    def get(*args, **kwargs): return FakeResponse()

def test_nba_scoreboard_maps_real_source_payload():
    result=nba_scoreboard(client=FakeClient)
    assert result["data_status"] == "LIVE_SOURCE"
    assert result["season"] == "2026/27"
    assert result["checked_at"].endswith("+00:00")
    assert result["games"][0]["home_score"] == 101
    assert result["games"][0]["away_abbreviation"] == "NYK"

def test_nba_scoreboard_uses_explicitly_labeled_cached_snapshot_on_source_failure(tmp_path, monkeypatch):
    import json
    monkeypatch.setenv("NBA_SNAPSHOT_DIR", str(tmp_path))
    (tmp_path / "scoreboard_20261021.json").write_text(json.dumps({
        "league": "NBA", "season": "2026/27", "data_status": "LIVE_SOURCE",
        "source": "ESPN", "games": [{"id": "saved-game", "home_score": 100}]
    }), encoding="utf-8")
    class FailingClient:
        @staticmethod
        def get(*args, **kwargs):
            raise OSError("network unavailable")
    result = nba_scoreboard(date="20261021", client=FailingClient)
    assert result["data_status"] == "CACHED_SNAPSHOT"
    assert result["cache_used"] is True
    assert result["games"][0]["id"] == "saved-game"
    assert "potrebbero non essere aggiornati" in result["message"]


def test_lba_import_reads_csv(tmp_path):
    (tmp_path/"games.csv").write_text("home,away,home_score,away_score\nMilano,Bologna,80,75\n", encoding="utf-8")
    result=lba_csv_games(tmp_path)
    assert result["data_status"] == "LIVE_SOURCE"
    assert result["files_found"] == 1
    assert result["rows"][0]["source_row"]["home"] == "Milano"

def test_lba_import_does_not_fabricate_data(tmp_path):
    result=lba_csv_games(tmp_path)
    assert result["data_status"] == "NO_IMPORTED_DATA"
    assert result["rows"] == []


def test_live_endpoints_disable_long_cache():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    response = client.get("/api/v1/live/lba/imported", params={"data_dir": "/tmp/definitely-no-basketball-data"})
    assert response.status_code == 200
    assert "no-store" in response.headers.get("cache-control", "")



def test_lba_summary_reports_file_inventory_without_inventing_stats(tmp_path):
    (tmp_path/"players.csv").write_text("player,points\nA Player,12\nB Player,8\n", encoding="utf-8")
    from app.providers import lba_csv_summary
    result = lba_csv_summary(tmp_path)
    assert result["data_status"] == "LIVE_SOURCE"
    assert result["files_found"] == 1
    assert result["total_rows"] == 2
    assert result["files"][0]["columns"] == ["player", "points"]
    assert "leaderboard" not in result


def test_lba_analytics_aggregates_only_recognized_game_rows(tmp_path):
    from app.providers import lba_current_analytics
    (tmp_path / "lba-2026-27.csv").write_text(
        "game_id,player_name,team_name,PTS,REB,AST\n"
        "g1,Giocatore Uno,Milano,10,4,3\n"
        "g2,Giocatore Uno,Milano,20,6,5\n", encoding="utf-8")
    result = lba_current_analytics(tmp_path)
    assert result["data_status"] == "LIVE_SOURCE"
    assert result["player_count"] == 1
    player = result["players"][0]
    assert player["games_played"] == 2
    assert player["totals"]["points"] == 30
    assert player["per_game"]["points"] == 15
    assert player["stat_grain"] == "game_rows"


def test_lba_analytics_does_not_guess_season_row_metric_grain(tmp_path):
    from app.providers import lba_current_analytics
    (tmp_path / "players.csv").write_text(
        "player_name,team_name,GP,PTS,REB\nGiocatore Uno,Milano,3,15,5\n", encoding="utf-8")
    result = lba_current_analytics(tmp_path)
    assert result["data_status"] == "RAW_DATA_ONLY"
    assert result["players"][0]["per_game"] is None
    assert result["players"][0]["source_values"]["points"] == "15"


def test_lba_analytics_skips_explicit_old_season_files(tmp_path):
    from app.providers import lba_current_analytics
    (tmp_path / "2025-2026").mkdir()
    (tmp_path / "2025-2026" / "players.csv").write_text(
        "game_id,player_name,team_name,PTS\ng1,Old Player,Milano,40\n", encoding="utf-8")
    result = lba_current_analytics(tmp_path)
    assert result["data_status"] == "RAW_DATA_ONLY"
    assert result["players"] == []


def test_lba_analytics_combines_games_across_separate_csv_files_without_double_counting(tmp_path):
    from app.providers import lba_current_analytics
    (tmp_path / "game-1.csv").write_text("game_id,player_name,team_name,PTS\ng1,Player One,Milano,10\n", encoding="utf-8")
    (tmp_path / "game-2.csv").write_text("game_id,player_name,team_name,PTS\ng2,Player One,Milano,20\n", encoding="utf-8")
    result = lba_current_analytics(tmp_path)
    player = result["players"][0]
    assert player["games_played"] == 2
    assert player["totals"]["points"] == 30
    assert player["per_game"]["points"] == 15


def test_lba_analytics_supports_basketballscraper_pbox_season_aggregates(tmp_path):
    from app.providers import lba_current_analytics
    season_dir = tmp_path / "LBA" / "2627"
    season_dir.mkdir(parents=True)
    (season_dir / "Pbox.csv").write_text(
        ",Team,Player,GP,MIN,PTS,P2M,P2A,P3M,P3A,FTM,FTA,OREB,DREB,AST,TOV,STL,BLK,PF,PM\n"
        "0,Milano,Giocatore Uno,3,90,45,12,24,5,15,6,8,3,9,12,4,3,1,6,18\n",
        encoding="utf-8")
    result = lba_current_analytics(tmp_path)
    assert result["data_status"] == "LIVE_SOURCE"
    assert result["player_count"] == 1
    player = result["players"][0]
    assert player["stat_grain"] == "season_aggregate"
    assert player["games_played"] == 3
    assert player["totals"]["points"] == 45
    assert player["per_game"]["points"] == 15
    assert player["totals"]["rebounds"] == 12
    assert player["per_game"]["assists"] == 4
    assert player["shooting"]["fg_pct"] == round(17 / 39, 4)


def test_lba_analytics_excludes_compact_previous_season_folder(tmp_path):
    from app.providers import lba_current_analytics
    old_dir = tmp_path / "LBA" / "2526"
    old_dir.mkdir(parents=True)
    (old_dir / "Pbox.csv").write_text(
        ",Team,Player,GP,MIN,PTS,P2M,P2A,P3M,P3A,FTM,FTA,OREB,DREB,AST,TOV,STL,BLK,PF,PM\n"
        "0,Milano,Giocatore Vecchio,3,90,45,12,24,5,15,6,8,3,9,12,4,3,1,6,18\n",
        encoding="utf-8")
    result = lba_current_analytics(tmp_path)
    assert result["players"] == []
    assert result["data_status"] == "RAW_DATA_ONLY"


def test_lba_summary_finds_nested_basketballscraper_season_files(tmp_path):
    from app.providers import lba_csv_summary
    season_dir = tmp_path / "2026-2027" / "LBA" / "2627"
    season_dir.mkdir(parents=True)
    (season_dir / "Pbox.csv").write_text("Team,Player,GP,PTS\nMilano,Player One,3,45\n", encoding="utf-8")
    result = lba_csv_summary(tmp_path)
    assert result["files_found"] == 1
    assert result["total_rows"] == 1
    assert result["files"][0]["name"].endswith("LBA/2627/Pbox.csv")


def test_nba_boxscore_normalizes_player_stats_from_source_payload():
    from app.providers import nba_boxscore

    class BoxscoreResponse:
        def raise_for_status(self):
            pass
        def json(self):
            return {
                "header": {"name": "Boston Celtics at New York Knicks", "competitions": [{"date": "2026-10-22T23:30Z"}]},
                "boxscore": {"players": [{
                    "team": {"displayName": "Boston Celtics", "abbreviation": "BOS"},
                    "statistics": [{"names": ["MIN", "FG", "3PT", "FT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TO", "PF", "PTS"],
                        "athletes": [{"athlete": {"id": "42", "displayName": "Test Player"},
                            "stats": ["32", "8-15", "2-5", "4-4", "1", "6", "7", "5", "1", "0", "2", "3", "22"]}]}]
                }]}
            }
    class BoxscoreClient:
        @staticmethod
        def get(*args, **kwargs):
            return BoxscoreResponse()

    result = nba_boxscore("12345", client=BoxscoreClient)
    assert result["data_status"] == "LIVE_SOURCE"
    assert result["player_count"] == 1
    player = result["players"][0]
    assert player["player"] == "Test Player"
    assert player["points"] == 22
    assert player["rebounds"] == 7
    assert player["assists"] == 5
    assert player["fgm"] == 8
    assert player["fga"] == 15
    assert player["advanced"]["efg_pct"] == round((8 + 0.5 * 2) / 15, 4)
    assert player["advanced"]["ts_pct"] == round(22 / (2 * (15 + 0.44 * 4)), 4)
    assert player["advanced"]["ast_to"] == 2.5
    assert result["analytics_status"] == "GAME_LEVEL_ADVANCED_DERIVED"


def test_nba_boxscore_rejects_invalid_event_id_without_network_call():
    from app.providers import nba_boxscore
    result = nba_boxscore("../other")
    assert result["data_status"] == "INVALID_EVENT_ID"
    assert result["players"] == []


def test_lba_import_validation_report_detects_usable_current_season_data(tmp_path):
    import importlib.util
    from pathlib import Path
    script = Path(__file__).resolve().parents[3] / "scripts" / "validate_lba_import.py"
    spec = importlib.util.spec_from_file_location("validate_lba_import", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    season_dir = tmp_path / "LBA" / "2627"
    season_dir.mkdir(parents=True)
    (season_dir / "Pbox.csv").write_text(
        ",Team,Player,GP,MIN,PTS,P2M,P2A,P3M,P3A,FTM,FTA,OREB,DREB,AST,TOV,STL,BLK,PF,PM\n"
        "0,Milano,Giocatore Uno,3,90,45,12,24,5,15,6,8,3,9,12,4,3,1,6,18\n",
        encoding="utf-8")
    report = module.build_report(tmp_path)
    assert report["status"] == "LIVE_SOURCE"
    assert report["analytics"]["player_count"] == 1
    assert report["analytics"]["stat_grains"] == {"season_aggregate": 1}
    assert report["publication_ready"] is False
    assert report["exit_code"] == 0


def test_lba_import_validation_report_fails_when_no_data(tmp_path):
    import importlib.util
    from pathlib import Path
    script = Path(__file__).resolve().parents[3] / "scripts" / "validate_lba_import.py"
    spec = importlib.util.spec_from_file_location("validate_lba_import_empty", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.build_report(tmp_path)
    assert report["status"] == "NO_IMPORTED_DATA"
    assert report["exit_code"] == 2
    assert report["analytics"]["player_count"] == 0


def test_nba_daily_refresh_is_configured_for_0800_rome():
    from pathlib import Path
    from app.scheduler import NIGHTLY_INGESTION_HOUR_ITALY, NIGHTLY_INGESTION_TIMEZONE
    worker_source = (Path(__file__).parents[1] / "app" / "worker.py").read_text(encoding="utf-8")
    assert 'timezone="Europe/Rome"' in worker_source
    assert '"nba-scoreboard-daily-0800-italy"' in worker_source
    assert 'crontab(minute=0, hour=8)' in worker_source
    assert NIGHTLY_INGESTION_HOUR_ITALY == 8
    assert NIGHTLY_INGESTION_TIMEZONE == "Europe/Rome"


def test_nba_season_analytics_aggregates_only_real_current_season_boxscores(tmp_path):
    import json
    from app.providers import nba_season_player_analytics
    season = tmp_path / "boxscores" / "2026-27"
    season.mkdir(parents=True)
    for event_id, points, fgm, fga, threes, fta in [
        ("game1", 20, 7, 14, 2, 4),
        ("game2", 30, 10, 20, 3, 5),
    ]:
        payload = {"event_id": event_id, "data_status": "LIVE_SOURCE", "players": [{
            "player_id": "42", "player": "Test Player", "team": "Boston Celtics",
            "minutes": 30, "points": points, "rebounds": 5, "assists": 4,
            "steals": 1, "blocks": 0, "turnovers": 2, "fgm": fgm,
            "fga": fga, "three_pm": threes, "fta": fta,
        }]}
        (season / f"{event_id}.json").write_text(json.dumps(payload), encoding="utf-8")
    old = tmp_path / "boxscores" / "2025-26"
    old.mkdir(parents=True)
    (old / "old.json").write_text(json.dumps({"data_status":"LIVE_SOURCE","players":[{"player_id":"99"}]}), encoding="utf-8")
    result = nba_season_player_analytics(tmp_path)
    assert result["data_status"] == "LIVE_SOURCE"
    assert result["games_aggregated"] == 2
    player = result["players"][0]
    assert player["games_played"] == 2
    assert player["per_game"]["points"] == 25
    assert player["advanced"]["efg_pct"] == round((17 + 0.5 * 5) / 34, 4)
    assert player["advanced"]["ts_pct"] == round(50 / (2 * (34 + 0.44 * 9)), 4)


def test_nba_boxscore_refresh_persists_final_game_snapshot_atomically(tmp_path, monkeypatch):
    import json
    from app.refresh import refresh_nba_boxscores
    monkeypatch.setenv("NBA_SNAPSHOT_DIR", str(tmp_path))
    (tmp_path / "scoreboard_20261030.json").write_text(json.dumps({"games": [
        {"id":"final123", "state":"post", "status":"Final"},
        {"id":"live123", "state":"in", "status":"In Progress"},
    ]}), encoding="utf-8")
    def fake_boxscore(event_id):
        return {"event_id":event_id, "data_status":"LIVE_SOURCE", "players":[{"player_id":"1"}]}
    result = refresh_nba_boxscores(days=["20261030"], fetcher=fake_boxscore)
    assert result["stored"] == 1
    saved = tmp_path / "boxscores" / "2026-27" / "final123.json"
    assert saved.exists()
    assert not (tmp_path / "boxscores" / "2026-27" / "live123.json").exists()

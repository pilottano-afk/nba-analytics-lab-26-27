from app.lba_results import load_lba_results, lba_standings, DEFAULT_RESULTS


def test_seeded_current_season_results_cover_three_rounds():
    result = load_lba_results()
    assert result["data_status"] == "IMPORTED_SNAPSHOT"
    assert result["game_count"] == 24
    assert result["rounds_covered"] == [1, 2, 3]
    assert len({g["home_team"] for g in result["games"]} | {g["away_team"] for g in result["games"]}) == 16
    assert all(g["source_url"].startswith("https://") for g in result["games"])


def test_standings_are_calculated_from_results():
    result = lba_standings()
    by_team = {row["team"]: row for row in result["standings"]}
    assert result["team_count"] == 16
    assert by_team["Napoli Basketball"]["wins"] == 3
    assert by_team["Napoli Basketball"]["league_points"] == 6
    assert by_team["Napoli Basketball"]["games_played"] == 3
    assert by_team["Napoli Basketball"]["points_for"] == 292
    assert by_team["Longobardi Scafati Basket"]["losses"] == 3
    assert result["standings"][0]["rank"] == 1


def test_missing_file_does_not_fabricate_results(tmp_path):
    result = load_lba_results(tmp_path / "missing.csv")
    assert result["data_status"] == "NO_IMPORTED_DATA"
    assert result["game_count"] == 0
    assert result["standings"] if "standings" in result else True


def test_invalid_rows_are_quarantined(tmp_path):
    file = tmp_path / "results.csv"
    file.write_text(
        "season,round,date,home_team,away_team,home_score,away_score,status,source_url,source_type\n"
        "2026/27,1,2026-09-26,Team A,Team B,80,80,final,https://example.com,secondary\n"
        "2026/27,1,2026-09-26,Team A,Team C,80,70,final,https://example.com,secondary\n",
        encoding="utf-8")
    result = load_lba_results(file)
    assert result["game_count"] == 1
    assert result["data_status"] == "PARTIAL_IMPORT"
    assert result["errors"] == ["INVALID_ROW:2"]


def test_live_api_exposes_lba_results_and_standings():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    results = client.get("/api/v1/live/lba/results")
    standings = client.get("/api/v1/live/lba/standings")
    assert results.status_code == 200 and results.json()["game_count"] == 24
    assert standings.status_code == 200 and standings.json()["team_count"] == 16
    assert "no-store" in standings.headers.get("cache-control", "")

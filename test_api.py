from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
def test_health(): assert c.get("/health").json()["status"]=="ok"
def test_leaderboard(): assert len(c.get("/api/v1/leaderboards").json()["rows"])>=5
def test_shot_chart(): assert "low_sample_size" in c.get("/api/v1/players/p1/shot-chart?quarter=1").json()


def test_current_snapshot_endpoint():
    r=c.get("/api/v1/snapshots/current")
    assert r.status_code == 200
    assert r.json()["competition_id"] == "lba-2026-27"


def test_italian_competitions_only():
    rows=c.get("/api/v1/competitions").json()
    assert [x["id"] for x in rows] == ["lba-2026-27", "a2-2026-27"]
    assert all(x["season"] == "2026/27" for x in rows)


def test_leaderboards_are_competition_scoped_and_marked_demo():
    lba=c.get("/api/v1/leaderboards?competition_id=lba-2026-27").json()
    a2=c.get("/api/v1/leaderboards?competition_id=a2-2026-27").json()
    assert len(lba["rows"]) == 6 and len(a2["rows"]) == 6
    assert {p["competition_id"] for p in lba["rows"]} == {"lba-2026-27"}
    assert {p["competition_id"] for p in a2["rows"]} == {"a2-2026-27"}
    assert lba["data_status"] == "SYNTHETIC_DEMO"


def test_official_source_links_are_explicit_about_ingestion_status():
    result=c.get("/api/v1/sources").json()
    assert len(result["sources"]) >= 2
    assert {s["competition_id"] for s in result["sources"]} >= {"lba-2026-27", "a2-2026-27"}
    assert "non sono ancora attivi" in result["note"]


def test_unknown_competition_returns_404():
    assert c.get("/api/v1/leaderboards?competition_id=unknown").status_code == 404


def test_source_check_endpoint_reports_http_reachability(monkeypatch):
    import app.main as main
    class FakeResponse:
        status_code = 200
    monkeypatch.setattr(main.httpx, "get", lambda *args, **kwargs: FakeResponse())
    result=c.get("/api/v1/sources/check")
    assert result.status_code == 200
    body=result.json()
    assert len(body["sources"]) == 3
    assert all(x["reachable"] is True and x["http_status"] == 200 for x in body["sources"])

from app.pipeline.db_sync import persist_batch_records
from app.pipeline.models import RawGamePayload, Snapshot
from app.pipeline.staging import RawStager
from app.pipeline.adapter import EuroLeagueDemoAdapter


class FakeRepo:
    def __init__(self):
        self.calls = []

    def store_raw_payload(self, competition, game_id, payload, checksum):
        self.calls.append(("raw", game_id, checksum))

    def upsert_game(self, game):
        self.calls.append(("game", game["game_id"], game["home_points"]))

    def quarantine(self, game_id, errors):
        self.calls.append(("quarantine", game_id, errors))


def test_batch_persists_raw_then_only_verified_games_and_quarantines():
    payloads = EuroLeagueDemoAdapter().fetch_batch()
    stager = RawStager()
    records = [RawGamePayload("euroleague", p["game_id"], p, stager.canonical_checksum(p), "2026-10-10T00:00:00+00:00") for p in payloads]
    snapshot = Snapshot("v1", "EuroLeague", [payloads[0]["game_id"]], "PARTIAL")
    quarantine = [{"game_id": payloads[1]["game_id"], "errors": ["test rejection"]}]
    repo = FakeRepo()

    counts = persist_batch_records(snapshot, records, quarantine, repo)

    assert counts == {"raw_payload_count": 2, "verified_game_rows": 1, "quarantined_game_count": 1}
    assert [c[0] for c in repo.calls] == ["raw", "game", "raw", "quarantine"]
    assert not any(c[0] == "game" and c[1] == payloads[1]["game_id"] for c in repo.calls)

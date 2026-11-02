from app.pipeline.adapter import EuroLeagueDemoAdapter
from app.pipeline.runner import EuroLeaguePipeline
from app.pipeline.snapshot import SnapshotRegistry
from app.pipeline.staging import RawStager


def test_euroleague_demo_batch_is_promotable(tmp_path):
    pipeline = EuroLeaguePipeline(stager=RawStager(str(tmp_path / "raw")), adapter=EuroLeagueDemoAdapter())
    snapshot, quarantined = pipeline.run_batch()
    assert snapshot.status == "PROMOTABLE"
    assert len(snapshot.games) == 2
    assert quarantined == []


def test_invalid_game_is_quarantined_without_blocking_valid_game(tmp_path):
    pipeline = EuroLeaguePipeline(stager=RawStager(str(tmp_path / "raw")))
    good = EuroLeagueDemoAdapter().fetch_batch()[0]
    bad = {**good, "game_id": "BAD-001", "away_points": 1}
    snapshot, quarantined = pipeline.run_batch([good, bad])
    assert snapshot.status == "PARTIAL"
    assert snapshot.games == ["EL-DEMO-001"]
    assert quarantined[0]["game_id"] == "BAD-001"


def test_snapshot_promotion_writes_current_pointer(tmp_path):
    pipeline = EuroLeaguePipeline(stager=RawStager(str(tmp_path / "raw")))
    snapshot, _ = pipeline.run_batch()
    registry = SnapshotRegistry(str(tmp_path / "snapshots"))
    path = registry.promote(snapshot)
    assert path.exists()
    assert (tmp_path / "snapshots" / "CURRENT").read_text() == snapshot.version

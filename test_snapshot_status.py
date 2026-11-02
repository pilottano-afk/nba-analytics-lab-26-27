from app.pipeline.models import Snapshot


def test_rejected_snapshot_cannot_be_promoted(tmp_path):
    import pytest
    from app.pipeline.snapshot import SnapshotRegistry
    registry = SnapshotRegistry(str(tmp_path))
    with pytest.raises(ValueError):
        registry.promote(Snapshot("v-rejected", "EuroLeague", [], "REJECTED"))
    assert not (tmp_path / "CURRENT").exists()

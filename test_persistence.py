from app.pipeline.models import Snapshot
from app.pipeline.persistence import persist_snapshot

class FakeRepo:
    def __init__(self): self.calls=[]
    def create_snapshot(self, **kwargs): self.calls.append(kwargs)

def test_only_promotable_snapshots_are_persisted():
    repo=FakeRepo()
    persist_snapshot(Snapshot("v1","EuroLeague",["g1"],"PROMOTABLE"), repo)
    persist_snapshot(Snapshot("v2","EuroLeague",[],"REJECTED"), repo)
    assert [c["version"] for c in repo.calls] == ["v1"]
    assert repo.calls[0]["verified_game_count"] == 1

from app.pipeline.runner import EuroLeaguePipeline

class MemoryStager:
    def __init__(self): self.records=[]
    def stage(self, competition, game_id, payload, received_at):
        from app.pipeline.models import RawGamePayload
        from app.pipeline.staging import RawStager
        record=RawGamePayload(competition, game_id, payload, RawStager.canonical_checksum(payload), received_at)
        self.records.append(record)
        return record

def test_pipeline_exposes_raw_records_for_durable_persistence():
    pipeline=EuroLeaguePipeline(stager=MemoryStager())
    snapshot, quarantined=pipeline.run_batch()
    assert len(pipeline.raw_records) == 2
    assert all(record.checksum for record in pipeline.raw_records)
    assert snapshot.status in {"PROMOTABLE", "PARTIAL"}

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_raw_payload_storage_is_idempotent_and_immutable_by_checksum():
    source = (ROOT / "app" / "db" / "postgres.py").read_text()
    schema = (ROOT.parent.parent / "infra" / "postgres" / "001_schema.sql").read_text()
    assert "ON CONFLICT (competition_id,game_id,checksum) DO NOTHING" in source
    assert "UNIQUE(competition_id,game_id,checksum)" in schema


def test_legacy_pipeline_keeps_raw_persistence_contract_but_is_not_scheduled():
    worker = (ROOT / "app" / "worker.py").read_text()
    sync_source = (ROOT / "app" / "pipeline" / "db_sync.py").read_text()
    assert "repo.store_raw_payload" in sync_source
    assert "repo.quarantine" in sync_source
    assert sync_source.index("repo.store_raw_payload") < sync_source.index("repo.upsert_game") < sync_source.index("repo.quarantine")
    assert '"app.worker.check_italian_sources"' in worker
    assert "run_euroleague_pipeline" not in worker

from app.scheduler import NIGHTLY_INGESTION_HOUR_ITALY, NIGHTLY_INGESTION_MINUTE_ITALY, NIGHTLY_INGESTION_TIMEZONE


def test_nba_nightly_schedule_is_eight_am_italy_time():
    assert (NIGHTLY_INGESTION_HOUR_ITALY, NIGHTLY_INGESTION_MINUTE_ITALY) == (8, 0)
    assert NIGHTLY_INGESTION_TIMEZONE == "Europe/Rome"


def test_worker_checks_italian_sources_without_ingesting_synthetic_games():
    from pathlib import Path
    worker = Path(__file__).parents[1] / "app" / "worker.py"
    source = worker.read_text(encoding="utf-8")
    assert '"app.worker.check_italian_sources"' in source
    assert '"SOURCE_CHECK_ONLY"' in source
    assert "run_euroleague_pipeline" not in source

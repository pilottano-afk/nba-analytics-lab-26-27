from app.db.postgres import PostgresRepository

def test_default_database_target_is_stats_hub(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    repo=PostgresRepository()
    assert repo.dsn.endswith("/stats_hub")

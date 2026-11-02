from __future__ import annotations
from .models import Snapshot
from ..db.postgres import PostgresRepository

def persist_snapshot(snapshot: Snapshot, repo: PostgresRepository | None = None) -> None:
    """Persist only promotable/partial snapshots; rejected snapshots never become current."""
    if snapshot.status not in {"PROMOTABLE", "PARTIAL"}:
        return
    own = repo is None
    repo = repo or PostgresRepository()
    try:
        repo.create_snapshot(
            version=snapshot.version,
            competition_id="el-2026-27",
            status=snapshot.status,
            game_count=len(snapshot.games),
            verified_game_count=len(snapshot.games),
        )
    finally:
        if own:
            repo.close()

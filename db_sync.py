"""Synchronize one validated pipeline batch to PostgreSQL in dependency order."""
from typing import Any, Protocol

from .models import RawGamePayload, Snapshot


class BatchRepository(Protocol):
    def store_raw_payload(self, competition: str, game_id: str, payload: dict[str, Any], checksum: str) -> None: ...
    def upsert_game(self, game: dict[str, Any]) -> None: ...
    def quarantine(self, game_id: str, errors: list[str]) -> None: ...


def persist_batch_records(
    snapshot: Snapshot,
    raw_records: list[RawGamePayload],
    quarantined: list[dict[str, Any]],
    repo: BatchRepository,
) -> dict[str, int]:
    """Persist raw records first, only validated games as canonical rows, and failures to quarantine."""
    verified_ids = set(snapshot.games)
    verified_count = 0
    for raw in raw_records:
        repo.store_raw_payload("el-2026-27", raw.game_id, raw.payload, raw.checksum)
        if raw.game_id in verified_ids:
            repo.upsert_game(raw.payload)
            verified_count += 1
    for item in quarantined:
        if item.get("game_id"):
            repo.quarantine(str(item["game_id"]), list(item.get("errors", [])))
    return {
        "raw_payload_count": len(raw_records),
        "verified_game_rows": verified_count,
        "quarantined_game_count": len(quarantined),
    }

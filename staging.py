"""Immutable raw staging boundary. Production can replace the filesystem adapter with object storage."""
from dataclasses import asdict
import hashlib, json
from pathlib import Path
from typing import Any
from .models import RawGamePayload

class RawStager:
    def __init__(self, root: str = ".data/raw"):
        self.root = Path(root)

    @staticmethod
    def canonical_checksum(payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    def stage(self, competition: str, game_id: str, payload: dict[str, Any], received_at: str) -> RawGamePayload:
        checksum = self.canonical_checksum(payload)
        record = RawGamePayload(competition, game_id, payload, checksum, received_at)
        path = self.root / competition.lower() / f"{game_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            return record
        path.write_text(json.dumps(asdict(record), sort_keys=True, indent=2), encoding="utf-8")
        return record

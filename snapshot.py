"""Small local snapshot registry. Production maps this contract to PostgreSQL/Redis."""
import json
from pathlib import Path
from .models import Snapshot

class SnapshotRegistry:
    def __init__(self, root: str = ".data/snapshots"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def promote(self, snapshot: Snapshot) -> Path:
        if snapshot.status not in {"PROMOTABLE", "PARTIAL"}:
            raise ValueError("only promotable snapshots can be promoted")
        path = self.root / f"{snapshot.version}.json"
        path.write_text(json.dumps(snapshot.__dict__, sort_keys=True, indent=2), encoding="utf-8")
        (self.root / "CURRENT").write_text(snapshot.version, encoding="utf-8")
        return path

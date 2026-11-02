from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class GameStatus(str, Enum):
    STAGED = "STAGED"
    VERIFIED = "VERIFIED"
    QUARANTINED = "QUARANTINED"

@dataclass(frozen=True)
class RawGamePayload:
    competition: str
    game_id: str
    payload: dict[str, Any]
    checksum: str
    received_at: str

@dataclass
class GameValidation:
    game_id: str
    status: GameStatus
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

@dataclass
class Snapshot:
    version: str
    competition: str
    games: list[str]
    status: str = "CANDIDATE"

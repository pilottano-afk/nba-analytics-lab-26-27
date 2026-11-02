from datetime import datetime, timezone
from .adapter import EuroLeagueDemoAdapter
from .circuit_breaker import CircuitBreaker
from .models import Snapshot
from .staging import RawStager
from .validator import GameValidator

class EuroLeaguePipeline:
    """Deterministic orchestration: fetch -> stage -> validate -> snapshot candidate."""
    def __init__(self, stager=None, validator=None, adapter=None, breaker=None):
        self.stager = stager or RawStager()
        self.validator = validator or GameValidator()
        self.adapter = adapter or EuroLeagueDemoAdapter()
        self.breaker = breaker or CircuitBreaker()
        self.raw_records = []

    def run_batch(self, games=None):
        if not self.breaker.allow():
            return Snapshot(self._version(), "EuroLeague", [], "CIRCUIT_OPEN"), [{"error": "circuit_breaker_open"}]
        games = self.adapter.fetch_batch() if games is None else games
        verified, quarantined = [], []
        self.raw_records = []
        now = datetime.now(timezone.utc).isoformat()
        for game in games:
            try:
                raw = self.stager.stage("euroleague", str(game["game_id"]), game, now)
                self.raw_records.append(raw)
                result = self.validator.validate(raw)
                if result.status.value == "VERIFIED": verified.append(result.game_id)
                else: quarantined.append({"game_id": result.game_id, "errors": result.errors})
            except Exception as exc:
                self.breaker.record_failure()
                quarantined.append({"game_id": str(game.get("game_id", "unknown")), "errors": [str(exc)]})
        if quarantined and not verified:
            self.breaker.record_failure()
        else:
            self.breaker.record_success()
        status = "PROMOTABLE" if verified and not quarantined else "PARTIAL" if verified else "REJECTED"
        return Snapshot(self._version(), "EuroLeague", verified, status), quarantined

    @staticmethod
    def _version():
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

from .models import GameStatus, GameValidation, RawGamePayload
from ..checksum import validate_box_score

class GameValidator:
    """Validate both teams of a staged game without mutating raw data."""
    def validate(self, raw: RawGamePayload) -> GameValidation:
        p = raw.payload
        errors: list[str] = []
        required = ("home_team_id", "away_team_id", "home_points", "away_points")
        errors.extend(f"missing:{key}" for key in required if key not in p)
        if not errors:
            checks = [
                ("home", p.get("home_player_points", []), p["home_points"], p.get("home_player_reb", []), p.get("home_official_reb", 0), p.get("home_player_tov", []), p.get("home_official_tov", 0), p.get("home_player_pf", []), p.get("home_official_pf", 0)),
                ("away", p.get("away_player_points", []), p["away_points"], p.get("away_player_reb", []), p.get("away_official_reb", 0), p.get("away_player_tov", []), p.get("away_official_tov", 0), p.get("away_player_pf", []), p.get("away_official_pf", 0)),
            ]
            for side, pts, score, reb, official_reb, tov, official_tov, pf, official_pf in checks:
                gate = validate_box_score(pts, score, reb, 0, official_reb, tov, 0, official_tov, pf, official_pf)
                errors.extend(f"{side}:{e}" for e in gate["errors"])
        status = GameStatus.QUARANTINED if errors else GameStatus.VERIFIED
        return GameValidation(raw.game_id, status, errors)

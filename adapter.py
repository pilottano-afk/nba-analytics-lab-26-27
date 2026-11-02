"""Competition-specific upstream adapter boundary.

The demo adapter produces deterministic EuroLeague-shaped payloads. A production
adapter can replace only this class while the staging/validation/promotion layers stay unchanged.
"""
from typing import Any

class EuroLeagueDemoAdapter:
    competition = "euroleague"

    def fetch_batch(self) -> list[dict[str, Any]]:
        return [
            self._game("EL-DEMO-001", "BAR", "OLY", 84, 79),
            self._game("EL-DEMO-002", "FEN", "RMA", 91, 88),
        ]

    @staticmethod
    def _game(game_id: str, home: str, away: str, home_points: int, away_points: int) -> dict[str, Any]:
        # Minimal deterministic box-score payload used to exercise the real pipeline contract.
        return {
            "game_id": game_id,
            "home_team_id": home,
            "away_team_id": away,
            "home_points": home_points,
            "away_points": away_points,
            "home_player_points": ([24, 18, 15, 12, 10, 5] if home_points == 84 else [25, 20, 16, 12, 10, 8]),
            "away_player_points": ([22, 17, 14, 11, 9, 6] if away_points == 79 else [24, 19, 15, 12, 10, 8]),
            "home_player_reb": [8, 6, 5, 4, 3, 2],
            "away_player_reb": [7, 6, 5, 4, 3, 2],
            "home_player_tov": [2, 2, 1, 1, 1, 1],
            "away_player_tov": [2, 2, 1, 1, 1, 1],
            "home_player_pf": [2, 2, 2, 1, 2, 1],
            "away_player_pf": [2, 2, 2, 1, 2, 1],
            "home_official_reb": 28,
            "away_official_reb": 27,
            "home_official_tov": 8,
            "away_official_tov": 8,
            "home_official_pf": 10,
            "away_official_pf": 10,
        }

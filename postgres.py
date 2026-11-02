from __future__ import annotations
import json
import os
from typing import Any

class PostgresRepository:
    """Small DB adapter for verified snapshots and analytics."""
    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or os.getenv("DATABASE_URL", "postgresql://stats:stats@localhost:5432/stats_hub")
        self._conn = None

    def connect(self):
        if self._conn is None:
            import psycopg
            self._conn = psycopg.connect(self.dsn)
        return self._conn

    def close(self):
        if self._conn is not None:
            self._conn.close(); self._conn = None

    def upsert_game(self, game: dict[str, Any]) -> None:
        conn=self.connect()
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO games(id,competition_id,home_team_id,away_team_id,game_date,home_score,away_score,status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET home_score=EXCLUDED.home_score,away_score=EXCLUDED.away_score,status=EXCLUDED.status""",
            (game["game_id"],game.get("competition_id","el-2026-27"),game["home_team_id"],game["away_team_id"],game.get("game_date"),game["home_points"],game["away_points"],"VERIFIED"))
        conn.commit()

    def store_raw_payload(self, competition: str, game_id: str, payload: dict[str, Any], checksum: str) -> None:
        conn=self.connect()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO raw_game_payloads(competition_id,game_id,payload,checksum) VALUES (%s,%s,%s,%s) ON CONFLICT (competition_id,game_id,checksum) DO NOTHING", (competition,game_id,json.dumps(payload),checksum))
        conn.commit()

    def quarantine(self, game_id: str, errors: list[str]) -> None:
        conn=self.connect()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO quarantined_games(game_id,errors) VALUES (%s,%s)", (game_id,json.dumps(errors)))
        conn.commit()

    def create_snapshot(self, version: str, competition_id: str, status: str, game_count: int, verified_game_count: int, checksum: str | None=None) -> None:
        conn=self.connect()
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO analytical_snapshots(version,competition_id,status,game_count,verified_game_count,checksum)
            VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(version) DO UPDATE SET status=EXCLUDED.status,game_count=EXCLUDED.game_count,verified_game_count=EXCLUDED.verified_game_count,checksum=EXCLUDED.checksum""",
            (version,competition_id,status,game_count,verified_game_count,checksum))
        conn.commit()

    def current_snapshot(self, competition_id: str) -> dict[str, Any] | None:
        conn=self.connect()
        with conn.cursor() as cur:
            cur.execute("""SELECT version,competition_id,status,created_at,game_count,verified_game_count,checksum
            FROM analytical_snapshots WHERE competition_id=%s AND status IN ('PROMOTED','PROMOTABLE','PARTIAL')
            ORDER BY created_at DESC LIMIT 1""", (competition_id,))
            row=cur.fetchone()
        if not row: return None
        return dict(zip(["version","competition_id","status","created_at","game_count","verified_game_count","checksum"],row))

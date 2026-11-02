from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class PossessionInputs:
    fga: float
    fta: float
    orb: float
    tov: float


def possessions(x: PossessionInputs) -> float:
    """Canonical fallback FIBA-style possession estimate."""
    return max(0.0, x.fga + 0.44 * x.fta - x.orb + x.tov)


def offensive_rating(points: float, poss: float) -> float | None:
    return None if poss <= 0 else 100.0 * points / poss


def true_shooting_pct(points: float, fga: float, fta: float) -> float | None:
    denom = 2.0 * (fga + 0.44 * fta)
    return None if denom <= 0 else points / denom


def effective_fg_pct(fgm: float, fga: float, three_pm: float) -> float | None:
    return None if fga <= 0 else (fgm + 0.5 * three_pm) / fga


def free_throw_rate(fta: float, fga: float) -> float | None:
    return None if fga <= 0 else fta / fga


def summarize_team_box(score: float, fga: float, fta: float, orb: float, tov: float, fgm: float, three_pm: float) -> dict:
    poss = possessions(PossessionInputs(fga, fta, orb, tov))
    return {
        "possessions": round(poss, 3),
        "ortg": None if offensive_rating(score, poss) is None else round(offensive_rating(score, poss), 3),
        "ts_pct": None if true_shooting_pct(score, fga, fta) is None else round(true_shooting_pct(score, fga, fta), 4),
        "efg_pct": None if effective_fg_pct(fgm, fga, three_pm) is None else round(effective_fg_pct(fgm, fga, three_pm), 4),
        "ftr": None if free_throw_rate(fta, fga) is None else round(free_throw_rate(fta, fga), 4),
    }

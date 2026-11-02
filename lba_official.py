"""Official LBA calendar/results adapter based on the public endpoints used by BasketballScrapeR."""
from __future__ import annotations
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup

BASE = "https://www.legabasket.it/"
SEASON_YEAR = 2026
SEASON_LABEL = "2026/27"
USER_AGENT = "ItalianBasketballAnalytics/0.3 (current-season results refresh)"


def _get_json(client: Any, url: str, params: dict | None = None) -> dict:
    response = client.get(url, params=params, timeout=20.0, follow_redirects=True, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or "data" not in payload:
        raise ValueError("Unexpected LBA JSON response")
    return payload["data"]


def _round_number(code: Any, ordinal: int, phase_code: str) -> int:
    match = re.search(r"\d+", str(code or ""))
    number = int(match.group()) if match else ordinal
    if "ritorno" in phase_code.casefold() and number <= 15:
        number += 15
    return number


def _parse_calendar_html(html: str, season_label: str, round_number: int, date_fallback: str | None = None) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    tbody = soup.find("tbody")
    if tbody is None:
        return []
    games = []
    for tr in tbody.find_all("tr"):
        result_node = tr.find(class_="result")
        if result_node is None:
            continue
        result_link = result_node.find("a", href=True)
        if not result_link:
            continue
        match = re.search(r"/game/(\d+)", result_link["href"])
        if not match:
            continue
        score_text = " ".join(result_node.get_text(" ", strip=True).split())
        score = re.search(r"(\d+)\s*[-–:]\s*(\d+)", score_text)
        if not score:
            continue  # scheduled / not-final rows do not enter the standings
        anchors = []
        for a in tr.find_all("a", href=True):
            href = a.get("href", "")
            name = " ".join(a.get_text(" ", strip=True).split())
            if name and "/game/" not in href and name not in anchors:
                anchors.append(name)
        # Team names are normally the two non-result team links in the calendar row.
        if len(anchors) < 2:
            continue
        cells = tr.find_all("td")
        raw_date = " ".join(cells[5].get_text(" ", strip=True).split()) if len(cells) > 5 else ""
        date = None
        for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y", "%d/%m/%y %H:%M", "%d/%m/%y"):
            try:
                date = datetime.strptime(raw_date, fmt).date().isoformat()
                break
            except ValueError:
                pass
        if date is None and date_fallback:
            date = date_fallback
        if date is None:
            continue
        games.append({
            "season": season_label, "round": round_number, "date": date,
            "home_team": anchors[0], "away_team": anchors[1],
            "home_score": int(score.group(1)), "away_score": int(score.group(2)),
            "status": "final", "source_url": urljoin(BASE, result_link["href"]), "source_type": "official_lba",
            "game_id": match.group(1),
        })
    return games


def fetch_official_lba_results(client: Any = httpx, year: int = SEASON_YEAR) -> dict:
    """Fetch current regular-season final scores; raise on schema/network errors so callers keep last good snapshot."""
    years_payload = _get_json(client, urljoin(BASE, "championship/429"))
    seasons = years_payload.get("years") or []
    season = next((item for item in seasons if int(item.get("year", -1)) == year), None)
    if not season or not season.get("id"):
        raise ValueError(f"LBA season {year} not found in official season list")
    championship_id = str(season["id"])
    season_payload = _get_json(client, urljoin(BASE, f"championship/{championship_id}"))
    phases = season_payload.get("phases") or []
    if not phases:
        raise ValueError("No phases returned by official LBA season endpoint")
    games_by_id = {}
    for phase in phases:
        phase_id = phase.get("id")
        if not phase_id:
            continue
        phase_code = str(phase.get("code", ""))
        phase_payload = _get_json(client, urljoin(BASE, f"phase/{phase_id}/{championship_id}"))
        days = phase_payload.get("days") or []
        for ordinal, day in enumerate(days, start=1):
            day_code = str(day.get("code", ""))
            params = {"s": year, "c": championship_id, "p": phase_id, "d": day_code}
            response = client.get(urljoin(BASE, "lba/6/calendario/calendar"), params=params, timeout=20.0,
                                  follow_redirects=True, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
            round_no = _round_number(day_code, ordinal, phase_code)
            for game in _parse_calendar_html(response.text, SEASON_LABEL, round_no):
                games_by_id[game["game_id"]] = game
    games = sorted(games_by_id.values(), key=lambda g: (g["date"], g["game_id"]))
    if len(games) < 8:
        raise ValueError(f"Official LBA response yielded only {len(games)} final games; refusing to replace snapshot")
    return {"league": "LBA", "season": SEASON_LABEL, "source": BASE + "competizioni", "games": games,
            "game_count": len(games), "rounds_covered": sorted({g["round"] for g in games}),
            "checked_at": datetime.now(timezone.utc).isoformat(), "data_status": "LIVE_SOURCE"}

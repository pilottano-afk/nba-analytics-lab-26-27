from fastapi import FastAPI,HTTPException
import httpx
from datetime import datetime, timezone
from fastapi.middleware.cors import CORSMiddleware
from .data import *
from .db.postgres import PostgresRepository
app=FastAPI(title="Italian Basketball Analytics API",version="0.2.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])
@app.middleware("http")
async def cache_headers(request,call_next):
    r=await call_next(request)
    if request.url.path.startswith("/api/v1/live/") or request.url.path.startswith("/api/v1/providers"):
        # Live scores and import status must never be cached for a full day.
        r.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    elif request.url.path.startswith("/api/v1"):
        r.headers["Cache-Control"]="public, s-maxage=86400, stale-while-revalidate=3600";r.headers["Cache-Tag"]="italian-basketball, season-2026-27"
    return r
@app.get("/health")
def health():return {"status":"ok","service":"italian-basketball-analytics-api","season":"2026/27"}
@app.get("/api/v1/competitions")
def competitions():return COMPETITIONS

OFFICIAL_SOURCES = [
    {"id":"lba-calendar","competition_id":"lba-2026-27","name":"Calendario ufficiale LBA","url":"https://www.legabasket.it/calendario/1/serie-a","kind":"calendar","status":"LINKED_NOT_INGESTED"},
    {"id":"a2-calendar","competition_id":"a2-2026-27","name":"Calendario ufficiale Serie A2 LNP","url":"https://www.legapallacanestro.com/serie/1/calendario","kind":"calendar","status":"LINKED_NOT_INGESTED"},
    {"id":"a2-pass","competition_id":"a2-2026-27","name":"LNP PASS — calendario e partite","url":"https://lnppass.legapallacanestro.com/?lang=it","kind":"calendar_and_video","status":"LINKED_NOT_INGESTED"},
]

@app.get("/api/v1/sources")
def sources():
    return {"season":"2026/27","mode":"source_links_plus_demo_fixtures","sources":OFFICIAL_SOURCES,
            "note":"Le statistiche visualizzate sono fixture sintetiche. Le fonti ufficiali sono collegate; il parsing e l'import automatico non sono ancora attivi."}

@app.get("/api/v1/sources/check")
def check_sources():
    checked=[]
    for source in OFFICIAL_SOURCES:
        item={**source,"checked_at":datetime.now(timezone.utc).isoformat(),"http_status":None,"reachable":False}
        try:
            response=httpx.get(source["url"],timeout=6.0,follow_redirects=True,headers={"User-Agent":"ItalianBasketballAnalytics/0.2 (source availability check)"})
            item["http_status"]=response.status_code
            item["reachable"]=response.status_code < 400
            item["status"]="REACHABLE_NOT_INGESTED" if item["reachable"] else "SOURCE_ERROR"
        except httpx.HTTPError as exc:
            item["status"]="UNREACHABLE"
            item["error"]=type(exc).__name__
        checked.append(item)
    return {"checked_at":datetime.now(timezone.utc).isoformat(),"sources":checked}

@app.get("/api/v1/leaderboards")
def leaderboards(metric="net_rtg",position="all",min_games=0,competition_id="lba-2026-27"):
    if competition_id not in {x["id"] for x in COMPETITIONS}: raise HTTPException(404,"Competition not found")
    rows=[x for x in leaderboard(competition_id) if x["games_played"]>=min_games and (position=="all" or x["primary_position"].lower()==position.lower())]
    return {"competition_id":competition_id,"metric":metric,"data_status":"SYNTHETIC_DEMO","rows":rows}
@app.get("/api/v1/players/{pid}")
def player(pid):
    p=next((x for x in PLAYERS if x["id"]==pid),None)
    if not p:raise HTTPException(404,"Player not found")
    return {**p,"stats":{p["competition_id"]:PLAYER_STATS[pid]},"data_status":"SYNTHETIC_DEMO"}
@app.get("/api/v1/players/{pid}/percentiles")
def percentiles(pid,position_peer="all"):
    if pid not in PERCENTILES:raise HTTPException(404,"Player not found")
    return {"player_id":pid,"competition_id":next(x["competition_id"] for x in PLAYERS if x["id"]==pid),"position_peer":position_peer,"dimensions":[{"label":l,"percentile":v} for l,v in zip(PERCENTILE_LABELS,PERCENTILES[pid])]}
@app.get("/api/v1/players/{pid}/shot-chart")
def shot_chart(pid,quarter="all",clutch=False,outcome="all"):
    if pid not in PLAYER_STATS:raise HTTPException(404,"Player not found")
    s=filter_shots(pid,quarter,outcome,clutch);fga=len(s);fgm=sum(x["is_made"] for x in s);th=sum(x["shot_type"]=="3PT" for x in s)
    return {"player_id":pid,"competition_id":next(x["competition_id"] for x in PLAYERS if x["id"]==pid),"total_fga":fga,"total_fgm":fgm,"fg_pct":round(fgm/fga,3) if fga else 0,"efg_pct":round((fgm+.5*th)/fga,3) if fga else 0,"pps":round(sum((3 if x["shot_type"]=="3PT" else 2) for x in s if x["is_made"])/fga,3) if fga else 0,"three_par":round(th/fga,3) if fga else 0,"low_sample_size":fga<15,"shots":s}
@app.get("/api/v1/teams/{tid}/stats")
def team_stats(tid):
    if not any(x["id"]==tid for x in TEAMS):raise HTTPException(404,"Team not found")
    return {"competition_id":next(x["competition_id"] for x in TEAMS if x["id"]==tid),"data_status":"SYNTHETIC_DEMO","pace":71.8,"ortg":116.2,"drtg":108.7,"net_rtg":7.5,"efg_pct":.566,"tov_pct":.129,"orb_pct":.274,"ftr":.218}


def _repo():
    try:
        return PostgresRepository()
    except Exception:
        return None

@app.get("/api/v1/snapshots/current")
def current_snapshot(competition_id="lba-2026-27"):
    repo=_repo()
    if repo is not None:
        try:
            row=repo.current_snapshot(competition_id)
            repo.close()
            if row: return row
        except Exception:
            if repo: repo.close()
    return {"competition_id":competition_id,"status":"DEMO_FALLBACK","version":"demo-2026-27","verified_game_count":0,"message":"PostgreSQL snapshot not available; serving demo dataset."}

# Live-source adapters for NBA and LBA. Existing demo analytics endpoints remain explicitly marked.
from .providers import nba_scoreboard, nba_boxscore, nba_season_player_analytics, lba_csv_games, lba_csv_summary, lba_current_analytics
from .lba_results import load_lba_results

@app.get("/api/v1/providers")
def providers_status():
    import os
    from pathlib import Path
    data_dir = Path(os.getenv("BASKETBALLSCRAPER_DATA_DIR", "./data/basketballscraper"))
    csv_count = len(list(data_dir.rglob("*.csv"))) if data_dir.exists() else 0
    return {"providers": [
        {"league":"NBA", "provider":"ESPN public scoreboard JSON", "status":"READY", "requires_api_key":False,
         "coverage":"Calendario, stato e punteggi; non tutte le statistiche avanzate"},
        {"league":"LBA", "provider":"BasketballScrapeR CSV import", "status":"DATA_IMPORTED" if csv_count else "WAITING_FOR_IMPORT",
         "requires_api_key":False, "csv_files":csv_count,
         "results_snapshot_status":load_lba_results().get("data_status"),
         "results_snapshot_games":load_lba_results().get("game_count", 0),
         "results_endpoint":"/api/v1/live/lba/results", "standings_endpoint":"/api/v1/live/lba/standings",
         "repository":"https://github.com/francescoolivo/BasketballScrapeR"}
    ], "demo_data_notice":"Gli endpoint legacy leaderboards/player/shot-chart continuano a usare fixture demo finché non viene completata la normalizzazione dei boxscore reali."}

@app.get("/api/v1/live/nba/scoreboard")
def live_nba_scoreboard(date: str | None = None):
    return nba_scoreboard(date=date)


@app.get("/api/v1/live/nba/boxscore/{event_id}")
def live_nba_boxscore(event_id: str):
    """Player box score for one NBA event returned by the live scoreboard."""
    return nba_boxscore(event_id=event_id)

@app.get("/api/v1/live/nba/players/advanced")
def live_nba_player_analytics(data_dir: str | None = None):
    """Current-season player leaders aggregated from persisted real ESPN box scores."""
    return nba_season_player_analytics(data_dir=data_dir)

@app.get("/api/v1/live/lba/imported")
def live_lba_imported(data_dir: str | None = None):
    return lba_csv_games(data_dir=data_dir)


@app.get("/api/v1/live/lba/summary")
def live_lba_summary(data_dir: str | None = None):
    """Inventory of imported LBA CSV files; does not treat raw rows as normalized statistics."""
    return lba_csv_summary(data_dir=data_dir)


@app.get("/api/v1/live/lba/analytics")
def live_lba_analytics(data_dir: str | None = None):
    """Conservative player stats derived only from recognized current-season CSVs."""
    return lba_current_analytics(data_dir=data_dir)


# Verified current-season LBA results and computed standings (separate from player-demo data).
from .lba_results import load_lba_results, lba_standings

@app.get("/api/v1/live/lba/results")
def live_lba_results(data_file: str | None = None):
    return load_lba_results(data_file=data_file)

@app.get("/api/v1/live/lba/standings")
def live_lba_standings(data_file: str | None = None):
    return lba_standings(data_file=data_file)

@app.get("/api/v1/refresh/status")
def data_refresh_status():
    """Last scheduled refresh attempts and outcomes for NBA and LBA."""
    from .refresh import refresh_status
    return refresh_status()

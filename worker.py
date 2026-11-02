"""Celery jobs for current-season basketball data refresh."""
import os
from datetime import datetime, timezone
import httpx
from celery import Celery
from celery.schedules import crontab

BROKER = os.getenv("REDIS_BROKER_URL", "redis://localhost:6379/0")
SOURCES = [
    {"competition_id":"lba-2026-27","name":"LBA","url":"https://www.legabasket.it/competizioni"},
    {"competition_id":"a2-2026-27","name":"Serie A2 LNP","url":"https://www.legapallacanestro.com/serie/1/calendario"},
]
celery_app = Celery("italian_basketball_stats", broker=BROKER, backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"))
celery_app.conf.update(
    timezone="Europe/Rome", enable_utc=True, task_serializer="json", accept_content=["json"], result_serializer="json",
    beat_schedule={
        "nba-scoreboard-daily-0800-italy": {"task":"app.worker.refresh_nba","schedule":crontab(minute=0, hour=8),"options":{"queue":"scrapers_queue"}},
        "lba-results-every-3-hours": {"task":"app.worker.refresh_lba_results","schedule":crontab(minute=35, hour="*/3"),"options":{"queue":"scrapers_queue"}},
        "lba-boxscores-nightly": {"task":"app.worker.refresh_lba","schedule":crontab(hour=2, minute=20),"options":{"queue":"scrapers_queue"}},
        "italian-source-check-nightly": {"task":"app.worker.check_italian_sources","schedule":crontab(hour=2, minute=0),"options":{"queue":"scrapers_queue"}},
    },
    task_routes={"app.worker.check_italian_sources":{"queue":"scrapers_queue"},"app.worker.refresh_nba":{"queue":"scrapers_queue"},"app.worker.refresh_lba":{"queue":"scrapers_queue"},"app.worker.refresh_lba_results":{"queue":"scrapers_queue"}},
)

@celery_app.task(name="app.worker.refresh_nba", bind=True, max_retries=1, default_retry_delay=120)
def refresh_nba(self):
    from .refresh import refresh_nba_scoreboards
    return refresh_nba_scoreboards()

@celery_app.task(name="app.worker.refresh_lba_results", bind=True, max_retries=1, default_retry_delay=120)
def refresh_lba_results(self):
    from .refresh import refresh_lba_results as run_refresh
    return run_refresh()

@celery_app.task(name="app.worker.refresh_lba", bind=True, max_retries=1, default_retry_delay=300)
def refresh_lba(self):
    from .refresh import refresh_lba_boxscores
    return refresh_lba_boxscores()

@celery_app.task(name="app.worker.check_italian_sources", bind=True, max_retries=1, default_retry_delay=120)
def check_italian_sources(self):
    results=[]
    for source in SOURCES:
        item={**source,"checked_at":datetime.now(timezone.utc).isoformat(),"reachable":False,"http_status":None}
        try:
            r=httpx.get(source["url"],timeout=8,follow_redirects=True,headers={"User-Agent":"ItalianBasketballAnalytics/0.3 source-check"})
            item["http_status"]=r.status_code; item["reachable"]=r.status_code<400
            item["status"]="REACHABLE_NOT_INGESTED" if item["reachable"] else "SOURCE_ERROR"
        except httpx.HTTPError as exc:
            item["status"]="UNREACHABLE"; item["error"]=type(exc).__name__
        results.append(item)
    return {"mode":"SOURCE_CHECK_ONLY","checked_at":datetime.now(timezone.utc).isoformat(),"sources":results,
            "note":"Il controllo verifica la raggiungibilità, non importa statistiche."}

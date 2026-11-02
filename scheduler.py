"""Local schedule constants and a safe manual entry point for smoke tests."""
NIGHTLY_INGESTION_HOUR_ITALY = 8
NIGHTLY_INGESTION_MINUTE_ITALY = 0
NIGHTLY_INGESTION_TIMEZONE = "Europe/Rome"

def run_once():
    from .refresh import refresh_nba_scoreboards
    return refresh_nba_scoreboards()

from app.analytics.metrics import PossessionInputs, possessions, true_shooting_pct, effective_fg_pct, summarize_team_box

def test_fiba_fallback_possessions():
    assert possessions(PossessionInputs(70, 20, 10, 8)) == 76.8

def test_shooting_metrics():
    assert round(true_shooting_pct(100, 80, 20), 6) == round(100 / (2 * (80 + 8.8)), 6)
    assert effective_fg_pct(32, 50, 12) == 0.76

def test_team_summary_is_deterministic():
    a = summarize_team_box(84, 68, 18, 10, 9, 32, 10)
    b = summarize_team_box(84, 68, 18, 10, 9, 32, 10)
    assert a == b
    assert a["possessions"] == 74.92

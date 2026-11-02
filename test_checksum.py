from app.checksum import ChecksumGate

def test_valid_box_score_passes():
    r=ChecksumGate().validate({"player_points":[60,40],"team_score":100,"player_reb":[20,15],"team_reb":5,"official_team_reb":40,"player_tov":[5,3],"team_tov":2,"official_team_tov":10,"player_pf":[8,7],"official_team_pf":15})
    assert r["verified"] and not r["errors"]

def test_points_mismatch_is_rejected():
    r=ChecksumGate().validate({"player_points":[60,39],"team_score":100,"player_reb":[20],"team_reb":0,"official_team_reb":20,"player_tov":[5],"team_tov":0,"official_team_tov":5,"player_pf":[5],"official_team_pf":5})
    assert not r["verified"]

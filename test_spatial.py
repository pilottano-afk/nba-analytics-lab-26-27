from app.spatial import *
def test_normalize(): assert normalize_euroleague(750,157.5)==(0,1.575)
def test_zones(): assert classify_shot_zone(0,2)=="RESTRICTED_AREA"; assert classify_shot_zone(-6.8,2.2)=="CORNER_3_LEFT"; assert classify_shot_zone(0,8.5)=="ABOVE_THE_BREAK_3"
def test_distance(): assert round(shot_distance(0,1.575),3)==0

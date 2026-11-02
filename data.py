import random
from .spatial import classify_shot_zone,shot_distance
COMPETITIONS=[
 {"id":"lba-2026-27","code":"LBA","name":"Serie A LBA","season":"2026/27","source_url":"https://www.legabasket.it/calendario/1/serie-a"},
 {"id":"a2-2026-27","code":"A2","name":"Serie A2 Old Wild West","season":"2026/27","source_url":"https://www.legapallacanestro.com/serie/1/calendario"},
]
TEAMS=[
 {"id":"lba-udine","name":"APU Old Wild West Udine","short_code":"UDN","competition_id":"lba-2026-27"},
 {"id":"lba-milano","name":"EA7 Emporio Armani Milano","short_code":"MIL","competition_id":"lba-2026-27"},
 {"id":"lba-bologna","name":"Virtus Bologna","short_code":"VBO","competition_id":"lba-2026-27"},
 {"id":"lba-venezia","name":"Umana Reyer Venezia","short_code":"VEN","competition_id":"lba-2026-27"},
 {"id":"a2-fortitudo","name":"Fortitudo Bologna","short_code":"FBO","competition_id":"a2-2026-27"},
 {"id":"a2-rimini","name":"Dole Basket Rimini","short_code":"RIM","competition_id":"a2-2026-27"},
 {"id":"a2-brindisi","name":"Valtur Brindisi","short_code":"BRI","competition_id":"a2-2026-27"},
 {"id":"a2-livorno","name":"Libertas Livorno","short_code":"LIV","competition_id":"a2-2026-27"},
]
# Player profiles and all player statistics below are synthetic fixtures, never official player data.
PLAYERS=[
 {"id":"p1","full_name":"Giocatore Demo 01","primary_position":"GUARD","team_id":"lba-udine","team":"APU Old Wild West Udine","competition_id":"lba-2026-27"},
 {"id":"p2","full_name":"Giocatore Demo 02","primary_position":"WING","team_id":"lba-milano","team":"EA7 Emporio Armani Milano","competition_id":"lba-2026-27"},
 {"id":"p3","full_name":"Giocatore Demo 03","primary_position":"GUARD","team_id":"lba-bologna","team":"Virtus Bologna","competition_id":"lba-2026-27"},
 {"id":"p4","full_name":"Giocatore Demo 04","primary_position":"BIG","team_id":"lba-venezia","team":"Umana Reyer Venezia","competition_id":"lba-2026-27"},
 {"id":"p5","full_name":"Giocatore Demo 05","primary_position":"WING","team_id":"lba-udine","team":"APU Old Wild West Udine","competition_id":"lba-2026-27"},
 {"id":"p6","full_name":"Giocatore Demo 06","primary_position":"BIG","team_id":"lba-milano","team":"EA7 Emporio Armani Milano","competition_id":"lba-2026-27"},
 {"id":"p7","full_name":"Giocatore Demo A2-01","primary_position":"GUARD","team_id":"a2-fortitudo","team":"Fortitudo Bologna","competition_id":"a2-2026-27"},
 {"id":"p8","full_name":"Giocatore Demo A2-02","primary_position":"WING","team_id":"a2-rimini","team":"Dole Basket Rimini","competition_id":"a2-2026-27"},
 {"id":"p9","full_name":"Giocatore Demo A2-03","primary_position":"GUARD","team_id":"a2-brindisi","team":"Valtur Brindisi","competition_id":"a2-2026-27"},
 {"id":"p10","full_name":"Giocatore Demo A2-04","primary_position":"BIG","team_id":"a2-livorno","team":"Libertas Livorno","competition_id":"a2-2026-27"},
 {"id":"p11","full_name":"Giocatore Demo A2-05","primary_position":"WING","team_id":"a2-fortitudo","team":"Fortitudo Bologna","competition_id":"a2-2026-27"},
 {"id":"p12","full_name":"Giocatore Demo A2-06","primary_position":"BIG","team_id":"a2-rimini","team":"Dole Basket Rimini","competition_id":"a2-2026-27"},
]
PLAYER_STATS={
"p1":{"games_played":9,"minutes_per_game":29.1,"ortg":121.4,"drtg":108.2,"net_rtg":13.2,"ts_pct":.624,"efg_pct":.581,"usg_pct":27.8,"ast_pct":25.4,"trb_pct":7.2,"stl_pct":2.1,"blk_pct":.7},
"p2":{"games_played":10,"minutes_per_game":31.0,"ortg":118.7,"drtg":105.6,"net_rtg":13.1,"ts_pct":.611,"efg_pct":.563,"usg_pct":24.1,"ast_pct":19.2,"trb_pct":10.3,"stl_pct":1.8,"blk_pct":1.1},
"p3":{"games_played":8,"minutes_per_game":28.4,"ortg":115.2,"drtg":109.8,"net_rtg":5.4,"ts_pct":.598,"efg_pct":.554,"usg_pct":26.2,"ast_pct":22.8,"trb_pct":6.8,"stl_pct":2.5,"blk_pct":.4},
"p4":{"games_played":10,"minutes_per_game":27.2,"ortg":119.1,"drtg":104.7,"net_rtg":14.4,"ts_pct":.671,"efg_pct":.642,"usg_pct":23.5,"ast_pct":11.4,"trb_pct":16.8,"stl_pct":1.1,"blk_pct":3.4},
"p5":{"games_played":7,"minutes_per_game":24.8,"ortg":112.6,"drtg":111.2,"net_rtg":1.4,"ts_pct":.574,"efg_pct":.538,"usg_pct":20.1,"ast_pct":15.7,"trb_pct":9.4,"stl_pct":1.6,"blk_pct":1.0},
"p6":{"games_played":9,"minutes_per_game":22.6,"ortg":110.8,"drtg":106.9,"net_rtg":3.9,"ts_pct":.592,"efg_pct":.567,"usg_pct":18.8,"ast_pct":10.8,"trb_pct":14.7,"stl_pct":1.4,"blk_pct":2.9}}
PERCENTILES={"p1":[92,88,81,76,79,74,91,83,62,71,58],"p2":[84,82,76,69,74,81,78,79,73,68,66],"p3":[88,79,72,73,70,76,85,77,60,74,51],"p4":[77,95,93,52,68,62,61,71,96,59,91],"p5":[69,72,65,61,63,70,67,74,71,64,60],"p6":[61,75,88,48,57,64,52,68,89,57,84]}
# A2 demo rows reuse the shape of the synthetic LBA fixtures with small deterministic offsets.
for new_id, source_id in zip(["p7","p8","p9","p10","p11","p12"],["p1","p2","p3","p4","p5","p6"]):
    PLAYER_STATS[new_id] = {k:(round(v + (0.8 if k == "net_rtg" else 0.0), 1) if isinstance(v, float) else v) for k,v in PLAYER_STATS[source_id].items()}
    PERCENTILES[new_id] = list(PERCENTILES[source_id])
PERCENTILE_LABELS=["Volume","TS%","Rim Finishing","3PT Volume","3PT Accuracy","AST%","Low TOV","USG%","TRB%","STL%","BLK%"]
def make_shots():
    rng=random.Random(42); zones=[(-.7,2),(-1.5,4.2),(.2,5.2),(-6.9,2.2),(6.9,2.3),(-3.5,6),(3.8,6.1),(0,8.2)]; shots=[]
    for i in range(42):
        cx,cy=zones[i%8]; x=max(-7.35,min(7.35,cx+rng.uniform(-.55,.55))); y=max(.1,min(13.8,cy+rng.uniform(-.4,.5)))
        d=shot_distance(x,y); made=rng.random()<(0.62 if d<5.8 else .39); q=i%4+1; clock=rng.randint(8,590)
        shots.append({"id":f"s{i+1}","x":round(x,3),"y":round(y,3),"zone_id":classify_shot_zone(x,y),"period":q,"clock":clock,"is_made":made,"is_clutch":q==4 and clock<=300 and rng.randint(-6,6)<=5,"shot_distance_m":round(d,2),"shot_type":"3PT" if d>=6.75 or abs(x)>=6.6 else "2PT","score_margin":rng.randint(-8,8)})
    return shots
SHOTS={p:make_shots() for p in PLAYER_STATS}
def leaderboard(competition_id=None):
    rows=[{**p,**PLAYER_STATS[p["id"]]} for p in PLAYERS if competition_id is None or p["competition_id"] == competition_id]
    return sorted(rows,key=lambda x:x["net_rtg"],reverse=True)
def filter_shots(pid,quarter="all",outcome="all",clutch=False):
    s=SHOTS[pid]
    if quarter!="all":s=[x for x in s if str(x["period"])==str(quarter)]
    if outcome=="made":s=[x for x in s if x["is_made"]]
    if outcome=="missed":s=[x for x in s if not x["is_made"]]
    if clutch:s=[x for x in s if x["is_clutch"]]
    return s

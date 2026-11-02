def validate_box_score(player_points, team_score, player_reb, team_reb_adjustment, official_team_reb,
                         player_tov, team_tov_adjustment, official_team_tov, player_pf, official_team_pf):
    errors=[]
    if sum(player_points)!=team_score: errors.append(f"PTS mismatch: {sum(player_points)} != {team_score}")
    if sum(player_reb)+team_reb_adjustment!=official_team_reb: errors.append("REB mismatch")
    if sum(player_tov)+team_tov_adjustment!=official_team_tov: errors.append("TOV mismatch")
    if sum(player_pf)!=official_team_pf: errors.append("PF mismatch")
    return {"verified":not errors,"errors":errors}

class ChecksumGate:
    def validate(self,payload):
        return validate_box_score(payload["player_points"],payload["team_score"],payload["player_reb"],payload.get("team_reb",0),payload["official_team_reb"],payload["player_tov"],payload.get("team_tov",0),payload["official_team_tov"],payload["player_pf"],payload["official_team_pf"])

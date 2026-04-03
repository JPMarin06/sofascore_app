import pandas as pd
import numpy as np


def parse_statistics(raw, home_team, away_team):
    if not raw or "statistics" not in raw:
        return pd.DataFrame()
    rows = []
    for period in raw["statistics"]:
        pname = period.get("period", "ALL")
        for group in period.get("groups", []):
            gname = group.get("groupName", "")
            for s in group.get("statisticsItems", []):
                rows.append({
                    "period": pname, "group": gname,
                    "stat": s.get("name", ""), "key": s.get("key", ""),
                    home_team: s.get("home"), away_team: s.get("away"),
                    "home_value": s.get("homeValue"), "away_value": s.get("awayValue"),
                    "compare_code": s.get("compareCode"),
                    "stat_type": s.get("statisticsType", ""),
                })
    return pd.DataFrame(rows)


def parse_incidents(raw, home_team, away_team):
    if not raw or "incidents" not in raw:
        return pd.DataFrame()
    rows = []
    for inc in raw["incidents"]:
        ts = inc.get("isHome")
        team = home_team if ts else (away_team if ts is not None else "N/A")
        pl = inc.get("player", {}) or {}
        pi = inc.get("playerIn", {}) or {}
        po = inc.get("playerOut", {}) or {}
        rows.append({
            "minute": inc.get("time"), "added_time": inc.get("addedTime"),
            "type": inc.get("incidentType", ""), "team": team,
            "player": pl.get("name", pi.get("name", "")),
            "player_in": pi.get("name", ""), "player_out": po.get("name", ""),
            "detail": inc.get("incidentClass", inc.get("description", "")),
            "is_home": ts,
        })
    return pd.DataFrame(rows).sort_values("minute").reset_index(drop=True)


def parse_lineups(raw, home_team, away_team):
    if not raw:
        return pd.DataFrame()
    rows = []
    for side, tname in [("home", home_team), ("away", away_team)]:
        for p in raw.get(side, {}).get("players", []):
            pi = p.get("player", {})
            s = p.get("statistics", {})
            rows.append({
                "team": tname, "side": side,
                "player_id": pi.get("id"), "player_name": pi.get("name", ""),
                "short_name": pi.get("shortName", ""),
                "position": p.get("position", ""),
                "jersey_number": p.get("jerseyNumber"),
                "is_starter": not p.get("substitute", True),
                "rating": s.get("rating"), "minutes_played": s.get("minutesPlayed"),
                "goals": s.get("goals", 0), "assists": s.get("goalAssist", 0),
                "shots_on_target": s.get("onTargetScoringAttempt", 0),
                "shots_off_target": s.get("shotOffTarget", 0),
                "big_chances": s.get("bigChanceCreated", 0),
                "xg": s.get("expectedGoals"), "xa": s.get("expectedAssists"),
                "passes_total": s.get("totalPass", 0),
                "passes_accurate": s.get("accuratePass", 0),
                "key_passes": s.get("keyPass", 0),
                "long_balls": s.get("accurateLongBalls", 0),
                "crosses": s.get("accurateCross", 0),
                "tackles": s.get("totalTackle", 0),
                "interceptions": s.get("interceptionWon", 0),
                "clearances": s.get("totalClearance", 0),
                "duels_won": s.get("duelWon", 0), "duels_lost": s.get("duelLost", 0),
                "aerial_won": s.get("aerialWon", 0), "aerial_lost": s.get("aerialLost", 0),
                "dribbles_won": s.get("wonContest", 0),
                "dribbles_lost": s.get("lostContest", 0),
                "yellow_cards": s.get("yellowCard", 0), "red_cards": s.get("redCard", 0),
                "fouls_committed": s.get("foulsCommited", 0),
                "fouls_won": s.get("wasFouled", 0),
                "saves": s.get("saves", 0),
                "goals_conceded": s.get("goalsConceded", 0),
                "avg_x": p.get("averageX"), "avg_y": p.get("averageY"),
            })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["pass_accuracy"] = np.where(
        df["passes_total"] > 0,
        (df["passes_accurate"] / df["passes_total"] * 100).round(1), 0
    )
    df["duel_win_rate"] = np.where(
        (df["duels_won"] + df["duels_lost"]) > 0,
        (df["duels_won"] / (df["duels_won"] + df["duels_lost"]) * 100).round(1), 0
    )
    return df


def parse_shotmap(raw, home_team, away_team):
    if not raw or "shotmap" not in raw:
        return pd.DataFrame()
    rows = []
    for shot in raw["shotmap"]:
        pl = shot.get("player", {}) or {}
        co = shot.get("playerCoordinates", {}) or {}
        rows.append({
            "player_id": pl.get("id"), "player_name": pl.get("name", ""),
            "team": home_team if shot.get("isHome") else away_team,
            "is_home": shot.get("isHome"), "minute": shot.get("time"),
            "shot_type": shot.get("shotType", ""),
            "situation": shot.get("situation", ""),
            "body_part": shot.get("bodyPart", ""),
            "goal_mouth_x": shot.get("goalMouthX"),
            "goal_mouth_y": shot.get("goalMouthY"),
            "player_coord_x": co.get("x"), "player_coord_y": co.get("y"),
            "xg": shot.get("xg"),
            "xgot": shot.get("xgot"),
            "is_goal": shot.get("shotType", "") == "goal",
        })
    return pd.DataFrame(rows)

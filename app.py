import pandas as pd
import requests
from datetime import datetime
import numpy as np

# -----------------------------
# CONFIG
# -----------------------------
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
TEAM_RPG_URL = "https://www.teamrankings.com/mlb/stat/runs-per-game"
TEAM_RPGA_URL = "https://www.teamrankings.com/mlb/stat/opponent-runs-per-game"
BULLPEN_URL = "https://www.covers.com/sport/baseball/mlb/statistics/team-bullpenera/2025"
SP_CSV_URL = "https://www.fangraphs.com/leaders.aspx?pos=all&stats=sta&lg=all&qual=0&type=8&season=2025&month=0&season1=2025&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=2025-01-01&enddate=2025-12-31&sort=20,d&csv=1"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# -----------------------------
# SCRAPING FUNCTIONS
# -----------------------------

def get_mlb_schedule():
    today = datetime.now().strftime("%Y%m%d")
    resp = requests.get(f"{ESPN_URL}?dates={today}").json()
    games = []

    for event in resp.get("events", []):
        comp = event["competitions"][0]
        home = comp["competitors"][0]
        away = comp["competitors"][1]

        home_pitcher = home.get("probables", [{}])[0].get("athlete", {}).get("displayName", "TBD")
        away_pitcher = away.get("probables", [{}])[0].get("athlete", {}).get("displayName", "TBD")

        game_time = datetime.fromisoformat(comp["date"][:-1]).strftime("%I:%M %p")
        ou = comp.get("odds", [{}])[0].get("overUnder", None)

        games.append({
            "Game Time": game_time,
            "Away Team": away["team"]["displayName"],
            "Home Team": home["team"]["displayName"],
            "Away Pitcher": away_pitcher,
            "Home Pitcher": home_pitcher,
            "Book O/U": ou
        })

    return pd.DataFrame(games)

def scrape_team_rpg():
    try:
        df = pd.read_html(TEAM_RPG_URL)[0][['Team', '2025']]
        df.columns = ['Team', 'RPG']
        return df
    except:
        return pd.DataFrame(columns=['Team','RPG'])

def scrape_bullpen_stats():
    try:
        df = pd.read_html(BULLPEN_URL)[0]
        df.columns = [c.strip() for c in df.columns]
        df = df[['Team', 'ERA', 'WHIP']]
        df.rename(columns={'ERA':'Bullpen_ERA','WHIP':'Bullpen_WHIP'}, inplace=True)
        return df
    except:
        return pd.DataFrame(columns=['Team','Bullpen_ERA','Bullpen_WHIP'])

def scrape_starting_pitchers():
    try:
        df = pd.read_csv(SP_CSV_URL)
        df = df[['Name','Team','ERA','FIP','WHIP']]
        df.rename(columns={'Name':'Pitcher'}, inplace=True)
        return df
    except:
        return pd.DataFrame(columns=['Pitcher','Team','ERA','FIP','WHIP'])

# -----------------------------
# MODEL CALCULATION
# -----------------------------

def calculate_daily_model():
    schedule = get_mlb_schedule()
    team_rpg = scrape_team_rpg()
    bullpen = scrape_bullpen_stats()
    sp_stats = scrape_starting_pitchers()

    if schedule.empty:
        return pd.DataFrame(columns=[
            "Game Time","Away Team","Away Score","Home Team","Home Score",
            "ML %","Book O/U","Model O/U","O/U Bet"
        ])

    merged = schedule.merge(sp_stats.add_prefix("Away_"), left_on="Away Pitcher", right_on="Away_Pitcher", how="left")\
                     .merge(sp_stats.add_prefix("Home_"), left_on="Home Pitcher", right_on="Home_Pitcher", how="left")

    merged = merged.merge(team_rpg, left_on="Away Team", right_on="Team", how="left").rename(columns={"RPG":"Away_RPG"}).drop(columns=["Team"])
    merged = merged.merge(team_rpg, left_on="Home Team", right_on="Team", how="left").rename(columns={"RPG":"Home_RPG"}).drop(columns=["Team"])

    merged = merged.merge(bullpen, left_on="Away Team", right_on="Team", how="left").rename(columns={"Bullpen_ERA":"Away_Bullpen_ERA"}).drop(columns=["Team","Bullpen_WHIP"])
    merged = merged.merge(bullpen, left_on="Home Team", right_on="Team", how="left").rename(columns={"Bullpen_ERA":"Home_Bullpen_ERA"}).drop(columns=["Team","Bullpen_WHIP"])

    # Expected runs
    merged["Away Exp Runs"] = (
        merged["Away_RPG"]*0.4 +
        merged["Home_ERA"]*0.3 +
        merged["Home_FIP"]*0.2 +
        merged["Home_Bullpen_ERA"]*0.1
    )
    merged["Home Exp Runs"] = (
        merged["Home_RPG"]*0.4 +
        merged["Away_ERA"]*0.3 +
        merged["Away_FIP"]*0.2 +
        merged["Away_Bullpen_ERA"]*0.1
    )

    merged["Model O/U"] = merged["Away Exp Runs"] + merged["Home Exp Runs"]

    # Betting Advice
    merged["O/U Bet"] = merged.apply(lambda x: (
        "BET THE OVER" if x["Model O/U"] >= (x["Book O/U"] or 0)+2
        else "BET THE UNDER" if x["Model O/U"] <= (x["Book O/U"] or 0)-2
        else "NO BET"
    ), axis=1)

    # -----------------------------
    # WIN PROBABILITY CALCULATION
    # -----------------------------
    run_diff = merged["Home Exp Runs"] - merged["Away Exp Runs"]
    merged["Home Win %"] = 1 / (1 + np.power(10, -run_diff/1.5))
    merged["Away Win %"] = 1 - merged["Home Win %"]

    # Pick team with higher win %
    merged["ML %"] = merged.apply(
        lambda x: f"{round(max(x['Home Win %'], x['Away Win %'])*100,1)}%", axis=1
    )

    merged["Away Score"] = 0
    merged["Home Score"] = 0

    display_cols = [
        "Game Time","Away Team","Away Score","Home Team","Home Score",
        "ML %","Book O/U","Model O/U","O/U Bet"
    ]
    return merged[display_cols]

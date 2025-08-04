import pandas as pd
import requests
from datetime import datetime

# -----------------------------
# URLs for scraping
# -----------------------------
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
TEAM_RPG_URL = "https://www.teamrankings.com/mlb/stat/runs-per-game"
TEAM_RPGA_URL = "https://www.teamrankings.com/mlb/stat/runs-allowed-per-game"
TEAM_WOBA_URL = "https://baseballsavant.mlb.com/leaderboard/team-batting?type=woba"
BULLPEN_URL = "https://www.mlb.com/stats/team/pitching/whip?split=rp&sortState=asc"

# -----------------------------
# Scraping Functions
# -----------------------------

def get_mlb_schedule():
    """Scrape ESPN for today's MLB games and odds"""
    today = datetime.now().strftime("%Y%m%d")
    resp = requests.get(f"{ESPN_URL}?dates={today}").json()
    games = []

    for event in resp.get("events", []

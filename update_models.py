import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# -----------------------
# DAILY MODEL SCRAPER
# -----------------------

def get_team_rpg():
    """Scrapes TeamRankings for Runs Per Game (Season and Last 5 Games)."""
    urls = {
        "RPG": "https://www.teamrankings.com/mlb/stat/runs-per-game",
        "RPG_Last5": "https://www.teamrankings.com/mlb/stat/runs-per-game?date=last-5"
    }

    data = {}
    for key, url in urls.items():
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")

        rows = soup.select("table.datatable tbody tr")
        for row in rows:
            cols = row.select("td")
            if len(cols) >= 2:
                team = cols[1].get_text(strip=True)
                stat = float(cols[2].get_text(strip=True))
                if team not in data:
                    data[team] = {}
                data[team][key] = stat

    return pd.DataFrame.from_dict(data, orient="index").reset_index().rename(columns={"index": "Team"})


def get_team_woba():
    """Scrapes Baseball Savant for team wOBA vs RHP (example URL for season)"""
    url = "https://baseballsavant.mlb.com/leaderboard/team-batting?type=team&year=2025&split=handedness&handedness=R"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.find("table")
    data = []
    if table:
        for row in table.select("tbody tr"):
            cols = [c.get_text(strip=True) for c in row.select("td")]
            if len(cols) >= 5:  # adjust based on real table layout
                team = cols[1]
                woba = cols[4]
                try:
                    woba = float(woba)
                except:
                    woba = None
                data.append([team, woba])

    return pd.DataFrame(data, columns=["Team", "wOBA"])


def get_bullpen_stats():
    """Scrapes FantasyTeamAdvisors for bullpen ERA & WHIP."""
    url = "https://fantasyteamadvisors.com/bullpen-mlb/"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.find("table")
    data = []
    if table:
        for row in table.select("tbody tr"):
            cols = [c.get_text(strip=True) for c in row.select("td")]
            if len(cols) >= 3:
                team = cols[0]
                era = float(cols[1]) if cols[1].replace(".","",1).isdigit() else None
                whip = float(cols[2]) if cols[2].replace(".","",1).isdigit() else None
                data.append([team, era, whip])

    return pd.DataFrame(data, columns=["Team", "Bullpen_ERA", "Bullpen_WHIP"])


def calculate_daily_model():
    """Combines all sources and computes the Daily Model output DataFrame."""
    # Step 1: Scrape data
    rpg_df = get_team_rpg()
    woba_df = get_team_woba()
    pen_df = get_bullpen_stats()

    # Merge team data
    team_data = rpg_df.merge(woba_df, on="Team", how="left").merge(pen_df, on="Team", how="left")

    # Step 2: Build sample games (placeholder: in live version, scrape ESPN schedule)
    games = [
        {"Game Time": "1:05 PM", "Away Team": "New York Yankees", "Home Team": "Boston Red Sox"},
        {"Game Time": "4:10 PM", "Away Team": "Chicago Cubs", "Home Team": "Los Angeles Dodgers"}
    ]
    df = pd.DataFrame(games)

    # Step 3: Compute fake model outputs (replace with your real formula)
    df["Pred Away Score"] = [4.3, 3.8]
    df["Pred Home Score"] = [5.1, 4.7]
    df["ML %"] = ["58%", "62%"]
    df["Book O/U"] = [8.5, 9.0]
    df["Model O/U"] = [9.4, 8.1]

    # O/U Bet logic
    def ou_pick(row):
        diff = row["Model O/U"] - row["Book O/U"]
        if diff >= 2:
            return "BET THE OVER"
        elif diff <= -2:
            return "BET THE UNDER"
        return "NO BET"

    df["O/U Bet"] = df.apply(ou_pick, axis=1)

    return df[[
        "Game Time", "Away Team", "Pred Away Score", "Home Team", "Pred Home Score",
        "ML %", "Book O/U", "Model O/U", "O/U Bet"
    ]]

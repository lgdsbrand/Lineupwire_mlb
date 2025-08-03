import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# -------------------------
# 1. Fetch MLB Schedule
# -------------------------
def fetch_mlb_schedule():
    today = datetime.now().strftime("%Y%m%d")
    url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates={today}"
    data = requests.get(url).json()

    games = []
    for event in data.get("events", []):
        game_time = datetime.fromisoformat(event["date"][:-1]).strftime("%I:%M %p ET")
        away_team = event["competitions"][0]["competitors"][1]["team"]["displayName"]
        home_team = event["competitions"][0]["competitors"][0]["team"]["displayName"]

        away_pitcher = "TBD"
        home_pitcher = "TBD"

        for comp in event["competitions"][0]["competitors"]:
            if "startingPitcher" in comp:
                pitcher_name = comp["startingPitcher"]["athlete"]["displayName"]
                if comp["homeAway"] == "home":
                    home_pitcher = pitcher_name
                else:
                    away_pitcher = pitcher_name

        games.append([game_time, away_team, home_team, away_pitcher, home_pitcher])

    return pd.DataFrame(games, columns=["Game Time", "Away Team", "Home Team", "Away Pitcher", "Home Pitcher"])


# -------------------------
# 2. Fetch Team NRFI Stats
# -------------------------
def fetch_team_nrfi_stats():
    url = "https://www.teamrankings.com/mlb/stat/1st-inning-runs-per-game"
    page = requests.get(url).text
    soup = BeautifulSoup(page, "html.parser")

    table = soup.find("table", {"class": "tr-table"})
    rows = table.find_all("tr")[1:]

    stats = {}
    for row in rows:
        cols = [c.text.strip() for c in row.find_all("td")]
        if len(cols) >= 2:
            team = cols[0]
            first_inning_runs = float(cols[1])
            stats[team] = first_inning_runs
    return stats


# -------------------------
# 3. NRFI Model Generator
# -------------------------
def generate_nrfi_model(schedule, team_stats):
    results = []
    for _, row in schedule.iterrows():
        away_team = row["Away Team"]
        home_team = row["Home Team"]

        away_rpg = team_stats.get(away_team, 0.5)
        home_rpg = team_stats.get(home_team, 0.5)

        away_nrfi = max(0.2, 1 - away_rpg / 1.0)
        home_nrfi = max(0.2, 1 - home_rpg / 1.0)

        nrfi_prob = round((away_nrfi * home_nrfi) * 100, 0)
        pick = "NRFI" if nrfi_prob >= 55 else "YRFI"

        results.append([
            row["Game Time"], away_team, home_team, row["Away Pitcher"], row["Home Pitcher"], pick, nrfi_prob
        ])

    df = pd.DataFrame(results, columns=[
        "Game Time", "Away Team", "Home Team", "Away Pitcher", "Home Pitcher", "Pick", "Confidence"
    ])
    df.to_csv("nrfi_model.csv", index=False)
    print("✅ NRFI model updated!")


# -------------------------
# 4. Daily Model Generator
# -------------------------
def generate_daily_model(schedule):
    results = []
    for _, row in schedule.iterrows():
        away_team = row["Away Team"]
        home_team = row["Home Team"]

        # Example projections - replace with weighted/Monte Carlo logic
        away_score = 3.5
        home_score = 4.2

        winner = home_team if home_score > away_score else away_team
        win_pct = 65  # Placeholder until model logic is integrated

        model_ou = round(away_score + home_score, 1)
        book_ou = 8.5  # Placeholder for FanDuel scraping

        results.append([
            row["Game Time"], away_team, home_team,
            away_score, home_score,
            f"{winner} ({win_pct}%)", book_ou, model_ou
        ])

    df = pd.DataFrame(results, columns=[
        "Game Time", "Away Team", "Home Team",
        "Away Score Proj", "Home Score Proj",
        "ML Bet", "Book O/U", "Model O/U"
    ])
    df.to_csv("daily_model.csv", index=False)
    print("✅ Daily MLB model updated!")


# -------------------------
# 5. Run Both Models
# -------------------------
if __name__ == "__main__":
    schedule = fetch_mlb_schedule()
    team_stats = fetch_team_nrfi_stats()

    generate_nrfi_model(schedule, team_stats)
    generate_daily_model(schedule)

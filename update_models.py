import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# -----------------------------
# CONFIG
# -----------------------------
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
FANDUEL_URL = "https://sportsbook.fanduel.com/cache/psmg/UK/2/baseball/mlb"
TEAMRANKINGS_BASE = "https://www.teamrankings.com/mlb/stat/"

def get_espn_games():
    """Scrape ESPN for today's MLB games, teams, pitchers, and times"""
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

        games.append({
            "Game Time": game_time,
            "Matchup": f"{away['team']['displayName']} @ {home['team']['displayName']}",
            "Home Team": home['team']['displayName'],
            "Away Team": away['team']['displayName'],
            "Pitchers": f"{away_pitcher} vs {home_pitcher}",
            "Home Pitcher": home_pitcher,
            "Away Pitcher": away_pitcher
        })

    return pd.DataFrame(games)


def get_teamrankings_stat(endpoint):
    """Scrape TeamRankings for a specific stat table (returns DataFrame with Team and Value)"""
    url = TEAMRANKINGS_BASE + endpoint
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", {"class": "tr-table"})
    rows = table.find_all("tr")[1:]

    data = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            team = cols[1].text.strip()
            value = float(cols[2].text.strip())
            data.append((team, value))
    return pd.DataFrame(data, columns=["Team", endpoint])


def get_team_stats():
    """Scrape core stats needed for scoring model"""
    runs_scored = get_teamrankings_stat("runs-per-game")
    runs_allowed = get_teamrankings_stat("runs-allowed-per-game")
    home_runs = get_teamrankings_stat("home-runs-per-game")
    return runs_scored.merge(runs_allowed, on="Team").merge(home_runs, on="Team")


def calculate_daily_model():
    """Combine schedule + stats + simple scoring model"""
    games_df = get_espn_games()
    stats_df = get_team_stats()

    results = []
    for _, row in games_df.iterrows():
        # Skip TBD pitchers
        if "TBD" in row["Pitchers"]:
            results.append({
                "Game Time": row["Game Time"],
                "Matchup": row["Matchup"],
                "Pitchers": row["Pitchers"],
                "Pred Score": "",
                "Sportsbook O/U": "",
                "Model Total": "",
                "Pick": "TBD",
            })
            continue

        # Merge team stats
        home_stats = stats_df[stats_df["Team"].str.contains(row["Home Team"].split()[-1], case=False, na=False)]
        away_stats = stats_df[stats_df["Team"].str.contains(row["Away Team"].split()[-1], case=False, na=False)]

        # Simple scoring model: avg runs scored vs opponent avg runs allowed
        home_score = (home_stats["runs-per-game"].values[0] + away_stats["runs-allowed-per-game"].values[0]) / 2
        away_score = (away_stats["runs-per-game"].values[0] + home_stats["runs-allowed-per-game"].values[0]) / 2

        model_total = round(home_score + away_score, 1)

        # Sportsbook line placeholder (FanDuel scrape integration optional)
        sportsbook_total = model_total  # replace with real FanDuel scrape

        # Determine pick
        diff = model_total - sportsbook_total
        if diff >= 2:
            pick = "BET THE OVER"
        elif diff <= -2:
            pick = "BET THE UNDER"
        else:
            pick = "NO BET"

        results.append({
            "Game Time": row["Game Time"],
            "Matchup": row["Matchup"],
            "Pitchers": row["Pitchers"],
            "Pred Score": f"{round(away_score,1)} - {round(home_score,1)}",
            "Sportsbook O/U": sportsbook_total,
            "Model Total": model_total,
            "Pick": pick
        })

    return pd.DataFrame(results)

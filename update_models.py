import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# ESPN & TeamRankings
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
TEAMRANKINGS_BASE = "https://www.teamrankings.com/mlb/stat/"

def get_espn_games():
    """Scrape ESPN for today's MLB games"""
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
            "Home Team": home['team']['displayName'],
            "Away Team": away['team']['displayName'],
            "Home Pitcher": home_pitcher,
            "Away Pitcher": away_pitcher
        })

    return pd.DataFrame(games)


def get_teamrankings_stat(endpoint):
    """Scrape TeamRankings stat table"""
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
    return runs_scored.merge(runs_allowed, on="Team")


def calculate_daily_model():
    """Return fully automatic daily model with required columns"""
    games_df = get_espn_games()
    stats_df = get_team_stats()

    results = []
    for _, row in games_df.iterrows():
        # Skip TBD pitchers
        if "TBD" in row["Home Pitcher"] or "TBD" in row["Away Pitcher"]:
            results.append({
                "Game Time": row["Game Time"],
                "Away Team": row["Away Team"],
                "Away Score": "",
                "Home Team": row["Home Team"],
                "Home Score": "",
                "ML (%)": "",
                "Book O/U": "",
                "Model O/U": "",
                "O/U Bet": "TBD"
            })
            continue

        # Merge team stats (simple substring match for now)
        home_stats = stats_df[stats_df["Team"].str.contains(row["Home Team"].split()[-1], case=False, na=False)]
        away_stats = stats_df[stats_df["Team"].str.contains(row["Away Team"].split()[-1], case=False, na=False)]

        # Simple scoring model
        home_score = (home_stats["runs-per-game"].values[0] + away_stats["runs-allowed-per-game"].values[0]) / 2
        away_score = (away_stats["runs-per-game"].values[0] + home_stats["runs-allowed-per-game"].values[0]) / 2

        model_total = round(home_score + away_score, 1)

        # Calculate ML win probability (home team)
        home_prob = round((home_score / model_total) * 100, 1)

        # Sportsbook O/U placeholder (replace with FanDuel scrape if needed)
        book_total = model_total  

        # Determine pick
        diff = model_total - book_total
        if diff >= 2:
            pick = "BET THE OVER"
        elif diff <= -2:
            pick = "BET THE UNDER"
        else:
            pick = "NO BET"

        results.append({
            "Game Time": row["Game Time"],
            "Away Team": row["Away Team"],
            "Away Score": round(away_score, 1),
            "Home Team": row["Home Team"],
            "Home Score": round(home_score, 1),
            "ML (%)": home_prob,
            "Book O/U": book_total,
            "Model O/U": model_total,
            "O/U Bet": pick
        })

    return pd.DataFrame(results)

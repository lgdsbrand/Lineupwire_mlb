import pandas as pd
import requests
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
FANDUEL_URL = "https://sportsbook.fanduel.com/cache/psmg/UK/2/baseball/mlb"  # endpoint may need rotating proxy in production

# Model Weights
WEIGHT_TEAM_AVG = 0.4    # Team season runs per game
WEIGHT_PITCHER = 0.3     # Starting pitcher runs allowed / ERA
WEIGHT_BULLPEN = 0.2     # Bullpen runs allowed
WEIGHT_PARK = 0.1        # Ballpark scoring factor

# --------------------------------
# Scraping Functions
# --------------------------------
def get_espn_games():
    """Scrape ESPN for today's MLB games"""
    today = datetime.now().strftime("%Y%m%d")
    resp = requests.get(f"{ESPN_URL}?dates={today}").json()
    games = []
    for event in resp.get("events", []):
        comp = event["competitions"][0]
        home = comp["competitors"][0]
        away = comp["competitors"][1]

        # Game Time
        game_time = datetime.fromisoformat(comp["date"][:-1]).strftime("%I:%M %p")

        # Pitchers
        home_pitcher = home.get("probables", [{}])[0].get("athlete", {}).get("displayName", "TBD")
        away_pitcher = away.get("probables", [{}])[0].get("athlete", {}).get("displayName", "TBD")

        games.append({
            "Game Time": game_time,
            "Home Team": home['team']['displayName'],
            "Away Team": away['team']['displayName'],
            "Home Pitcher": home_pitcher,
            "Away Pitcher": away_pitcher
        })
    return pd.DataFrame(games)

def scrape_fanduel_ou():
    """Placeholder: returns dictionary of team matchup -> O/U line.
       Replace with real FanDuel scraper if needed."""
    return {}

# --------------------------------
# Model Calculation
# --------------------------------
def calculate_daily_model():
    games_df = get_espn_games()
    if games_df.empty:
        return pd.DataFrame(columns=[
            "Game Time","Away Team","Away Score","Home Team","Home Score",
            "ML (%)","Book O/U","Model O/U","O/U Bet"
        ])

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

        # -----------------------------
        # Dummy Stats for Formula (replace with your real data source)
        # -----------------------------
        team_runs_per_game_home = 4.5
        team_runs_per_game_away = 4.3
        pitcher_home_era = 3.8
        pitcher_away_era = 4.2
        bullpen_home_ra = 3.9
        bullpen_away_ra = 4.1
        park_factor = 1.02  # >1 favors runs, <1 favors pitchers

        # -----------------------------
        # Weighted Score Prediction
        # -----------------------------
        home_score = (
            team_runs_per_game_home * WEIGHT_TEAM_AVG +
            pitcher_away_era * WEIGHT_PITCHER +
            bullpen_away_ra * WEIGHT_BULLPEN
        ) * park_factor

        away_score = (
            team_runs_per_game_away * WEIGHT_TEAM_AVG +
            pitcher_home_era * WEIGHT_PITCHER +
            bullpen_home_ra * WEIGHT_BULLPEN
        ) * park_factor

        home_score = round(home_score, 1)
        away_score = round(away_score, 1)
        model_total = round(home_score + away_score, 1)

        # Moneyline Win Probability (approximate)
        home_prob = round((home_score / model_total) * 100, 1)

        # Sportsbook O/U (placeholder)
        book_total = 9.0

        # Determine O/U Bet
        diff = model_total - book_total
        if diff >= 2:
            ou_bet = "BET THE OVER"
        elif diff <= -2:
            ou_bet = "BET THE UNDER"
        else:
            ou_bet = "NO BET"

        results.append({
            "Game Time": row["Game Time"],
            "Away Team": row["Away Team"],
            "Away Score": away_score,
            "Home Team": row["Home Team"],
            "Home Score": home_score,
            "ML (%)": home_prob,
            "Book O/U": book_total,
            "Model O/U": model_total,
            "O/U Bet": ou_bet
        })

    return pd.DataFrame(results)

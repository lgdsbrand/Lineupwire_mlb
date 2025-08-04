import pandas as pd
import requests
from datetime import datetime

ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"

def calculate_daily_model():
    """Scrape MLB daily schedule and generate model predictions"""
    today = datetime.now().strftime("%Y%m%d")
    url = f"{ESPN_URL}?dates={today}"
    
    try:
        resp = requests.get(url).json()
    except:
        return pd.DataFrame(columns=[
            "Game Time","Away Team","Away Score","Home Team","Home Score",
            "ML (%)","Book O/U","Model O/U","O/U Bet"
        ])

    games = []
    for event in resp.get("events", []):
        comp = event.get("competitions", [{}])[0]
        if not comp:
            continue

        # Teams
        home = comp["competitors"][0]
        away = comp["competitors"][1]

        # Scores if available
        home_score = home.get("score", "0")
        away_score = away.get("score", "0")

        # Game Time in ET
        game_time = datetime.fromisoformat(comp["date"][:-1]).strftime("%I:%M %p")

        # Dummy model predictions
        model_total = 8.5  # Placeholder for your model O/U
        book_total = 9.0   # Placeholder for sportsbook O/U
        ml_pct = 55        # Placeholder for your ML % prediction

        # Determine O/U Bet
        if model_total >= book_total + 2:
            ou_bet = "BET THE OVER"
        elif model_total <= book_total - 2:
            ou_bet = "BET THE UNDER"
        else:
            ou_bet = "NO BET"

        games.append({
            "Game Time": game_time,
            "Away Team": away["team"]["displayName"],
            "Away Score": away_score,
            "Home Team": home["team"]["displayName"],
            "Home Score": home_score,
            "ML (%)": ml_pct,
            "Book O/U": book_total,
            "Model O/U": model_total,
            "O/U Bet": ou_bet
        })

    return pd.DataFrame(games)

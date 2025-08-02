import pandas as pd
import requests
from datetime import datetime

# ----------- MLB DAILY MODEL -----------
def fetch_daily_model():
    today = datetime.now().strftime("%Y%m%d")
    espn_url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates={today}"
    data = requests.get(espn_url).json()

    games = []
    for event in data.get("events", []):
        game_time = datetime.fromisoformat(event["date"].replace("Z", "+00:00")).strftime("%I:%M %p ET")
        away_team = event["competitions"][0]["competitors"][1]["team"]["displayName"]
        home_team = event["competitions"][0]["competitors"][0]["team"]["displayName"]

        # --- SIMPLE MODEL (replace with weighted formula) ---
        away_score = round(2.5 + len(away_team) % 4, 1)
        home_score = round(2.5 + len(home_team) % 4, 1)
        model_ou = round(away_score + home_score, 1)
        book_ou = model_ou - 0.5  # placeholder until odds API wired in

        home_win_prob = round((home_score / (home_score + away_score)) * 100)
        ml_display = f"{home_team if home_win_prob >= 50 else away_team} ({home_win_prob}%)"

        games.append([game_time, away_team, away_score, home_team, home_score,
                      ml_display, book_ou, model_ou])

    columns = ["Game Time", "Away Team", "Away Score Proj", "Home Team",
               "Home Score Proj", "ML Bet", "Book O/U", "Model O/U"]

    df = pd.DataFrame(games, columns=columns)
    df.to_csv("daily_model.csv", index=False)



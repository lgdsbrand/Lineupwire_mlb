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


# ----------- NRFI / YRFI MODEL -----------
def fetch_nrfi_model():
    today = datetime.now().strftime("%Y%m%d")
    espn_url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates={today}"
    data = requests.get(espn_url).json()

    games = []
    for event in data.get("events", []):
        game_time = datetime.fromisoformat(event["date"].replace("Z", "+00:00")).strftime("%I:%M %p ET")
        away_team = event["competitions"][0]["competitors"][1]["team"]["displayName"]
        home_team = event["competitions"][0]["competitors"][0]["team"]["displayName"]

        # --- Dummy NRFI/YRFI logic (replace w/ full formula) ---
        nrfi_conf = (len(away_team) + len(home_team)) % 100
        yrfi_conf = 100 - nrfi_conf
        pick = "NRFI" if nrfi_conf >= yrfi_conf else "YRFI"
        conf = max(nrfi_conf, yrfi_conf)

        games.append([game_time, away_team, home_team, pick, conf])

    columns = ["Game Time", "Away Team", "Home Team", "NRFI/YRFI", "Confidence"]
    df = pd.DataFrame(games, columns=columns)
    df.to_csv("nrfi_model.csv", index=False)


if __name__ == "__main__":
    fetch_daily_model()
    fetch_nrfi_model()
    print("✅ Models updated:", datetime.now())

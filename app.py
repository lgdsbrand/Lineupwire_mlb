import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(layout="wide")

# ---------------------------
# HEADER
# ---------------------------
st.markdown(
    """
    <style>
        .back-btn {
            background-color: black;
            color: white;
            padding: 8px 20px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: bold;
        }
        .back-btn:hover {
            background-color: #333;
        }
    </style>
    <a class="back-btn" href="https://lineupwire.com">⬅ Back to Homepage</a>
    """,
    unsafe_allow_html=True
)

st.markdown("<h1>⚾ MLB Daily Model</h1>", unsafe_allow_html=True)

# ---------------------------
# ESPN API - MLB Games Today
# ---------------------------
today = datetime.now().strftime("%Y%m%d")
url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates={today}"
data = requests.get(url).json()

games = []
for event in data.get("events", []):
    game_time = datetime.fromisoformat(event["date"].replace("Z", "+00:00")).strftime("%I:%M %p ET")
    away_team = event["competitions"][0]["competitors"][1]["team"]["displayName"]
    home_team = event["competitions"][0]["competitors"][0]["team"]["displayName"]
    
    # Dummy example model calculation
    # Replace with your weighted formula
    away_score = round(2.5 + len(away_team) % 4, 1)
    home_score = round(2.5 + len(home_team) % 4, 1)
    model_ou = round(away_score + home_score, 1)
    
    # Placeholder FanDuel scrape (replace with real odds if desired)
    book_ou = model_ou - 0.5
    
    # Model ML Bet
    home_win_prob = round((home_score / (home_score + away_score)) * 100)
    ml_bet = home_team if home_win_prob >= 50 else away_team
    ml_display = f"{ml_bet} ({home_win_prob}%)"

    games.append([
        game_time, away_team, away_score, home_team, home_score,
        ml_display, book_ou, model_ou
    ])

columns = ["Game Time", "Away Team", "Away Score Proj", "Home Team",
           "Home Score Proj", "ML Bet", "Book O/U", "Model O/U"]

df = pd.DataFrame(games, columns=columns)

st.dataframe(df, hide_index=True, use_container_width=True)

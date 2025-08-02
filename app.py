import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz

# --- PAGE CONFIG ---
st.set_page_config(page_title="MLB Daily Model", layout="wide")
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- BACK TO HOMEPAGE BUTTON ---
st.markdown("""
<div style="text-align: left; margin-bottom: 10px;">
    <a href="https://lineupwire.com" target="_self" 
       style="background-color: black; color: white; padding: 6px 16px; 
              border-radius: 12px; text-decoration: none;">
        ⬅ Back to Homepage
    </a>
</div>
""", unsafe_allow_html=True)

st.markdown("<h1 style='display: inline;'>⚾ MLB Daily Model</h1>", unsafe_allow_html=True)

# --- LOAD LIVE MLB SCHEDULE (ESPN) ---
@st.cache_data(ttl=3600)
def fetch_mlb_schedule():
    today = datetime.now().strftime("%Y%m%d")
    url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates={today}"
    r = requests.get(url)
    data = r.json()
    
    games = []
    est = pytz.timezone('US/Eastern')
    for event in data.get("events", []):
        game_time_utc = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
        game_time_est = game_time_utc.astimezone(est).strftime("%I:%M %p")

        competitions = event.get("competitions", [])[0]
        teams = competitions["competitors"]
        home_team = next(t["team"]["displayName"] for t in teams if t["homeAway"] == "home")
        away_team = next(t["team"]["displayName"] for t in teams if t["homeAway"] == "away")
        
        # --- MODEL SIMULATION PLACEHOLDER (replace with weighted formula logic) ---
        # Example projected scores (use your weighted stats logic)
        away_score = round(3 + len(away_team)%3 + 0.2, 1)
        home_score = round(4 + len(home_team)%3 + 0.3, 1)
        ml_winner = home_team if home_score > away_score else away_team
        ml_win_pct = 65 if home_score != away_score else 55
        book_ou = 8.5
        model_ou = round(away_score + home_score, 1)

        games.append([
            game_time_est,
            away_team, away_score,
            home_team, home_score,
            f"{ml_winner} ({ml_win_pct}%)",
            book_ou, model_ou
        ])

    df = pd.DataFrame(games, columns=[
        "Game Time", "Away Team", "Away Score Proj",
        "Home Team", "Home Score Proj", "ML Bet",
        "Book O/U", "Model O/U"
    ])
    return df

df = fetch_mlb_schedule()

# --- DISPLAY TABLE ---
st.dataframe(df, use_container_width=True, hide_index=True)

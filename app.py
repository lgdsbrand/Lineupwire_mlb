import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
import math

st.set_page_config(page_title="Daily MLB Model", layout="wide")

# -----------------------------
# Utility Functions
# -----------------------------

def fetch_espn_games():
    """Fetch today's MLB games from ESPN API"""
    today = datetime.now().strftime("%Y%m%d")
    url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates={today}"
    resp = requests.get(url)
    data = resp.json()

    games = []
    for event in data.get("events", []):
        comp = event.get("competitions", [])[0]
        competitors = comp.get("competitors", [])

        away = next((t for t in competitors if t["homeAway"] == "away"), None)
        home = next((t for t in competitors if t["homeAway"] == "home"), None)
        if not away or not home:
            continue

        game_time = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
        game_time = game_time.astimezone(pytz.timezone("US/Eastern")).strftime("%I:%M %p ET")

        games.append({
            "Game Time": game_time,
            "Away Team": away["team"]["displayName"],
            "Home Team": home["team"]["displayName"]
        })

    return pd.DataFrame(games)

def fetch_fanduel_odds():
    """
    Fetch MLB odds from FanDuel API.
    Returns dict with key=(AwayTeam,HomeTeam) and values BookML, BookOU.
    """
    try:
        url = "https://sportsbook.fanduel.com/cache/psmg/BASEBALL/MLB/Odds.json"
        resp = requests.get(url)
        data = resp.json()
        odds_map = {}

        for game in data.get("events", []):
            teams = game.get("participants", [])
            if len(teams) != 2:
                continue
            away = teams[0]["name"].strip()
            home = teams[1]["name"].strip()

            markets = game.get("markets", [])
            book_ml = ""
            book_ou = ""

            for m in markets:
                if "moneyline" in m["name"].lower():
                    book_ml = m["outcomes"][0]["price"]["american"]
                if "total" in m["name"].lower():
                    book_ou = m["outcomes"][0]["line"]

            odds_map[(away, home)] = {"Book ML": book_ml, "Book O/U": book_ou}

        return odds_map
    except:
        return {}

def model_projected_scores(df):
    """
    Compute model projected scores and win % using weighted stats.
    Currently using a simplified scoring proxy for demonstration.
    """

    # Example expected runs formula
    # In final build, this would use your weighted stats
    df["Away Score Proj"] = df["Away Team"].apply(lambda x: (len(x) % 5) + 2)
    df["Home Score Proj"] = df["Home Team"].apply(lambda x: (len(x) % 5) + 2)

    # Compute Model O/U
    df["Model O/U"] = df["Away Score Proj"] + df["Home Score Proj"]

    # Determine winner and model ML%
    df["ML Bet"] = df.apply(lambda x: x["Away Team"] if x["Away Score Proj"] > x["Home Score Proj"] else x["Home Team"], axis=1)
    max_runs = df[["Away Score Proj", "Home Score Proj"]].max(axis=1)
    df["Model Win %"] = (max_runs / df["Model O/U"]) * 100
    df["Model Win %"] = df["Model Win %"].round().astype(int)

    return df

def highlight_win(val):
    """Highlight ML Win % green if ≥65"""
    try:
        val = int(val)
        if val >= 65:
            return "color: green; font-weight: bold"
    except:
        return ""
    return ""

# -----------------------------
# Main App
# -----------------------------
st.title("⚾ Daily MLB Model (Table View)")

games_df = fetch_espn_games()

if games_df.empty:
    st.info("No MLB games available right now. Check back after the next refresh.")
else:
    # Compute projections
    games_df = model_projected_scores(games_df)

    # Merge in FanDuel odds if available
    odds_map = fetch_fanduel_odds()
    games_df["Book ML"] = ""
    games_df["Book O/U"] = ""

    for idx, row in games_df.iterrows():
        key = (row["Away Team"], row["Home Team"])
        if key in odds_map:
            games_df.loc[idx, "Book ML"] = odds_map[key]["Book ML"]
            games_df.loc[idx, "Book O/U"] = odds_map[key]["Book O/U"]

    # Reorder columns for display
    games_df = games_df[[
        "Game Time", "Away Team", "Away Score Proj",
        "Home Team", "Home Score Proj",
        "ML Bet", "Model Win %", "Book ML", "Book O/U", "Model O/U"
    ]]

    # Whole numbers only
    for col in ["Away Score Proj", "Home Score Proj", "Model O/U"]:
        games_df[col] = games_df[col].astype(int)

    # Display formatted table
    st.dataframe(
        games_df.style.applymap(highlight_win, subset=["Model Win %"]),
        use_container_width=True,
        hide_index=True
    )

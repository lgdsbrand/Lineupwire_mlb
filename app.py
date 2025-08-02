import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz

st.set_page_config(page_title="LineupWire MLB Model — Daily Predictions", layout="wide")

st.title("📊 LineupWire MLB Model — Daily Predictions (Table View)")

# -----------------------------
# Fetch MLB Games from ESPN
# -----------------------------
def fetch_espn_games():
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

# -----------------------------
# Fetch FanDuel O/U Odds
# -----------------------------
def fetch_fanduel_odds():
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
            book_ou = ""

            for m in markets:
                if "total" in m["name"].lower():
                    book_ou = m["outcomes"][0]["line"]

            odds_map[(away, home)] = {"Book O/U": book_ou}

        return odds_map
    except:
        return {}

# -----------------------------
# Full Weighted Model for Projected Scores
# -----------------------------
def model_projected_scores(df):
    # Replace this logic with your exact stat-weighted calculations if needed
    # Example: Weighted sum of RPG, RPGA, SP, bullpen, and park/weather adjustments

    def project_score(team_name, home=True):
        # Simulated weighted formula: modify to actual model coefficients
        base_rpg = len(team_name) % 5 + (2.5 if home else 2.3)
        # Example small boost for home team
        return base_rpg

    df["Away Score Proj"] = df["Away Team"].apply(lambda x: project_score(x, home=False))
    df["Home Score Proj"] = df["Home Team"].apply(lambda x: project_score(x, home=True))

    df["Model O/U"] = df["Away Score Proj"] + df["Home Score Proj"]

    # Determine ML Bet & Confidence %
    df["ML Bet"] = df.apply(
        lambda x: x["Away Team"] if x["Away Score Proj"] > x["Home Score Proj"] else x["Home Team"],
        axis=1
    )
    df["Confidence"] = (
        df[["Away Score Proj", "Home Score Proj"]].max(axis=1) / df["Model O/U"] * 100
    ).round().astype(int)

    return df

# -----------------------------
# Main App
# -----------------------------
games_df = fetch_espn_games()

if games_df.empty:
    st.info("No MLB games available right now. Check back after the next refresh.")
else:
    # Compute projections
    games_df = model_projected_scores(games_df)

    # Merge FanDuel Book O/U
    odds_map = fetch_fanduel_odds()
    games_df["Book O/U"] = ""
    for idx, row in games_df.iterrows():
        key = (row["Away Team"], row["Home Team"])
        if key in odds_map:
            games_df.loc[idx, "Book O/U"] = odds_map[key]["Book O/U"]

    # Format numeric columns
    games_df["Away Score Proj"] = games_df["Away Score Proj"].map("{:.1f}".format)
    games_df["Home Score Proj"] = games_df["Home Score Proj"].map("{:.1f}".format)
    games_df["Model O/U"] = games_df["Model O/U"].map("{:.1f}".format)

    # Reorder columns for display
    games_df = games_df[[
        "Game Time", "Away Team", "Away Score Proj",
        "Home Team", "Home Score Proj",
        "ML Bet", "Book O/U", "Model O/U", "Confidence"
    ]]

    # Sort by Confidence descending
    games_df = games_df.sort_values(by="Confidence", ascending=False)

    # --- Responsive Table Styling ---
    st.markdown(
        """
        <style>
        table {
            width: 100% !important;
        }
        thead tr th {
            background-color: #f0f2f6;
            text-align: center;
        }
        tbody tr td {
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Display table (index hidden)
    st.dataframe(games_df, use_container_width=True, hide_index=True)

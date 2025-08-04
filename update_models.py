import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import numpy as np
import streamlit as st

# -----------------------------
# CONFIG
# -----------------------------
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
BALLPARKPAL_URL = "https://www.ballparkpal.com/mlb/"
SONNY_MOORE_URL = "https://sonnymoorepowerratings.com/mlb.htm"

# Model Weights
WEIGHTS = {
    "team_rpg": 0.25,
    "team_rpg_l5": 0.15,
    "opp_rpga": 0.20,
    "opp_rpga_l5": 0.10,
    "wrc_plus": 0.05,
    "ba_vs_hand": 0.05,
    "sp_fip": 0.05,
    "bullpen_siera": 0.10,
    "park_factor": 0.05
}
HOME_FIELD_ADV = 0.15

# -----------------------------
# SCRAPING HELPERS
# -----------------------------
def get_espn_games():
    """Scrape today's MLB schedule with starting pitchers"""
    today = datetime.now().strftime("%Y%m%d")
    resp = requests.get(f"{ESPN_URL}?dates={today}").json()
    games = []
    for event in resp.get("events", []):
        comp = event["competitions"][0]
        home = comp["competitors"][0]
        away = comp["competitors"][1]

        game_time = datetime.fromisoformat(comp["date"][:-1]).strftime("%I:%M %p")

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


def get_sonny_moore_ratings():
    """Scrape Sonny Moore power ratings for MLB teams"""
    resp = requests.get(SONNY_MOORE_URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text()
    lines = text.splitlines()
    
    ratings = {}
    for line in lines:
        parts = line.split()
        if len(parts) >= 3:
            try:
                rating = float(parts[-1])
                team_name = " ".join(parts[1:-1])
                ratings[team_name] = rating
            except:
                continue
    return ratings


def get_ballpark_factors():
    """Scrape BallparkPal scoring factors"""
    resp = requests.get(BALLPARKPAL_URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    factors = {}
    for row in soup.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) > 1:
            team = cols[0].get_text(strip=True)
            try:
                factor = float(cols[1].get_text(strip=True))
                factors[team] = factor
            except:
                continue
    return factors


# -----------------------------
# MODEL CALCULATION (CACHED)
# -----------------------------
@st.cache_data(ttl=86400)  # Cache for 24 hours
def calculate_daily_model():
    games_df = get_espn_games()
    if games_df.empty:
        return pd.DataFrame(columns=[
            "Game Time","Away Team","Away Score","Home Team","Home Score",
            "ML (%)","Book O/U","Model O/U","O/U Bet"
        ])

    sonny_ratings = get_sonny_moore_ratings()
    park_factors = get_ballpark_factors()

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
        # LIVE STAT SCRAPING (replace dummy with real)
        # -----------------------------
        # In production: integrate TeamRankings + FanGraphs + ESPN/BR here.
        # For now, simulate realistic numbers:
        team_rpg_home = 4.5
        team_rpg_away = 4.3
        team_rpg_l5_home = 4.8
        team_rpg_l5_away = 4.4
        team_rpga_home = 4.1
        team_rpga_away = 4.2
        team_rpga_l5_home = 4.0
        team_rpga_l5_away = 4.5
        wrc_home = 105
        wrc_away = 102
        ba_vs_home = 0.255
        ba_vs_away = 0.248
        sp_fip_home = 3.7
        sp_fip_away = 4.2
        bp_siera_home = 3.9
        bp_siera_away = 4.0
        park_factor_home = park_factors.get(row["Home Team"], 1.0)

        # -----------------------------
        # Weighted Score Prediction
        # -----------------------------
        away_score = (
            team_rpg_away * WEIGHTS["team_rpg"] +
            team_rpg_l5_away * WEIGHTS["team_rpg_l5"] +
            team_rpga_home * WEIGHTS["opp_rpga"] +
            team_rpga_l5_home * WEIGHTS["opp_rpga_l5"] +
            wrc_away/100 * WEIGHTS["wrc_plus"] +
            ba_vs_away * WEIGHTS["ba_vs_hand"] +
            sp_fip_home/5 * WEIGHTS["sp_fip"] +
            bp_siera_home/5 * WEIGHTS["bullpen_siera"]
        ) * park_factor_home

        home_score = (
            team_rpg_home * WEIGHTS["team_rpg"] +
            team_rpg_l5_home * WEIGHTS["team_rpg_l5"] +
            team_rpga_away * WEIGHTS["opp_rpga"] +
            team_rpga_l5_away * WEIGHTS["opp_rpga_l5"] +
            wrc_home/100 * WEIGHTS["wrc_plus"] +
            ba_vs_home * WEIGHTS["ba_vs_hand"] +
            sp_fip_away/5 * WEIGHTS["sp_fip"] +
            bp_siera_away/5 * WEIGHTS["bullpen_siera"]
        ) * park_factor_home + HOME_FIELD_ADV

        home_score = round(home_score, 1)
        away_score = round(away_score, 1)
        model_total = round(home_score + away_score, 1)

        # Moneyline % using scoring + Sonny Moore
        home_prob = (home_score / (home_score + away_score)) * 100
        sonny_home = sonny_ratings.get(row["Home Team"], 150)
        sonny_away = sonny_ratings.get(row["Away Team"], 150)
        sonny_adj = (sonny_home - sonny_away) / 50  # small weight
        ml_pct = round(min(max(home_prob + sonny_adj, 0), 100), 1)

        # Sportsbook O/U placeholder
        book_total = 9.0
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
            "ML (%)": ml_pct,
            "Book O/U": book_total,
            "Model O/U": model_total,
            "O/U Bet": ou_bet
        })

    return pd.DataFrame(results)

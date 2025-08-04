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

TEAMRANKINGS_RPG = "https://www.teamrankings.com/mlb/stat/runs-per-game"
TEAMRANKINGS_RPG_L5 = "https://www.teamrankings.com/mlb/stat/runs-per-game?date=last-5"
TEAMRANKINGS_RPGA = "https://www.teamrankings.com/mlb/stat/runs-allowed-per-game"
TEAMRANKINGS_RPGA_L5 = "https://www.teamrankings.com/mlb/stat/runs-allowed-per-game?date=last-5"
TEAMRANKINGS_BULLPEN_ERA = "https://www.teamrankings.com/mlb/stat/bullpen-era"

# FanGraphs & Baseball Reference URLs
FANGRAPHS_TEAM_SPLITS = "https://www.fangraphs.com/leaders/splits-leaderboards?splitArr=42&strgroup=team"
BASEBALLREF_SP_PITCHING = "https://www.baseball-reference.com/leagues/majors/2025-starter-pitching.shtml"

# FanDuel Odds API
ODDS_API_KEY = "YOUR_ODDS_API_KEY_HERE"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

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
# SCRAPERS
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

def scrape_teamrankings(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table")
    data = {}
    if not table:
        return data
    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) >= 2:
            team = cols[0].get_text(strip=True)
            try:
                stat = float(cols[1].get_text(strip=True))
                data[team] = stat
            except:
                continue
    return data

def get_sonny_moore_ratings():
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

def get_fangraphs_team_splits():
    """Scrape FanGraphs team splits for wRC+ and BA vs hand."""
    resp = requests.get(FANGRAPHS_TEAM_SPLITS)
    tables = pd.read_html(resp.text)
    # Assume first table is correct
    df = tables[0]
    df.columns = [c.strip() for c in df.columns]
    data = {}
    for _, row in df.iterrows():
        team = row['Team']
        try:
            wrc = float(row['wRC+'])
            ba = float(row['AVG'])
            data[team] = {'wrc_plus': wrc, 'ba_vs_hand': ba}
        except:
            continue
    return data

def get_pitcher_fip_data():
    """Scrape Baseball Reference SP FIP and ERA (home/away)"""
    resp = requests.get(BASEBALLREF_SP_PITCHING)
    tables = pd.read_html(resp.text)
    df = tables[0]
    df.columns = [c[1] if isinstance(c, tuple) else c for c in df.columns]
    data = {}
    for _, row in df.iterrows():
        pitcher = row['Name']
        try:
            fip = float(row['FIP'])
            era = float(row['ERA'])
            data[pitcher] = {'fip': fip, 'era': era}
        except:
            continue
    return data

def get_fanduel_totals():
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "totals",
        "oddsFormat": "decimal"
    }
    resp = requests.get(ODDS_API_URL, params=params)
    if resp.status_code != 200:
        return {}

    data = resp.json()
    totals_map = {}

    for game in data:
        home = game["home_team"]
        away = game["away_team"]

        for book in game.get("bookmakers", []):
            if book["key"] == "fanduel":
                for market in book["markets"]:
                    if market["key"] == "totals":
                        total = float(market["outcomes"][0]["point"])
                        key = f"{away} @ {home}"
                        totals_map[key] = total
    return totals_map

# -----------------------------
# MODEL CALCULATION
# -----------------------------
@st.cache_data(ttl=86400)
def calculate_daily_model():
    games_df = get_espn_games()
    if games_df.empty:
        return pd.DataFrame(columns=[
            "Game Time","Away Team","Away Score","Home Team","Home Score",
            "ML (%)","Book O/U","Model O/U","O/U Bet"
        ])

    # Live data
    sonny_ratings = get_sonny_moore_ratings()
    park_factors = get_ballpark_factors()
    fanduel_totals = get_fanduel_totals()
    fg_team_splits = get_fangraphs_team_splits()
    sp_fip_data = get_pitcher_fip_data()

    team_rpg = scrape_teamrankings(TEAMRANKINGS_RPG)
    team_rpg_l5 = scrape_teamrankings(TEAMRANKINGS_RPG_L5)
    team_rpga = scrape_teamrankings(TEAMRANKINGS_RPGA)
    team_rpga_l5 = scrape_teamrankings(TEAMRANKINGS_RPGA_L5)
    bullpen_era = scrape_teamrankings(TEAMRANKINGS_BULLPEN_ERA)

    results = []
    for _, row in games_df.iterrows():
        if "TBD" in row["Home Pitcher"] or "TBD" in row["Away Pitcher"]:
            continue

        home_team = row["Home Team"]
        away_team = row["Away Team"]
        home_pitcher = row["Home Pitcher"]
        away_pitcher = row["Away Pitcher"]
        game_key = f"{away_team} @ {home_team}"

        if home_team not in team_rpg or away_team not in team_rpg:
            continue

        # Gather stats
        team_rpg_home = team_rpg.get(home_team, 4.0)
        team_rpg_away = team_rpg.get(away_team, 4.0)
        team_rpg_l5_home = team_rpg_l5.get(home_team, team_rpg_home)
        team_rpg_l5_away = team_rpg_l5.get(away_team, team_rpg_away)

        team_rpga_home = team_rpga.get(home_team, 4.5)
        team_rpga_away = team_rpga.get(away_team, 4.5)
        team_rpga_l5_home = team_rpga_l5.get(home_team, team_rpga_home)
        team_rpga_l5_away = team_rpga_l5.get(away_team, team_rpga_away)

        bp_siera_home = bullpen_era.get(home_team, 4.0)
        bp_siera_away = bullpen_era.get(away_team, 4.0)
        park_factor_home = park_factors.get(home_team, 1.0)

        wrc_home = fg_team_splits.get(home_team, {'wrc_plus':100})['wrc_plus']
        wrc_away = fg_team_splits.get(away_team, {'wrc_plus':100})['wrc_plus']
        ba_vs_home = fg_team_splits.get(home_team, {'ba_vs_hand':0.25})['ba_vs_hand']
        ba_vs_away = fg_team_splits.get(away_team, {'ba_vs_hand':0.25})['ba_vs_hand']

        sp_fip_home = sp_fip_data.get(home_pitcher, {'fip':4.0})['fip']
        sp_fip_away = sp_fip_data.get(away_pitcher, {'fip':4.0})['fip']

        # Weighted scoring
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

        home_prob = (home_score / (home_score + away_score)) * 100
        sonny_home = sonny_ratings.get(home_team, 150)
        sonny_away = sonny_ratings.get(away_team, 150)
        sonny_adj = (sonny_home - sonny_away) / 50
        ml_pct = round(min(max(home_prob + sonny_adj, 0), 100), 1)

        # Use real FanDuel O/U
        book_total = fanduel_totals.get(game_key, 9.0)
        diff = model_total - book_total
        if diff >= 2:
            ou_bet = "BET THE OVER"
        elif diff <= -2:
            ou_bet = "BET THE UNDER"
        else:
            ou_bet = "NO BET"

        results.append({
            "Game Time": row["Game Time"],
            "Away Team": away_team,
            "Away Score": away_score,
            "Home Team": home_team,
            "Home Score": home_score,
            "ML (%)": ml_pct,
            "Book O/U": book_total,
            "Model O/U": model_total,
            "O/U Bet": ou_bet
        })

    return pd.DataFrame(results)

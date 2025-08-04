import pandas as pd
import requests
from datetime import datetime, timedelta
import os

# -----------------------------
# CONFIG
# -----------------------------
TEAM_SPLITS_CSV = "team_splits.csv"
PITCHER_SPLITS_CSV = "pitcher_splits.csv"

# Google Sheets fallbacks (replace with your real export links)
GOOGLE_TEAM_SPLITS = "https://docs.google.com/spreadsheets/d/1Hbl2EHW_ac0mVa1F0lNxuaeDV2hcuo7K_Uyhb-HOU6E/edit?gid=496743641#gid=496743641/export?format=csv&gid=496743641"
GOOGLE_PITCHER_SPLITS = "https://docs.google.com/spreadsheets/d/1Hbl2EHW_ac0mVa1F0lNxuaeDV2hcuo7K_Uyhb-HOU6E/export?format=csv&gid=313531137"

CACHE_EXPIRY_HOURS = 24  # auto-refresh once per day


def is_cache_stale(file_path):
    """Check if CSV is missing or older than CACHE_EXPIRY_HOURS."""
    if not os.path.exists(file_path):
        return True
    file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))
    return file_age > timedelta(hours=CACHE_EXPIRY_HOURS)


# -----------------------------
# SCRAPING FUNCTIONS
# -----------------------------
def scrape_fangraphs_team_splits():
    """Scrape FanGraphs team splits (static tables) and return DataFrame."""
    url = "https://www.fangraphs.com/leaders/splits-leaderboards?splitArr=42&strgroup=team"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    tables = pd.read_html(resp.text)
    if tables:
        df = tables[0]
        df.columns = [c.strip() for c in df.columns]
        return df
    return pd.DataFrame()


def scrape_baseball_reference_pitchers():
    """Scrape Baseball Reference starter pitching table."""
    url = "https://www.baseball-reference.com/leagues/majors/2025-starter-pitching.shtml"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    tables = pd.read_html(resp.text)
    if tables:
        df = tables[0]
        df.columns = [c.strip() for c in df.columns]
        return df
    return pd.DataFrame()


# -----------------------------
# LOADERS WITH CACHE + FALLBACK
# -----------------------------
def load_team_splits():
    """Load team splits: CSV → scrape → Google Sheet fallback."""
    if not is_cache_stale(TEAM_SPLITS_CSV):
        return pd.read_csv(TEAM_SPLITS_CSV)

    try:
        df = scrape_fangraphs_team_splits()
        if not df.empty:
            df.to_csv(TEAM_SPLITS_CSV, index=False)
            print("✅ Team splits scraped & cached")
            return df
    except Exception as e:
        print("❌ FanGraphs scrape failed:", e)

    try:
        print("⚠ Using Google Sheets fallback for team splits")
        return pd.read_csv(GOOGLE_TEAM_SPLITS)
    except:
        print("❌ Google Sheets fallback failed for team splits")
        return pd.DataFrame()


def load_pitcher_splits():
    """Load pitcher splits: CSV → scrape → Google Sheet fallback."""
    if not is_cache_stale(PITCHER_SPLITS_CSV):
        return pd.read_csv(PITCHER_SPLITS_CSV)

    try:
        df = scrape_baseball_reference_pitchers()
        if not df.empty:
            df.to_csv(PITCHER_SPLITS_CSV, index=False)
            print("✅ Pitcher splits scraped & cached")
            return df
    except Exception as e:
        print("❌ Baseball Reference scrape failed:", e)

    try:
        print("⚠ Using Google Sheets fallback for pitcher splits")
        return pd.read_csv(GOOGLE_PITCHER_SPLITS)
    except:
        print("❌ Google Sheets fallback failed for pitcher splits")
        return pd.DataFrame()


# -----------------------------
# MAIN DAILY MODEL FUNCTION
# -----------------------------
def calculate_daily_model():
    team_splits = load_team_splits()
    pitcher_splits = load_pitcher_splits()

    if team_splits.empty or pitcher_splits.empty:
        print("⚠ Warning: Missing splits data, model may skip some calculations")

    # EXAMPLE: Return a DataFrame your app.py can display
    # Replace this with your real scoring logic
    return pd.DataFrame({
        "Game Time": ["7:05 PM", "9:10 PM"],
        "Away Team": ["Yankees", "Dodgers"],
        "Away Score": [4.2, 5.1],
        "Home Team": ["Red Sox", "Giants"],
        "Home Score": [3.8, 4.0],
        "ML (%)": [55.0, 60.5],
        "Book O/U": [9.0, 8.5],
        "Model O/U": [8.0, 9.7],
        "O/U Bet": ["BET THE UNDER", "BET THE OVER"]
    })

import pandas as pd
import requests

# -------------------------
# CONFIG
# -------------------------
GOOGLE_SHEET_RPG = "https://docs.google.com/spreadsheets/d/1Hbl2EHW_ac0mVa1F0lNxuaeDV2hcuo7K_Uyhb-HOU6E/export?format=csv"
ROBA_CSV = "team_rOBA.csv"

# -------------------------
# LOAD FUNCTIONS
# -------------------------

def load_team_rpg():
    """Load team RPG and RPGa from Google Sheet CSV"""
    try:
        df = pd.read_csv(GOOGLE_SHEET_RPG)
        df = df[['Team', 'RPG', 'RPGa']]  # Adjust to your column names
        return df
    except Exception as e:
        print(f"Failed to load RPG from Google Sheets: {e}")
        return pd.DataFrame(columns=['Team','RPG','RPGa'])

def load_roba():
    """Load team rOBA from local CSV"""
    try:
        df = pd.read_csv(ROBA_CSV)
        df = df[['Tm', 'rOBA']]  # Adjust to your CSV columns
        df.rename(columns={'Tm':'Team'}, inplace=True)
        return df
    except Exception as e:
        print(f"Failed to load rOBA: {e}")
        return pd.DataFrame(columns=['Team','rOBA'])

def load_bullpen():
    """Scrape bullpen ERA & WHIP from Covers"""
    url = "https://www.covers.com/sport/baseball/mlb/statistics/team-bullpenera/2025"
    try:
        tables = pd.read_html(url)
        df = tables[0]
        df = df[['Team','ERA','WHIP']]
        df.rename(columns={'ERA':'Bullpen_ERA','WHIP':'Bullpen_WHIP'}, inplace=True)
        return df
    except Exception as e:
        print(f"Failed to scrape bullpen stats: {e}")
        return pd.DataFrame(columns=['Team','Bullpen_ERA','Bullpen_WHIP'])

def load_sp_stats():
    """Scrape SP ERA & FIP from Baseball Reference"""
    url = "https://www.baseball-reference.com/leagues/majors/2025-standard-pitching.shtml"
    try:
        tables = pd.read_html(url)
        df = tables[0]
        df = df[['Tm','ERA','FIP']]
        df.rename(columns={'Tm':'Team','ERA':'SP_ERA','FIP':'SP_FIP'}, inplace=True)
        return df
    except Exception as e:
        print(f"Failed to scrape SP stats: {e}")
        return pd.DataFrame(columns=['Team','SP_ERA','SP_FIP'])

# -------------------------
# COMBINE INTO DAILY MODEL
# -------------------------

def calculate_daily_model():
    """Main function to calculate daily MLB model"""

    team_rpg = load_team_rpg()
    roba = load_roba()
    bullpen = load_bullpen()
    sp_stats = load_sp_stats()

    # Merge all data
    df = team_rpg.merge(roba, on='Team', how='outer')
    df = df.merge(bullpen, on='Team', how='outer')
    df = df.merge(sp_stats, on='Team', how='outer')

    # Example model total (replace with your real formula/weights)
    df['Model_Total'] = df[['RPG','RPGa']].mean(axis=1)

    # Simple O/U bet logic
    df['O/U Bet'] = df['Model_Total'].apply(
        lambda x: "BET THE OVER" if x >= 1 else "NO BET"
    )

    return df

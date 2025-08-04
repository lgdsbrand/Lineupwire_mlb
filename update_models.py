import pandas as pd
import requests

# -------------------------------
# TEAM NAME NORMALIZATION
# -------------------------------
TEAM_NAME_MAP = {
    "Arizona Diamondbacks": "AZ",
    "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC",
    "Chicago White Sox": "CHW",
    "Cincinnati Reds": "CIN",
    "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL",
    "Detroit Tigers": "DET",
    "Houston Astros": "HOU",
    "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA",
    "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN",
    "New York Mets": "NYM",
    "New York Yankees": "NYY",
    "Oakland Athletics": "ATH",
    "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SD",
    "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA",
    "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TB",
    "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR",
    "Washington Nationals": "WSH"
}

def normalize_team_names(df):
    """Convert full team names to 3-letter codes for merging"""
    if 'Team' in df.columns:
        df['Team'] = df['Team'].map(TEAM_NAME_MAP).fillna(df['Team'])
    return df

def normalize_team_names(df):
    """Map team names to match Google Sheet short names."""
    if 'Team' in df.columns:
        df['Team'] = df['Team'].replace(TEAM_MAP)
    return df

# -------------------------------
# LOAD FUNCTIONS (CSV fallback for now)
# -------------------------------
def load_team_rpg():
    df = pd.read_csv("team_rpg.csv")  # already exported from Google Sheet
    df = normalize_team_names(df)
    return df[['Team','RPG']]

def load_team_rpga():
    df = pd.read_csv("team_rpga.csv")
    df = normalize_team_names(df)
    return df[['Team','RPGA']]

def load_roba():
    df = pd.read_csv("team_roba.csv")  # CSV exported from Baseball Reference
    df = normalize_team_names(df)
    return df[['Team','rOBA']]

def load_bullpen():
    df = pd.read_csv("bullpen_stats.csv")  # CSV exported or scraped
    df = normalize_team_names(df)
    return df[['Team','Bullpen_ERA','Bullpen_WHIP']]

def load_sp_stats():
    df = pd.read_csv("sp_stats.csv")  # CSV exported or scraped
    df = normalize_team_names(df)
    return df[['Team','SP_ERA','SP_FIP']]

# -------------------------------
# CALCULATE DAILY MODEL
# -------------------------------
def calculate_daily_model():
    """Main function to calculate daily MLB model."""

    # Load all datasets
    team_rpg = load_team_rpg()
    team_rpga = load_team_rpga()
    roba = load_roba()
    bullpen = load_bullpen()
    sp_stats = load_sp_stats()

    # Merge all sources
    df = team_rpg.merge(team_rpga, on='Team', how='outer')
    df = df.merge(roba, on='Team', how='outer')
    df = df.merge(bullpen, on='Team', how='outer')
    df = df.merge(sp_stats, on='Team', how='outer')

    # Diagnostic: show any teams that are missing values
    missing = df[df.isna().any(axis=1)]
    if not missing.empty:
        print("⚠️ Teams with missing stats after merge:")
        print(missing[['Team']])

    # Example Model Total (replace with weighted formula later)
    df['Model_Total'] = df[['RPG','RPGA']].sum(axis=1)

    # Example simple O/U bet rule
    df['O/U Bet'] = df['Model_Total'].apply(
        lambda x: "BET THE OVER" if x >= 10 else "NO BET"
    )

    return df

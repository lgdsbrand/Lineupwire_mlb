import pandas as pd
import requests

# -------------------------------
# TEAM NAME NORMALIZATION
# -------------------------------
TEAM_MAP = {
    "Arizona Diamondbacks": "Arizona",
    "Atlanta Braves": "Atlanta",
    "Baltimore Orioles": "Baltimore",
    "Boston Red Sox": "Boston",
    "Chicago Cubs": "Chi Cubs",
    "Chicago White Sox": "Chi Sox",
    "Cincinnati Reds": "Cincinnati",
    "Cleveland Guardians": "Cleveland",
    "Colorado Rockies": "Colorado",
    "Detroit Tigers": "Detroit",
    "Houston Astros": "Houston",
    "Kansas City Royals": "Kansas City",
    "Los Angeles Angels": "LA Angels",
    "Los Angeles Dodgers": "LA Dodgers",
    "Miami Marlins": "Miami",
    "Milwaukee Brewers": "Milwaukee",
    "Minnesota Twins": "Minnesota",
    "New York Mets": "NY Mets",
    "New York Yankees": "NY Yankees",
    "Oakland Athletics": "Oakland",
    "Philadelphia Phillies": "Philadelphia",
    "Pittsburgh Pirates": "Pittsburgh",
    "San Diego Padres": "San Diego",
    "San Francisco Giants": "SF Giants",
    "Seattle Mariners": "Seattle",
    "St. Louis Cardinals": "St. Louis",
    "Tampa Bay Rays": "Tampa Bay",
    "Texas Rangers": "Texas",
    "Toronto Blue Jays": "Toronto",
    "Washington Nationals": "Washington"
}

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

import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime

# ------------------------
# Scraper functions
# ------------------------

def load_team_rpg():
    """Scrape team RPG (Runs Per Game) from TeamRankings."""
    url = "https://www.teamrankings.com/mlb/stat/runs-per-game"
    try:
        tables = pd.read_html(url)
        df = tables[0]
        df = df[['Team', '2025']]
        df.rename(columns={'2025': 'RPG'}, inplace=True)
        return df
    except Exception as e:
        print(f"Failed to scrape team RPG: {e}")
        return pd.DataFrame(columns=['Team', 'RPG'])

def load_team_rpga():
    """Scrape team RPG allowed (Runs Per Game Allowed) from TeamRankings."""
    url = "https://www.teamrankings.com/mlb/stat/runs-allowed-per-game"
    try:
        tables = pd.read_html(url)
        df = tables[0]
        df = df[['Team', '2025']]
        df.rename(columns={'2025': 'RPGa'}, inplace=True)
        return df
    except Exception as e:
        print(f"Failed to scrape team RPGa: {e}")
        return pd.DataFrame(columns=['Team', 'RPGa'])

def load_roba():
    """Scrape team rOBA from Baseball Reference."""
    url = "https://www.baseball-reference.com/leagues/majors/2025-advanced-batting.shtml"
    try:
        tables = pd.read_html(url)
        df = tables[0]
        
        # Clean column names (handles MultiIndex columns)
        df.columns = [col[1] if isinstance(col, tuple) else col for col in df.columns]
        
        df = df[['Tm', 'rOBA']].copy()
        df.rename(columns={'Tm': 'Team'}, inplace=True)
        
        # Drop total/team summary rows like "MLB" or "League"
        df = df[~df['Team'].str.contains('MLB|League', na=False)]
        df.reset_index(drop=True, inplace=True)
        return df
    except Exception as e:
        print(f"Failed to scrape rOBA: {e}")
        return pd.DataFrame(columns=['Team', 'rOBA'])

def load_bullpen():
    """Scrape bullpen ERA & WHIP from Covers."""
    url = "https://www.covers.com/sport/baseball/mlb/statistics/team-bullpenera/2025"
    try:
        tables = pd.read_html(url)
        df = tables[0]
        # Assuming first table has columns ['Team','ERA','WHIP'] or similar
        df = df[['Team', 'ERA', 'WHIP']].copy()
        df.rename(columns={'ERA': 'Bullpen_ERA', 'WHIP': 'Bullpen_WHIP'}, inplace=True)
        return df
    except Exception as e:
        print(f"Failed to scrape bullpen stats: {e}")
        return pd.DataFrame(columns=['Team','Bullpen_ERA','Bullpen_WHIP'])

def load_sp_stats():
    """Scrape starting pitcher stats (FIP, ERA) from Baseball Reference."""
    url = "https://www.baseball-reference.com/leagues/majors/2025-standard-pitching.shtml"
    try:
        tables = pd.read_html(url)
        df = tables[0]
        
        # Clean column names
        df.columns = [col[1] if isinstance(col, tuple) else col for col in df.columns]
        
        # Keep team & core SP stats (filtering pitchers with >0 GS for starters)
        if 'GS' in df.columns:
            df = df[df['GS'] > 0]  # Only starters
        df = df[['Tm', 'ERA', 'FIP']].copy() if 'FIP' in df.columns else df[['Tm', 'ERA']]
        df.rename(columns={'Tm': 'Team', 'ERA': 'SP_ERA', 'FIP': 'SP_FIP'}, inplace=True)
        return df
    except Exception as e:
        print(f"Failed to scrape SP stats: {e}")
        return pd.DataFrame(columns=['Team','SP_ERA','SP_FIP'])

# ------------------------
# Combine into daily model
# ------------------------

def calculate_daily_model():
    """Main function to calculate daily MLB model."""

    # Load data sources
    team_rpg = load_team_rpg()
    team_rpga = load_team_rpga()
    roba = load_roba()
    bullpen = load_bullpen()
    sp_stats = load_sp_stats()

    # Merge datasets
    df = team_rpg.merge(team_rpga, on='Team', how='outer')
    df = df.merge(roba, on='Team', how='outer')
    df = df.merge(bullpen, on='Team', how='outer')
    df = df.merge(sp_stats, on='Team', how='outer')

    # Calculate model total (simplified placeholder formula)
    # You can replace with your weighted formula here
    df['Model_Total'] = df['RPG'] + df['RPGa']

    # Betting recommendation (simple version)
    df['O/U Bet'] = df['Model_Total'].apply(
        lambda x: "BET THE OVER" if x >= 10 else ("BET THE UNDER" if x <= 7 else "NO BET")
    )

    return df

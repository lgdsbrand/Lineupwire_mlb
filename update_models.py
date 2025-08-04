import pandas as pd
import requests

# ---------------------------
# Team Runs Per Game
# ---------------------------
def load_team_rpg():
    url = "https://www.teamrankings.com/mlb/stat/runs-per-game"
    try:
        tables = pd.read_html(url)
        df = tables[0][['Team', '2025', 'Last 5', 'Home/Away']].copy()
        df.rename(columns={'2025': 'RPG'}, inplace=True)
        df['RPG'] = pd.to_numeric(df['RPG'], errors='coerce')
        return df[['Team', 'RPG']]
    except Exception as e:
        print(f"Failed to scrape team RPG: {e}")
        return pd.DataFrame(columns=['Team', 'RPG'])


# ---------------------------
# Team Runs Allowed Per Game
# ---------------------------
def load_team_rpga():
    url = "https://www.teamrankings.com/mlb/stat/runs-allowed-per-game"
    try:
        tables = pd.read_html(url)
        df = tables[0][['Team', '2025', 'Last 5', 'Home/Away']].copy()
        df.rename(columns={'2025': 'RPGa'}, inplace=True)
        df['RPGa'] = pd.to_numeric(df['RPGa'], errors='coerce')
        return df[['Team', 'RPGa']]
    except Exception as e:
        print(f"Failed to scrape team RPGa: {e}")
        return pd.DataFrame(columns=['Team', 'RPGa'])


# ---------------------------
# Team rOBA (from Baseball Reference)
# ---------------------------
def load_roba():
    url = "https://www.baseball-reference.com/leagues/majors/2025-advanced-batting.shtml"
    try:
        tables = pd.read_html(url, header=1)
        df = tables[0]

        # Drop summary rows like MLB and LgAvg
        df = df[~df['Tm'].isin(['LgAvg', 'MLB'])]

        # Select team and wOBA columns as rOBA proxy
        df = df[['Tm', 'wOBA']].copy()
        df.rename(columns={'Tm': 'Team', 'wOBA': 'rOBA'}, inplace=True)

        df['rOBA'] = pd.to_numeric(df['rOBA'], errors='coerce')
        df.reset_index(drop=True, inplace=True)
        return df
    except Exception as e:
        print(f"Failed to scrape rOBA: {e}")
        return pd.DataFrame(columns=['Team', 'rOBA'])


# ---------------------------
# Bullpen Stats (ERA & WHIP from Covers)
# ---------------------------
def load_bullpen():
    url = "https://www.covers.com/sport/baseball/mlb/statistics/team-bullpenera/2025"
    try:
        tables = pd.read_html(url)
        df = tables[0].copy()

        # Standardize column names
        df.rename(columns={'Team': 'Team', 'ERA': 'Bullpen_ERA', 'WHIP': 'Bullpen_WHIP'}, inplace=True)

        df['Bullpen_ERA'] = pd.to_numeric(df['Bullpen_ERA'], errors='coerce')
        df['Bullpen_WHIP'] = pd.to_numeric(df['Bullpen_WHIP'], errors='coerce')
        return df[['Team', 'Bullpen_ERA', 'Bullpen_WHIP']]
    except Exception as e:
        print(f"Failed to scrape bullpen stats: {e}")
        return pd.DataFrame(columns=['Team', 'Bullpen_ERA', 'Bullpen_WHIP'])


# ---------------------------
# Starting Pitcher Stats (from Baseball Reference)
# ---------------------------
def load_sp_stats():
    url = "https://www.baseball-reference.com/leagues/majors/2025-standard-pitching.shtml"
    try:
        tables = pd.read_html(url, header=1)
        df = tables[0]

        # Drop total and league average rows
        df = df[~df['Tm'].isin(['LgAvg', 'MLB'])]

        df = df[['Tm', 'FIP', 'ERA']].copy()
        df.rename(columns={'Tm': 'Team', 'ERA': 'SP_ERA', 'FIP': 'SP_FIP'}, inplace=True)

        df['SP_ERA'] = pd.to_numeric(df['SP_ERA'], errors='coerce')
        df['SP_FIP'] = pd.to_numeric(df['SP_FIP'], errors='coerce')
        return df
    except Exception as e:
        print(f"Failed to scrape SP stats: {e}")
        return pd.DataFrame(columns=['Team', 'SP_ERA', 'SP_FIP'])


# ---------------------------
# Combine into daily model
# ---------------------------
def calculate_daily_model():
    """Main function to calculate daily MLB model"""
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

    # Calculate model total (example placeholder formula)
    df['Model_Total'] = df['RPG'] + df['RPGa'] * 0.5  # adjust weight later

    # Betting recommendation
    df['O/U Bet'] = df['Model_Total'].apply(
        lambda x: "BET THE OVER" if x >= 9 else ("BET THE UNDER" if x <= 7 else "NO BET")
    )

    return df[['Team', 'RPG', 'RPGa', 'rOBA', 'Bullpen_ERA', 'Bullpen_WHIP', 'SP_ERA', 'SP_FIP', 'Model_Total', 'O/U Bet']]

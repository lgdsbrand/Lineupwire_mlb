import pandas as pd
import requests
import datetime

# -----------------------------
# CONFIG
# -----------------------------
TEAM_RPG_URL = "https://www.teamrankings.com/mlb/stat/runs-per-game"
TEAM_RPGA_URL = "https://www.teamrankings.com/mlb/stat/opponent-runs-per-game"
BULLPEN_API = "https://statsapi.mlb.com/api/v1/teams/stats?group=pitching&type=season&season=2025"
TEAM_WOBA_URL = "https://baseballsavant.mlb.com/leaderboard/custom?type=bat&year=2025&stats=woba&team=all"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# -----------------------------
# SCRAPING FUNCTIONS
# -----------------------------

def scrape_team_rpg():
    try:
        df = pd.read_html(TEAM_RPG_URL)[0]
        df = df[['Team', '2025']]
        df.columns = ['Team', 'RPG']
        return df
    except Exception as e:
        print("Team RPG scrape failed:", e)
        return pd.DataFrame(columns=['Team', 'RPG'])

def scrape_team_rpga():
    try:
        df = pd.read_html(TEAM_RPGA_URL)[0]
        df = df[['Team', '2025']]
        df.columns = ['Team', 'RPGa']
        return df
    except Exception as e:
        print("Team RPGa scrape failed:", e)
        return pd.DataFrame(columns=['Team', 'RPGa'])

def scrape_team_woba():
    try:
        resp = requests.get(TEAM_WOBA_URL, headers=HEADERS)
        df = pd.read_html(resp.text)[0]
        df = df[['Team', 'wOBA']]  # Adjust if column name differs
        return df
    except Exception as e:
        print("Team wOBA scrape failed:", e)
        return pd.DataFrame(columns=['Team', 'wOBA'])

def scrape_bullpen_stats():
    try:
        resp = requests.get(BULLPEN_API, headers=HEADERS).json()
        rows = []
        for team_data in resp.get("stats", []):
            team = team_data['team']['name']
            era = team_data['stats'][0].get('era', None)
            whip = team_data['stats'][0].get('whip', None)
            rows.append([team, era, whip])
        return pd.DataFrame(rows, columns=['Team', 'Bullpen_ERA', 'Bullpen_WHIP'])
    except Exception as e:
        print("Bullpen API scrape failed:", e)
        return pd.DataFrame(columns=['Team', 'Bullpen_ERA', 'Bullpen_WHIP'])

# -----------------------------
# MAIN DAILY MODEL
# -----------------------------

def calculate_daily_model():
    team_rpg = scrape_team_rpg()
    team_rpga = scrape_team_rpga()
    team_woba = scrape_team_woba()
    bullpen_stats = scrape_bullpen_stats()

    # Merge all data on Team
    df = team_rpg.merge(team_rpga, on='Team', how='outer')\
                 .merge(team_woba, on='Team', how='outer')\
                 .merge(bullpen_stats, on='Team', how='outer')

    # Simple example formula for Model Total & Pick
    df['Model Total'] = (df['RPG'] + df['RPGa']) / 2
    df['Sportsbook O/U'] = 8  # placeholder until odds integrated
    df['Diff'] = df['Model Total'] - df['Sportsbook O/U']

    def ou_pick(diff):
        if diff >= 2: return "BET THE OVER"
        elif diff <= -2: return "BET THE UNDER"
        else: return "NO BET"

    df['O/U Bet'] = df['Diff'].apply(ou_pick)

    # Final columns for Streamlit
    return df[['Team','RPG','RPGa','wOBA','Bullpen_ERA','Bullpen_WHIP',
               'Sportsbook O/U','Model Total','O/U Bet']]

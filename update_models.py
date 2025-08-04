import pandas as pd
import requests
from datetime import datetime

# -------------------------
# CONFIG
# -------------------------
TEAM_SPLITS_CSV = "https://docs.google.com/spreadsheets/d/1Hbl2EHW_ac0mVa1F0lNxuaeDV2hcuo7K_Uyhb-HOU6E/export?format=csv&gid=496743641"
PITCHER_SPLITS_CSV = "https://docs.google.com/spreadsheets/d/1Hbl2EHW_ac0mVa1F0lNxuaeDV2hcuo7K_Uyhb-HOU6E/export?format=csv&gid=313531137"

ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"

# -------------------------
# HELPER FUNCTIONS
# -------------------------

def get_today_games():
    """Scrape today's MLB games from ESPN with game time and teams."""
    today = datetime.now().strftime("%Y%m%d")
    resp = requests.get(f"{ESPN_URL}?dates={today}").json()

    games = []
    for event in resp.get("events", []):
        comp = event["competitions"][0]
        home = comp["competitors"][0]
        away = comp["competitors"][1]

        game_time = datetime.fromisoformat(comp["date"][:-1]).strftime("%I:%M %p")

        games.append({
            "Game Time": game_time,
            "Away Team": away["team"]["displayName"],
            "Home Team": home["team"]["displayName"],
            "Sportsbook O/U": 8,  # Placeholder until live odds API is added
        })

    return pd.DataFrame(games)

def load_google_sheets():
    """Load team and pitcher stats from Google Sheets CSV export links."""
    team_splits = pd.read_csv(TEAM_SPLITS_CSV)
    pitcher_splits = pd.read_csv(PITCHER_SPLITS_CSV)
    return team_splits, pitcher_splits

def calculate_model_row(row, team_splits, pitcher_splits):
    """
    Calculate model predictions for each game.
    Uses weighted stats: RPG, RPG Allowed, FIP, Bullpen Sierra, etc.
    """
    # Example simple logic: Home RPG + Away RPG Allowed (placeholder)
    home_stats = team_splits[team_splits['Team'] == row['Home Team']].iloc[0]
    away_stats = team_splits[team_splits['Team'] == row['Away Team']].iloc[0]

    # Example scoring model
    model_total = round(
        (home_stats['RPG'] + away_stats['RPGa'] +
         away_stats['RPG'] + home_stats['RPGa']) / 2, 1
    )

    # Determine O/U bet
    sportsbook_total = row['Sportsbook O/U']
    if model_total >= sportsbook_total + 2:
        pick = "BET THE OVER"
    elif model_total <= sportsbook_total - 2:
        pick = "BET THE UNDER"
    else:
        pick = "NO BET"

    return pd.Series({
        "Model Total": model_total,
        "O/U Bet": pick
    })

def calculate_daily_model():
    """Main function to scrape games and calculate daily predictions."""
    games_df = get_today_games()
    if games_df.empty:
        return pd.DataFrame()

    team_splits, pitcher_splits = load_google_sheets()

    predictions = games_df.apply(
        lambda row: calculate_model_row(row, team_splits, pitcher_splits),
        axis=1
    )

    df = pd.concat([games_df, predictions], axis=1)
    return df

if __name__ == "__main__":
    df = calculate_daily_model()
    print(df)

import pandas as pd
import requests
from datetime import datetime
import math

# -----------------------------
# CONFIG
# -----------------------------
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
FANDUEL_URL = "https://sportsbook.fanduel.com/cache/psmg/UK/2/baseball/mlb"  # Example feed
OUTPUT_CSV = "daily_model.csv"

def get_today_games():
    """Scrape ESPN for today's games and starting pitchers"""
    today = datetime.now().strftime("%Y%m%d")
    resp = requests.get(f"{ESPN_URL}?dates={today}").json()
    games = []

    for event in resp.get("events", []):
        comp = event["competitions"][0]
        home = comp["competitors"][0]
        away = comp["competitors"][1]

        home_pitcher = home.get("probables", [{}])[0].get("athlete", {}).get("displayName", "TBD")
        away_pitcher = away.get("probables", [{}])[0].get("athlete", {}).get("displayName", "TBD")
        game_time = datetime.fromisoformat(comp["date"][:-1]).strftime("%I:%M %p")

        # Weather info
        venue = comp.get("venue", {}).get("fullName", "")
        is_dome = any(x in venue.lower() for x in ["dome", "roof"])
        if is_dome:
            weather_icon = "🏟️ Dome"
            weather_desc = "0% / 0 mph"
        else:
            weather_icon = "☀️"
            weather_desc = "10% / 5 mph"  # Placeholder real weather API could be integrated

        games.append({
            "Game Time": game_time,
            "Matchup": f"{away['team']['displayName']} @ {home['team']['displayName']}",
            "Home Team": home['team']['displayName'],
            "Away Team": away['team']['displayName'],
            "Pitchers": f"{away_pitcher} vs {home_pitcher}",
            "Weather": f"{weather_icon} {weather_desc}"
        })

    return pd.DataFrame(games)


def get_fanduel_odds():
    """Scrape FanDuel MLB odds (simplified)"""
    try:
        resp = requests.get(FANDUEL_URL).json()
        # This depends on actual FanDuel API structure
        # Return DataFrame with: Matchup, Moneyline Away, Moneyline Home, Total
        return pd.DataFrame(columns=["Matchup", "Moneyline Away", "Moneyline Home", "Total"])
    except:
        return pd.DataFrame(columns=["Matchup", "Moneyline Away", "Moneyline Home", "Total"])


def calculate_daily_model():
    """Combine games + odds + model logic for predictions"""
    games_df = get_today_games()
    odds_df = get_fanduel_odds()

    merged = pd.merge(games_df, odds_df, on="Matchup", how="left")

    results = []
    for _, row in merged.iterrows():
        # Model predicted score (placeholder logic: 4 + 3)
        away_score = 3.8
        home_score = 4.2
        model_total = round(away_score + home_score, 1)

        # Compare to sportsbook total
        sportsbook_total = float(row["Total"]) if not pd.isna(row["Total"]) else model_total
        diff = model_total - sportsbook_total

        if diff >= 2:
            ou_pick = "BET THE OVER"
        elif diff <= -2:
            ou_pick = "BET THE UNDER"
        else:
            ou_pick = "NO BET"

        results.append({
            "Game Time": row["Game Time"],
            "Matchup": row["Matchup"],
            "Pitchers": row["Pitchers"],
            "Sportsbook O/U": sportsbook_total,
            "Model Total": model_total,
            "Pick": ou_pick,
            "Moneyline Away": row.get("Moneyline Away", ""),
            "Moneyline Home": row.get("Moneyline Home", ""),
            "Weather": row["Weather"]
        })

    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV, index=False)
    return df

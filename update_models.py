import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup

CSV_FILENAME = "daily_model.csv"

# -------------------------------
# 1. Get Today's Games from ESPN
# -------------------------------
def get_espn_games():
    today = datetime.now().strftime("%Y%m%d")
    url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates={today}"
    resp = requests.get(url).json()

    games = []
    for event in resp.get("events", []):
        comp = event["competitions"][0]
        teams = comp["competitors"]
        home = next(t for t in teams if t["homeAway"] == "home")["team"]["displayName"]
        away = next(t for t in teams if t["homeAway"] == "away")["team"]["displayName"]

        # Game time in 12-hour ET
        game_time = datetime.strptime(event["date"], "%Y-%m-%dT%H:%MZ").strftime("%I:%M %p")

        games.append({
            "game_time": game_time,
            "home_team": home,
            "away_team": away
        })
    return pd.DataFrame(games)


# -------------------------------
# 2. Get FanDuel Book O/U Lines
# -------------------------------
def get_fanduel_odds():
    url = "https://sportsbook.fanduel.com/navigation/mlb"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")

    # Example scraping logic — this may need tweaking if Fanduel changes layout
    lines = {}
    for game_block in soup.find_all("div", class_="event"):
        teams = [t.get_text(strip=True) for t in game_block.select(".name")]
        ou_tag = game_block.find("span", class_="total")  # placeholder class
        if len(teams) == 2 and ou_tag:
            lines[f"{teams[0]} vs {teams[1]}"] = ou_tag.get_text(strip=True)

    return lines


# -------------------------------
# 3. Daily Model Formula
# -------------------------------
def calculate_model_scores(row):
    # Example weighted formula (adjustable)
    # Replace with your real stats integration
    away_score = (row.get("away_rpg25", 4.2) + row.get("home_rpga25", 4.1)) / 2
    home_score = (row.get("home_rpg25", 4.5) + row.get("away_rpga25", 4.0)) / 2

    # Example O/U projection
    model_ou = round(away_score + home_score, 1)

    # Determine ML favorite and win %
    if home_score > away_score:
        ml_winner = f"{row['home_team']} ({int(60 + (home_score-away_score)*5)}%)"
    else:
        ml_winner = f"{row['away_team']} ({int(60 + (away_score-home_score)*5)}%)"

    return pd.Series([round(away_score, 1), round(home_score, 1), ml_winner, model_ou])


# -------------------------------
# 4. Main Function
# -------------------------------
def main():
    games_df = get_espn_games()
    # Merge in future team stats if available for the formula
    # For now using simple weights and placeholders for stats

    games_df[["away_score", "home_score", "ml_winner", "model_ou"]] = games_df.apply(calculate_model_scores, axis=1)

    # Pull book O/U
    fanduel_lines = get_fanduel_odds()
    games_df["book_ou"] = games_df.apply(
        lambda row: fanduel_lines.get(f"{row['away_team']} vs {row['home_team']}", "N/A"), axis=1
    )

    # Reorder columns for final CSV
    output_df = games_df[[
        "game_time", "away_team", "away_score", "home_team", "home_score",
        "ml_winner", "book_ou", "model_ou"
    ]]

    output_df.to_csv(CSV_FILENAME, index=False)
    print(f"Daily MLB model updated: {CSV_FILENAME}")


if __name__ == "__main__":
    main()

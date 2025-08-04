import streamlit as st
import pandas as pd
from update_models import calculate_daily_model

st.set_page_config(page_title="MLB Daily Model", layout="wide")
st.title("⚾ MLB Daily Betting Model (Automatic)")

# ---------------------------
# Load data
# ---------------------------
with st.spinner("Scraping live MLB stats and calculating model..."):
    df = calculate_daily_model()

# ---------------------------
# Define columns to display
# ---------------------------
display_cols = [
    'Team',           # Team name
    'RPG',            # Runs per Game
    'RPGa',           # Runs Allowed per Game
    'rOBA',           # Team rOBA (Baseball Reference)
    'Bullpen_ERA',    # Bullpen ERA
    'Bullpen_WHIP',   # Bullpen WHIP
    'SP_ERA',         # Starting Pitcher ERA
    'SP_FIP',         # Starting Pitcher FIP
    'Model_Total',    # Our calculated total runs
    'O/U Bet'         # Bet recommendation
]

df_display = df[display_cols].copy()

# ---------------------------
# Color function for O/U Bet
# ---------------------------
def style_ou(val):
    if val == "BET THE OVER":
        return "background-color: #d1f7c4;"  # light green
    elif val == "BET THE UNDER":
        return "background-color: #fcd7d7;"  # light red
    elif val == "NO BET":
        return "background-color: #f1f1f1;"  # light gray
    return ""

# ---------------------------
# Handle empty dataframe
# ---------------------------
if df_display.empty:
    st.warning("No MLB data available today. Please check sources or try again later.")
else:
    # Reset index for clean display
    df_display = df_display.reset_index(drop=True)

    # Apply styling to O/U Bet column only
    st.dataframe(
        df_display.style.applymap(style_ou, subset=['O/U Bet']),
        use_container_width=True
    )

# ---------------------------
# Optional navigation
# ---------------------------
if st.button("⬅️ Back to Homepage"):
    st.switch_page("pages/home.py")

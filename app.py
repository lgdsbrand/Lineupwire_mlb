import streamlit as st
import pandas as pd
from update_models import calculate_daily_model

# -----------------------------
# STREAMLIT PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="MLB Daily Betting Model",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit default menu and footer
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# -----------------------------
# PAGE HEADER
# -----------------------------
st.markdown("[⬅️ Back to Homepage](https://lgdsbrand.streamlit.app)", unsafe_allow_html=True)
st.title("MLB Daily Betting Model (Automatic)")
st.markdown("---")

# -----------------------------
# LOAD DAILY MODEL DATA
# -----------------------------
df = calculate_daily_model()

# Expected 9 columns
expected_cols = [
    "Game Time", "Away Team", "Away Score",
    "Home Team", "Home Score", "ML (%)",
    "Book O/U", "Model O/U", "O/U Bet"
]

# Reindex to ensure all expected columns exist
df = df.reindex(columns=expected_cols)

# -----------------------------
# STYLE THE TABLE
# -----------------------------
def color_ou(val):
    if val == "BET THE OVER":
        return "background-color: #d1f7c4; color: black; font-weight: bold;"  # green
    elif val == "BET THE UNDER":
        return "background-color: #fcd7d7; color: black; font-weight: bold;"  # red
    elif val == "NO BET":
        return "background-color: #f1f1f1; color: black;"  # grey
    else:
        return ""

styled_df = df.style.applymap(color_ou, subset=["O/U Bet"])

# Display table without index
st.dataframe(styled_df, use_container_width=True, hide_index=True)

import streamlit as st
import pandas as pd
from update_models import calculate_daily_model

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="MLB Daily Model",
    layout="wide"
)

# -----------------------------
# STYLE HELPERS
# -----------------------------
def style_ou(val):
    """Color code Over/Under picks"""
    if val == "BET THE OVER":
        return "background-color:#d1f7c4;color:black;font-weight:bold"  # green
    elif val == "BET THE UNDER":
        return "background-color:#fcd7d7;color:black;font-weight:bold"  # red
    else:
        return "background-color:#f1f1f1;color:black"  # gray

# -----------------------------
# TITLE + NAV
# -----------------------------
st.markdown("<h1 style='text-align:center;'>⚾ MLB Daily Model</h1>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;margin-bottom:20px;'>"
            "<a href='https://lineupwire.com' style='text-decoration:none;font-size:18px;'>⬅️ Back to Homepage</a>"
            "</div>", unsafe_allow_html=True)

# -----------------------------
# CALCULATE MODEL
# -----------------------------
with st.spinner("Calculating daily model..."):
    df = calculate_daily_model()

if df.empty:
    st.warning("No games or data available today.")
else:
    # Reset index for cleaner table
    df_reset = df.reset_index(drop=True)

    # Show styled dataframe
    st.dataframe(
        df_reset.style.applymap(style_ou, subset=["O/U Bet"]),
        use_container_width=True
    )

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.caption("LineupWire MLB Model – Auto-updates daily using ESPN, TeamRankings, Covers, and Fangraphs.")

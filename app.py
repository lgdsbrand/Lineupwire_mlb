import streamlit as st
import pandas as pd
import os
from update_models import calculate_daily_model

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Daily MLB Betting Model", layout="wide")

st.title("Daily MLB Betting Model")
st.markdown("[⬅️ Back to Homepage](https://lineupwire.com)")

# -----------------------------
# LOAD PREDICTIONS WITH FALLBACK
# -----------------------------
try:
    df = calculate_daily_model()
except Exception as e:
    st.warning(f"⚠️ Live model failed: {e}. Loading last saved CSV.")
    if os.path.exists("daily_model.csv"):
        df = pd.read_csv("daily_model.csv")
    else:
        st.error("❌ No live data or saved CSV available.")
        st.stop()

# -----------------------------
# COLOR FUNCTION
# -----------------------------
def color_pick(val):
    if val == "BET THE OVER":
        return "background-color: #d1f7c4;"  # green
    elif val == "BET THE UNDER":
        return "background-color: #fcd7d7;"  # red
    elif val == "NO BET":
        return "background-color: #f1f1f1;"  # gray
    return ""

# -----------------------------
# DISPLAY TABLE
# -----------------------------
if df.empty:
    st.warning("No games available today.")
else:
    styled = df.style.applymap(color_pick, subset=["Pick"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

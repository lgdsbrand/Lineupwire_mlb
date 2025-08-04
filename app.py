import streamlit as st
from update_models import calculate_daily_model

st.set_page_config(page_title="MLB Daily Model", layout="wide")
st.title("MLB Daily Betting Model (Automatic)")

with st.spinner("Scraping live data and calculating model predictions..."):
    df = calculate_daily_model()

# Color function for O/U Bet column
def color_pick(val):
    if val == "BET THE OVER":
        return "background-color: #d1f7c4;"  # green
    elif val == "BET THE UNDER":
        return "background-color: #fcd7d7;"  # red
    elif val == "NO BET":
        return "background-color: #f1f1f1;"  # gray
    return ""

if df.empty:
    st.warning("No games available today.")
else:
    styled = df.style.applymap(color_pick, subset=["O/U Bet"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

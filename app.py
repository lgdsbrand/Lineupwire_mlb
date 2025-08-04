import streamlit as st
from update_models import calculate_daily_model

# Hide Streamlit menu and footer
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.set_page_config(page_title="MLB Daily Model", layout="wide")

# Back to Homepage button
st.markdown("[⬅️ Back to Homepage](https://lgdsbrand.streamlit.app)")

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
    st.markdown(styled.to_html(index=False), unsafe_allow_html=True)

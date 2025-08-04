import streamlit as st
from update_models import calculate_daily_model

st.set_page_config(page_title="MLB Daily Model")
st.title("MLB Daily Betting Model (Automatic)")

with st.spinner("Scraping live data and calculating model..."):
    df = calculate_daily_model()

# Color function for O/U Bet column
def color_pick(val):
    if val == "BET THE OVER":
        return "background-color: #d1f7c4;"  # light green
    elif val == "BET THE UNDER":
        return "background-color: #fcd7d7;"  # light red
    elif val == "NO BET":
        return "background-color: #f1f1f1;"  # gray
    return ""

if df.empty:
    st.warning("No games available today.")
else:
    # Apply style and render as HTML to keep colors
    styled = df.style.applymap(color_pick, subset=["O/U Bet"])
    st.markdown(styled.to_html(), unsafe_allow_html=True)

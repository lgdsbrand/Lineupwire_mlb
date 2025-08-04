import streamlit as st
import pandas as pd
from update_models import calculate_daily_model

st.set_page_config(page_title="MLB Daily Model", layout="wide")

st.title("⚾ MLB Daily Model")
st.markdown("[🔙 Back to Homepage](https://lineupwire.com)")

# Calculate daily model DataFrame
df = calculate_daily_model()

# Color function for O/U pick
def style_ou(val):
    if val == "BET THE OVER":
        return "background-color: #c8e6c9; color: black;"  # green
    elif val == "BET THE UNDER":
        return "background-color: #ffcdd2; color: black;"  # red
    else:
        return "background-color: #f0f0f0; color: black;"  # gray

# Display styled table
st.dataframe(
    df.style.applymap(style_ou, subset=["O/U Bet"]),
    use_container_width=True
)

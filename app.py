import streamlit as st
import pandas as pd
from update_models import calculate_daily_model

# -----------------------------
# STREAMLIT CONFIG
# -----------------------------
st.set_page_config(
    page_title="MLB Daily Model",
    page_icon="⚾",
    layout="wide"
)

st.title("⚾ MLB Daily Betting Model (Automatic)")

# Load data
df = calculate_daily_model()

# Replace None/NaN with blank for cleaner UI
df = df.fillna("")

# Columns to display (match your model output)
display_cols = [
    'Team', 'RPG', 'RPGa', 'rOBA',
    'Bullpen_ERA', 'Bullpen_WHIP',
    'SP_ERA', 'SP_FIP',
    'Model_Total', 'O/U Bet'
]

# Only show columns that exist
display_cols = [c for c in display_cols if c in df.columns]

st.dataframe(
    df[display_cols],
    use_container_width=True
)

# Back to homepage button
if st.button("⬅ Back to Homepage"):
    st.switch_page("Home.py")

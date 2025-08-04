import streamlit as st
import pandas as pd
from update_models import calculate_daily_model

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(
    page_title="MLB Daily Betting Model",
    page_icon="⚾",
    layout="wide",
)

# Hide Streamlit default menu, footer, and GitHub icon
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# -------------------------------
# HEADER
# -------------------------------
st.title("⚾ MLB Daily Betting Model (Automatic)")

# -------------------------------
# LOAD DAILY MODEL
# -------------------------------
with st.spinner("Calculating model..."):
    df = calculate_daily_model()

# -------------------------------
# DISPLAY MODEL TABLE
# -------------------------------
display_cols = [
    "Team", "RPG", "RPGA", "rOBA",
    "Bullpen_ERA", "Bullpen_WHIP",
    "SP_ERA", "SP_FIP",
    "Model_Total", "O/U Bet"
]

# Handle if any columns are missing (e.g., during first run)
df_reset = df.reset_index(drop=True)
for col in display_cols:
    if col not in df_reset.columns:
        df_reset[col] = None

st.dataframe(
    df_reset[display_cols],
    use_container_width=True
)

st.success("✅ Model updated automatically.")

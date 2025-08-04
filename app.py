import streamlit as st
import pandas as pd
from update_models import calculate_daily_model

# -----------------------------
# STREAMLIT PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="MLB Daily Model", layout="wide")

# Hide Streamlit menu & footer for a cleaner UI
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------
col1, col2 = st.columns([8,2])
with col1:
    st.title("⚾ MLB Daily Model")
with col2:
    st.markdown(
        """
        <a href="/" target="_self">
            <button style="background-color:#1f77b4;color:white;padding:8px 12px;border:none;border-radius:5px;cursor:pointer;">
            Back to Homepage
            </button>
        </a>
        """, 
        unsafe_allow_html=True
    )

st.write("Model auto-updates daily with real stats and FanDuel O/U lines.")

# -----------------------------
# CALCULATE MODEL
# -----------------------------
with st.spinner("Calculating today's model..."):
    df = calculate_daily_model()

if df.empty:
    st.warning("No MLB games found for today.")
else:
    # Remove index for cleaner view
    df_reset = df.reset_index(drop=True)
    
    # Style O/U Bet column
    def style_ou(val):
        if val == "BET THE OVER":
            return "background-color: #d4f7d4; color: black;"  # green
        elif val == "BET THE UNDER":
            return "background-color: #f7d4d4; color: black;"  # red
        else:
            return "background-color: #f0f0f0; color: black;"  # gray

    st.subheader("📊 Daily Score & O/U Predictions")

# Create styled DataFrame as HTML because st.dataframe can't handle Styler
styled_html = df_reset.style.applymap(style_ou, subset=["O/U Bet"]).to_html()
st.markdown(styled_html, unsafe_allow_html=True)

st.markdown("---")
st.caption("Data Sources: ESPN, TeamRankings, FanGraphs, Baseball Reference, BallparkPal, Sonny Moore, FanDuel Odds")

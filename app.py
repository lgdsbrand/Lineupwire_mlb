import streamlit as st
import pandas as pd

# Simulated daily MLB model output
def load_model_predictions():
    return pd.DataFrame({
        'Game': ['Giants @ Blue Jays', 'Orioles @ Yankees', 'Rangers @ Mariners'],
        'Game Time': ['3:07 PM', '4:05 PM', '9:10 PM'],
        'Win %': ['44% / 56%', '49% / 51%', '46% / 54%'],
        'Proj Score': ['3.9 - 5.1', '4.1 - 4.2', '4.3 - 4.7'],
        'Model O/U': ['9.0', '8.3', '9.0'],
        'Sportsbook O/U': ['8.5', '8.0', '7.5'],
        'Bet': ['BET THE OVER', 'NO BET', 'BET THE OVER'],
        'NRFI %': ['51%', '58%', '54%'],
        'Confidence': ['8', '6', '9']
    })

st.set_page_config(page_title="LineupWire MLB Model", layout="wide")
st.title("📊 LineupWire MLB Model — Daily Predictions")

df = load_model_predictions()
st.dataframe(df, use_container_width=True)

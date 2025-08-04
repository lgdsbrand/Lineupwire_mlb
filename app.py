import streamlit as st
import pandas as pd
from update_models import calculate_daily_model  # Make sure this returns a DataFrame

st.set_page_config(page_title="MLB Daily Model", layout="wide")
st.title("MLB Daily Betting Model (Automatic)")

with st.spinner("Scraping live data and calculating model..."):
    try:
        df = calculate_daily_model()
    except Exception as e:
        st.warning(f"⚠️ Live data failed. Loading fallback CSV. Error: {e}")
        try:
            df = pd.read_csv("sample_data.csv")
        except:
            df = pd.DataFrame()

# Color function for O/U Bet column
def color_pick(val):
    if val == "BET THE OVER":
        return "background-color: #d1f7c4;"  # light green
    elif val == "BET THE UNDER":
        return "background-color: #fcd7d7;"  # light red
    elif val == "NO BET":
        return "background-color: #f1f1f1;"  # light gray
    return ""

# Display table
if df.empty:
    st.warning("No games available today.")
else:
    st.subheader("Today's Model Predictions")

    # Try styling only if O/U Bet column exists
    if "O/U Bet" in df.columns:
        styled = df.style.applymap(color_pick, subset=["O/U Bet"])
        st.markdown(styled.to_html(index=False), unsafe_allow_html=True)
    else:
        st.dataframe(df, use_container_width=True)

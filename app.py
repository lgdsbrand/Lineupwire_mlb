import streamlit as st
import pandas as pd
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="MLB Daily Model", layout="wide")
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- BACK TO HOMEPAGE BUTTON ---
st.markdown("""
<div style="text-align: left; margin-bottom: 10px;">
    <a href="https://lineupwire.com" target="_self" 
       style="background-color: black; color: white; padding: 6px 16px; 
              border-radius: 12px; text-decoration: none;">
        ⬅ Back to Homepage
    </a>
</div>
""", unsafe_allow_html=True)

# --- TITLE ---
st.markdown("<h1 style='display: inline;'>⚾ MLB Daily Model</h1>", unsafe_allow_html=True)

# --- TOGGLE BUTTONS ---
toggle = st.radio("Select View", ["Card View", "Table View", "Records"], horizontal=True)

# --- LOAD DAILY MODEL ---
@st.cache_data(ttl=60*60)
def load_daily_model():
    return pd.read_csv("daily_model.csv")

try:
    df = load_daily_model()
except FileNotFoundError:
    st.error("Daily model data not found. Wait for next refresh.")
    st.stop()

# --- CLEAN DATA ---
if df.columns[0].lower() in ['unnamed: 0', 'index']:
    df = df.drop(df.columns[0], axis=1)

score_cols = ['Away Score Proj', 'Home Score Proj', 'Book O/U', 'Model O/U']
for col in score_cols:
    if col in df.columns:
        df[col] = df[col].map(lambda x: f"{x:.1f}" if pd.notnull(x) else "")

# --- SORT BY GAME TIME ---
if 'Game Time' in df.columns:
    try:
        df['sort_time'] = pd.to_datetime(df['Game Time'], errors='coerce')
        df = df.sort_values('sort_time').drop(columns=['sort_time'])
    except:
        pass

# --- AUTO RECORD TRACKING ---
record_file = "daily_records.csv"
today = datetime.now().date()
if "ML Bet" in df.columns:
    wins = sum(df["ML Bet"].str.contains("W", na=False))
    losses = sum(~df["ML Bet"].str.contains("W", na=False))
    today_record = pd.DataFrame([[today, "Daily Model", wins, losses,
                                  f"{(wins/(wins+losses))*100:.0f}%"]],
                                  columns=["Date","Model","Wins","Losses","Win%"])
    try:
        old_records = pd.read_csv(record_file)
    except:
        old_records = pd.DataFrame(columns=today_record.columns)
    if str(today) not in old_records["Date"].astype(str).values:
        pd.concat([old_records, today_record], ignore_index=True).to_csv(record_file, index=False)

# --- TOGGLE VIEWS ---
if toggle == "Table View":
    st.dataframe(df, use_container_width=True, hide_index=True)

elif toggle == "Card View":
    for _, row in df.iterrows():
        st.markdown(f"""
        <div style="border:1px solid #ccc; border-radius:12px; padding:10px; margin-bottom:10px;">
            <strong>{row['Game Time']}</strong>  
            <h4>{row['Away Team']} ({row['Away Score Proj']}) @ 
            {row['Home Team']} ({row['Home Score Proj']})</h4>
            <p><b>ML Bet:</b> {row['ML Bet']}</p>
            <p><b>Book O/U:</b> {row['Book O/U']} | <b>Model O/U:</b> {row['Model O/U']}</p>
        </div>
        """, unsafe_allow_html=True)

elif toggle == "Records":
    try:
        rec = pd.read_csv(record_file)
        # Weekly / Monthly summaries
        rec['Date'] = pd.to_datetime(rec['Date'])
        rec['Week'] = rec['Date'].dt.isocalendar().week
        rec['Month'] = rec['Date'].dt.month
        st.subheader("Daily Records")
        st.dataframe(rec.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)
        st.subheader("Weekly Summary")
        st.dataframe(rec.groupby("Week")[["Wins","Losses"]].sum(), use_container_width=True)
        st.subheader("Monthly Summary")
        st.dataframe(rec.groupby("Month")[["Wins","Losses"]].sum(), use_container_width=True)
    except FileNotFoundError:
        st.info("No record file yet.")

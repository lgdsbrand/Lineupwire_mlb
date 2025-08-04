import streamlit as st
import pandas as pd

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="MLB Daily Model", layout="wide")

st.title("⚾ MLB Daily Model")

# Back to Homepage button
if st.button("🏠 Back to Homepage"):
    st.switch_page("app.py")  # Works if using Streamlit multipage structure

# ---------------------------
# LOAD GOOGLE SHEET CSV
# ---------------------------
sheet_url = "https://docs.google.com/spreadsheets/d/1Hbl2EHW_ac0mVa1F0lNxuaeDV2hcuo7K_Uyhb-HOU6E/gviz/tq?tqx=out:csv&sheet=DailyModel"

try:
    df = pd.read_csv(sheet_url)
    
    # Optional: clean None / NaN
    df.fillna("", inplace=True)
    
    # Display table
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error("⚠️ Could not load Daily Model from Google Sheets. Check the sheet URL and sharing settings.")
    st.text(str(e))

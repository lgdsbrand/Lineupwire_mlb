import streamlit as st
import pandas as pd
from update_models import calculate_daily_model

# ---------------------------
# STREAMLIT PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="MLB Daily Model", layout="wide")
st.title("MLB Daily Model (Live)")

# ---------------------------
# LOAD MODEL DATA
# ---------------------------
with st.spinner("Calculating daily model..."):
    df = calculate_daily_model()

# ---------------------------
# DISPLAY RESULTS OR DIAGNOSTICS
# ---------------------------
if df is None or df.empty:
    st.error("⚠ No data returned from calculate_daily_model(). Showing diagnostics below.")
    
    # Try to show diagnostics CSV if it exists
    try:
        diag = pd.read_csv("diagnostics.csv")
        st.dataframe(diag, use_container_width=True)
    except FileNotFoundError:
        st.warning("No diagnostics.csv found. Check update_models.py scraping functions.")
else:
    # Main display
    st.success("✅ Model data loaded successfully!")
    st.dataframe(df, use_container_width=True)

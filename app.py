import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    table td, table th {
        text-align: center !important;
        font-size: 18px !important;
    }
    .stDataFrame {height: auto !important;}
    </style>
    """, unsafe_allow_html=True
)

st.title("MLB Daily Model")

# Back to Homepage Button
st.markdown(
    '<a href="https://lineupwire.com" style="display:inline-block; padding:10px 20px; background:black; color:white; text-decoration:none; border-radius:8px;">Back to Homepage</a>',
    unsafe_allow_html=True
)

# Load daily_model.csv
df = pd.read_csv("daily_model.csv")

# Ensure no index and auto-fit width
st.dataframe(df, use_container_width=True, hide_index=True)

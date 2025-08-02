import streamlit as st
import pandas as pd
import datetime as dt

# ===== PAGE CONFIG =====
st.set_page_config(page_title="MLB Daily Model", layout="wide")

# Hide Streamlit menu and footer
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Back to Homepage button
st.markdown(
    """
    <a href="https://lineupwire.com" target="_self">
        <button style="
            background-color: black;
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            border: none;
            font-size: 16px;
            cursor: pointer;
        ">Back to Homepage</button>
    </a>
    """,
    unsafe_allow_html=True
)

st.title("⚾ MLB Daily Model")

# ===== LOAD DATA (replace with your Google Sheet or data source) =====
# Example using CSV or Google Sheet (update with your link)
try:
    # Example: Replace with your real data source
    df = pd.read_csv("daily_model.csv")

    # Ensure proper formatting
    df["Game Time"] = pd.to_datetime(df["Game Time"])
    df = df.sort_values("Game Time")

    # Format scores to single decimal
    df["Away Score"] = df["Away Score"].map(lambda x: f"{x:.1f}")
    df["Home Score"] = df["Home Score"].map(lambda x: f"{x:.1f}")

    # Drop index column for clean look
    df.reset_index(drop=True, inplace=True)

    # Create a styled HTML table
    styled_table = df.to_html(
        index=False,
        classes="styled-table",
        escape=False
    )

    # Add table styling with rounded red/blue border
    st.markdown(
        """
        <style>
        .styled-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 16px;
            text-align: center;
            border: 2px solid blue;
            border-radius: 10px;
            overflow: hidden;
        }
        .styled-table th, .styled-table td {
            border: 1px solid red;
            padding: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(styled_table, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error loading Daily Model: {e}")

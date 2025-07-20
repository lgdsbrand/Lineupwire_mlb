import streamlit as st
import pandas as pd

# Simulated daily MLB model output
def load_model_predictions():
    return pd.DataFrame({
        'Game': ['Giants @ Blue Jays', 'Orioles @ Yankees', 'Rangers @ Mariners

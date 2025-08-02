import pandas as pd
from datetime import datetime
from nrfi_model import generate_nrfi_model  # function that returns a dataframe
from daily_model import generate_daily_model  # function that returns a dataframe

    # === 2. Generate Daily MLB Model ===
    try:
        daily_df = generate_daily_model()
        daily_filename = "daily_model.csv"
        daily_df.to_csv(daily_filename, index=False)
        print(f"[{datetime.now()}] Daily model saved as {daily_filename}")
    except Exception as e:
        print(f"Error generating Daily model: {e}")

if __name__ == "__main__":
    update_models()

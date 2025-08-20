import pandas as pd
from pathlib import Path
from datetime import datetime

def incremental_load():
    refresh_file = pd.read_csv(Path(__file__).resolve().parent / "time_tracker" / "refresh_file_releases.csv")

    timestamp = datetime.now()
    today = datetime.today().date()

    new_row = pd.DataFrame([[today,timestamp]], columns=['refresh_date', 'timestamp'])

    refresh_file = pd.concat([refresh_file, new_row], ignore_index=True)

    refresh_file.to_csv(Path(__file__).resolve().parent / "time_tracker" / "refresh_file_releases.csv", index=False)

def full_refresh():
    timestamp = datetime.now()
    today = datetime.today().date()

    refresh_file = pd.DataFrame([[today,timestamp]], columns=['refresh_date', 'timestamp'])

    refresh_file.to_csv(Path(__file__).resolve().parent / "time_tracker" / "refresh_file_releases.csv", index=False)

incremental_load()
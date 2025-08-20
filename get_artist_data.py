import requests
import os
import pandas as pd
import random
import time
from datetime import datetime
import mysql.connector
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent / "music_bot.env")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

connection = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_DATABASE"),
)

cursor = connection.cursor()

def get_spotify_token():
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    )
    return resp.json()["access_token"]

def get_spotify_artist(spotify_artist_id, token):

    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.spotify.com/v1/artists/{spotify_artist_id}"

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"[ERROR] Failed to fetch artist {spotify_artist_id}: {resp.status_code}")
        return None
    
    return resp.json()

def throttle_requests(min_delay=0.1, max_delay=0.2):
    # Wait between API requests to stay under 10/sec with jitter.
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)

artists_df = pd.read_csv(Path(__file__).resolve().parent / "following" / "all_artist_data.csv")

list_of_artist_data = []
toke = get_spotify_token()

for artist_name,artist_id,following in zip(artists_df['artist'], artists_df['id'], artists_df['following']):

    result_json = get_spotify_artist(artist_id,toke)
    
    artist_row = (
        result_json["name"],
        result_json["id"],
        result_json["followers"]["total"],
        result_json["type"],
        ", ".join(result_json["genres"]),
        result_json["popularity"],
        result_json["images"][1]["url"] if len(result_json.get("images", [])) > 1 else "",
        result_json["images"][2]["url"] if len(result_json.get("images", [])) > 2 else "",
        datetime.now()
    )

    list_of_artist_data.append(artist_row)
    throttle_requests()

cursor.executemany("""
insert into music_db.artist_data (name, id, followers, type, genres, popularity, small_image, medium_image, `timestamp`)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
""", list_of_artist_data)

connection.commit()
cursor.close()
connection.close()
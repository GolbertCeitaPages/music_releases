##########################################################################################################################################################################
# Purpose: Gets the most recent release of every artist specified in the all_artist_data.csv file in the "following" folder
##########################################################################################################################################################################

import discord
import requests
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import subprocess

load_dotenv(dotenv_path=Path(__file__).resolve().parent / "music_bot.env")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

# All artist ids
artists = pd.read_csv(Path(__file__).resolve().parent / "following" / "all_artist_data.csv") 

log_path = Path(__file__).resolve().parent / "debug_log.txt"
csv_path = Path(__file__).resolve().parent / "following" / "all_artist_data.csv"

with open(log_path, "w", encoding="utf-8") as log:
    log.write(f"[DEBUG] CSV path: {csv_path}\n")
    log.write(f"[DEBUG] File exists: {csv_path.exists()}\n")

    if csv_path.exists():
        content_preview = csv_path.read_text(encoding="utf-8")[:300]
        log.write(f"[DEBUG] File preview:\n{content_preview}\n")

    try:
        artists = pd.read_csv(csv_path)
        log.write(f"[DEBUG] Type after read_csv: {type(artists)}\n")
        log.write(f"[DEBUG] Columns: {artists.columns.tolist()}\n")
        log.write(f"[DEBUG] Head:\n{artists.head().to_string()}\n")
    except Exception as e:
        log.write(f"[ERROR] Failed to load CSV: {e}\n")
        artists = None  # fail

# last run
runtime_csv = pd.read_csv(Path(__file__).resolve().parent / "time_tracker" / "refresh_file.csv")

def get_spotify_token():
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    )
    return resp.json()["access_token"]

def get_albums_for_artists(artists, token):
    headers = {"Authorization": f"Bearer {token}"}
    list_of_jsons = []
    list_for_discord = []
    list_for_csv = []
 
    for artist,id,following in zip(artists['artist'],artists['id'],artists['following']):

        url = f"https://api.spotify.com/v1/artists/{id}/albums"
        params = {
            "include_groups": "album,single",
            "limit": 30,
            "market": "NL"
        }
        
        if following == True:
            resp = requests.get(url, headers=headers, params=params)
            data = resp.json()
        
        if resp.status_code != 200:
            print(f"Error fetching {artist[0]}: {data}")
            continue
        
        album_list = data.get("items", [])

        last_rundate = datetime.strptime(runtime_csv["refresh_date"].min(), "%Y-%m-%d")

        # only try to append when there are values present in the dataset and the release data was after the last rundate
        if album_list:
            for album in album_list:
                release_date = album.get('release_date')
                if release_date:
                    try:
                        release = datetime.strptime(release_date, "%Y-%m-%d")
                        if release > last_rundate:
                            list_of_jsons.append(album)
                            list_for_discord.append(
                            f"🎵 **{artist}** - {album['name']} - released on: {release_date} ({album['external_urls']['spotify']})"
                        )   
                            list_for_csv.append((artist,album['name'],release_date,album['type'],", ".join([a['name'] for a in album['artists']]),datetime.now()))
                    except ValueError:
                        pass

    return list_of_jsons,list_for_discord,list_for_csv

if datetime.strptime(runtime_csv["refresh_date"].max(), "%Y-%m-%d").date() < datetime.now().date():
    token = get_spotify_token()
    jsons,disc,csv_list = get_albums_for_artists(artists,token)

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n[DEBUG] Processing {len(csv_list)} album rows for deduplication...\n")

    # Remove duplicates by keying on (album title, release date, type, artists)
    unique_entries = {}
    for i, row in enumerate(csv_list):
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(f"\n[DEBUG] Processing row {i}: {row}\n")

        if not isinstance(row, (list, tuple)) or len(row) != 6:
            with open(log_path, "a", encoding="utf-8") as log:
                log.write(f"[WARNING] Skipping malformed row {i}: {row}\n")
            continue

        tracked_artist, album_title, release_date, album_type, artists, timestamp = row

        # Debug each element in the key
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(f"[DEBUG] Key parts types: {type(album_title)}, {type(release_date)}, {type(album_type)}, {type(artists)}\n")

        # Check if artists is a list or dict (unhashable)
        if isinstance(artists, (list, dict)):
            with open(log_path, "a", encoding="utf-8") as log:
                log.write(f"[ERROR] Unhashable type in 'artists' at row {i}: {artists} ({type(artists)})\n")
            continue

        key = (album_title, release_date, album_type, artists)
        unique_entries[key] = (tracked_artist, album_title, release_date, album_type, artists, timestamp)
            
    updated_csv_list = list(unique_entries.values())
    
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"[DEBUG] After deduplication: {len(updated_csv_list)} unique rows.\n")

    # load and add the new rows to the tracker list
    try:
        run_tracker = pd.read_csv(Path(__file__).resolve().parent / "time_tracker" / "album_trail.csv")
        new_row = pd.DataFrame([updated_csv_list], columns=["tracked artist","album title","release date","type","artists","timestamp"])
        run_tracker = pd.concat([run_tracker, new_row], ignore_index=True)
        
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(f"[DEBUG] Loaded existing album_trail.csv with {len(run_tracker)} rows.\n")

    except FileNotFoundError:
        run_tracker = pd.DataFrame(updated_csv_list,columns=["tracked artist","album title","release date","type","artists","timestamp"])
        print("no base file")
        with open(log_path, "a", encoding="utf-8") as log:
            log.write("[DEBUG] album_trail.csv not found. Created new file.\n")

    # create csv
    run_tracker.to_csv(Path(__file__).resolve().parent / "time_tracker" / "album_trail.csv",index=False)

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"[DEBUG] album_trail.csv written with {len(run_tracker)} total rows.\n")

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}")
        channel = client.get_channel(DISCORD_CHANNEL_ID)

        for album_info in disc:
            await channel.send(album_info)

        await client.close()

    client.run(DISCORD_TOKEN)

    subprocess.run(["python", str(Path(__file__).resolve().parent / "refresh_script.py")])
##########################################################################################################################################################################
# Purpose: Gets the most recent release of every artist specified in the all_artist_data.csv file in the "following" folder
##########################################################################################################################################################################

import discord
import requests
import os
import time
import mysql.connector
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import random
import subprocess

load_dotenv(dotenv_path=Path(__file__).resolve().parent / "music_bot.env")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

connection = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_DATABASE"),
)

cursor = connection.cursor()

# All artist ids and debug file
log_path = Path(__file__).resolve().parent / "debug_log_new_releases.txt"
excel_path = Path(__file__).resolve().parent / "following" / "all_artists.xlsx"

with open(log_path, "w", encoding="utf-8") as log:
    log.write(f"[DEBUG] {datetime.now()} CSV path: {excel_path}\n")
    log.write(f"[DEBUG] {datetime.now()} File exists: {excel_path.exists()}\n")

    try:
        # get the artist names and ids of artists that are tracked 
        artists = pd.read_excel(excel_path)
        log.write(f"[DEBUG] {datetime.now()} Type after read_csv: {type(artists)}\n")
        log.write(f"[DEBUG] {datetime.now()} Columns: {artists.columns.tolist()}\n")
        log.write(f"[DEBUG] {datetime.now()} Head:\n{artists.head().to_string()}\n")
    except Exception as e:
        log.write(f"[ERROR] {datetime.now()} Failed to load CSV: {e}\n")
        artists = None  


def throttle_requests(min_delay=0.1, max_delay=0.2):
    # Wait between API requests to stay under 10/sec with jitter.
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)

# last run
runtime_csv = pd.read_csv(Path(__file__).resolve().parent / "time_tracker" / "refresh_file_releases.csv")

cursor.execute("SELECT album_id FROM music_db.album_trail")
spotify_album_id_list = [row[0] for row in cursor.fetchall()]

def get_spotify_token():
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    )
    return resp.json()["access_token"]

def get_albums_for_artists(artists, token):
    headers = {"Authorization": f"Bearer {token}"}
    list_for_translation_table = []
    list_for_discord = []
    list_for_album_trail = []
    id_validation_list = []

    for artist, artist_id in zip(artists['artist'], artists['artist_id']):

        url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
        params = {
            "include_groups": "album,single",
            "limit": 30,
            "market": "NL"
        }

        while url:
            resp = requests.get(url, headers=headers, params=params)
            params = None

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 1))

                with open(log_path, "a", encoding="utf-8") as log:
                    log.write(f"\n[DEBUG] {datetime.now()} Rate limited. Retrying after {retry_after} seconds...\n")
                time.sleep(retry_after)
                resp = requests.get(url, headers=headers)

            if resp.status_code != 200:

                with open(log_path, "a", encoding="utf-8") as log:
                    log.write(f"\n[DEBUG] {datetime.now()} Error fetching {artist}: HTTP {resp.status_code}\nResponse text: {resp.text}\n")
                break

            try:
                data = resp.json()
            except requests.exceptions.JSONDecodeError:

                with open(log_path, "a", encoding="utf-8") as log:
                    log.write(f"\n[DEBUG] {datetime.now()} Could not decode JSON for artist: {artist} \n")
                break

            album_list = data.get("items", [])
            time.sleep(0.5)

            last_rundate = datetime.strptime(runtime_csv["refresh_date"].max(), "%Y-%m-%d")
            if album_list:
                for album in album_list:
                    release_date = album.get('release_date')
                    if release_date:
                        try:
                            release = datetime.strptime(release_date, "%Y-%m-%d")
                            if release >= last_rundate and album['id'] not in spotify_album_id_list and album['id'] not in id_validation_list:
                                id_validation_list.append(album['id'])
                                list_for_discord.append(
                                    f"🎵 **{', '.join([a['name'] for a in album['artists']])}** - {album['name']} - released on: {release_date} ({album['external_urls']['spotify']})"
                                )
                                list_for_album_trail.append((
                                    artist,
                                    album["name"],
                                    ', '.join([a['name'] for a in album['artists']]),
                                    ', '.join([i['id'] for i in album['artists']]),
                                    album["album_type"],
                                    album["type"],
                                    album.get("album_group",""),
                                    album["total_tracks"],
                                    ', '.join(album.get("available_markets","")),
                                    album["id"],
                                    album["release_date"],
                                    album["release_date_precision"],
                                    False,
                                    album["images"][0]["url"] if len(album.get("images", [])) > 0 else "",
                                    album["images"][1]["url"] if len(album.get("images", [])) > 1 else "",
                                    album["images"][2]["url"] if len(album.get("images", [])) > 2 else "",
                                    album["external_urls"]["spotify"],
                                    album["href"],
                                    album["uri"],
                                    datetime.now()
                                ))
                                # create translation table for multi-artist albums/songs
                                for tl_artist in album["artists"]:
                                    list_for_translation_table.append((
                                        album["id"],
                                        tl_artist["id"],
                                        datetime.now()
                                        ))
                        except ValueError:
                            pass

            # Check if there’s a next page
            url = data.get("next")
            throttle_requests()

            with open(log_path, "a", encoding="utf-8") as log:
                log.write(f"\n[DEBUG] {datetime.now()} Processing {artist}")


    return list_for_discord,list_for_album_trail,list_for_translation_table

if datetime.strptime(runtime_csv["refresh_date"].max(), "%Y-%m-%d").date() < datetime.now().date():
    token = get_spotify_token()
    discord_msg,trail_list,translation_table_list = get_albums_for_artists(artists,token)

    # insert values into album trail table
    cursor.executemany("""
    insert into music_db.album_trail (tracked_artist,album_name,all_artists,artist_ids,album_type,`type`,album_group,total_tracks,available_markets,album_id,release_date,release_date_precision,track_retrieval_status,big_image,medium_image,small_image,spotify_url,href,uri,`timestamp`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, trail_list)

    # insert values into 
    cursor.executemany("""
    insert into music_db.artist_album_translation_table (album_id,artist_id,`timestamp`)
        VALUES (%s, %s, %s)
    """, translation_table_list)

    connection.commit()
    cursor.close()
    connection.close()
    if DISCORD_CHANNEL_ID and DISCORD_TOKEN:
        intents = discord.Intents.default()
        client = discord.Client(intents=intents)
        
        @client.event
        async def on_ready():
            
            channel = client.get_channel(DISCORD_CHANNEL_ID)

            for album_info in discord_msg:
                await channel.send(album_info)

            await client.close()

        client.run(DISCORD_TOKEN)

    # update the run to be the current date if there was a successful run
    subprocess.run(["python", str(Path(__file__).resolve().parent / "refresh_script_releases.py")])
    
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n[DEBUG] {datetime.now()} Script has successfully finished")
else:
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n[DEBUG] {datetime.now()} last run was on the same day.")
        log.write(f"\n[DEBUG] {datetime.now()} Exiting script!")
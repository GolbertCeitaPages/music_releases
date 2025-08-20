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

connection = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_DATABASE"),
)

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

cursor = connection.cursor()

def get_spotify_token():
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    )
    return resp.json()["access_token"]

def get_spotify_tracks_from_album(album_id, token):

    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"[ERROR] Failed to fetch artist {album_id}: {resp.status_code}")
        return None
    
    return resp.json()

def get_spotify_tracks(track_ids, token):

    headers = {"Authorization": f"Bearer {token}"}

    if isinstance(track_ids, str):
        track_ids = [track_ids]
    
    ids_param = ",".join(track_ids)
    url = f"https://api.spotify.com/v1/tracks?ids={ids_param}"

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"[ERROR] Failed to fetch track(s) {ids_param}: {resp.status_code}")
        return None
    
    return resp.json()

def throttle_requests(min_delay=0.1, max_delay=0.2):
    # Wait between API requests to stay under 10/sec with jitter.
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)

cursor.execute("select album_id from music_db.album_trail where track_retrieval_status = false")

list_of_album_ids = cursor.fetchall()

spot_acc_token = get_spotify_token()

list_for_tracks_table = []
list_for_artist_track_translation = []

for album_id_tuple in list_of_album_ids:
    album_id = album_id_tuple[0]
    tracks_in_album_response = get_spotify_tracks_from_album(album_id, spot_acc_token)

    if not tracks_in_album_response or "items" not in tracks_in_album_response or not tracks_in_album_response["items"]:
        # log warning
        continue

    list_of_track_ids = [track['id'] for track in tracks_in_album_response["items"]]
    track_response = get_spotify_tracks(list_of_track_ids, spot_acc_token)

    if not track_response or "tracks" not in track_response or not track_response["tracks"]:
        # log warning
        continue

    list_for_tracks_table = []
    list_for_artist_track_translation = []

    for track in track_response['tracks']:
        minutes, seconds = divmod(int(track['duration_ms'] / 1000), 60)

        list_for_tracks_table.append((
            track['name'],
            ', '.join([a['name'] for a in track['artists']]),
            ', '.join([i['id'] for i in track['artists']]),
            album_id,  # album id
            track['disc_number'],
            track['track_number'],
            track['type'],
            track['popularity'],
            track['duration_ms'],
            round(track['duration_ms'] / 1000, 2),
            f"{minutes}:{seconds:02d}",
            track['explicit'],
            track['is_local'],
            ', '.join(track['available_markets']),
            track['id'],
            track['external_urls']['spotify'],
            track['href'],
            track['uri'],
            track['preview_url'],
            datetime.now()
        ))
        for tl_artist in track["artists"]:
            list_for_artist_track_translation.append((
                track["id"],
                tl_artist["id"],
                datetime.now()
            ))

    # Insert per album
    cursor.executemany("""
        insert into music_db.track_data (track_name, artists, artist_ids, album_id, disc_number,
        track_number, `type`, popularity, duration_ms, duration_s, duration_m_s, explicit, is_local,
        available_markets, track_id, spotify_url, href, uri, preview_url, `timestamp`)
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, list_for_tracks_table)

    cursor.executemany("""
        insert into music_db.artist_track_translation_table (track_id, artist_id, `timestamp`)
        values (%s, %s, %s)
    """, list_for_artist_track_translation)

    # update album status if inserts succeeded
    cursor.execute("""
        update music_db.album_trail
        SET track_retrieval_status = TRUE
        WHERE album_id = %s
    """, (album_id,))

    connection.commit()

    throttle_requests()


album_ids_to_update = [ids[0] for ids in list_of_album_ids]

if album_ids_to_update:  # only run if not empty
    update_query = """
        update music_db.album_trail
        set track_retrieval_status = true
        where album_id in ({})
    """.format(", ".join(["%s"] * len(album_ids_to_update)))

    cursor.execute(update_query, album_ids_to_update)
    connection.commit()

cursor.close()
connection.close()
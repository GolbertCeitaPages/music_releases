######################################################################################################################################################################
# Purpose: Get the playlists directly from deezer and spotify using the API. Make sure to unhide playlists on deezer
######################################################################################################################################################################

from pathlib import Path
import pandas as pd
import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(Path(__file__).resolve().parent / "music_bot.env")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")

# All ids 
id_file = pd.read_excel(Path(__file__).resolve().parent / "playlist_ids" / "playlist_ids.xlsx")
DEEZER_ALL = id_file["playlist_id"][id_file["platform"].str.lower().str.strip() == "deezer"]
SPOTIFY_ALL = id_file["playlist_id"][id_file["platform"].str.lower().str.strip() == "spotify"]

jsons_folder = Path(__file__).resolve().parent / "api_jsons"
jsons_folder.mkdir(parents=True, exist_ok=True)

# add txt file for debugging/logging
log_path = Path(__file__).resolve().parent / "debug_log_deezer_spotify_playlist.txt"

def get_deezer_playlist(deezer_playlist_id):
    # Fetch playlist metadata
    url = f"https://api.deezer.com/playlist/{deezer_playlist_id}"
    deezer_response = requests.get(url)
    if deezer_response.status_code != 200:
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(f"\n[DEBUG] {datetime.now()} Failed to fetch data from Deezer: {deezer_response.status_code}\n")
        return None
    
    playlist_data = deezer_response.json()

    # Check if playlist has tracks and a "tracks" key
    if "tracks" not in playlist_data or "data" not in playlist_data["tracks"]:
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(f"\n[DEBUG] {datetime.now()} No tracks found in the Deezer playlist...\n")
        return playlist_data

    tracks = playlist_data["tracks"]["data"]

    # If 'next' exists, keep fetching tracks
    next_url = playlist_data["tracks"].get("next")

    while next_url:
        next_response = requests.get(next_url)
        if next_response.status_code != 200:
            with open(log_path, "a", encoding="utf-8") as log:
                log.write(f"\n[DEBUG] {datetime.now()} Failed to fetch next page: {next_response.status_code}\n")
            break
        
        next_data = next_response.json()
        tracks.extend(next_data.get("data", []))
        next_url = next_data.get("next")

    # Replace the original tracks data with the full list
    playlist_data["tracks"]["data"] = tracks

    with open(jsons_folder / f"{playlist_data['title'].lower()}-deezer-response.json", "w") as deezer_json_extraction:
        json.dump(playlist_data, deezer_json_extraction, indent=2)

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n[DEBUG] {datetime.now()} Retrieved playlist as {playlist_data['title'].lower()}-deezer-response.json\n")

    return playlist_data

def refresh_access_token():
    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": SPOTIFY_REFRESH_TOKEN,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

def get_spotify_token():
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    )
    return resp.json()["access_token"]

def get_spotify_playlist(spotify_playlist_id):
    token = refresh_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get playlist metadata
    url = f"https://api.spotify.com/v1/playlists/{spotify_playlist_id}"
    spotify_response = requests.get(url, headers=headers)
    
    if spotify_response.status_code != 200:
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(f"\n[DEBUG] {datetime.now()} Failed to fetch Spotify playlist data: {spotify_response.status_code}\n")
        return None
    
    spotify_playlist_data = spotify_response.json()
    
    # Paginate through all tracks
    tracks = []
    limit = 100
    offset = 0
    
    while True:
        tracks_url = f"https://api.spotify.com/v1/playlists/{spotify_playlist_id}/tracks?limit={limit}&offset={offset}"
        tracks_response = requests.get(tracks_url, headers=headers)
        
        if tracks_response.status_code != 200:
            with open(log_path, "a", encoding="utf-8") as log:
                log.write(f"\n[DEBUG] {datetime.now()} Failed to fetch tracks at offset {offset}: {tracks_response.status_code}\n")
            break
        
        tracks_data = tracks_response.json()
        tracks.extend(tracks_data["items"])
        
        if tracks_data["next"] is None:
            break
        
        offset += limit
    
    # Replace the partial tracks data with the full list
    spotify_playlist_data["tracks"]["items"] = tracks
    
    with open(jsons_folder / f"{spotify_playlist_data['name'].lower()}-spotify-response.json", "w") as spotify_json_extraction:
            json.dump(spotify_playlist_data, spotify_json_extraction, indent=2)

    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n[DEBUG] {datetime.now()} Retrieved playlist as {spotify_playlist_data['name'].lower()}-spotify-response.json\n")
    
    return spotify_playlist_data

with open(log_path, "w", encoding="utf-8") as log:
    log.write(f"[DEBUG] {datetime.now()} Start fetching Deezer playlists\n")

for deezer_input_ids in DEEZER_ALL:
    get_deezer_playlist(deezer_input_ids)

with open(log_path, "a", encoding="utf-8") as log:
    log.write(f"\n[DEBUG] {datetime.now()} Start fetching Spotify playlists\n")

for spotify_input_ids in SPOTIFY_ALL:
    get_spotify_playlist(spotify_input_ids)
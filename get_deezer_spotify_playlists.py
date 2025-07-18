######################################################################################################################################################################
# Purpose: Get the playlists directly from deezer and spotify using the API. Make sure to unhide playlists on deezer
######################################################################################################################################################################

from pathlib import Path
import pandas as pd
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path("discord_bots") / "music_releases" / "music_bot.env")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")

# Playlists
# Deezer ids 
DEEZER_WORKOUT_ID=os.getenv("DEEZER_WORKOUT_ID")
DEEZER_CHH_ID=os.getenv("DEEZER_CHH_ID")
DEEZER_DRILL_UK_RAP_ID=os.getenv("DEEZER_DRILL_UK_RAP_ID")
DEEZER_KPOP_ID=os.getenv("DEEZER_KPOP_ID")
DEEZER_EDM_ID=os.getenv("DEEZER_EDM_ID")
DEEZER_LOFI_ID=os.getenv("DEEZER_LOFI_ID")

# Spotify
SPOTIFY_WORKOUT_ID=os.getenv("SPOTIFY_WORKOUT_ID")
SPOTIFY_CHH_ID=os.getenv("SPOTIFY_CHH_ID")
SPOTIFY_DRILL_UK_RAP_ID=os.getenv("SPOTIFY_DRILL_UK_RAP_ID")
SPOTIFY_KPOP_ID=os.getenv("SPOTIFY_KPOP_ID")
SPOTIFY_EDM_ID=os.getenv("SPOTIFY_EDM_ID")
SPOTIFY_LOFI_ID=os.getenv("SPOTIFY_LOFI_ID")

def get_deezer_playlist(deezer_playlist_id, override=False):
    if override:
        print("overriden")
        if deezer_response.status_code == 200:
            return None
        else:
            print(f"Failed to fetch data: {deezer_response.status_code}")
            return None
    else:
        # Fetch playlist metadata
        url = f"https://api.deezer.com/playlist/{deezer_playlist_id}"
        deezer_response = requests.get(url)
        if deezer_response.status_code != 200:
            print(f"Failed to fetch data: {deezer_response.status_code}")
            return None
        
        playlist_data = deezer_response.json()

        # Check if playlist has tracks and a "tracks" key
        if "tracks" not in playlist_data or "data" not in playlist_data["tracks"]:
            print("No tracks found in the playlist response.")
            return playlist_data

        tracks = playlist_data["tracks"]["data"]

        # Pagination: if 'next' exists, keep fetching tracks
        next_url = playlist_data["tracks"].get("next")

        while next_url:
            next_response = requests.get(next_url)
            if next_response.status_code != 200:
                print(f"Failed to fetch next page: {next_response.status_code}")
                break
            
            next_data = next_response.json()
            tracks.extend(next_data.get("data", []))
            next_url = next_data.get("next")

        # Replace the original tracks data with the full list
        playlist_data["tracks"]["data"] = tracks

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
        print(f"Failed to fetch playlist data: {spotify_response.status_code}")
        return None
    
    data = spotify_response.json()
    
    # Paginate through all tracks
    tracks = []
    limit = 100
    offset = 0
    
    while True:
        tracks_url = f"https://api.spotify.com/v1/playlists/{spotify_playlist_id}/tracks?limit={limit}&offset={offset}"
        tracks_response = requests.get(tracks_url, headers=headers)
        
        if tracks_response.status_code != 200:
            print(f"Failed to fetch tracks at offset {offset}: {tracks_response.status_code}")
            break
        
        tracks_data = tracks_response.json()
        tracks.extend(tracks_data["items"])
        
        if tracks_data["next"] is None:
            break
        
        offset += limit
    
    # Replace the partial tracks data with the full list
    data["tracks"]["items"] = tracks
    
    return data

def execute_extraction(SPOTIFY_ID,DEEZER_ID,playlist_name=""):
    if SPOTIFY_ID:
        spotify_pl_data = get_spotify_playlist(SPOTIFY_ID)
    if DEEZER_ID:
        deezer_pl_data = get_deezer_playlist(DEEZER_ID,override=False)

    # Write the deezer json object into a local json file
    if DEEZER_ID and "error" in deezer_pl_data:
        print("error message spotted. Playlist is most likely private. not overriding json")
    elif DEEZER_ID and "error" not in deezer_pl_data:
        with open(Path("discord_bots") / "music_releases" / "api_jsons" / f"{playlist_name}-deezer-response.json", "w") as deezer_kpop_json_extraction:
            json.dump(deezer_pl_data, deezer_kpop_json_extraction, indent=2)
        print(f"Deezer Json overridden. Saved as {playlist_name}-deezer-response.json")

    # Write the spotify json object into a local json file
    if SPOTIFY_ID:
        with open(Path("discord_bots") / "music_releases" / "api_jsons" / f"{playlist_name}-spotify-response.json", "w") as spotify_kpop_json_extraction:
            json.dump(spotify_pl_data, spotify_kpop_json_extraction, indent=2)
        print(f"Spotify Json overriden. Saved as {playlist_name}-spotify-response.json")

# Call the main function to get all playlists that are needed
#execute_extraction(SPOTIFY_ID=SPOTIFY_KPOP_ID,DEEZER_ID=DEEZER_KPOP_ID,playlist_name="kpop")
#execute_extraction(SPOTIFY_ID=SPOTIFY_WORKOUT_ID,DEEZER_ID=DEEZER_WORKOUT_ID,playlist_name="workout")
#execute_extraction(DEEZER_ID=DEEZER_CHH_ID,playlist_name="chh",SPOTIFY_ID=SPOTIFY_CHH_ID)
execute_extraction(DEEZER_ID=DEEZER_DRILL_UK_RAP_ID,playlist_name="drill_uk_rap",SPOTIFY_ID=SPOTIFY_DRILL_UK_RAP_ID)

# Not checked yet. Will do so at a later time.
#execute_extraction(SPOTIFY_ID=SPOTIFY_EDM_ID,DEEZER_ID=DEEZER_EDM_ID,playlist_name="edm")
#execute_extraction(SPOTIFY_ID=SPOTIFY_LOFI_ID,DEEZER_ID=DEEZER_LOFI_ID,playlist_name="lofi")


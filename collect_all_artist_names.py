###############################################################################################################################################################################
# Purpose: get the artist and artist id from the spotify jsons
###############################################################################################################################################################################
import pandas as pd 
from pathlib import Path
import json
from datetime import datetime

def make_artist_csv(playlist_json_path,not_interested=[]):
    with open(playlist_json_path, "r") as spotify_json_extraction:
        raw_spotify_data = json.load(spotify_json_extraction)

    # get the playlist name to add as a column
    playlist_name = playlist_json_path.name.split("-spotify-response.json")[0]
    
    spotify_tracks = raw_spotify_data["tracks"]["items"]
    
    artist_list = []

    for spotify_track in spotify_tracks:
        track_info = spotify_track["track"]
        
        for artist in track_info["artists"]:
            name = artist["name"]
            artist_id = artist["id"]
            
            if name not in [a[0] for a in artist_list] and name not in not_interested:
                artist_list.append([name, artist_id,playlist_name,datetime.now()])

    df = pd.DataFrame(artist_list,columns=['artist','artist_id','playlist','timestamp'])
    df = df.sort_values(by="artist", key=lambda col: col.str.lower(), ascending=True)

    return df

def remove_ignored_artists(artist_df):
    ignored_artists_df = pd.read_csv(ignored_artists_folder / "ignored_artists.csv")
    ignored_artists_list = ignored_artists_df["artist_name"].to_list()

    filtered_df = artist_df[~artist_df["artist"].isin(ignored_artists_list)]

    return filtered_df

ignored_artists_folder = Path(__file__).resolve().parent / "ignored_artists"
ignored_artists_folder.mkdir(parents=True, exist_ok=True)

# create a list of dfs to merge
list_of_dfs = []

# Get all of the spotify jsons from the folder 
jsons_folder = Path(__file__).resolve().parent / "api_jsons"
list_of_spotify_jsons = [spotify_f for spotify_f in jsons_folder.iterdir() if spotify_f.is_file() and "spotify-response.json" in spotify_f.name]

# Check if the folder for artist data exists. If not create it
aritst_folder = Path(__file__).resolve().parent / "following"
aritst_folder.mkdir(parents=True, exist_ok=True)

for spotify_jsons in list_of_spotify_jsons:
    df_per_playlist = make_artist_csv(spotify_jsons)
    list_of_dfs.append(df_per_playlist)

full_artist_df = pd.concat(list_of_dfs)
full_artist_df = full_artist_df.drop_duplicates(subset=["artist_id"])

fdf = remove_ignored_artists(full_artist_df)
fdf.to_csv(aritst_folder / "all_artists.csv",index=False)
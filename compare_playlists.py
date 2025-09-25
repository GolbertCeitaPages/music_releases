###############################################################################################################################################################################
# Compare the spotify and deezer playlists to each other to see which ones are missing anything
###############################################################################################################################################################################

from pathlib import Path
import pandas as pd
import json
from dotenv import load_dotenv

load_dotenv(dotenv_path= Path(__file__).resolve().parent / "music_bot.env")

def comparison(deezer_json,spotify_json):
    # Load both JSON files
    with open(deezer_json, "r") as deezer_json_extraction:
        raw_deezer_data = json.load(deezer_json_extraction)

    with open(spotify_json, "r") as spotify_json_extraction:
        raw_spotify_data = json.load(spotify_json_extraction)

    # Deezer music
    deezer_tracks = raw_deezer_data["tracks"]["data"]
    deezer_list = []

    # Loop through tracks and get song and album
    for deezer_track in deezer_tracks:
        deezer_song_title = deezer_track["title"]
        deezer_album_title = deezer_track["album"]["title"]
        deezer_list.append([deezer_song_title,
                            deezer_album_title])

    # spotify music
    spotify_tracks = raw_spotify_data["tracks"]["items"]

    spotify_list = []

    for spotify_track in spotify_tracks:
        track_info = spotify_track["track"]
        spotify_song_title = track_info["name"]
        spotify_album_title = track_info["album"]["name"]
        spotify_list.append([spotify_song_title,
                            spotify_album_title])

    list_in_both = []
    only_on_deezer = []
    only_on_spotify = []

    missing_in_spotify_number = 1
    for deezer_check_track in deezer_list:
        if deezer_check_track in spotify_list:
            list_in_both.append(deezer_check_track)
        else:
            only_on_deezer.append([*deezer_check_track,deezer_json.name.replace('-deezer-response.json', ''),"on Deezer",f"In Deezer playlist but not in Spotify playlist"])
            missing_in_spotify_number+=1

    missing_in_deezer_numer = 1
    for spotify_check_track in spotify_list:
        if spotify_check_track not in deezer_list:
            only_on_spotify.append([*spotify_check_track,spotify_json.name.replace('-spotify-response.json', ''),"on Spotify" ,f"In Spotify playlist but not in Deezer playlist"])
            missing_in_deezer_numer+=1

    on_deezer_df = pd.DataFrame(only_on_deezer,columns=["song","album","playlist","platform","status"])
    on_spotify_df = pd.DataFrame(only_on_spotify,columns=["song","album","playlist","platform","status"])

    on_spotify_df.sort_values(by="album")

    return on_deezer_df,on_spotify_df

# create a list of dfs to merge
list_of_dfs = []

# Get all of the spotify and deezer jsons from the folder 
jsons_folder = Path(__file__).resolve().parent / "api_jsons"

spotify_files = {f.stem.replace("-spotify-response", ""): f for f in jsons_folder.iterdir() if f.is_file() and "spotify-response.json" in f.name}
deezer_files = {f.stem.replace("-deezer-response", ""): f for f in jsons_folder.iterdir() if f.is_file() and "deezer-response.json" in f.name}

pairs = [(deezer_files[k],spotify_files[k]) for k in spotify_files.keys() & deezer_files.keys()]
spotify_exclusive_playlists = [spotify_files[k] for k in spotify_files.keys() - deezer_files.keys()]
deezer_exclusive_playlists  = [deezer_files[k] for k in deezer_files.keys() - spotify_files.keys()]

# get a dataframe for each of the playlists
for p in pairs:
    ood_df, oos_df = comparison(p[0],p[1])
    list_of_dfs.append(ood_df)
    list_of_dfs.append(oos_df)

full_missing_df = pd.concat(list_of_dfs)

fals_positive_file = pd.read_excel(Path(__file__).resolve().parent / "false_positives" / "all_false_positives.xlsx")

filtered_full_df = full_missing_df[~full_missing_df["song"].isin(fals_positive_file["song"])]

filtered_full_df.to_excel(Path(__file__).resolve().parent / "following" / "missing_tracks.xlsx",index=False)
###############################################################################################################################################################################
# Compare the playlists to each other to see which ones are missing anything
###############################################################################################################################################################################

from pathlib import Path
import pandas as pd
import json
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path("discord_bots") / "music_releases" / "music_bot.env")

def comparison(playlist_name,ignore_csv):
    # Load both JSON files
    with open(Path("discord_bots") / "music_releases" / "api_jsons" / f"{playlist_name}-deezer-response.json", "r") as deezer_json_extraction:
        raw_deezer_data = json.load(deezer_json_extraction)

    with open(Path("discord_bots") / "music_releases" / "api_jsons" / f"{playlist_name}-spotify-response.json", "r") as spotify_json_extraction:
        raw_spotify_data = json.load(spotify_json_extraction)

    # Deezer music
    deezer_tracks = raw_deezer_data["tracks"]["data"]
    deezer_list = []
    deezer_counter = 0
    # Loop through tracks and print song, artist, and album
    for deezer_track in deezer_tracks:
        deezer_song_title = deezer_track["title"]
        deezer_artist_name = deezer_track["artist"]["name"]
        deezer_album_title = deezer_track["album"]["title"]
        deezer_list.append([deezer_song_title,
                            #deezer_artist_name, artists not included as it makes the process way harder than it needs to be with encoding and multiple artists
                            deezer_album_title])
        deezer_counter +=1

    # spotify music
    spotify_tracks = raw_spotify_data["tracks"]["items"]

    spotify_list = []
    spotify_counter = 0
    for spotify_track in spotify_tracks:
        # needed to get the artists
        track_info = spotify_track["track"]
        spotify_song_title = track_info["name"]
        spotify_artist_names = ", ".join([artist["name"] for artist in track_info["artists"]])
        spotify_album_title = track_info["album"]["name"]
        spotify_list.append([spotify_song_title,
                            #spotify_artist_names, artists not included as it makes the process way harder than it needs to be with encoding and multiple artists
                            spotify_album_title])
        spotify_counter +=1

    list_in_both = []
    only_on_deezer = []
    only_on_spotify = []
    
    if ignore_csv:
        # read and use the csv with outlier titles between playlists This is made manually in the make_csv file
        df = pd.read_csv(Path("discord_bots") / "music_releases" / "false_positives" / ignore_csv)
        false_positive = df[['song_title', 'album_title']].values.tolist()
    else:
        false_positive = []


    fp_counter = 0
    for deezer_check_track in deezer_list:
        if deezer_check_track in spotify_list:
            list_in_both.append(deezer_check_track)
        elif deezer_check_track in false_positive and deezer_check_track not in spotify_list:
            pass
            fp_counter +=1
        else:
            only_on_deezer.append(deezer_check_track)

    for spotify_check_track in spotify_list:
        if spotify_check_track not in deezer_list and spotify_check_track not in false_positive:
            only_on_spotify.append(spotify_check_track)

    print(f"list in both: {len(list_in_both)+fp_counter}")
    print(f"only on deezer: {len(only_on_deezer)}")
    print(f"only on spotify: {len(only_on_spotify)}")

    # Order the lists on the song title if [0] and album title if [1]
    only_on_deezer.sort(key=lambda x: x[0])
    only_on_spotify.sort(key=lambda x: x[0])

    #print("only on deezer:\n",only_on_deezer)
    #print("only on spotify:\n",only_on_spotify)
    return only_on_deezer,only_on_spotify

#comparison(playlist_name="kpop",ignore_csv="kpop-false-positives.csv")
#comparison(playlist_name="workout",ignore_csv="workout-false-positives.csv")
#on_deezer,on_spotify = comparison(playlist_name="chh",ignore_csv="chh-false-positives.csv")

on_deezer,on_spotify = comparison(playlist_name="drill_uk_rap",ignore_csv="drill-uk-rap-false-positives.csv")



# Not doing EDM until CHH, Drill and Kpop is set up
#comparison(playlist_name="edm",ignore_csv=None)

# this below is to print each row in terminal to check per row and make csv
if on_deezer:
    print("song_title,album_title")
for dz,sp in zip(on_deezer,on_spotify):
    print(f"{dz[0]},{dz[1]}")
    print(f"{sp[0]},{sp[1]}")
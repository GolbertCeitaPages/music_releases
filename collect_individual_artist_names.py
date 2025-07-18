###############################################################################################################################################################################
# Purpose: get the artist and artist id from the spotify json
###############################################################################################################################################################################
import pandas as pd 
from pathlib import Path
import json
 
kpop_blacklist = pd.read_csv(Path("discord_bots") / "music_releases" / "blacklist" / "kpop_blacklist.csv")
initial_kpop_not_interested = kpop_blacklist["artist_name"].to_list()

workout_blacklist = pd.read_csv(Path("discord_bots") / "music_releases" / "blacklist" / "workout_blacklist.csv")
initial_workout_not_interested = workout_blacklist["artist_name"].to_list()

chh_blacklist = pd.read_csv(Path("discord_bots") / "music_releases" / "blacklist" / "chh_blacklist.csv")
initial_chh_not_interested = chh_blacklist["artist_name"].to_list()

drill_uk_rap_blacklist = pd.read_csv(Path("discord_bots") / "music_releases" / "blacklist" / "drill_uk_rap_blacklist.csv")
initial_drill_uk_rap_blacklist = drill_uk_rap_blacklist["artist_name"].to_list()

def make_artist_csv(playlist_name,not_interested=[]):
    with open(Path("discord_bots") / "music_releases" / "api_jsons" / f"{playlist_name}-spotify-response.json", "r") as spotify_json_extraction:
        raw_spotify_data = json.load(spotify_json_extraction)

    spotify_tracks = raw_spotify_data["tracks"]["items"]

    artist_list = []

    for spotify_track in spotify_tracks:
        track_info = spotify_track["track"]
        
        for artist in track_info["artists"]:
            name = artist["name"]
            artist_id = artist["id"]
            
            if name not in [a[0] for a in artist_list] and name not in not_interested:
                artist_list.append([name, artist_id,True])
            #elif name not in [a[0] for a in artist_list]:
            #    artist_list.append([name, artist_id,False])

    df = pd.DataFrame(artist_list,columns=['artist','id','following'])
    #print(not_interested)
    #print(df['artist'].to_list())
    df.to_csv(Path("discord_bots") / "music_releases"  / "following" / f"{playlist_name}_artist_data.csv",index=False)
    return df['artist'].to_list()

#make_artist_csv(playlist_name="kpop",not_interested=initial_kpop_not_interested)
#make_artist_csv(playlist_name="workout",not_interested=initial_workout_not_interested)

#make_artist_csv(playlist_name="chh",not_interested=initial_chh_not_interested)

make_list = make_artist_csv(playlist_name="drill_uk_rap",not_interested=initial_drill_uk_rap_blacklist)

#print("artist_name")
#for items in make_list:
#    print(items)
###############################################################################################################################################################################
# Purpose: get all artist names and id's from the files so that one can be tracked
###############################################################################################################################################################################
import pandas as pd 
from pathlib import Path

#for things in list_of_playlists:
chh = pd.read_csv(Path("discord_bots") / "music_releases"  / "following" / "chh_artist_data.csv")
drill_uk_rap = pd.read_csv(Path("discord_bots") / "music_releases"  / "following" / "drill_uk_rap_artist_data.csv")
workout = pd.read_csv(Path("discord_bots") / "music_releases"  / "following" / "workout_artist_data.csv")
kpop = pd.read_csv(Path("discord_bots") / "music_releases"  / "following" / "kpop_artist_data.csv")

list_of_all_artists = chh["artist"].to_list() + drill_uk_rap["artist"].to_list() + workout["artist"].to_list() + kpop["artist"].to_list()
list_of_all_ids = chh["id"].to_list() + drill_uk_rap["id"].to_list() + workout["id"].to_list() + kpop["id"].to_list()
list_of_all_followdata = chh["following"].to_list() + drill_uk_rap["following"].to_list() + workout["following"].to_list() + kpop["following"].to_list()

combined_list = []
for artist,id,follow in zip(list_of_all_artists,list_of_all_ids,list_of_all_followdata):
    if artist not in combined_list:
        combined_list.append((artist,id,follow))

df = pd.DataFrame(combined_list,columns=["artist","id","following"])

df = df.drop_duplicates(subset=["artist", "id"])

df.to_csv(Path("discord_bots") / "music_releases"  / "following" / "all_artist_data.csv",index=False)
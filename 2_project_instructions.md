## Instructions
1. Remove all "template_" prefixes from the files
2. Populate those files with the required values. You can leave the discord ones empty or remove them completely if you won't use a discord bot.
3. Make sure that the all_artists excel file is filled with artist IDs
4. Run the SQL scripts in MySQL workbench to make sure that the tables can get created ending with sql_create_track_fact.sql
5. Optionally add the get_new_releases file to task scheduler to automate.

## Spotifiy artist tracker
This repo contains various different scripts. If you want to use this repo please remove "template_" from the files

    ## collect_all_artist_names
    Collects the artist names of all artists from the spotify json files in the api_jsons folder 

    ## compare playlists
    Compares the jsons from spotify and deezer to check if any tracks sre missing. Some tracks might not get flagged properly due to inconsistancy in name between the two platforms
    This is solved by putting the inconsistant album names with song names from both platforms in the false_positives folder
    It's very important that the playlists have the same name on both platforms, if not you should change them, or you alter the name of the json file after using get_deezer_spotify_playlists
    
    ## get_artist_data
    Uses the all_artist excel file to get the popularity and genres of the artists in the file. This is done using the spotify API. 

    This is not automated but could be in the future to get weekly changes in popularity

    ## get_deezer_spotify_playlists
    Uses playlist ids provided in the music_bot.env file and get the json files of the playlists on spotify and deezer

    ## get_new_releases
    Main file of the project. For each artist in the all_artist excel checks the most recent album. 
    If the there's a new album adds it to a database and sends a message in the specified channel on the instant messaging and VoIP social platform Discord based on the given channel_id.
    
    This script can be put into windows task scheduler to automate it. To do so create a task and add a trigger, I recommend on startup for pcs. 
    Lastly add the location of your python.exe as program/script in actions and the location of the get_new_releases script to arguements

    ## get_track_data 
    Is an extention of get_new_releases, as it collects all songs from an album when triggered. 
    
    It curently is not automated but can be by adding a new file in the time_tracker  

    ## refresh_script_releases
    Is a small script that controls how the dates are handled. 
    On a full refresh it removes all previous dates and only adds the current rundate/today.
    On incremental load it adds the current rundate as an extra row to rhe existing dates 

## sql
All sql tables should be executed prior to using the python scripts
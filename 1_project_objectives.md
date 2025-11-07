## Spotifiy artist tracker
Welcome to my spotify repository. The objective of this repo is to create a workflow that allows me and possibly other users to get a daily update on music releases based on a specified list of artists.
This list of artists is an excel file. 
The primary file that will do this is the get_new_releases file.

Prerequisites to using this file are the following:
MySQL 8.0
Python 3.9.x

Python libraries:
discord
requests
os
time
mysql.connector
pandas
pathlib
datetime
dotenv
random
subprocess

Optionally you may create a discord bot, you will need to put the discord channel ID and bot ID into the .env file 
This allows you to send notifications to a channel making it easier to track when an artist has released a new song.
Having the discord bot is not necessary as the releases get saved in the MySQL table as well.

Other python scripts will need the json library

## sql
All sql tables should be executed prior to using the python scripts
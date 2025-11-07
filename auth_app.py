############################################################################################################################################################################################################################################################################
# I don't remember what this is for, I think it's for authentication for spotify. Makes it so that you don't need a new spotify token each time you run get_new_releases or any other files that hit an api. THIS WAS VIBE CODED
############################################################################################################################################################################################################################################################################

from flask import Flask, request, redirect
import requests
import os
import urllib.parse
from dotenv import load_dotenv
from pathlib import Path

app = Flask(__name__)

load_dotenv(dotenv_path=Path(__file__).resolve().parent / "music_bot.env")

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPE = "playlist-read-private"

def get_token(code):
    token_url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    response = requests.post(token_url, data=data)
    return response.json()

@app.route("/")
def index():
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
    }
    url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)
    return redirect(url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_info = get_token(code)
    access_token = token_info.get("access_token")
    refresh_token = token_info.get("refresh_token")
    return f"""
    <h1>Spotify Authorization Complete</h1>
    <p><b>Access Token:</b> {access_token}</p>
    <p><b>Refresh Token:</b> {refresh_token}</p>
    <p>Use these tokens in your scripts to access private playlists.</p>
    """

if __name__ == "__main__":
    app.run(port=8888)

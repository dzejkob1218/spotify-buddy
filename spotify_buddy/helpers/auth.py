# handles API tokens, authorisation, environment variables
import os

def check_spotify_credentials():
    spotify_username = os.getenv('SPOTIFY_USERNAME')

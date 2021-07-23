# handles API tokens, authorisation, environment variables
import os

def get_spotify_credentials():
    spotify_username = os.getenv('SPOTIFY_USERNAME')

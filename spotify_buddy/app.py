# builtin modules
import os

# local modules
from helpers import auth

# imported modules
import spotipy

credentials = auth.get_spotify_credentials()
USERNAME = os.getenv('SPOTIFY_USERNAME')


print(USERNAME)

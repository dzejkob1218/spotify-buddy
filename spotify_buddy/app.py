# builtin modules
import os

# local modules
from helpers import auth

# imported modules
import spotipy

credentials = auth.checkSpotifyCredentials()
USERNAME = os.getenv('SPOTIFY_USERNAME')


print(USERNAME)

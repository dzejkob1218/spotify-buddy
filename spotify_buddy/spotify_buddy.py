# builtin modules
from classes.spotify_session import SpotifySession
from classes.collection import Collection
from helpers.parser import print_songs
# packages
from dotenv import load_dotenv
from classes.filters import first_letter
from flask import Flask

load_dotenv()
app = Flask(__name__)

@app.route('/')
def run_app():
    sesh = SpotifySession()
    playlists = sesh.fetch_user_playlists()
    return playlists

"""
sesh = SpotifySession()

new_collection = Collection('new_collection')

#playlist = sesh.fetch_playlist('0idBt8K93C3UMOwgNLpdHB')  # *
playlist = sesh.fetch_playlist('6RA3mmWJG6wDrzZEcZIwnK') # P

new_collection.subcolls.append(playlist)

filters = [first_letter.Filter('c')]

result = new_collection.apply_filters(filters)

print_songs(result.tracks)
"""
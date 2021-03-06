from spotipy import Spotify
# from .collections.playlist import Playlist
import os
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from spotipy.cache_handler import CacheFileHandler
from helpers.parser import uri_to_url, filter_false_tracks
import time
from dotenv import load_dotenv

"""
Responsible for connecting and exchanging data with spotify


"""

load_dotenv()


# The authorization scope for Spotify API needed to run this app
SCOPE = 'user-top-read user-read-currently-playing user-modify-playback-state playlist-read-private playlist-read-collaborative playlist-modify-private'

class SpotifySession:

    # AUTHORIZATION

    def __init__(self, cache_path):
        self.authorized = False
        self.cache_handler = CacheFileHandler(cache_path=cache_path)
        # TODO: this auth manager is not used yet, it is waiting to react when user wants to authenticate, it should be initialized at a later time though
        self.auth_manager = SpotifyOAuth(scope=SCOPE, cache_handler=self.cache_handler, show_dialog=True)
        # This initializes an unauthorized connection - only endpoints not accessing user info will work.
        self.connection: Spotify = Spotify(auth_manager=SpotifyClientCredentials())

    def remove_cache(self):
        os.remove(self.cache_handler.cache_path)

    def authorize(self, code):
        self.auth_manager.get_access_token(code)
        self.connection = Spotify(auth_manager=self.auth_manager)
        # TODO: get a better way of checking if the authorization was successful
        self.authorized = True

    # AUTHORIZED SCOPE
    # TODO: Add some authorize checks and exceptions for these
    # Get current user's playlists

    def get_unique_name(self, name):
        all_names = [p['name'] for p in self.fetch_user_playlists()]
        if name in all_names:
            i = 2
            while name + f" ({i})" in all_names:
                i += 1
            name += f" ({i})"
        return name

    def create_playlist(self, name, tracks):
        user_id = self.fetch_user()['id']
        name = self.get_unique_name(name)
        new_playlist = self.connection.user_playlist_create(user_id, name=name)
        self.connection.playlist_add_items(new_playlist['id'], tracks)

    def fetch_user_playlists(self):
        if self.authorized:
            # TODO: Make this load all playlists instead of first 50
            result = self.connection.current_user_playlists(limit=50)
            if 'items' in result:
                return result['items']

    def fetch_user(self):
        if self.authorized:
            return self.connection.current_user()

    def fetch_currently_playing(self):
        if self.authorized:
            return self.connection.currently_playing()

    def play(self, uris, queue=False):
        if self.authorized:
            if queue:
                for uri in uris:
                    self.connection.add_to_queue(uri)
            else:
                self.connection.start_playback(uris=uris)

    # GENERAL SCOPE
    # Takes a list of track uris and returns a list of audio features
    # TODO: Test that this works on a static playlist
    def fetch_track_features(self, uris):
        result = []
        total_tracks = len(uris)
        # Run a loop requesting a 100 tracks at a time
        for i in range(-(-total_tracks // 100)):
            chunk = uris[(i * 100):(i * 100) + 100]
            features = self.connection.audio_features(chunk)
            result += features
        # It's important that the input and output lists are the same length since they may be later combined entry for entry
        if not len(result) == total_tracks:
            raise Exception('Failed to fetch track features for all tracks')
        return result

    # TODO: Test that this works on a static playlist
    # Takes a playlist ID and returns a list of all tracks within it
    def fetch_playlist_tracks(self, collection_uri, total_tracks):
        playlist_tracks = []
        # Run a loop requesting a 100 tracks at a time
        for i in range(-(-total_tracks // 100)):
            response = self.connection.playlist_items(collection_uri, offset=(i * 100), limit=100)
            playlist_tracks += filter_false_tracks(response['items'])  # remove local tracks and podcasts from the result

        return playlist_tracks

    def search(self, query, search_type):
        results = self.connection.search(q=query, type=search_type, limit=50)
        return results[search_type + 's']

    def fetch_item(self, uri):
        url = uri_to_url(uri)
        return self.connection._get(url)


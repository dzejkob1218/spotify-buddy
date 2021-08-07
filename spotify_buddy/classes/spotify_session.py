import spotipy
from .collections.playlist import Playlist
import os
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheFileHandler

"""
Responsible for connecting and exchanging data with spotify


"""
# The authorization scope for Spotify API needed to run this app
SCOPE = 'user-top-read user-modify-playback-state playlist-modify-private'


class SpotifySession:
    def __init__(self, cache_path):
        self.cache_handler = CacheFileHandler(cache_path=cache_path)
        self.auth_manager = SpotifyOAuth(scope=SCOPE, cache_handler=self.cache_handler, show_dialog=True)
        self.connection: spotipy.Spotify = None

    def connect(self, code):
        self.auth_manager.get_access_token(code)
        self.connection = spotipy.Spotify(auth_manager=self.auth_manager)

    # Get current user's playlists
    def fetch_user_playlists(self):
        return self.connection.current_user_playlists()

    # Takes a playlist ID and returns a Playlist object with all tracks
    def fetch_playlist(self, sp_id):
        playlist_json = self.connection.playlist(sp_id)
        total_to_get = playlist_json['tracks']['total']
        playlist_tracks = []
        for i in range(-(-total_to_get // 100)):
            offset = i * 100
            response = self.connection.playlist_items(sp_id, offset=offset, limit=100)
            for it in response['items']:
                if not it['is_local']:
                    playlist_tracks.append(it['track'])
        return Playlist.make_from_json(playlist_json, playlist_tracks)

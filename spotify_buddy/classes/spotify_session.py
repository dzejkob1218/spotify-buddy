import spotipy
from .collections.playlist import Playlist
import os
from spotipy.oauth2 import SpotifyOAuth

"""
Responsible for connecting and exchanging data with spotify


"""
# The authorization scope for Spotify API needed to run this app
SCOPE = 'user-top-read user-modify-playback-state playlist-modify-private'


class SpotifySession:
    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE))

    # Takes a playlist ID and returns a Playlist object with all tracks
    def fetch_playlist(self, sp_id):
        playlist_json = self.sp.playlist(sp_id)
        total_to_get = playlist_json['tracks']['total']
        playlist_tracks = []
        for i in range(-(-total_to_get // 100)):
            offset = i * 100
            response = self.sp.playlist_items(sp_id, offset=offset, limit=100)
            for it in response['items']:
                if not it['is_local']:
                    playlist_tracks.append(it['track'])
        return Playlist.make_from_json(playlist_json, playlist_tracks)

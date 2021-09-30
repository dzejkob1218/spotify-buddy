from helpers.parser import get_img_urls, parse_artists, track_key
from .collection import Collection


class Track(Collection):

    def __init__(self, uri, sp, subcolls=None, details=None, spotify_object=None, audio_features=None):
        self.audio_features = audio_features
        super(Track, self).__init__(uri, sp, subcolls, spotify_object)
        self.type = 'track'

    def load_details(self):
        # Load details from Spotify.track
        # TODO: is the call to helpers here neccessery?
        image_urls = get_img_urls(self.spotify_object, 'track')
        self.details = {
            'uri': self.uri,
            'name': self.spotify_object['name'],
            'miniature': image_urls[0] if image_urls else None,
            'image': image_urls[-1] if image_urls else None,
            'multiple_artists': len(self.spotify_object['artists']),
            # TODO: perhaps parse artists can be elsewhere?
            'artists': parse_artists(self.spotify_object['artists']),
            'popularity': self.spotify_object['popularity'],
            'explicit': self.spotify_object['explicit'],
            'duration': self.spotify_object['duration_ms'],
            'number': self.spotify_object['track_number'],
            'release': self.spotify_object['album']['release_date'],
            'release_precision': self.spotify_object['album']['release_date_precision'],
            'release_year': int(self.spotify_object['album']['release_date'][:4]),
        }

        # Load parent details from Spotify.track
        # In this case the parent is the album
        self.parent = {
            'uri': self.spotify_object['album']['uri'],
            'name': self.spotify_object['album']['name'],
            'miniature': self.details['miniature'],
            'artists': self.details['artists'],
        }

        # Load details from track features
        if not self.audio_features:
            self.audio_features = self.sp.fetch_track_features([self.uri])[0]

        if self.audio_features:
            self.details.update({
                'mood': self.audio_features['valence'] * 100,
                'energy': self.audio_features['energy'] * 100,
                'dance': self.audio_features['danceability'] * 100,
                'speech': self.audio_features['speechiness'] * 100,
                'acoustic': self.audio_features['acousticness'] * 100,
                'instrumental': self.audio_features['instrumentalness'] * 100,
                'live': self.audio_features['liveness'] * 100,
                'tempo': self.audio_features['tempo'],
                'key': self.audio_features['key'],  # this is the root note of the song's key (used for filtering)
                'mode': self.audio_features['mode'],
                # this is the mode itself for sorting songs into major and minor keys (used for filtering)
                # TODO: key_name probably doesn't need to be here
                'key_name': track_key(self.audio_features['key'], self.audio_features['mode']),
                # this is a string representation of the song's key including it's mode (used for display)
                'signature': self.audio_features['time_signature'],
            })

    """
    def get_lyrics(self):
        # Load confidence ratings from audio analysis 
        # Spotify isn't perfect at guessing some features of a song and only commonly used keys and time signatures are recognized, so some attributes comes with a confidence rating
        # Making a request for each song takes too much time and there is no endpoint in spotify API for getting multiple songs analysed
        # Later make this data load only when the song's details show up
        audio_analysis = self.sp.connection.audio_analysis(self.uri)['track']
        self.details.update({
            'tempo_confidence': audio_analysis['tempo_confidence'],
            'key_confidence': audio_analysis['key_confidence'],
            'mode_confidence': audio_analysis['mode_confidence'],
            'signature_confidence': audio_analysis['time_signature_confidence'],
        })
    """

from helpers.parser import get_img_urls, filter_false_tracks
from .track import Track
from .collection import Collection
import time


class Playlist(Collection):

    def __init__(self, uri, sp, subcolls=None, spotify_object=None):
        super(Playlist, self).__init__(uri, sp, subcolls, spotify_object)
        self.type = 'playlist'
        #self.filters = ['number', 'signature', 'release_year', 'duration', 'tempo', 'popularity', 'dance', 'energy', 'speech', 'acoustic', 'instrumental', 'live', 'valence', 'mode', 'explicit']

    def load_details(self):
        print("Loading own details")
        # Load details from Spotify.playlist
        image_urls = get_img_urls(self.spotify_object, 'playlist')
        self.details = {
            'uri': self.uri,
            'name': self.spotify_object['name'],
            'miniature': image_urls[0] if image_urls else None,
            'image': image_urls[-1] if image_urls else None,
            'followers': self.spotify_object['followers']['total'],
            'owner': self.spotify_object['owner']['id'],
            'owner_name': self.spotify_object['owner']['display_name'],
            'public': self.spotify_object['public'],
            'total': self.spotify_object['tracks']['total'],
            'description': self.spotify_object['description']
        }

    def load_children(self):
        total_tracks = self.spotify_object['tracks']['total']
        if total_tracks > 100:
            # If there are more than 100 songs, multiple requests will be needed to get all of them
            all_tracks = self.sp.fetch_playlist_tracks(self.uri, total_tracks)
        else:
            # The first 100 tracks are already in the 'playlist' response, so there is no need for another request if the playlist is smaller than 100 songs
            all_tracks = filter_false_tracks(self.spotify_object['tracks']['items'])

        track_features = self.sp.fetch_track_features([item['uri'] for item in all_tracks])
        # Some requests for track features return None - count only the valid results for use in calculations
        features_count = sum(x is not None for x in track_features)

        # Saves all tracks and their audio features into a list of children objects
        for i in range(len(all_tracks)):
            self.subcolls.append(
                Track(all_tracks[i]['uri'], self.sp, spotify_object=all_tracks[i], audio_features=track_features[i]))

        # Count up attributes of included songs which can be nicely averaged out and presented
        # TODO : Add a functionality for presenting attributes which can't be just averaged (date, key, signature, most popular artist etc.)
        summable_child_attributes = {'signature', 'release_year', 'tempo', 'popularity', 'duration', 'valence', 'dance', 'speech', 'acoustic', 'instrumental', 'live', 'number', 'energy', 'explicit', 'mode'}

        self.average_children_details(summable_child_attributes, features_count)

    def get_track_features(self):
        """ Returns a list of track details that successfully loaded their features and can be filtered and sorted """
        loaded, unloaded = [], []
        for track in self.subcolls:
            loaded.append(track.details) if track.audio_features else unloaded.append(track.details)
        return loaded, unloaded

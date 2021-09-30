from helpers.parser import uniform_title
from fuzzywuzzy import fuzz
from lyricsgenius import Genius
from requests.exceptions import ProxyError
import os


class GeniusSession:
    def __init__(self):
        self.connection = Genius(os.environ.get("GENIUS_SECRET"))

    def get_lyrics(self, track):
        """Search genius.com for lyrics to a song
        Genius doesn't always return the right lyric as the first result, especially with less popular songs.
        Some songs on Spotify have multiple artists listed and it's not always the first one who is credited as
        the author on Genius.
        """

        name = uniform_title(track.details['name'])

        # TODO: If performance is poor for songs with multiple artists, try searching for each one
        artists = track.details['artists'].split(', ')
        print(artists)
        print(f"Searching for lyrics to {name} by {artists[0]}")

        try:
            page = self.connection.search_song(name, artists[0])
        except ProxyError:
            raise

        # Check if any of the listed artists and the track title more or less match the result.
        artist_match = any([(fuzz.ratio(page.artist.lower(), artist.lower()) > 70) for artist in artists])
        title_match = fuzz.partial_ratio(page.title.lower(), name.lower()) > 70

        if title_match and artist_match:
            print(type(page.lyrics))
            return remove_embed(page.lyrics)
        else:
            return 'No lyrics found'


def remove_embed(text):
    """Removes the weird string from the end of genius results"""
    lyric = text.split('EmbedShare URLCopyEmbedCopy')[0]
    while lyric[-1].isnumeric():
        lyric = lyric[:-1]
    return lyric

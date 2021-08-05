from unittest import TestCase
import pytest

# packages
from dotenv import load_dotenv

from spotify_buddy.classes.spotify_session import SpotifySession


class TestSpotifySession(TestCase):

    def test_fetch_playlist(self):
        load_dotenv()
        playlist = SpotifySession().fetch_playlist('6RA3mmWJG6wDrzZEcZIwnK')
        assert len(playlist.tracks) == 275
        assert playlist.name == 'P'
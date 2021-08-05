class Collection:

    def __init__(self, name, tracks=None, subcolls=None):
        self.tracks = tracks if tracks else []
        self.subcolls = subcolls if subcolls else []
        self.name = name

    def apply_filters(self, filters):
        tracks = self.gather_tracks()  # always apply filters to all tracks under subcollections
        for f in filters:
            tracks = filter(f.apply, tracks)
        return Collection(self.name + '_filtered', tracks)

    # returns all tracks from this collection and it's subcollections
    def gather_tracks(self):
        tracks = self.tracks
        for sub in self.subcolls:
            tracks += sub.gather_tracks()
        return tracks
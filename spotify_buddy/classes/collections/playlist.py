from ..collection import Collection

class Playlist(Collection):
    def __init__(self, name, sp_id, tracks=None):
        Collection.__init__(self, name, tracks)
        self.sp_id = sp_id

    @staticmethod
    def make_from_json(json, tracks=None):
        return Playlist(json['name'], json['id'], tracks)

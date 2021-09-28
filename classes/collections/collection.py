from helpers.parser import get_img_urls


class Collection:

    def __init__(self, uri, sp=None, subcolls=None, spotify_object=None):
        self.spotify_object = spotify_object  # The response from spotify describing the item
        self.uri = uri  # TODO: Does this really need to be duplicated?
        self.sp = sp #TODO: Is this needed past init?
        self.subcolls = subcolls if subcolls else []
        self.details = {}
        self.averages = {}
        self.parent = {}
        self.filters = []  # The list of attributes by which items of this class can be filtered

        self.load_spotify_object()
        self.load_details()
        self.children_loaded = False
        #self.load_children()
        # TODO : check if this has any effect on performance
        # self.__delattr__('spotify_object')

    # Call this function to make sure the subcolls are loaded only once
    def request_children(self):
        if not self.children_loaded:
            self.children_loaded = True
            self.load_children()

    # In many cases, while querying spotify about it's children, an object automatically receives details about them
    def load_details(self):
        pass

    def load_children(self):
        pass

    def load_spotify_object(self):
        if not self.spotify_object:
            self.spotify_object = self.sp.fetch_item(self.uri)

    # Returns all tracks from this collection and it's subcollections
    def gather_tracks(self):
        tracks = []
        for sub in self.subcolls:
            if sub.item_type == 'track':
                tracks += sub
            else:
                tracks += sub.gather_tracks()
        return tracks

    # Recursively looks for a collection with specified uri
    def find_uri(self, uri):
        if self.uri == uri:
            return self

        for sub in self.subcolls:
            res = sub.find_uri(uri)
            if res:
                return res
        return None

    # Takes a list of attribute names and returns average, minimum and maximum values for sub-collections
    def average_children_details(self, attributes, child_number):
        # Initialize the dictionary for child attributes where each value is an array of [average, min, max]
        base_dict = {'avg': 0, 'min': None, 'max': None}
        child_attributes = dict.fromkeys(attributes)
        for attr in child_attributes:
            child_attributes[attr] = base_dict.copy()

        # Iterate through each child and add up the values
        for sub in self.subcolls:
            for attr in attributes:
                if attr in sub.details:
                    new_value = sub.details[attr]
                    total = child_attributes[attr]
                    total['avg'] += new_value
                    total['min'] = new_value if total['min'] is None or total['min'] > new_value else total['min']
                    total['max'] = new_value if total['max'] is None or total['max'] < new_value else total['max']


        # Divide the attributes by total tracks
        for attr in child_attributes:
            total = child_attributes[attr]
            total['avg'] /= child_number
            total['min'], total['max'] = round(total['min']), round(total['max'])


        self.averages.update(child_attributes)

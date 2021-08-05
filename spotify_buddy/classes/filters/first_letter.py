class Filter:

    name = "First Letter"
    desc = "Select songs with titles starting from the given letter (case insensitive)"

    def __init__(self, letter):
        self.letter = letter.lower()

    def apply(self, track):
        return track['name'][0].lower() == self.letter

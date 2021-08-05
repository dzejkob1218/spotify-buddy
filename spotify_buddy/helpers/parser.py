def show(l, attr=None):
    for i in l:
        print(i[attr] if attr else i)


def print_songs(songs):
    for s in songs:
        print(s['name'])

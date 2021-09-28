# Temporary function for saving strings to a text file on the server to make up for clunky logging
def out(s, end='\n'):
    f = open("output.txt", "a")
    f.write(s + end)
    f.close()


def show(l, attr=None):
    for i in l:
        print(f"{i} -> {l[i]}")

def keys(l):
    for i in l:
        print(i)


def print_songs(songs):
    for s in songs:
        print(s['name'])

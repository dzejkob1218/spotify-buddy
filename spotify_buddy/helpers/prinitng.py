# Temporary function for saving strings to a text file on the server to make up for clunky logging
def out(s, end='\n'):
    f = open("output.txt", "a")
    f.write(s + end)
    f.close()

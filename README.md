# spotify-buddy
A dynamic Flask web app that connects to Spotify API to let you view metadata about songs, filter your tracks, create new playlists and more.

## A word about the lyrics
Spotify Buddy displays lyrics for each song selected as they appear on genius.com.

However, the [preview site](https://dzejkob1218.pythonanywhere.com/) is currently hosted for free, which means it has limited access to the web.

Unfortunately, genius.com, as well as many other lyrics sites, don't provide access to the lyrics themselves through their APIs, at least not for free, because of copyright problems.

Displaying the link to the page with the lyrics is the best alternative Spotify Buddy can provide right now.

If, somehow, there is a demand, I could shell out a couple $ to move the site somewhere where it can access the web freely.

Meanwhile, if you like the app and want to use it in its full functionality, you can download the source code and run it yourself.

To do that, you would have to acquire API credentials for both Spotify and genius.com and store them as environment variables where the app is running. 
Spotify Buddy will then be able to scrape genius.com and display lyrics on the page.
Just please don't make the site you host yourself available to the public (see license).




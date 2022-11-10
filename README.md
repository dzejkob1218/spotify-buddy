# Spotify Buddy
[**Preview in action!**](https://dzejkob1219.pythonanywhere.com/)

A dynamic Flask web app that connects to Spotify API to let you view metadata about songs, filter your tracks, create new playlists and more.

![screenshot](screenshot.png)

## Bugs and performance
Spotify Buddy is a work in progress.
Because of the great variability of content on Spotify, some playlists may still contain items that hang up the code. If the site looks stuck, try loading a different playlist. Large playlist (with thousands of songs) can take some time to load.

## How to use
In the upper left corner you'll find the **search bar**, use it to search for a playlist.

Alternatively you can **log in** to Spotify and select playlists from your library.

When a playlist loads, on the right you'll see **filters**. The value you see next to each name gives you the average for all tracks in a playlist. Click a filter to apply **sorting**, click again to reverse sort. Hover over a bar to see the minimum and maximum values in the playlist. Drag the values to filter out tracks outside the range. 

Click a track in the playlist view or the search results to view details.

Click on an image to see full-resolution album art.

If you connect to Spotify, you can **play or queue** the selected track, as well as the results of sorting and filtering a playlist, or **save** them to a new playlist in your library.

## A word about the lyrics
Spotify Buddy displays lyrics for each song selected as they appear on genius.com.

However, the [preview site](https://dzejkob1219.pythonanywhere.com/) is currently hosted for free, which means it has limited access to the web.

Unfortunately, genius.com, as well as many other lyrics sites, don't provide access to the lyrics themselves through their APIs, at least not for free, because of copyright problems.

Displaying the link to the page with the lyrics is the best alternative Spotify Buddy can provide right now.

If, somehow, there is a demand, I could shell out a couple $ to move the site somewhere where it can access the web freely.

Meanwhile, if you like the app and want to use it in its full functionality, you can download the source code and run it yourself.

To do that, you'd need to acquire API credentials for both Spotify and genius.com and store them as environment variables where the app is running. 
Spotify Buddy will then be able to scrape genius.com and display lyrics on the page.
Just please don't make the site you host yourself available to the public (see license).




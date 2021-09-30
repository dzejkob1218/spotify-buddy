import os
import json
from flask import Flask, session, request, redirect, render_template, jsonify, url_for
from classes.spotify_session import SpotifySession
from classes.genius_session import GeniusSession
from classes.collections.playlist import Playlist
from classes.collections.track import Track
# from classes.collections.collection import Collection
from flask_session import Session
from helpers.parser import parse_item
from helpers.colors import gradient_from_url, DEFAULT_COLORS
from helpers.printing import show
import uuid
from babel.dates import format_datetime
from datetime import datetime, timedelta
from time import time
from requests.exceptions import ProxyError

# flask and flask_session setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)  # secret key for flask sessions
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

# Make sure there is a folder to store caches
caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)


# Returns the path to cache for each session
def session_cache_path():
    return caches_folder + session.get('uuid')


# TODO: Right now a new user can just bypass getting a session by visiting a url different than index

def check_session():
    # Gives a random ID to a new user without a session
    if not session.get('uuid'):
        print("STARTING SESSION")
        session['uuid'] = str(uuid.uuid4())
        sp = SpotifySession(session_cache_path())
        session['sp'] = sp
        session['genius'] = GeniusSession()
        # session['collection'] = Collection("selected_items")
        session['banned_songs'] = []


# Returns redirect to the last visited page
def go_back():
    if session.get('selected_collection'):
        return redirect('/?collection=' + session.get('selected_collection').uri)
    else:
        return redirect('/')


# default route
@app.route('/')
def index():
    check_session()
    # If a collection is specified (for example when being redirected back) it will be requested when the page loads
    request_collection = request.args.get('collection')
    # f = open("templates/rendered_file.html", "w")
    # f.write(render_template('index.html', data=data))

    return render_template('index.html', user=session.get('user'), collection=request_collection)


@app.route('/_collection')
def view_collection():
    """
    Returns the rendered site with only the information that are quick to load
    """
    sp = session.get('sp')
    requested_uri = request.args.get('uri', type=str)
    refresh = json.loads(request.args.get('refresh'))
    collection = None
    previously_selected = session.get('selected_collection')

    if not refresh and previously_selected and (previously_selected.uri == requested_uri or not requested_uri):
        collection = previously_selected
    elif requested_uri:
        # Load a new collection object (for now only playlists are supported)
        collection = Playlist(requested_uri, sp)
        session['selected_collection'] = collection
    else:
        return render_template('welcome_page.html')

    if collection:
        # Initialize criteria stack
        session['new_playlist_name'] = collection.details['name'] + " (by SpotifyBuddy)"
        session['filters_stack'] = []
        session['sort_criterium'] = None
        session['explicit_order'] = None

        return render_template('dynamic/collection_details.html',
                               collection=collection.details)


@app.route('/refresh')
def refresh_collection():
    """
    Loads currently selected collection again
    """
    selected = session.get('selected_collection')
    if not selected:
        return redirect('/')
    else:
        # Remove the collection from session and make it load again
        selected_uri = selected.uri
        session['selected_collection'] = None
        return redirect(url_for('view_collection', uri=selected_uri))


@app.route('/_details')
def load_collection_details():
    """
    The function that loads the initial tracklist, filters and background gradient
    """
    sp = session.get('sp')
    collection = session.get('selected_collection')

    if not collection.details['total']:
        return "Collection empty - nothing to load", 400

    collection.request_children()
    tracks = collection.get_track_features()

    # Try to make a gradient from collection image and use default colors if something goes wrong
    try:
        gradient_colors = gradient_from_url(collection.details['image'])
    except:
        gradient_colors = DEFAULT_COLORS

    # Sort out attributes which have one value for all songs
    averages, invalid_averages = {}, {}
    for attribute in collection.averages:
        average = collection.averages[attribute]
        if average['max'] == average['min']:
            invalid_averages[attribute] = average
        else:
            averages[attribute] = average

    # Save results to session for easy pagination
    session['latest_included_tracks'] = tracks[0]
    session['latest_rejected_tracks'] = tracks[1]
    tracklist_html = show_page()

    filters_html = render_template('dynamic/filters.html', averages=averages, invalid=invalid_averages)

    return {'gradient_colors': gradient_colors, 'filters_html': filters_html, 'tracklist_html': tracklist_html}


@app.route('/_order')
def order_tracks():
    """
    This route should also be the one that loads the tracks the first time
    TODO: Describe here what exactly happens with filtering and sorting if specified in the request
    """
    sp = session.get('sp')
    request_data = json.loads(request.args.get('sorting_details'))

    session['new_playlist_name'] = funny_playlist_name_generator(session.get('selected_collection').details['name'],
                                                                 request_data)

    # Set the received criterium as either the sorting criterium or a new filter
    if request_data['explicit_sort']:
        session['sort_criterium'] = request_data['sort_criterium']
        session['explicit_order'] = request_data['sort_order']
    else:
        update_filter_stack(request_data['sort_criterium'], request_data['filters'])

    # The 'stack' are names of sorting criteria in order of most recently used
    stack = get_latest_stack()

    # The sorting function used for tracks
    def sorter(t):
        # Name is used when there is no other criterium to sort by, if there is one, name is still the secondary key
        return sorted(t, key=lambda k: (k[stack[0]], k['name']) if stack else k['name'],
                      reverse=session.get('explicit_order') if session.get('sort_criterium') else request_data[
                          'sort_order'])

    # Load, filter and sort tracks from the requested collection
    tracks = session.get('selected_collection').get_track_features()
    tracks_filtered = filter_tracks(tracks[0], request_data['filters'])

    # Save results to session for easy pagination
    session['latest_included_tracks'] = sorter(tracks_filtered[0])
    session['latest_rejected_tracks'] = sorter(tracks_filtered[1] + tracks[1])

    return show_page()


@app.route('/_page')
def show_page():
    page = 0
    page_len = 300

    if request.args.get('page'):
        page = int(request.args.get('page'))

    all_included = session.get('latest_included_tracks')
    all_excluded = session.get('latest_rejected_tracks')

    total_tracks = len(all_included) + len(all_excluded)
    total_pages = -(-total_tracks // page_len)

    # Get the included data that should be displayed on page
    included_page = all_included[(page * page_len): (page * page_len) + page_len]
    excluded_page = []

    remaining_space = page_len - len(included_page)
    # If there is space left on the page, fill it with rejected tracks
    if remaining_space and not remaining_space == page_len and len(all_excluded) > 0:
        excluded_page = all_excluded[0: remaining_space]
    elif remaining_space == page_len:
        page_offset = (len(all_included) // page_len) + 1
        data_offset = len(all_included) % page_len
        exc_page = page - page_offset
        excluded_page = all_excluded[exc_page * page_len + data_offset: (exc_page + 1) * page_len + data_offset]

    return render_template('dynamic/collection_tracks.html',
                           data=included_page,
                           disabled_data=excluded_page,
                           criteria_stack=get_latest_stack(),
                           explicit_sort=True if session.get('sort_criterium') else False,
                           included_number=len(all_included),
                           current_page=page,
                           pages=get_page_bar_numbers(page, total_pages),
                           new_name=session.get('new_playlist_name'),
                           check_failure=check_failure)


def funny_playlist_name_generator(name, changes):
    """
    Generates a playlist name based on applied filters like this:
    playlist_name but ... (by Spotify Buddy)
    """

    #  The strings to add to the name of a  new playlist.
    #  The order is important to preserve the structure of the new sentence.
    texts = {

        'number': ["it's all off the tops of the tracklists", "it's all from way down the tracklist"],
        'live': ["it's the best version because it's the studio version", 'it sounds just like live'],

        'explicit': ['squeaky clean', 'only songs with bad no-no words in them'],

        'tempo': ['slow', ' f a s t '],
        'release_year': ['old', 'fresh'],
        'mood': ['serious', "more up-beat"],

        'signature': ['in wacky time signatures', 'in standard time signature'],
        'dance': ['impossible to dance to', 'only tracks you can dance to'],
        'speech': ['with no talking', 'with a lot said'],
        'mode': ['in a minor mode', 'in a major mode'],

        'duration': ['short', 'only long tracks'],
        'popularity': ["only obsure tracks only I listen to", 'only stuff everybody else listens to'],
        'acoustic': ['only songs you can cover with your acoustic guitar at a houseparty', "it's all electric"],
        'instrumental': ["only the juicy extended instrumental sections", 'no unnecessary solos'],
        'energy': ["only downers", "only uppers"],

    }

    # if changes['explicit_sort']:
    fixes = []

    if changes['filters']:
        # Iterate through texts in order to keep better sentence structure
        for attribute in texts:
            if attribute in changes['filters']:
                conditions = changes['filters'][attribute]
                if 'min' in conditions and 'max' not in conditions:
                    fixes.append(texts[attribute][1])
                if 'max' in conditions and 'min' not in conditions:
                    fixes.append(texts[attribute][0])
                if 'switch' in conditions:
                    if conditions['switch']:
                        fixes.append(texts[attribute][1])
                    else:
                        fixes.append(texts[attribute][0])

        name += ', but'

        if len(fixes) == 1:
            name += ' ' + fixes[0]
        else:
            for fix in fixes[0:-1]:
                if len(name) + len(fix) < 175:  # Spotify limits playlist name to 200 characters
                    name += ' ' + fix + ','
            name = name[:-1]
            name += ' and ' + fixes[-1]

    return name + " (by Spotify Buddy)"


def get_page_bar_numbers(current, total):
    """
    Returns up to five numbers which will be used in the page bar.
    First page is always page 0 and last is always last.
    If current page is 1 and there are more than five, pages should be 0,1,2,3,last
    Similarly, if current page is the penultimate: 0, -3, -2, -1, last
    In any other case: 0, cur-1, cur, cur+1, last
    """
    # If there are five or less simply number them.
    if total <= 5:
        return list(range(total))
    elif current <= 1:
        return list(range(4)) + [total - 1]
    elif current >= total - 2:
        return [0] + list(range(total - 4, total))
    else:
        return [0] + list(range(current - 1, current + 2)) + [total - 1]


# FILTERING
def filter_tracks(tracks, filters):
    rejects = []
    for f in filters:
        for track in tracks:
            if not check_failure(track[f], filters[f]) and track not in rejects:
                rejects.append(track)

    filtered = [t for t in tracks if t not in rejects]
    return filtered, rejects


# TODO: It makes no sense for items to be filtered twice. Maybe pass failure information along with rejected tracks. AT LEAST make check_failure function do work for filter_tracks
# TODO: Once there is information on how to filter a given attribute, there must also be a way to append information on how to display it
def check_failure(value, filter):
    """
    This function is passed to jinja as a value.
    Checks
    """
    if ('min' in filter and value < filter['min'] or
            'max' in filter and value > filter['max'] or
            'switch' in filter and not value == filter['switch']):
        return False
    return True


# The filters stack keeps track of the order in which filter requests came in.
# It keeps up the cool effect of sorting by the latest active filter
def update_filter_stack(new_criterium, active_filters):
    stack = session.get('filters_stack')
    # Remove criteria which are no longer used as filters
    for criterium in stack:
        if criterium not in active_filters:
            stack.remove(criterium)
    # If the new criterium is valid, move it to front
    if new_criterium:
        if new_criterium in stack:
            stack.remove(new_criterium)
        stack.insert(0, new_criterium)


def get_latest_stack():
    # The final stack is the result of pushing the explicit criterium to front of stack
    stack = list(session.get('filters_stack'))  # Make a copy of filters stack
    explicit_criterium = session.get('sort_criterium')
    if explicit_criterium:
        if explicit_criterium in stack:
            stack.remove(explicit_criterium)
        stack.insert(0, explicit_criterium)
    return stack


# AUTHORIZATION
@app.route('/login')
def login():
    sp = session.get('sp')
    # Redirect the user to authorization site
    if not sp.auth_manager.validate_token(sp.cache_handler.get_cached_token()):
        auth_url = sp.auth_manager.get_authorize_url()
        return redirect(auth_url)
    else:
        # Redirect back to home page if user already logged in
        return go_back()


@app.route('/callback')
def callback():
    if request.args.get("code"):
        sp = session.get('sp')
        sp.authorize(request.args.get("code"))
        session['user'] = sp.fetch_user()
        return go_back()


@app.route('/logout')
def logout():
    last_page = go_back()
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    return last_page


# AJAX


@app.route('/_search')
def search():
    sp = session.get('sp')
    if not sp:
        check_session()
        exit()
    query = request.args.get('q', type=str)
    search_type = request.args.get('type', type=str)
    # Search spotify
    if search_type in ['playlist', 'track'] and query:
        search_results = sp.search(query, search_type)['items']
        parsed_results = [parse_item(item, search_type) for item in search_results]
    # Get user playlists and match names for the query
    if search_type == 'library' and sp.authorized:
        results = sp.fetch_user_playlists()
        parsed_results = [parse_item(item, 'playlist') for item in results]
        if query:
            parsed_results = [p for p in parsed_results if query.lower() in p['name'].lower()]
        search_type = 'playlist'
    return render_template('dynamic/search_results_list.html', data=parsed_results, item_type=search_type)


@app.route('/_track')
def track_details():
    sp = session.get('sp')
    uri = request.args.get('uri', type=str)
    track = None
    # check if the track is already loaded in the selected collection
    if session.get('selected_collection'):
        track = session.get('selected_collection').find_uri(uri)
    # if not, load a new one
    if not track:
        track = Track(uri, sp)
    session['selected_track'] = track
    return render_template('dynamic/track.html',
                           data=track.details,
                           parent=track.parent,
                           auth=sp.authorized,
                           has_features=True if track.audio_features else False)


@app.route('/_lyrics')
def track_lyrics():
    track = session.get('selected_track')
    # TODO: Show a link to lyrics on genius.com along with the message
    # On pythonanywhere.com the app will be prevented from accessing the web and a ProxyError will be raised
    try:
        lyrics = session.get('genius').get_lyrics(track)
    except ProxyError:
        return render_template('components/display/lyrics_blocked.html', link=None)

    return lyrics


@app.route('/_current')
def currently_playing():
    sp = session.get('sp')
    current = sp.fetch_currently_playing()
    if current:  # and current['context'] and current['context']['type'] == 'playlist':
        # collection = sp.fetch_item(current['context']['uri'])
        # parsed_collection = parse_item(collection, 'playlist')
        return render_template('dynamic/currently_playing.html',
                               track=parse_item(current['item'], 'track'))  # ,collection=collection)
    else:
        return 'Nothing playing'


@app.route('/_create', methods=['POST'])
def create_playlist():
    print("Creating")
    sp = session.get('sp')
    name = request.form.get('name')
    number = json.loads(request.form.get('number'))
    random = json.loads(request.form.get('random'))
    latest_tracks = [track['uri'] for track in session.get('latest_included_tracks')[:number]]
    sp.create_playlist(name, latest_tracks)


@app.route('/_play-track', methods=['POST'])
def play_track():
    sp = session.get('sp')
    queue = json.loads(request.form.get('queue'))
    uri = session.get('selected_track').uri
    sp.play([uri], queue)


@app.route('/_play', methods=['POST'])
def play():
    sp = session.get('sp')
    queue, number, random = (json.loads(request.form.get(k)) for k in request.form.keys())
    latest_tracks = session.get('latest_included_tracks')[:number]
    uris = [track['uri'] for track in latest_tracks]

    sp.play(uris, queue)


@app.template_filter()
def format_date(parent):
    if parent['release_precision'] == 'year':
        return parent['release']
    if parent['release_precision'] == 'day':
        date = datetime.strptime(parent['release'], "%Y-%m-%d")
    return format_datetime(date, format='d MMMM yyyy')


@app.template_filter()
def format_duration(ms):
    seconds = ms / 1000
    minutes = seconds // 60
    remainder = seconds - minutes * 60
    return '{:02}:{:02}'.format(int(minutes), int(round(remainder)))


@app.template_filter()
def fraction_to_decimal(val):
    return int(round(val * 100))


@app.template_filter()
def limit_length(text, max_len):
    if len(text) < max_len:
        return text
    else:
        return text[:max_len].strip() + '...'

@app.template_filter()
def format_attribute_name(name):
    return name.replace('_', ' ').title()

@app.template_filter()
def format_attribute(value, attribute, average=False):
    """
    Returns a human-readable string according to type of the attribute.
    If average is True, a variant for displaying the average of the attribute will be returned
    """
    if attribute in ['number', 'release_year']:
        return str(round(value))

    if attribute in ['popularity', 'dance', 'energy', 'speech', 'acoustic', 'instrumental', 'live', 'live', 'mood']:
        return str(round(value)) + ('%' if average else '')

    if attribute == 'tempo':
        return str(round(value)) + (' BPM' if average else '')

    if attribute == 'duration':
        return format_duration(value)

    if attribute in ['explicit']:
        if average:
            return str(round(value * 100)) + '% Explicit'
        else:
            return 'Yes' if value else 'No'

    if attribute == 'mode':
        if average:
            return str(round(value * 100)) + '% Major'
        else:
            return 'Major' if value else 'Minor'

    if attribute == 'key':
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        return keys[value]

    if attribute == 'signature':
        return str(round(value, 2 if average else 0)) + '/4'


"""

@app.route('/_add-item')
def add_item():
    sp = session.get('sp')
    requested_uri = request.args.get('uri', type=str)
    # create a new collection object
    new_item = Collection(item_uri)
    # add item to selected_items
    session.get('collection').subcolls.append(new_item)
    return {
        'items': render_template('dynamic/selected_items_list.html', list=session.get('collection').subcols),
        'songs': render_template('dynamic/included_songs_list.html', list=session.get('collection').gather_tracks())
    }



# HELPERS

# Fetches an item
def get_spotify_item(uri):
    sp = session.get('sp')
    response = sp.fetch_item(uri)

"""
if __name__ == '__main__':
    app.run()

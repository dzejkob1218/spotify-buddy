import os
from flask import Flask, session, request, redirect
from classes.spotify_session import SpotifySession
from flask_session import Session
import uuid

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


# default route
@app.route('/')
def index():
    # Gives a random ID to a new user without a session
    if not session.get('uuid'):
        session['uuid'] = str(uuid.uuid4())

    if not session.get('sp'):
        return '<h2><a href="/login">Sign in</a></h2>'

    sp = session.get('sp')
    return f'<h2>Hi, {sp.connection.me()["display_name"]}' \
           f'<small><a href="/logout">[sign out]<a/></small></h2>'


@app.route('/login')
def login():
    # Create a SpotifySession object which will initialize spotipy Authorization Manager to validate user
    sp = SpotifySession(session_cache_path())
    session['sp'] = sp

    # Redirect the user to authorization site
    if not sp.auth_manager.validate_token(sp.cache_handler.get_cached_token()):
        auth_url = sp.auth_manager.get_authorize_url()
        return redirect(auth_url)
    else:
        # Redirect back to home page if user already logged in
        return redirect('/')


@app.route('/callback')
def callback():
    if request.args.get("code"):
        sp = session.get('sp')
        sp.connect(request.args.get("code"))
        return redirect('/')


@app.route('/logout')
def logout():
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    return redirect('/')

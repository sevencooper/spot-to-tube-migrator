import os
import spotipy
import ytmusicapi
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic
from flask import Flask, session, request, redirect, render_template, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Spotify API configuration
SPOTIFY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SPOTIFY_SCOPE = "playlist-read-private playlist-read-collaborative"

def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPE
    )

def get_spotify_client():
    token_info = session.get('spotify_token_info', None)
    if not token_info:
        return None
    
    # Check if token is expired and refresh if necessary
    if get_spotify_oauth().is_token_expired(token_info):
        token_info = get_spotify_oauth().refresh_access_token(token_info['refresh_token'])
        session['spotify_token_info'] = token_info

    return spotipy.Spotify(auth=token_info['access_token'])

@app.route('/')
def index():
    return render_template('index.html', spotify_user=session.get('spotify_user'))

@app.route('/login/spotify')
def login_spotify():
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    sp_oauth = get_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['spotify_token_info'] = token_info
    
    sp = get_spotify_client()
    user_info = sp.current_user()
    session['spotify_user'] = user_info['display_name']
    
    return redirect('/')

@app.route('/logout/spotify')
def logout_spotify():
    session.pop('spotify_token_info', None)
    session.pop('spotify_user', None)
    return redirect('/')

@app.route('/api/spotify-playlists')
def get_spotify_playlists():
    sp = get_spotify_client()
    if not sp:
        return jsonify({"error": "User not authenticated with Spotify"}), 401
    
    playlists = []
    results = sp.current_user_playlists(limit=50)
    while results:
        playlists.extend(results['items'])
        if results['next']:
            results = sp.next(results)
        else:
            results = None
            
    formatted_playlists = [
        {"id": p['id'], "name": p['name'], "track_count": p['tracks']['total']}
        for p in playlists
    ]
    return jsonify(formatted_playlists)

@app.route('/api/verify-youtube', methods=['POST'])
def verify_youtube():
    data = request.get_json()
    headers_raw = data.get('headers_raw')
    if not headers_raw:
        return jsonify({"error": "Headers are required"}), 400
    
    try:
        ytmusicapi.setup(headers_raw=headers_raw, filepath="browser.json")
        session['ytmusic_headers'] = headers_raw
        return jsonify({"success": True, "message": "YouTube Music connection successful!"})
    except Exception as e:
        return jsonify({"error": f"Failed to initialize YTMusic. Error: {str(e)}"}), 500

@app.route('/api/migrate', methods=['POST'])
def migrate():
    data = request.get_json()
    playlist_ids = data.get('playlist_ids', [])
    
    sp = get_spotify_client()
    yt_headers = session.get('ytmusic_headers')

    if not sp or not yt_headers:
        return jsonify({"error": "Authentication missing for Spotify or YouTube Music"}), 401
    
    try:
        yt = YTMusic("browser.json")
    except Exception as e:
        return jsonify({"error": f"Failed to authenticate with YouTube Music. Please re-verify. Error: {str(e)}"}), 401

    log = []
    summary = {"success": 0, "failed": 0, "playlists": []}

    for playlist_id in playlist_ids:
        try:
            # 1. Get Spotify playlist details
            sp_playlist = sp.playlist(playlist_id, fields="name,description,tracks.items(track(name,artists(name)))")
            sp_playlist_name = sp_playlist['name']
            sp_playlist_desc = sp_playlist.get('description', '')
            log.append(f"Processing playlist '{sp_playlist_name}'...")

            # 2. Create YouTube Music playlist
            yt_playlist_id = yt.create_playlist(sp_playlist_name, sp_playlist_desc)
            log.append(f"  -> Created YouTube Music playlist '{sp_playlist_name}'.")

            playlist_summary = {"name": sp_playlist_name, "found": 0, "not_found": [], "total": 0}

            # 3. Get all tracks from Spotify playlist
            tracks = []
            results = sp.playlist_items(playlist_id)
            tracks.extend(results['items'])
            while results['next']:
                results = sp.next(results)
                tracks.extend(results['items'])

            playlist_summary['total'] = len(tracks)

            # 4. Search and add tracks to YouTube Music
            video_ids_to_add = []
            for item in tracks:
                track = item['track']
                if not track: continue
                
                track_name = track['name']
                artist_name = track['artists'][0]['name']
                query = f"{track_name} {artist_name}"
                log.append(f"  -> Searching for '{query}'...")

                search_results = yt.search(query, filter="songs", limit=1)
                if search_results and search_results[0]['videoId']:
                    video_id = search_results[0]['videoId']
                    video_ids_to_add.append(video_id)
                    playlist_summary['found'] += 1
                    log.append(f"     Found: '{search_results[0]['title']}'. Adding to queue.")
                else:
                    playlist_summary['not_found'].append(query)
                    log.append(f"     NOT FOUND.")
            
            if video_ids_to_add:
                yt.add_playlist_items(yt_playlist_id, video_ids_to_add, duplicates=True)
                log.append(f"  -> Added {len(video_ids_to_add)} songs to '{sp_playlist_name}' on YouTube Music.")

            summary['success'] += playlist_summary['found']
            summary['failed'] += len(playlist_summary['not_found'])
            summary['playlists'].append(playlist_summary)
            log.append("-" * 20)

        except Exception as e:
            log.append(f"!! An error occurred while processing playlist ID {playlist_id}: {str(e)}")
            log.append("-" * 20)

    return jsonify({"log": "\n".join(log), "summary": summary})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
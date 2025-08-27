from flask import Flask, redirect, request, render_template, session
import json
import os
import base64
import requests

# Flask: web framework for web apps, routes, http requests etc, creates app
# json: work with json data files (for config)
# base64: encode/decode data (for auth header)
# requests: library for http requests (couldn't pull from spotify api without it)
# os: operating system interface

"""---------------------------------------------------------------------------------"""

# Load Spotify API credentials from config file
with open("config.json") as f:
    config = json.load(f)

CLIENT_ID = config["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = config["SPOTIFY_CLIENT_SECRET"]
REDIRECT_URI = config["SPOTIFY_REDIRECT_URI"]

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for using sessions

# Define "cool" genres for scoring algorithm
COOL_GENRES = [
    "deathcore", "grindcore", "post-hardcore", "art pop", "experimental", "metal", "death metal", "metalcore",
    "black metal", "emo", "midwest emo", "djent", "math rock", "experimental hip hop", "hardcore", "hardcore punk",
    "powerviolence", "shoegaze", "rnb", "r&b", "soul", "synthpop", "new wave", "alternative rnb", "deathgrind",
    "brutal death metal", "speed metal", "electronic", "trip hop", "indie rock", "melodic hardcore", "noise",
    "noisecore", "noise rock", "noisegrind", "gorenoise", "slowcore", "thrash metal", "crust punk", "technical death metal", "chamber pop",
    "screamo", "post-rock", "folk metal", "dream pop", "post-punk", "industrial rock", "deathrash",
    "death metal/black metal", "crossover thrash", "avant-garde", "drone", "emoviolence", "emocore", "j-rock",
    "alternative hip-hop", "doom metal", "post-metal", "idm", "mathcore", "horrorcore", "hyperpop", "dark ambient",
    "ambient", "proto-punk", "house", "downtempo", "atmospheric black metal", "goregrind", "pornogrind", "trance",
    "breakcore", "jazz", "sludge metal", "emo pop", "rage rap", "rage", "folk punk", "industrial", "art rock",
    "neofolk", "skate punk", "jazz fusion", "jazz funk", "space rock", "big beat", "breakbeat", "hardcore techno", 
    "disco", "hi-nrg", "french house", "electronica", "electro", "ebm", "alternative rock", "progressive rock", 
    "progressive metal", "punk", "groove metal", "heavy metal", "grunge", "speed metal", "hip hop", "east coast hip hop", 
    "southern hip hop", "rap", "jazz rap", "garage rock", "indie punk", "soundtrack", "ska punk", "cloud rap", 
    "gangster rap", "memphis rap", "madchester", "dark trap", "crunk", "underground rap", "underground hip hop", "mincecore", 
    "stoner metal", "stoner rock", "drone metal", "slam death metal", "slamming brutal death metal", "disco"
]


def calculate_cool_score(track_item, artist_metadata):
    """
    Calculate the 'cool score' for a track based on multiple factors
    """
    artist_id = track_item["artists"][0]["id"]
    artist_data = artist_metadata.get(artist_id, {})
    genres = artist_data.get("genres", [])
    popularity = artist_data.get("popularity", None)
    followers = artist_data.get("followers", None)
    
    score = 0
    
    # Genre bonus - rewards listening to "cool" genres
    if any(g in COOL_GENRES for g in genres):
        score += 50
    
    # Explicit content bonus
    if track_item["explicit"]:
        score += 5
    
    # Artist popularity scaling - less popular = more points
    if popularity is not None:
        if popularity < 50:
            score += 18
        elif popularity < 60:
            score += 14
        elif popularity < 70:
            score += 10
        elif popularity < 80:
            score += 6
        elif popularity < 90:
            score += 4
        elif popularity < 100:
            score += 2
    
    # Follower tier bonus - supports smaller artists
    if followers is not None:
        if followers < 100000:
            score += 16
        elif followers < 200000:
            score += 14
        elif followers < 300000:
            score += 13
        elif followers < 400000:
            score += 12
        elif followers < 500000:
            score += 11
        elif followers < 600000:
            score += 10
        elif followers < 700000:
            score += 9
        elif followers < 800000:
            score += 8
        elif followers < 900000:
            score += 7
        elif followers < 1000000:
            score += 6
    
    # Track popularity scaling - underground tracks score higher
    if track_item["popularity"] < 50:
        score += 11
    elif track_item["popularity"] < 60:
        score += 9
    elif track_item["popularity"] < 70:
        score += 7
    elif track_item["popularity"] < 80:
        score += 5
    elif track_item["popularity"] < 90:
        score += 3
    elif track_item["popularity"] < 100:
        score += 1
    
    # Cap score at 100 and round to 2 decimal places
    return round(min(score, 100), 2)


def get_spotify_data(access_token):
    """
    Fetch user data from Spotify API
    """
    api_headers = {"Authorization": f"Bearer {access_token}"}
    
    # Get user profile
    profile_response = requests.get("https://api.spotify.com/v1/me", headers=api_headers)
    username = "there"  # Default fallback
    if profile_response.status_code == 200:
        profile_data = profile_response.json()
        username = profile_data.get("display_name", "there")
    
    # Get user's top 20 tracks
    tracks_response = requests.get("https://api.spotify.com/v1/me/top/tracks?limit=20", headers=api_headers)
    tracks_data = tracks_response.json()
    
    # Get user's top 20 artists for additional context
    artists_response = requests.get("https://api.spotify.com/v1/me/top/artists?limit=20", headers=api_headers)
    top_artists_data = artists_response.json()
    
    return username, tracks_data, top_artists_data


def collect_artist_metadata(tracks_data, api_headers):
    """
    Collect detailed metadata for all artists in the tracks
    """
    # Get unique artist IDs
    artist_ids = list(set([item["artists"][0]["id"] for item in tracks_data["items"]]))
    artist_metadata = {}
    
    for artist_id in artist_ids:
        artist_url = f"https://api.spotify.com/v1/artists/{artist_id}"
        artist_response = requests.get(artist_url, headers=api_headers)
        
        if artist_response.status_code == 200:
            artist_data = artist_response.json()
            artist_metadata[artist_id] = {
                "name": artist_data["name"],
                "genres": artist_data["genres"],
                "popularity": artist_data["popularity"],
                "followers": artist_data["followers"]["total"]
            }
        else:
            print(f"Failed to get data for artist {artist_id}")
    
    return artist_metadata


# Route: Landing page
@app.route("/")
def landing():
    return render_template('landing.html')

# Route: Review page - displays track analysis interface
@app.route("/review", methods=["GET", "POST"])
def review():
    # Redirect to login if no tracks available
    if "structured_tracks" not in session or not session["structured_tracks"]:
        return redirect("/login")
    
    # Reset track index if it's out of bounds (happens when coming back from results)
    if "track_index" not in session or session["track_index"] >= len(session["structured_tracks"]):
        session["track_index"] = 0
    
    # Handle "next track" button
    if request.method == "POST":
        session["track_index"] += 1
        if session["track_index"] >= len(session["structured_tracks"]):
            return redirect("/results")  # Go to results instead of looping
        return redirect("/review")
    
    # Get current track data
    current_track = session["structured_tracks"][session["track_index"]]
    
    return render_template(
        'index.html', 
        track=current_track, 
        username=session.get("username", "there"),
        tracks=session["structured_tracks"]
    )

# Route: Results page - displays final score and track breakdown
@app.route("/results")
def results():
    # Redirect to login if no tracks available
    if "structured_tracks" not in session or not session["structured_tracks"]:
        return redirect("/login")
    
    # Calculate final statistics
    scored_tracks = [track for track in session["structured_tracks"] if track.get("is_scored", False)]
    unscored_count = session.get("unscored_count", 0)
    
    if scored_tracks:
        total_score = sum(track.get("cool_score", 0) for track in scored_tracks)
        final_score = round(total_score / len(scored_tracks), 2)
    else:
        final_score = 0.0
    
    # Generate score-based commentary
    def get_score_commentary(score):
        if score >= 90:
            return "absolutely legendary taste! you're discovering the underground gems that matter."
        elif score >= 80:
            return "solid taste! you've got a good ear for quality music outside the mainstream."
        elif score >= 70:
            return "decent taste, but there's room for exploration in more underground territory."
        elif score >= 60:
            return "you're on the right track, but could dive deeper into more experimental sounds."
        elif score >= 50:
            return "pretty mainstream taste, but everyone starts somewhere. time to explore!"
        else:
            return "very mainstream taste detected. let's work on finding some hidden gems."
    
    commentary = get_score_commentary(final_score)
    
    # Sort tracks by score for display (scored tracks first, then unscored)
    scored_sorted = sorted(scored_tracks, key=lambda x: x.get("cool_score", 0), reverse=True)
    unscored_tracks = [track for track in session["structured_tracks"] if not track.get("is_scored", False)]
    all_tracks_sorted = scored_sorted + unscored_tracks
    
    return render_template(
        'results.html',
        final_score=final_score,
        commentary=commentary,
        tracks=all_tracks_sorted,
        total_tracks=len(session["structured_tracks"]),
        scored_count=len(scored_tracks),
        unscored_count=unscored_count,
        username=session.get("username", "there")
    )


# Route: Spotify login redirect
@app.route("/login")
def login():
    scopes = "user-top-read user-read-private"
    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={scopes}"
    )
    return redirect(auth_url)


# Route: OAuth callback handler
@app.route("/callback")
def callback():
    # Get authorization code from callback
    code = request.args.get("code")
    if not code:
        return "Authorization failed - no code received from Spotify"
    
    # Exchange authorization code for access token
    token_url = "https://accounts.spotify.com/api/token"
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    
    token_headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    
    # Request access token
    token_response = requests.post(token_url, data=token_data, headers=token_headers)
    if token_response.status_code != 200:
        return f"Failed to get access token: {token_response.text}"
    
    # Extract access token
    token_info = token_response.json()
    access_token = token_info["access_token"]
    api_headers = {"Authorization": f"Bearer {access_token}"}
    
    # Fetch user data from Spotify
    username, tracks_data, top_artists_data = get_spotify_data(access_token)
    session["username"] = username
    
    # Collect detailed artist metadata
    artist_metadata = collect_artist_metadata(tracks_data, api_headers)
    
    # Process tracks and calculate scores
    structured_tracks = []
    unscored_count = 0
    
    for track_item in tracks_data["items"]:
        artist_id = track_item["artists"][0]["id"]
        artist_data = artist_metadata.get(artist_id, {})
        
        # Check if track has genres for scoring
        has_genres = artist_data.get("genres") and len(artist_data.get("genres", [])) > 0
        
        if has_genres:
            cool_score = calculate_cool_score(track_item, artist_metadata)
            is_scored = True
        else:
            cool_score = None  # No score for genre-less tracks
            unscored_count += 1
            is_scored = False
            print(f"Track with no genres (unscored): {track_item['name']} by {track_item['artists'][0]['name']}")
        
        structured_tracks.append({
            "track_name": track_item["name"],
            "artist_name": artist_data.get("name", track_item["artists"][0]["name"]),
            "track_popularity": track_item["popularity"],
            "cool_score": cool_score,
            "genres": artist_data.get("genres", []) if has_genres else [],
            "is_scored": is_scored
        })
    
    # Save processed data to session
    session["structured_tracks"] = structured_tracks
    session["unscored_count"] = unscored_count  # Store for display
    session["track_index"] = 0  # Start at first track
    
    return redirect("/review")


if __name__ == "__main__":
    app.run(debug=True)
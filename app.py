from flask import Flask, redirect, request, render_template, session
import json
import os
import base64
import requests

# flask: web framework for web apps, routes, http requests etc, creates app
# json: work with json data files (for config)
# base64: encode/decode data (for auth header)
# requests: library for http requests (couldnt pull from spotify api without it)
# os (to work with os but not used rn)

"""---------------------------------------------------------------------------------"""

# pull spotify api pwd stuff from config json
with open("config.json") as f:
    config = json.load(f)

CLIENT_ID = config["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = config["SPOTIFY_CLIENT_SECRET"]
REDIRECT_URI = config["SPOTIFY_REDIRECT_URI"]

app = Flask(__name__)
app.secret_key = os.urandom(24)  # required for using sessions


# home route, main landing page
@app.route("/", methods=["GET", "POST"])
def home():
    # ensure session stores the current track index
    if "track_index" not in session:
        session["track_index"] = 0  # Start at the first track

    # ensure that structured_tracks is in the session
    if "structured_tracks" not in session or not session["structured_tracks"]:
        # if it's not there, or it's empty, initialize it (or handle the error)
        return "Error: No tracks available to display."

    # get the current track data
    current_track = session.get("structured_tracks", [])[session["track_index"]]

    # calculate the final score from the structured tracks
    total_score = 0
    for track in session.get("structured_tracks", []):
        total_score += track.get("cool_score", 0)
    final_score = round(total_score / len(session.get("structured_tracks", [])), 2) if session.get("structured_tracks") else 0

    # if the user clicks "next", go to the next track
    if request.method == "POST":
        session["track_index"] += 1
        if session["track_index"] >= len(session.get("structured_tracks", [])):
            session["track_index"] = 0  # restart from the beginning
        return redirect("/")  # reload the page to show the new track

    return render_template('index.html', track=current_track, final_score=final_score, username=session.get("username"), tracks=session.get("structured_tracks", []))


# login route, redirects the user to spotify login
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


# callback route, this route is called after the user logs in and grants access
@app.route("/callback")
def callback():
    # Get the authorization code from the callback URL
    code = request.args.get("code")
    if code is None:
        return "No code found in callback :("
    print("Received code from Spotify:", code)

    # Get access token using the authorization code
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

    # Send token request
    token_response = requests.post(token_url, data=token_data, headers=token_headers)
    if token_response.status_code != 200:
        print("Failed to get token:", token_response.text)
        return "Failed to get access token from Spotify"

    token_info = token_response.json()
    access_token = token_info["access_token"]
    print("Access token:", access_token)

    api_headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Get user profile info
    profile_url = "https://api.spotify.com/v1/me"
    profile_response = requests.get(profile_url, headers=api_headers)
    if profile_response.status_code == 200:
        profile_data = profile_response.json()
        username = profile_data["display_name"]
        print(f"\nHi, {username}!! Welcome to Spotijudge!")
    else:
        username = "there"
        print(f"\nHi, {username}!! Welcome to Spotijudge!")

    # Save username in session
    session["username"] = username

    # Get the user's top 20 tracks
    tracks_data = requests.get("https://api.spotify.com/v1/me/top/tracks?limit=20", headers=api_headers).json()

    # Get the user's top 20 artists
    top_artists_data = requests.get("https://api.spotify.com/v1/me/top/artists?limit=20", headers=api_headers).json()
    top_artists = top_artists_data["items"]
    top_artist_names = set(artist["name"] for artist in top_artists)

    # Collect artist metadata (genres, popularity, followers)
    artist_ids = list(set([item["artists"][0]["id"] for item in tracks_data["items"]]))
    artist_meta = {}

    for artist_id in artist_ids:
        artist_url = f"https://api.spotify.com/v1/artists/{artist_id}"
        artist_response = requests.get(artist_url, headers=api_headers)

        if artist_response.status_code != 200:
            print(f"failed to get artist {artist_id}")
            continue

        artist_data = artist_response.json()
        artist_meta[artist_id] = {
            "name": artist_data["name"],
            "genres": artist_data["genres"],
            "popularity": artist_data["popularity"],
            "followers": artist_data["followers"]["total"]
        }

    # Define cool genres based on what I like (just for fun)
    cool_genres = [
        "deathcore", "grindcore", "post-hardcore", "art pop", "experimental", "metal", "death metal", "metalcore",
        "black metal", "emo", "midwest emo", "djent", "math rock", "experimental hip hop", "hardcore", "hardcore punk",
        "powerviolence", "shoegaze", "rnb", "r&b", "soul", "synthpop", "new wave", "alternative rnb", "deathgrind",
        "brutal death metal", "speed metal", "electronic", "trip hop", "indie rock", "melodic hardcore", "noise",
        "noisecore", "noise rock", "slowcore", "thrash metal", "crust punk", "technical death metal", "chamber pop",
        "screamo", "post-rock", "folk metal", "dream pop", "post-punk", "industrial rock", "deathrash",
        "death metal/black metal", "crossover thrash", "avant-garde", "drone", "emoviolence", "emocore", "j-rock",
        "alternative hip-hop", "doom metal", "post-metal", "idm", "mathcore", "horrorcore", "hyperpop", "dark ambient",
        "ambient", "proto-punk", "house", "downtempo", "atmospheric black metal", "goregrind", "pornogrind", "trance",
        "breakcore", "jazz", "sludge metal", "emo pop", "rage rap", "rage", "folk punk", "industrial", "art rock",
        "neofolk", "skate punk", "jazz fusion", "jazz funk", "space rock"
    ]

    structured_tracks = []

    # Loop through the tracks and calculate cool score
    for item in tracks_data["items"]:
        artist_id = item["artists"][0]["id"]
        artist_data = artist_meta.get(artist_id, {})
        genres = artist_data.get("genres", [])
        popularity = artist_data.get("popularity", None)
        followers = artist_data.get("followers", None)
        artist_name = artist_data.get("name", item["artists"][0]["name"])

        score = 0

        # genre bonus
        if any(g in cool_genres for g in genres):
            score += 50  # genre bonus adjusted to 50 points
        # explicit bonus
        if item["explicit"]:
            score += 5 
        # artist popularity scaling
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
        # follower tier bonus
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
        # track popularity scaling
        if item["popularity"] < 50:
            score += 11
        elif item["popularity"] < 60:
            score += 9
        elif item["popularity"] < 70:
            score += 7
        elif item["popularity"] < 80:
            score += 5
        elif item["popularity"] < 90:
            score += 3
        elif item["popularity"] < 100:
            score += 1
        # final score for the track
        final_score = round(min(score, 100), 2)
        # collects everything in structured list
        structured_tracks.append({
            "track_name": item["name"],
            "artist_name": artist_name,
            "track_popularity": item["popularity"],
            "cool_score": final_score,
            "genres": genres
        })

    # Save structured tracks to session
    session["structured_tracks"] = structured_tracks

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
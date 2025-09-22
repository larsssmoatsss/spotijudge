from flask import Flask, redirect, request, render_template, session, jsonify
import os
import base64
import requests
from datetime import datetime
from dotenv import load_dotenv

# Import our database models
from models import (
    db, init_db, User, AnalysisSession, Artist, Track, TrackAnalysis,
    get_or_create_user, get_or_create_artist, get_or_create_track
)

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)

# Configuration from environment variables
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))

# Spotify API credentials from environment
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

# Initialize database
init_db(app)

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
    user_data = None
    if profile_response.status_code == 200:
        user_data = profile_response.json()
    
    # Get user's top 20 tracks
    tracks_response = requests.get("https://api.spotify.com/v1/me/top/tracks?limit=20", headers=api_headers)
    tracks_data = tracks_response.json()
    
    # Get user's top 20 artists for additional context
    artists_response = requests.get("https://api.spotify.com/v1/me/top/artists?limit=20", headers=api_headers)
    top_artists_data = artists_response.json()
    
    return user_data, tracks_data, top_artists_data


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
    # Check if we have a current session
    if "session_id" not in session:
        return redirect("/login")
    
    # Get the analysis session from database
    analysis_session = AnalysisSession.query.get(session["session_id"])
    if not analysis_session:
        return redirect("/login")
    
    # Get all track analyses for this session, ordered by position
    track_analyses = TrackAnalysis.query.filter_by(session_id=analysis_session.id).order_by(TrackAnalysis.track_position).all()
    
    if not track_analyses:
        return redirect("/login")
    
    # Handle "next track" button
    if request.method == "POST":
        session["track_index"] = session.get("track_index", 0) + 1
        if session["track_index"] >= len(track_analyses):
            return redirect("/results")
        return redirect("/review")
    
    # Reset track index if it's out of bounds
    if "track_index" not in session or session["track_index"] >= len(track_analyses):
        session["track_index"] = 0
    
    # Get current track analysis
    current_analysis = track_analyses[session["track_index"]]
    
    # Format the track data for the template (same structure as before)
    current_track = {
        "track_name": current_analysis.track.name,
        "artist_name": current_analysis.track.artist.name,
        "track_popularity": current_analysis.track.popularity,
        "cool_score": float(current_analysis.cool_score) if current_analysis.cool_score else None,
        "genres": current_analysis.track.artist.genres or [],
        "is_scored": current_analysis.is_scored
    }
    
    return render_template(
        'index.html', 
        track=current_track, 
        username=analysis_session.user.display_name or "there",
        tracks=[{"track_name": ta.track.name} for ta in track_analyses]  # Just for count
    )


# Route: Results page - displays final score and track breakdown
@app.route("/results")
def results():
    # Check if we have a current session
    if "session_id" not in session:
        return redirect("/login")
    
    # Get the analysis session from database
    analysis_session = AnalysisSession.query.get(session["session_id"])
    if not analysis_session:
        return redirect("/login")
    
    # Get all track analyses for this session
    track_analyses = TrackAnalysis.query.filter_by(session_id=analysis_session.id).all()
    
    # Calculate statistics
    scored_analyses = [ta for ta in track_analyses if ta.is_scored and ta.cool_score is not None]
    unscored_count = len([ta for ta in track_analyses if not ta.is_scored])
    
    if scored_analyses:
        total_score = sum(float(ta.cool_score) for ta in scored_analyses)
        final_score = round(total_score / len(scored_analyses), 2)
        
        # Update the session with final score
        analysis_session.final_score = final_score
        analysis_session.completed_at = datetime.utcnow()
        db.session.commit()
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
    scored_sorted = sorted(scored_analyses, key=lambda x: float(x.cool_score), reverse=True)
    unscored_analyses = [ta for ta in track_analyses if not ta.is_scored]
    all_analyses_sorted = scored_sorted + unscored_analyses
    
    # Format tracks for template
    tracks = []
    for ta in all_analyses_sorted:
        tracks.append({
            "track_name": ta.track.name,
            "artist_name": ta.track.artist.name,
            "track_popularity": ta.track.popularity,
            "cool_score": float(ta.cool_score) if ta.cool_score else None,
            "genres": ta.track.artist.genres or [],
            "is_scored": ta.is_scored
        })
    
    return render_template(
        'results.html',
        final_score=final_score,
        commentary=commentary,
        tracks=tracks,
        total_tracks=len(track_analyses),
        scored_count=len(scored_analyses),
        unscored_count=unscored_count,
        username=analysis_session.user.display_name or "there"
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
    user_data, tracks_data, top_artists_data = get_spotify_data(access_token)
    
    # Create or get user
    user = get_or_create_user(
        spotify_id=user_data["id"],
        display_name=user_data.get("display_name", "there")
    )
    
    # Create new analysis session
    analysis_session = AnalysisSession(
        user_id=user.id,
        total_tracks=len(tracks_data["items"]),
        scored_tracks=0,  # Will be updated as we process
        unscored_tracks=0  # Will be updated as we process
    )
    db.session.add(analysis_session)
    db.session.flush()  # Get the ID without committing
    
    # Collect detailed artist metadata
    artist_metadata = collect_artist_metadata(tracks_data, api_headers)
    
    # Process tracks and calculate scores
    scored_count = 0
    unscored_count = 0
    
    for position, track_item in enumerate(tracks_data["items"], 1):
        artist_id = track_item["artists"][0]["id"]
        artist_data = artist_metadata.get(artist_id, {})
        
        # Create or get artist
        artist = get_or_create_artist(
            spotify_id=artist_id,
            name=artist_data.get("name", track_item["artists"][0]["name"]),
            genres=artist_data.get("genres", []),
            popularity=artist_data.get("popularity"),
            followers=artist_data.get("followers")
        )
        
        # Create or get track
        track = get_or_create_track(
            spotify_id=track_item["id"],
            name=track_item["name"],
            artist=artist,
            popularity=track_item["popularity"],
            explicit=track_item["explicit"]
        )
        
        # Check if track has genres for scoring
        has_genres = artist_data.get("genres") and len(artist_data.get("genres", [])) > 0
        
        if has_genres:
            cool_score = calculate_cool_score(track_item, artist_metadata)
            is_scored = True
            scored_count += 1
        else:
            cool_score = None
            is_scored = False
            unscored_count += 1
            print(f"Track with no genres (unscored): {track_item['name']} by {track_item['artists'][0]['name']}")
        
        # Create track analysis
        track_analysis = TrackAnalysis(
            session_id=analysis_session.id,
            track_id=track.id,
            cool_score=cool_score,
            is_scored=is_scored,
            track_position=position
        )
        db.session.add(track_analysis)
    
    # Update session with counts
    analysis_session.scored_tracks = scored_count
    analysis_session.unscored_tracks = unscored_count
    
    # Commit all changes
    db.session.commit()
    
    # Store session ID for navigation
    session["session_id"] = analysis_session.id
    session["track_index"] = 0
    
    return redirect("/review")


# API Routes (bonus endpoints for portfolio)
@app.route("/api/sessions/<int:session_id>")
def api_get_session(session_id):
    """API endpoint to get session data as JSON"""
    analysis_session = AnalysisSession.query.get_or_404(session_id)
    return jsonify(analysis_session.to_dict())


@app.route("/api/users/<int:user_id>/sessions")
def api_get_user_sessions(user_id):
    """API endpoint to get all sessions for a user"""
    user = User.query.get_or_404(user_id)
    sessions = AnalysisSession.query.filter_by(user_id=user_id).order_by(AnalysisSession.created_at.desc()).all()
    return jsonify([session.to_dict() for session in sessions])


if __name__ == "__main__":
    # Bind to 0.0.0.0 so Docker can access it
    app.run(host="0.0.0.0", port=5000, debug=True)
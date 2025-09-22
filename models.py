"""
Database models for Spotijudge application using SQLAlchemy
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import ARRAY, UUID

db = SQLAlchemy()

class User(db.Model):
    """User model for storing Spotify user information"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(255), unique=True, nullable=False)
    display_name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('AnalysisSession', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.display_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'spotify_id': self.spotify_id,
            'display_name': self.display_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AnalysisSession(db.Model):
    """Analysis session model for storing user analysis results"""
    __tablename__ = 'analysis_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_uuid = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    final_score = db.Column(db.Numeric(5, 2))
    total_tracks = db.Column(db.Integer)
    scored_tracks = db.Column(db.Integer)
    unscored_tracks = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    track_analyses = db.relationship('TrackAnalysis', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AnalysisSession {self.session_uuid}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_uuid': str(self.session_uuid),
            'final_score': float(self.final_score) if self.final_score else None,
            'total_tracks': self.total_tracks,
            'scored_tracks': self.scored_tracks,
            'unscored_tracks': self.unscored_tracks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class Artist(db.Model):
    """Artist model for caching Spotify artist data"""
    __tablename__ = 'artists'
    
    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(500), nullable=False)
    genres = db.Column(ARRAY(db.String))  # PostgreSQL array
    popularity = db.Column(db.Integer)
    followers = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tracks = db.relationship('Track', backref='artist', lazy=True)
    
    def __repr__(self):
        return f'<Artist {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'spotify_id': self.spotify_id,
            'name': self.name,
            'genres': self.genres or [],
            'popularity': self.popularity,
            'followers': self.followers,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Track(db.Model):
    """Track model for storing Spotify track information"""
    __tablename__ = 'tracks'
    
    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(500), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    popularity = db.Column(db.Integer)
    explicit = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    track_analyses = db.relationship('TrackAnalysis', backref='track', lazy=True)
    
    def __repr__(self):
        return f'<Track {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'spotify_id': self.spotify_id,
            'name': self.name,
            'artist_id': self.artist_id,
            'popularity': self.popularity,
            'explicit': self.explicit,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'artist': self.artist.to_dict() if self.artist else None
        }


class TrackAnalysis(db.Model):
    """Track analysis model for storing individual track scores"""
    __tablename__ = 'track_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('analysis_sessions.id'), nullable=False)
    track_id = db.Column(db.Integer, db.ForeignKey('tracks.id'), nullable=False)
    cool_score = db.Column(db.Numeric(5, 2))
    is_scored = db.Column(db.Boolean, default=True)
    track_position = db.Column(db.Integer)  # 1-20 for top tracks ranking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TrackAnalysis {self.track.name if self.track else "Unknown"}: {self.cool_score}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'track_id': self.track_id,
            'cool_score': float(self.cool_score) if self.cool_score else None,
            'is_scored': self.is_scored,
            'track_position': self.track_position,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'track': self.track.to_dict() if self.track else None
        }


def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        print("Database initialized successfully!")


def get_or_create_user(spotify_id, display_name):
    """Get existing user or create new one"""
    user = User.query.filter_by(spotify_id=spotify_id).first()
    
    if not user:
        user = User(spotify_id=spotify_id, display_name=display_name)
        db.session.add(user)
        db.session.commit()
        print(f"Created new user: {display_name}")
    else:
        # Update display name if it changed
        if user.display_name != display_name:
            user.display_name = display_name
            db.session.commit()
            print(f"Updated user display name: {display_name}")
    
    return user


def get_or_create_artist(spotify_id, name, genres=None, popularity=None, followers=None):
    """Get existing artist or create new one"""
    artist = Artist.query.filter_by(spotify_id=spotify_id).first()
    
    if not artist:
        artist = Artist(
            spotify_id=spotify_id,
            name=name,
            genres=genres or [],
            popularity=popularity,
            followers=followers
        )
        db.session.add(artist)
        db.session.commit()
        print(f"Created new artist: {name}")
    else:
        # Update artist info if needed (genres, popularity change over time)
        updated = False
        if artist.genres != (genres or []):
            artist.genres = genres or []
            updated = True
        if artist.popularity != popularity:
            artist.popularity = popularity
            updated = True
        if artist.followers != followers:
            artist.followers = followers
            updated = True
        
        if updated:
            db.session.commit()
            print(f"Updated artist info: {name}")
    
    return artist


def get_or_create_track(spotify_id, name, artist, popularity=None, explicit=False):
    """Get existing track or create new one"""
    track = Track.query.filter_by(spotify_id=spotify_id).first()
    
    if not track:
        track = Track(
            spotify_id=spotify_id,
            name=name,
            artist_id=artist.id,
            popularity=popularity,
            explicit=explicit
        )
        db.session.add(track)
        db.session.commit()
        print(f"Created new track: {name} by {artist.name}")
    else:
        # Update track info if needed
        updated = False
        if track.popularity != popularity:
            track.popularity = popularity
            updated = True
        if track.explicit != explicit:
            track.explicit = explicit
            updated = True
        
        if updated:
            db.session.commit()
            print(f"Updated track info: {name}")
    
    return track
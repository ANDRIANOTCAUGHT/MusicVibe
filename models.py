from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True)
    bio = db.Column(db.Text, default="Artist bio will appear here.")
    image = db.Column(db.String(200), default="default_artist.jpg")


class Music(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    genre = db.Column(db.String(50))
    preview = db.Column(db.String(200))
    musiclink = db.Column(db.String(500))
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
    
    artist = db.relationship('Artist', backref=db.backref('songs', lazy=True))


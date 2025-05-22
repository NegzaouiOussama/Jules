from datetime import datetime
from app import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # e.g., 'driver', 'passenger', 'admin'

    # Relationships
    listings = db.relationship('Listing', backref='driver', lazy=True)
    reservations = db.relationship('Reservation', backref='passenger', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    available_seats = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    # Relationships
    reservations = db.relationship('Reservation', backref='listing', lazy=True)

    def __repr__(self):
        return f'<Listing {self.id} from {self.origin} to {self.destination}>'

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    passenger_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)
    seats_reserved = db.Column(db.Integer, nullable=False, default=1)

    def __repr__(self):
        return f'<Reservation {self.id} for Listing {self.listing_id} by User {self.passenger_id}>'

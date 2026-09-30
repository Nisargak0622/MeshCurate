from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

CATEGORIES = [
    "Recipe", "Motivational", "Traditional", "Fitness",
    "Travel", "Comedy", "Tech", "Fashion", "Other"
]


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship("SavedPost", backref="owner", lazy=True, cascade="all, delete-orphan")


class SavedPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    url = db.Column(db.String(500), nullable=False)
    platform = db.Column(db.String(20), nullable=False)  # "instagram" or "facebook"
    caption = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False, default="Other")
    note = db.Column(db.Text, nullable=True)
    is_favorite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

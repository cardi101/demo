# models.py
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(1000))
    role = db.Column(db.String(50), nullable=False, default='user')

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_number = db.Column(db.String(50), unique=True, nullable=False)
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    equipment = db.Column(db.String(100), nullable=False)
    issue_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    client = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    assigned_to = db.Column(db.String(100))
    comments = db.relationship('Comment', backref='request', lazy=True)

    def __repr__(self):
        return f"<Request {self.request_number}>"

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False)

    def __repr__(self):
        return f"<Comment {self.id}>"

class Executor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<Executor {self.name}>"

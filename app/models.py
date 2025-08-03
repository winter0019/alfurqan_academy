from . import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    """
    A User model for storing user account details.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    # Corrected column name to password_hash
    password_hash = db.Column(db.String(128), nullable=False) 
    role = db.Column(db.String(20))

    def __repr__(self):
        return f'<User {self.username}>'


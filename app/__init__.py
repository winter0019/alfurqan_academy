import os
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user

# Initialize extensions outside of the factory function
db = SQLAlchemy()
bcrypt = Bcrypt()
csrf = CSRFProtect()
login_manager = LoginManager()

# The factory function to create the app
def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Configure the database connection
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # Use the PostgreSQL database URL from Render
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace("://", "ql://", 1)
    else:
        # Fallback to a local SQLite database for local development
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
        # This line prevents a deprecation warning
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key')
    
    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    
    # The Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    # Import the models and routes
    from . import models, routes

    # The crucial line to register the blueprint
    app.register_blueprint(routes.main_bp)

    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()

    return app


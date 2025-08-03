import os
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions outside of the factory function
db = SQLAlchemy()
bcrypt = Bcrypt()
csrf = CSRFProtect()
login_manager = LoginManager()

# The factory function to create the app
def create_app():
    # Create the Flask application instance
    app = Flask(__name__, instance_relative_config=True)

    # Configure the database connection
    # Render automatically provides a DATABASE_URL environment variable
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # Use the PostgreSQL database URL from Render
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace("://", "ql://", 1)
    else:
        # Fallback to a local SQLite database for local development
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-very-hard-to-guess-secret-key')
    
    # Initialize extensions with the application
    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login' # Set the login view
    
    # The Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    # Import and register the blueprint for routes
    from .routes import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        # Import models and create all database tables if they don't exist
        from . import models
        db.create_all()

    return app


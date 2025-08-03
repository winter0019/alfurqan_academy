import os
from flask import Flask, g
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker

# Import the database URL from Render, if it exists
database_url = os.environ.get("DATABASE_URL")

# Set up the Flask application and extensions
def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Configure the database connection
    if database_url:
        # Use the PostgreSQL database URL from Render
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace("://", "ql://", 1)
        # SQLAlchemy and psycopg2 are used to connect to PostgreSQL.
        # This line ensures the app knows which database to connect to.
        # The replace is a small fix for how psycopg2-binary handles the URL scheme.
    else:
        # Fallback to a local SQLite database for local development
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

    app.config['SECRET_KEY'] = 'your_very_secret_key_that_you_should_change'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    with app.app_context():
        from . import routes
        app.register_blueprint(routes.main_bp)

        # Create database tables if they don't exist
        db.create_all()

    return app

# Initialize extensions outside of the factory function
db = SQLAlchemy()
bcrypt = Bcrypt()
csrf = CSRFProtect()


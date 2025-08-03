# /wsgi.py

# This file is a standard entry point for running your web application with
# a production server like Gunicorn.

from app import create_app

# We call the create_app() factory function to create a new Flask application instance.
# Gunicorn will use this 'app' object as the WSGI callable.
app = create_app()

# This part is optional but useful for local testing.
if __name__ == "__main__":
    app.run()

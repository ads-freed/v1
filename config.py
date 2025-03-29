import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Security and Environment Variables
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(basedir, 'app.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'zip'}

    # Session Lifetime
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    # Rate Limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour"

    # Logging
    LOG_FILE = os.path.join(basedir, 'logs', 'app.log')

    # SocketIO
    SOCKETIO_ASYNC_MODE = 'eventlet'

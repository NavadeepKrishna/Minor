import os

class Config:
    # Security Key (replace with a complex key in production)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-default-secret-key-12345'
    
    # Database Configuration (SQLite)
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit
    
    # Debugging setting for clarity
    FLASK_ENV = 'development'
    DEBUG = True
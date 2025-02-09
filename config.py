import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'hard-to-guess-string')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///default.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', "http://localhost:5000/google/callback")


    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads/')
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://jackyk:PaY4L5JmUsqh@ep-green-paper-a5j86671.us-east-2.aws.neon.tech/spazanet?sslmode=require')

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///spaza.db')
    DEBUG = False

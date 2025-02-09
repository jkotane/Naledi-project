import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI", "postgresql://user:password@localhost/dbname")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "your-google-client-id")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "your-google-client-secret")


   


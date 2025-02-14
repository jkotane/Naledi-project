import os
from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from naledi.naledimodels import User, UserProfile
from naledi.extensions import db, login_manager, oauth, migrate


load_dotenv()

# Initialize Extensions
# initialization done in extensions.py
"""db = SQLAlchemy()
login_manager = LoginManager()
oauth = OAuth()"""


# Define the user_loader function
@login_manager.user_loader
def load_user(user_id):
    """Load the user by their user_id."""
    return UserProfile.query.get(int(user_id))


# Define the naledi blueprint at the module level
naledi_bp = Blueprint('naledi', __name__)



def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object("config.DevelopmentConfig")

    # Initialize extensions with the Flask app
    db.init_app(app)
    login_manager.init_app(app)
    oauth.init_app(app)
    migrate.init_app(app, db)  # Initialize Migrate here

    # Register OAuth Providers
    google = oauth.register(
            name="google",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            access_token_url="https://oauth2.googleapis.com/token",
            #access_token_url="https://accounts.google.com/o/oauth2/token",
            authorize_url="https://accounts.google.com/o/oauth2/auth",
            api_base_url="https://www.googleapis.com/oauth2/v1/",
            userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
            client_kwargs={"scope": "openid email profile"},
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration"  # ✅ Explicitly add metadata URL
        )



    # Import routes for this blueprint (after blueprint declaration)
    from . import routes  # Import routes after blueprint definition
   

    # Register the naledi blueprint
    app.register_blueprint(naledi_bp)

    # Register other blueprints
    from spazachain.spachainauth import spachainauth
    from spazachain.spachainview import spachainview
    from mncchain.mncauth import mncauth
    from mncchain.mncview import mncview

    app.register_blueprint(spachainauth, url_prefix='/spazachain/home')
    app.register_blueprint(spachainview, url_prefix='/spazachain/view')
    app.register_blueprint(mncauth, url_prefix='/mncchain/home')
    app.register_blueprint(mncview, url_prefix='/mncchain/view')


        # Configure the upload folder and allowed extensions
    app.config['UPLOAD_FOLDER'] = 'uploads/'  # This is where the files will be stored on your server
    app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'jpg', 'jpeg', 'png'}

    return app
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Blueprint



load_dotenv()

# ✅ Initialize Extensions
db = SQLAlchemy()
login_manager = LoginManager()
oauth = OAuth()  # ✅ Now OAuth is initialized globally





def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object("config.DevelopmentConfig")

    # ✅ Initialize extensions with the Flask app
    db.init_app(app)
    login_manager.init_app(app)
    oauth.init_app(app)


    #print("GOOGLE_CLIENT_ID:", os.getenv("GOOGLE_CLIENT_ID"))
    #print("GOOGLE_CLIENT_SECRET:", os.getenv("GOOGLE_CLIENT_SECRET"))


    # ✅ Register OAuth Providers
    oauth.register(
        name="google",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        access_token_url="https://oauth2.googleapis.com/token",
        authorize_url="https://accounts.google.com/o/oauth2/auth",
        api_base_url="https://www.googleapis.com/oauth2/v1/",
        userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
        client_kwargs={"scope": "openid email profile"},
    )
    


    naledi = Blueprint('naledi', __name__)

    # Import routes (make sure this does not create a circular import)
    from . import routes  # This imports routes from routes.py


    # ✅ Import Blueprints & Register Routes
    from spazachain.spachainauth import spachainauth
    from spazachain.spachainview import spachainview
    from mncchain.mncauth import mncauth
    from mncchain.mncview import mncview

    """ app.register_blueprint(spachainauth, url_prefix='/spazachain')
    app.register_blueprint(spachainview, url_prefix='/spazachain')
    app.register_blueprint(mncauth, url_prefix='/mncchain')
    app.register_blueprint(mncview, url_prefix='/mncchain') """     

    return app


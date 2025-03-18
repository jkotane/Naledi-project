import os
from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from naledi.naledimodels import User, UserProfile
from naledi.extensions import db, oauth, migrate, mail, generate_serializer
from flask_mailman import Mail
from itsdangerous import URLSafeTimedSerializer
from ldap3 import Server, Connection, ALL  # For AD authentication
from flask.helpers import get_root_path
import dash
import dash_bootstrap_components as dbc
from naledi.naledimodels import StoreDetails
from flask import current_app
import re
import jwt, requests
from jwt import PyJWKClient,InvalidTokenError
from msal import ConfidentialClientApplication
from flask_session import Session


load_dotenv()

# Define the naledi blueprint at the module level
naledi_bp = Blueprint('naledi', __name__)
#admin_bp = Blueprint('admin', __name__)

# ✅ Initialize two login managers
user_login_manager = LoginManager()
#user_login_manager.session_protection = "strong"
#user_login_manager.login_view = 'naledi.naledi_login'  # Store users login page

admin_manager = LoginManager()
#admin_manager.session_protection = "strong"
#admin_manager.login_view = 'naledi.naledi_admin_login'  # Admin login page

official_login_manager = LoginManager()


jwks_client = PyJWKClient(os.getenv('AZURE_JWKS_URL'))


print("azure reditect uri",os.getenv('AZURE_REDIRECT_URI'))

# Initialize OAuth and register Azure AD as an OAuth client
# Retrieve tenant ID
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
if not AZURE_TENANT_ID:
    raise ValueError("Azure Tenant ID is missing. Set the AZURE_TENANT_ID environment variable.")

azure = oauth.register(
    name='azure',
    client_id=os.getenv('AZURE_CLIENT_ID'),
    client_secret=os.getenv('AZURE_CLIENT_SECRET'),
    authorize_url=f'https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/authorize',
    access_token_url=f'https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token',
    api_base_url='https://graph.microsoft.com/',
    client_kwargs={'scope': 'openid email profile'},
    jwks_uri=f'https://login.microsoftonline.com/{AZURE_TENANT_ID}/discovery/v2.0/keys',
    redirect_uri="http://localhost:5001/official/azure/callback"  # Hardcoded for local testing
)

# verify the azure token 
def verify_azure_token(id_token):
    """Verify the Azure AD ID token."""
    try:
        # Fetch the signing key for the token
        signing_key = jwks_client.get_signing_key_from_jwt(id_token)

        # Decode and verify the token
        decoded_token = jwt.decode(
            id_token,
            key=signing_key.key,
            algorithms=["RS256"],  # Azure AD uses RS256 for signing
            audience=os.getenv('AZURE_CLIENT_ID'),  # Validate the audience
            issuer=os.getenv('AZURE_ISSUER'),  # Validate the issuer
            options={"verify_exp": True},  # Validate token expiration
        )

        print("Decoded Azure ID Token:", decoded_token)
        return decoded_token

    except InvalidTokenError as e:
        print(f"Invalid token received from Azure: {e}")
        return None
    except Exception as e:
        print(f"Token verification error: {e}")
        return None



def create_app(app_type="store"):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object("config.DevelopmentConfig")

    # Initialize extensions with the Flask app
    db.init_app(app)
    #user_login_manager.init_app(app)
    #admin_manager.init_app(app)          # Manages MncUser logins
    oauth.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    app.serializer = generate_serializer(app)




    # setup up the login manager based on the app type

    if app_type == "store":
        user_login_manager.init_app(app)  # Normal users only
    elif app_type == "official":
        official_login_manager.init_app(app)  # Officials use the normal user login manager
    else:  # If it's an admin app, only initialize the admin manager
        admin_manager.init_app(app)




    if app_type == "store":
        # Register OAuth Providers for store users
        google = oauth.register(
            name="google",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            access_token_url="https://oauth2.googleapis.com/token",
            authorize_url="https://accounts.google.com/o/oauth2/auth",
            api_base_url="https://www.googleapis.com/oauth2/v1/",
            userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
            client_kwargs={"scope": "openid email profile"},
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            redirect_uri=os.getenv("GOOGLE_REDIRECT_URI_PROD")
        )

        # Register store-specific blueprints
        from spazachain.spachainauth import spachainauth
        from spazachain.spachainview import spachainview
        app.register_blueprint(spachainauth, url_prefix='/spazachain/home')
        app.register_blueprint(spachainview, url_prefix='/spazachain/view')

    elif app_type == "official":
        # Configure AD authentication for official users

        app.config['AD_SERVER'] = os.getenv("AD_SERVER")  # e.g., ldap://your-ad-server
        app.config['AD_DOMAIN'] = os.getenv("AD_DOMAIN")  # e.g., municipality.gov

        # Register official-specific blueprints
        from mncchain.mncauth import mncauth
        from mncchain.mncview import mncview
        app.register_blueprint(mncauth, url_prefix='/mncchain/home')
        app.register_blueprint(mncview, url_prefix='/mncchain/view')

    else:     # maybe the user is admin
        #raise ValueError("Invalid app_type. Must be 'store' or 'official'.")
        from naledi.adminchain.adminroutes import admin_bp 
        app.register_blueprint(admin_bp, url_prefix="/admin")   # Admin users

    # Register the naledi blueprint
   

    
    from naledi.routes import naledi_bp
    #from naledi.adminroutes import admin_bp   
    app.register_blueprint(naledi_bp, url_prefix='/')       # User routes
    #app.register_blueprint(admin_bp, url_prefix="/admin")   # Admin users


    # Configure the upload folder and allowed extensions
    app.config['UPLOAD_FOLDER'] = 'uploads/'
    app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'jpg', 'jpeg', 'png'}


    #app.config['SESSION_TYPE'] = 'filesystem'
    #app.config['SESSION_PERMANENT'] = False
    #app.config['SESSION_USE_SIGNER'] = True
    

    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'  # Directory to store session files
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_USE_SIGNER'] = True



    Session(app)


    return app



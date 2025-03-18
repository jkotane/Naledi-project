import os
from flask import Flask, Blueprint,g
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
import google.auth
from google.auth import  default, identity_pool
from google.cloud import storage



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

# Retrieve configuration values
def get_credentials():
    """Fetch Workforce Identity Federation credentials."""
    WORKFORCE_POOL_ID = os.getenv("WORKFORCE_POOL_ID")
    PROVIDER_ID = os.getenv("WORKFORCE_PROVIDER_ID")
    SERVICE_ACCOUNT_EMAIL = os.getenv("SERVICE_ACCOUNT_EMAIL")
    AUDIENCE = f"//iam.googleapis.com/locations/global/workforcePools/{WORKFORCE_POOL_ID}/providers/{PROVIDER_ID}"

    credentials = identity_pool.Credentials.from_info({
        "type": "external_account",
        "audience": AUDIENCE,
        "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
        "token_url": "https://sts.googleapis.com/v1/token",
        "credential_source": {
            "file": os.getenv("OIDC_TOKEN_PATH")  # Path to your OIDC token
        },
        "service_account_impersonation_url": f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{SERVICE_ACCOUNT_EMAIL}:generateAccessToken",
    })
    return credentials




# include the bucket-name for official users
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
if not GCS_BUCKET_NAME:
    raise ValueError("GCS Bucket Name is missing. Set the GCS_BUCKET_NAME environment variable.")

# azure oauth for officials 
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





def create_app(app_type="official"):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object("config.DevelopmentConfig")

    # ✅ Initialize extensions
    db.init_app(app)
    oauth.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    app.serializer = generate_serializer(app)
    
   

    if app_type is None:
        app_type = os.getenv("FLASK_APP_TYPE", "official")  # Default to store

    print(f"✅ Flask App Type: {app_type}")  # Debugging

    # ✅ Setup login manager based on app type
    if app_type == "store":
        user_login_manager.init_app(app)  # Normal users only
    elif app_type == "official":
        official_login_manager.init_app(app)  # Official users
    elif app_type == "admin":
        print("Admin login manager initialized")
        admin_manager.init_app(app)  # Admin users

    # ✅ Register Google OAuth (Always Needed for Store Users)
    if app_type == "store":
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

    # ✅ Register Store-Specific Blueprints
    if app_type == "store":
        from spazachain.spachainauth import spachainauth
        from spazachain.spachainview import spachainview
        app.register_blueprint(spachainauth, url_prefix='/spazachain')
        app.register_blueprint(spachainview, url_prefix='/spazachain/view')

    # ✅ Register Official-Specific Blueprints (Only for `official`)
    if app_type == "official":
        app.config['AD_SERVER'] = os.getenv("AD_SERVER")  # e.g., ldap://your-ad-server
        app.config['AD_DOMAIN'] = os.getenv("AD_DOMAIN")  # e.g., municipality.gov
        from mncchain.mncauth import mncauth
        from mncchain.mncview import mncview
        app.register_blueprint(mncauth, url_prefix='/mncauth')
        app.register_blueprint(mncview, url_prefix='/mncview')

    # ✅ Register Admin-Specific Blueprints **Outside the If Statement**
    from adminchain.adminroutes import admin_bp 
    from adminchain.adminauth import adminauth

    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(adminauth, url_prefix="/admin")


    #from mncchain.mncauth import mncauth
    #from mncchain.mncview import mncview
    #app.register_blueprint(mncauth, url_prefix='/mncauth')
    #app.register_blueprint(mncview, url_prefix='/mncview')
    

    # ✅ Register Naledi Blueprints (Always Needed)
    from naledi.routes import naledi_bp
    app.register_blueprint(naledi_bp, url_prefix='/')

    # ✅ Configure Upload Folder and Sessions
    app.config['UPLOAD_FOLDER'] = 'uploads/'
    app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'jpg', 'jpeg', 'png'}
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_USE_SIGNER'] = True

    Session(app)
    return app
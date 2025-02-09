from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
#from  import db
#from spazanet.mainmodels import HealthCompliance, FoodItems


# Define Blueprints
spachainauth_bp = Blueprint("spachainauth", __name__)
spachainview_bp = Blueprint("spachainview", __name__)

@spachainauth_bp.route("/login/google")
def google_login():
    redirect_uri = url_for("spachainauth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@spachainauth_bp.route("/login/google/callback")
def google_callback():
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.get("userinfo").json()

    email = user_info["email"]
    name = user_info["name"]

    user = UserProfile.query.filter_by(email=email).first()
    if not user:
        user = UserProfile(username=name, email=email)
        db.session.add(user)
        db.session.commit()

    login_user(user)
    flash("Logged in successfully!", "success")
    return redirect(url_for("spachainview.home"))

@spachainview_bp.route("/")
def home():
    return render_template("spazachain/home.html")

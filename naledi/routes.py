from . import naledi_bp  # Import the naledi blueprint
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from naledi.naledimodels import UserProfile, User, StoreDetails, SpazaOwner
from .utils import is_valid_email, is_valid_cellno, is_valid_password # Import from utils.py
from naledi import oauth
from naledi import db


#naledi_bp = Blueprint('naledi_bp', __name__)




google = oauth.create_client('google')  # create the google oauth client
login_manager = LoginManager()  # Create a login manager instance

@login_manager.user_loader
def load_user(user_id):
    user = UserProfile.query.get(user_id)
    if user:
        print(f"User loaded: {user.username}")
        return user

    print(f"user not not exist /  not found: {user_id}")    
    return None



"""@naledi_bp.route('/')
def home():
    return "Welcome to the Home Page for Naledi!"""

# Validation helper function for email 
@naledi_bp.route('/naledi_login', methods=['GET', 'POST'])
#@login_required
def naledi_login():
    if current_user.is_authenticated:
        # Redirect to home if already logged in
        return redirect(url_for('naledi.naledi_home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if email is provided
        if not email:
            flash('Email is required.', category='error')
            return render_template("naledi_login.html", user=current_user)

        # Fetch user by email
        user = UserProfile.query.filter_by(email=email).first()

        if user:
            # Check if the user is a Google user
            if user.is_social_login_user:
                flash(
                    'This account uses Google Sign-In. Please use the "Sign in with Google" button.',
                    category='info')
                return render_template(
                    "naledi_login.html", user=current_user, is_social_login_user=True, google_login_url=url_for('naledi.google_auth'))

            # Validate password for standard users
            if check_password_hash(user.user_password, password):
                login_user(user, remember=True)
                flash('Logged in successfully!', category='success')
                return redirect(url_for('naledi.naledi_home'))
            else:
                flash('Invalid password. Please try again.', category='error')
        else:
            flash('No account found with this email.', category='error')
            return redirect(url_for('naledi.sign_up'))

    # Add the Google login URL for GET requests or after errors
    google_login_url = url_for('naledi.google_auth', _external=True)

    # Render the login form
    return render_template(
        "naledi_login.html", user=current_user, is_social_login_user=False, google_login_url=google_login_url )


@naledi_bp.route('/')
def landing_page():

     # If the user is logged in, redirect to the home page
    if current_user.is_authenticated:
        print("Reached landing  route.")
        print("User ID:", current_user.id)
        return redirect(url_for('naledi.naledi_home'))
    #return render_template("naledibase.html")
    # if the user is not logged in, render the landing page
 
    print("Rendering the landing page.")
    #return render_template("naledi_home.html")

    return render_template("naledi_login.html")




"""@naledi_bp.route('/naledi_home')
@login_required
def naledi_home():
    print("Reached naledi_home route.")
    print("User ID:", current_user.id)
    
    return render_template("naledi_home.html", user=current_user)"""

@naledi_bp.route('/naledi_home')
@login_required
def naledi_home():
    print("Reached naledi_home route.")
    print("User ID:", current_user.id)
    flash("Welcome to the Naledi Home Page", category="success")

    print("Checking store registration status")
    spaza_owner = SpazaOwner.query.filter_by(user_id=current_user.id).first()
    
    # Initialize store variable to None as a fallback
    store = None

    if spaza_owner:
        print(f"Spaza owner details: {spaza_owner.name}")
        print("Owner ID for the store:", spaza_owner.id)
        print("User ID for the store:", spaza_owner.user_id)
        
        # Query for the store details
        store = StoreDetails.query.filter_by(owner_id=spaza_owner.id).first()
        
        if store:
            # Check for both registered and draft statuses
            if store.reg_status == 'registered' or store.reg_status == 'draft': 
                print("Store has been registered or is in draft status")
                current_user.has_registered_store = True
                if store.reg_status == 'registered':
                    flash('You have already registered your store!', category='success')
                else:
                    flash('Your store is in draft status. Please complete the registration.', category='info')
            else:
                current_user.has_registered_store = False
                flash('Your store registration is pending or in an unknown status.', category='warning')
        else:
            # If store is not found, handle this case too
            current_user.has_registered_store = False
            flash('No store registered!', category='warning')
    else:
        current_user.has_registered_store = False

    return render_template("naledi_home.html", user=current_user, store=store)



@naledi_bp.route('/services')
#@login_required
def naledi_services():
    return render_template("naledi_services.html", user=current_user)

# Unified login/sign-up route
@naledi_bp.route('/auth/google')
def google_auth():
    redirect_uri = url_for('naledi.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

# Callback route for Google OAuth
@naledi_bp.route('/auth/google/callback')
def google_callback():
    try:
        # Fetch token and user info from Google
        token = google.authorize_access_token()
        user_info = google.get('userinfo').json()
        print("Google Token:", token)
        print("Google User Info:", user_info)

        email = user_info.get('email')
        name = user_info.get('name')

        # Check if the user exists
        user = UserProfile.query.filter_by(email=email).first()

        if not user:
            # Create a new user if they don’t exist
            new_user = UserProfile(
                username=name,
                email=email,
                cellno='N/A',  # Default value for Google users
                user_password='N/A',  # Default value for Google users
                is_social_login_user=True,
                 user_type='spaza_user')   # since this for spaza owner the default user type is spaza_user
            
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash('login with Google successful!', category='success')
            return redirect(url_for('naledi.naledi_home'))
        else:
            flash('Logged in successfully!', category='success')

        # Log the user in
        login_user(user)
        return redirect(url_for('naledi.naledi_home'))  # Redirect to home page
    except Exception as e:
        print(f"Error during Google callback: {e}")
        flash('An error occurred during Google authentication.', category='error')
        return redirect(url_for('naledi.naledi_login'))

# Standard sign-up process for users without Google OAuth
@naledi_bp.route('/naledi_sign_up', methods=['GET', 'POST'])
def naledi_sign_up():

    if request.method == 'POST':
        first_name = request.form.get('firstName')
        email = request.form.get('email')
        cellno = request.form.get('cellno')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

            # Log input valuesç
        print(f"Sign-up form submitted: {first_name}, {email}, {cellno}")

        # Check if the username, email, or cell number already exists
        user = UserProfile.query.filter(
            (UserProfile.username == first_name) |
            (UserProfile.email == email) |
            (UserProfile.cellno == cellno)
             ).first()

        if user:
            print("Validation: User already exists.")
            flash('Username, email, or cell number already exists.', category='error')
            return redirect(url_for('naledi.naledi_sign_up'))
        elif not is_valid_email(email):
            flash('Invalid email format.', category='error')
            return redirect(url_for('naledi.naledi_sign_up'))
        elif not is_valid_cellno(cellno):
            flash('Provide only a valid South African cell number.', category='error')
            return redirect(url_for('naledi.naledi_sign_up'))
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
            return redirect(url_for('naledi.naledi_sign_up'))
        elif not is_valid_password(password1):
            flash('Password must include at least 8 characters, one uppercase letter, one lowercase letter, one digit, and one special character.', category='error') 
            return redirect(url_for('naledi.naledi_sign_up'))   
        else:
            # create a new user taking into account the social lig
            new_user = UserProfile(
            username=first_name,
                email=email,
                cellno=cellno,
                user_password=generate_password_hash(password1, method='pbkdf2:sha256'),
                is_social_login_user=False, # Explicitly set this to False
                user_type='spaza_user')

            print(f"New user object: {new_user}")

            try:
                db.session.add(new_user)
                db.session.commit()
                print("User added successfully.")
                login_user(new_user)
                flash('Account created and logged in successfully!', category='success')
                return redirect(url_for('naledi.naledi_home', user_id=new_user.id))
            except Exception as e:
                 db.session.rollback()
                 print(f"Database error: {e}")
                 flash('An error occurred while creating your account.', category='error')
                 return redirect(url_for('naledi.naledi_sign_up'))
            
    google_login_url = url_for('naledi.google_auth', _external=True) 
       
    #return redirect(url_for('naledi.naledi_home',google_login_url=google_login_url )) 
    #return render_template('naledi_sign_up.html',google_login_url=google_login_url ) 
    return render_template('naledi_sign_up.html', user=current_user, google_login_url=google_login_url)
   

"""@naledi_bp.route('/check_registration_status')
def check_registration_status():
    # Query the store registration status
    store = StoreDetails.query.filter_by(owner_id=current_user.id).first()

    print("checking store registration status")

    if store:
        if store.reg_status == 'registered':  # You can adjust this condition as per your criteria
            current_user.has_registered_store = True

        else:
            current_user.has_registered_store = False
    else:
        current_user.has_registered_store = False
    
    return redirect(url_for('naledi.naledi_home'))  # Or wherever you need to redirect """


@naledi_bp.route('/logout')
@login_required
def naledi_logout():
    logout_user()
    flash('Logged out successfully.', category='success')
    return redirect(url_for('naledi.naledi_login'))
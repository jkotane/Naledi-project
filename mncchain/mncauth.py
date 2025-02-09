import re
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from naledi.naledimodels import UserProfile, SpazaOwner, StoreDetails, RegistrationForm, RegistrationProgress, Lesee, FoodItems,HealthCompliance
from datetime import datetime
from naledi  import oauth
from naledi import db


mncauth  = Blueprint('mncauth', __name__)

google = oauth.google

# Validation helper function for email 
def is_valid_email(email):
    """Validate email format."""
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email)


# validation helper function for cell nunber 
def is_valid_cellno(cellno):
    """Validate South African cell number format."""
    regex = r'^(0|\+27)[6-8][0-9]{8}$'
    return re.match(regex, cellno)

# validation helper function for password

def is_valid_password(password):
    """
    Validate password format.
    Must include:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$'
    return re.match(regex, password)


# Validation helper function for email 
@mncauth.route('/mnclogin', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect to home if already logged in
        return redirect(url_for('mncview.mnchome'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if email is provided
        if not email:
            flash('Email is required.', category='error')
            return render_template("mnclogin.html", user=current_user)

        # Fetch user by email
        user = UserProfile.query.filter_by(email=email).first()

        if user:
            # Check if the user is a Google user
            if user.is_social_login_user:
                flash(
                    'This account uses Google Sign-In. Please use the "Sign in with Google" button.',
                    category='info')
                return render_template(
                    "mnclogin.html", user=current_user, is_social_login_user=True, google_login_url=url_for('mncauth.google_auth'))

            # Validate password for standard users
            if check_password_hash(user.user_password, password):
                login_user(user, remember=True)
                flash('Logged in successfully!', category='success')
                return redirect(url_for('mncview.home'))
            else:
                flash('Invalid password. Please try again.', category='error')
        else:
            flash('No account found with this email.', category='error')
            return redirect(url_for('mncauth.sign_up'))

    # Add the Google login URL for GET requests or after errors
    google_login_url = url_for('mncauth.google_auth', _external=True)

    # Render the login form
    return render_template(
        "mnclogin.html", user=current_user, is_social_login_user=False, google_login_url=google_login_url )
     

# Unified login/sign-up route
@mncauth.route('/auth/google')
def google_auth():
    redirect_uri = url_for('mnc.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

# Callback route for Google OAuth
@mncauth.route('/auth/google/callback')
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
                is_social_login_user=True
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash('login with Google successful!', category='success')
            return redirect(url_for('spachainview.home'))
        else:
            flash('Logged in successfully!', category='success')

        # Log the user in
        login_user(user)
        return redirect(url_for('spachainview.home'))  # Redirect to home page
    except Exception as e:
        print(f"Error during Google callback: {e}")
        flash('An error occurred during Google authentication.', category='error')
        return redirect(url_for('spachainauth.login'))


#standard logout route
@mncauth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', category='success')
    return redirect(url_for('spachainauth.login'))


# Standard sign-up process for users without Google OAuth
@mncauth.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
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
            return redirect(url_for('spachainauth.sign_up'))
        elif not is_valid_email(email):
            flash('Invalid email format.', category='error')
            return redirect(url_for('spachainauth.sign_up'))
        elif not is_valid_cellno(cellno):
            flash('Provide only a valid South African cell number.', category='error')
            return redirect(url_for('spachainauth.sign_up'))
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
            return redirect(url_for('spachainauth.sign_up'))
        elif not is_valid_password(password1):
            flash('Password must include at least 8 characters, one uppercase letter, one lowercase letter, one digit, and one special character.', category='error') 
            return redirect(url_for('spachainauth.sign_up'))   
        else:
            # create a new user taking into account the social lig
            new_user = UserProfile(
            username=first_name,
                email=email,
                cellno=cellno,
                user_password=generate_password_hash(password1, method='pbkdf2:sha256'),
                is_social_login_user=False  # Explicitly set this to False
            )

            print(f"New user object: {new_user}")

            try:
                db.session.add(new_user)
                db.session.commit()
                print("User added successfully.")
                flash('Account created successfully!', category='success')
                return redirect(url_for('spachainview.spusers', user_id=new_user.id))
            except Exception as e:
                 db.session.rollback()
                 print(f"Database error: {e}")
                 flash('An error occurred while creating your account.', category='error')
                 return redirect(url_for('spachainauth.sign_up'))
            
    # pass the google login url to the sign up page       
    google_login_url = url_for('spachainauth.google_sign_up', _external=True)  
    #return redirect(url_for('spachainview.home',google_login_url=google_login_url ))     
    return redirect(url_for('spachainview.home',google_login_url=google_login_url ))


# tracking the registratin progress 

@mncauth.route('/store-details/<int:owner_id>', methods=['GET', 'POST'])
@login_required
def store_details(owner_id):
    owner = SpazaOwner.query.get(owner_id)
    if not owner:
        flash('Owner details not found. Please complete owner details first.', category='error')
        return redirect(url_for('spachainauth.owner_details', user_id=current_user.id))

    if request.method == 'POST':
        store_name = request.form.get('store_name')
        location = request.form.get('location')
        address = request.form.get('address')

        # Add store details
        new_store = StoreDetails(
            owner_id=owner.id,
            store_name=store_name,
            location=location,
            address=address
        )
        db.session.add(new_store)
        db.session.commit()
        flash('Store details saved successfully!', category='success')
        return redirect(url_for('spachainview.home'))

    return render_template("store_details.html", owner=owner)




@mncauth.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    # Check if the user has a profile or services to display
    user_profile = UserProfile.query.get(current_user.id)
    
    if not user_profile:
        # If no profile exists, redirect to registration or an appropriate page
        flash("Please complete your profile to access services.", category="warning")
        return redirect(url_for('spachainauth.register'))

    # If the user has a profile, display their services or profile
    return render_template("services.html", user=user_profile)


# done for showing customer profile of an authenticated user
@mncauth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # Check if the user has a profile or services to display
    user_profile = UserProfile.query.get(current_user.id)
    print(f"User profile is : {user_profile}")
    
    if not user_profile:
        # If no profile exists, redirect to registration or an appropriate page
        flash("Please complete your profile to access services.", category="warning")
        return redirect(url_for('spachainauth.sign_up'))

    # If the user has a profile, display their services or profile
    #return render_template("sign_up.html", user=user_profile)
    return render_template("profile.html", user=user_profile)


# done for showing customer registration details
@mncauth.route('/reg_detail', methods=['GET', 'POST'])
@login_required
def reg_detail():
    # Check if the user has a profile or services to display
     if current_user.is_authenticated:
    
         registration = RegistrationForm.query.filter_by(user_id=current_user.id).first()

         current_user.registration_completed = bool(
            registration and registration.status in ['submitted', 'completed']
            )

         #return render_template("reg_detail.html", registration = registration,user=current_user)
         return render_template("reg_detail.html", registration=registration, user=current_user)

    # If the user has a profile, display their services or profile
     return render_template("home.html", user=current_user, registration=registration)

# Route to capture food list items for the store 
# the route to handle food items selected by the store owner
@mncauth.route('/food_items', methods=['GET', 'POST'])
@login_required
def food_items():
    if request.method == 'POST':
        # Capture selected food items
        selected_items = request.form.getlist('food_items')
        other_item = request.form.get('food_other')

        # Append "Other" item if specified
        if 'Other' in selected_items and other_item:
            selected_items.append(other_item)

        # Save food items to the database
        food_entry = FoodItems(
            user_id=current_user.id,
            selected_items=selected_items
        )
        try:
            db.session.add(food_entry)
            db.session.commit()
            flash('Food items saved successfully!', category='success')
            return redirect(url_for('spachainview.home',user=current_user))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving your food items.', category='error')
            print(f'Error: {e}')

    return render_template('food_items.html',user=current_user)

# The route for health compliance for the store owner
@mncauth.route('/store_health', methods=['GET', 'POST'])
@login_required
def store_health():
    user_id = current_user.id

    print(f"Health Compliance User ID: {user_id}")

    owner = SpazaOwner.query.filter_by(user_id=user_id).first()
    if not owner:
        flash('Owner details not found. Please complete owner details first.', category='error')
        return redirect(url_for('spachainauth.owner_details', user_id=current_user.id))

    print(f"health Owner ID: {owner.id}")
    if request.method == 'POST':
        # Capture form data
        sanitary_facilities = request.form.getlist('sanitary_facilities')
        cleaning_facilities = request.form.getlist('cleaning_facilities')
        handwashing_stations = request.form.getlist('handwashing_stations')
        waste_disposal = request.form.getlist('waste_disposal')
        food_handling = request.form.getlist('food_handling')
        food_storage = request.form.getlist('food_storage')
        food_preparation = request.form.getlist('food_preparation')
        food_prep_tools = request.form.getlist('food_prep_tools')
        employees = {
            "men": request.form.get('men-employed'),
            "women": request.form.get('women-employed'),
            "total": request.form.get('total-employed')
        }
    
        fields_completed = { "sanitary_facilities": sanitary_facilities, "cleaning_facilities": cleaning_facilities,
                            "handwashing_stations": handwashing_stations, "waste_disposal": waste_disposal,
                            "food_handling": food_handling, "food_storage": food_storage,
                            "food_preparation": food_preparation, "food_prep_tools": food_prep_tools, 
                              "employees": employees}
        
        print(f"Health Compliance data: {fields_completed}")
        
    
        # Create a new record in the HealthCompliance table
        health_compliance = HealthCompliance(
            user_id=current_user.id,
            sanitary_facilities=sanitary_facilities,
            cleaning_facilities=cleaning_facilities,
            handwashing_stations=handwashing_stations,
            waste_disposal=waste_disposal,
            food_handling=food_handling,
            food_storage=food_storage,
            food_preparation=food_preparation,
            food_prep_tools=food_prep_tools,
            employees=employees
        )

        try:
            db.session.add(health_compliance)
            db.session.commit()
            flash('Health compliance data saved successfully!', category='success')
            return redirect(url_for('spachainview.home',user=current_user))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving the data.', category='error')
            print(f'Error: {e}')
            return redirect(url_for('spachainview.health_compliance',owner=owner,user=current_user))

    return render_template('store_health.html',user=current_user)


@mncauth.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        cellno = request.form.get('cellno')
        address = request.form.get('address')

        # Validate inputs
        if not is_valid_cellno(cellno):
            flash('Invalid phone number.', category='error')
            return redirect(url_for('spachainauth.update_profile'))

        # Update the current user's profile
        current_user.username = name
        current_user.cellno = cellno
        owner = SpazaOwner.query.filter_by(user_id=current_user.id).first()
        if not owner:
            owner = SpazaOwner(user_id=current_user.id)
            db.session.add(owner)
        owner.address = address
        db.session.commit()

        flash('Profile updated successfully!', category='success')
        return redirect(url_for('spachainauth.profile'))

    # Render update form for GET request
    return render_template('update_profile.html', user=current_user)

# done for showing customer compliance tracking progress
@mncauth.route('/spusers', methods=['GET', 'POST'])
@login_required
def spusers():
    # Check if the user has a profile or services to display
    user_profile = UserProfile.query.get(current_user.id)
    
    if not user_profile:
        # If no profile exists, redirect to registration or an appropriate page
        flash("Please complete your profile to access services.", category="warning")
        return redirect(url_for('spachainauth.sign_up'))

    # If the user has a profile, display their services or profile
    return render_template("sign_up.html", user=user_profile)


# to be done to include services to subscribe to like compliance tracking
@mncauth.route('/services')
def services():
    #return render_template("services.html", user=current_user)
    return render_template("services.html", user=current_user)


# Route to displace compliance actions for the store owner
@mncauth.route('/compliance_actions')
@login_required
def compliance_actions():
    #return render_template("services.html", user=current_user)
    return render_template("compliance_actions.html", user=current_user)

# Route to display  health compliance actions for the store owner
"""@spachainauth.route('/compliance/store_health', methods=['GET', 'POST'])
@login_required
def store_health():
    #return render_template("services.html", user=current_user)
    return render_template("store_health.html", user=current_user)"""

# Route to display  fire safety compliance actions for the store owner
@mncauth.route('/compliance/store_fire', methods=['GET', 'POST'])
@login_required
def store_fire():
    #return render_template("services.html", user=current_user)
    return render_template("store_fire.html", user=current_user)

# Route to display  zoning by laws alignment for the store 
@mncauth.route('/compliance/store_zoning', methods=['GET', 'POST'])
@login_required
def store_zoning():
    #return render_template("services.html", user=current_user)
    return render_template("store_zoning.html", user=current_user)

# Route to display  electrical compliance  by laws alignment for the store 
@mncauth.route('/compliance/store_electrical', methods=['GET', 'POST'])
@login_required
def store_electrical():
    #return render_template("services.html", user=current_user)
    return render_template("store_electrical.html", user=current_user)

# Route to display  building plans alignment  by laws alignment for the store 
@mncauth.route('/compliance/store_building', methods=['GET', 'POST'])
@login_required
def store_building():
    #return render_template("services.html", user=current_user)
    return render_template("store_building.html", user=current_user)
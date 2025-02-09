import re
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .chainmodels import db, UserProfile, SpazaOwner, StoreDetails, RegistrationForm, RegistrationProgress, Lesee
from datetime import datetime
#from spazachain  import oauth


spachainauth = Blueprint('spachainauth', __name__)

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
@spachainauth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect to home if already logged in
        return redirect(url_for('spachainview.home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if email and password are provided
        if not email or not password:
            flash('Email and password are required.', category='error')
            return render_template("login.html", user=current_user)  # Ensure user context is passed

        # Fetch user by email
        user = UserProfile.query.filter_by(email=email).first()

        # Validate user and password
        if user:
            if check_password_hash(user.user_password, password):
                login_user(user, remember=True)
                flash('Logged in successfully!', category='success')
                return redirect(url_for('spachainview.home'))
            else:
                flash('Invalid password. Please try again.', category='error')
        else:
            flash('No account found with this email.', category='error')
            return redirect(url_for('spachainauth.sign_up'))
    

    # add the google login to the login page

    google_login_url = url_for('spachainauth.google_login', _external=True)
    # Render the login form for GET requests or after errors
    return render_template("login.html", user=current_user, google_login_url=google_login_url)

# Google OAuth login route
@spachainauth.route('/login/google')
def google_login():
    redirect_uri = url_for('spachainauth.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)
    
# Google OAuth callback route
@spachainauth.route('/login/google/callback')
def google_callback():
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()


    print("Token received:", token)
    print("User info received from Google:", user_info)

    # Extract user details
    email = user_info.get('email')
    name = user_info.get('name')

    # Check if the user exists in the database
    user = UserProfile.query.filter_by(email=email).first()

     # Check if the user exists
    user = UserProfile.query.filter_by(email=email).first()
    if user:
        flash('User already exists. Please log in.', category='info')
        return redirect(url_for('spachainauth.login'))
    
     # Create a new user with Google details
    new_user = UserProfile(
        username=name,  # Google users might not have a username, so using name
        email=email,
        user_password=None,  # Google users don't have a traditional password
        cellno=None  # No cell number for Google users by default
        )


    if not user:
        # If the user doesn't exist, create a new one
        user = UserProfile(email=email, name=name, user_password=None)  # No password for Google users
        db.session.add(user)
        db.session.commit()

    try:
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash('Sign-up with Google successful!', category='success')
        return redirect(url_for('spachainview.home')) 

    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        flash('An error occurred while signing up with Google.', category='error')
        return redirect(url_for('spachainauth.sign_up'))  

# Google OAuth sign-up route
@spachainauth.route('/sign_up/google')
def google_sign_up():
    print("Google sign-up initiated.")
    redirect_uri = url_for('spachainauth.google_sign_up_callback', _external=True)
    response = google.authorize_redirect(redirect_uri)
    print("Redirecting to Google OAuth with URI:", redirect_uri)
    #return oauth.google.authorize_redirect(redirect_uri)
    return response


@spachainauth.route('/sign_up/google/callback', methods=['GET'])
def google_sign_up_callback():
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.get('userinfo').json()

    # Extract user details
    email = user_info.get('email')
    name = user_info.get('name')

    # Check if the user exists in the database
    user = UserProfile.query.filter_by(email=email).first()
    if user:
        flash('User already exists. Please log in.', category='info')
        return redirect(url_for('spachainauth.login'))

    # Create a new user
    new_user = UserProfile(
        username=name,
        email=email,
        user_password=None,  # No password for Google users
        cellno=None
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash('Sign-up with Google successful!', category='success')
        return redirect(url_for('spachainview.home'))
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        flash('An error occurred while signing up with Google.', category='error')
        return redirect(url_for('spachainauth.sign_up'))


@spachainauth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', category='success')
    return redirect(url_for('spachainauth.login'))


@spachainauth.route('/sign_up', methods=['GET', 'POST'])
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
            # create new user

            new_user = UserProfile(
            username=first_name,
                email=email,
                cellno=cellno,
                user_password=generate_password_hash(password1, method='pbkdf2:sha256')
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
    return redirect(url_for('spachainview.sign_up',google_login_url=google_login_url ))

@spachainauth.route('/register', methods=['POST'])
@login_required
def register():
    if request.method == 'POST':
        user_id = current_user.id
        business_type = request.form.get('businessType')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        dob = request.form.get('dob')
        gender = request.form.get('gender')
        email = current_user.email
        cellno = current_user.cellno
        citizenship = request.form.get('citizenship')
        id_number = request.form.get('saId')
        street_address = request.form.get('streetAddress')
        address2 = request.form.get('address2')
        city = request.form.get('city')
        province = request.form.get('province')
        postal_code = request.form.get('postcode')
        district_mnc = request.form.get('municipality')


        # check if the user profile exsits:

        user_profile = UserProfile.query.filter_by(id=user_id).first()
        print(f"User profile User ID is: {user_id}")

        if not user_profile:
            flash('No user profile found. Please complete your profile first.', category='error')
            return redirect(url_for('spachainauth.sign_up'))
        else:
            user_id = user_profile.id
            email = user_profile.email
            cellno = user_profile.cellno    
            print(f" User ID is: {user_id}, email is: {email}, cell number is: {cellno}")
        
        try:
             # Ensure user profile exists

            existing_owner = SpazaOwner.query.filter_by(user_id=user_id).first()
            
            if not existing_owner:
                new_owner = SpazaOwner(
                    name=first_name.strip(),
                    surname=last_name.strip(),
                    email=email,
                    address=street_address.strip(),
                    said=id_number.strip() if id_number else 'N/A',
                    user_id=user_profile.id
                )
                db.session.add(new_owner)
                db.session.commit()
                flash('Spaza Owner registration successful!', category='success')
            else:
                flash('Spaza Owner already exists.', category='error')
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", category='error')
        
        # Validate required fields
        required_fields = {
            "Business Type": business_type, "First Name": first_name,
            "Last Name": last_name, "Date of Birth": dob, "Gender": gender,
            "ID Number": id_number if citizenship == 'South Africa' else 'N/A',
            "Street Address": street_address, "City": city,
            "Postal Code": postal_code, "Province": province, "District": district_mnc
        }

        print(f"Store details: {required_fields}")
        
        missing_fields = [field for field, value in required_fields.items() if not value]

        if missing_fields:
            flash(f"Please provide values for: {', '.join(missing_fields)}", category='error')
            return redirect(url_for('spachainauth.register'))

        # Check if registration already exists
        existing_registration = RegistrationForm.query.filter_by(user_id=user_id).first()
        if existing_registration:
            flash('You are already registered. Please update your details if needed.', category='info')
            return redirect(url_for('spachainview.home'))

        try:
            # Create new registration
            registration = RegistrationForm(
                user_id=user_id,
                business_type=business_type.strip(),
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                dob=dob.strip(),
                gender=gender.strip(),
                citizenship=citizenship.strip(),
                id_number=id_number.strip() if id_number else None,
                street_address=street_address.strip(),
                address2=address2.strip(),
                city=city.strip(),
                postal_code=postal_code.strip(),
                province=province.strip(),
                district_mnc=district_mnc.strip(),
                status="submitted"
            )
            db.session.add(registration)
            db.session.commit()
            flash('Main Registration successful!', category='success')
        except    Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", category='error')
            return redirect(url_for('spachainauth.register'))

        #return redirect(url_for('spachainview.home'))
            
    return redirect(url_for('spachainauth.register'))


# tracking the registratin progress 

@spachainauth.route('/update_progress', methods=['POST'])
@login_required
def update_progress():
    user_id = current_user.id
    form_id = request.form.get('form_id')
    section = request.form.get('section')  # e.g., "personal_details", "address"

    # Retrieve or create progress record
    progress = RegistrationProgress.query.filter_by(user_id=user_id, form_id=form_id).first()
    if not progress:
        progress = RegistrationProgress(user_id=user_id, form_id=form_id)
        db.session.add(progress)

    # Update the relevant section
    if section == "personal_details":
        progress.personal_details_completed = True
    elif section == "address":
        progress.address_details_completed = True
    elif section == "business_details":
        progress.business_details_completed = True

    # Check if all sections are completed
    if (
        progress.personal_details_completed and
        progress.address_details_completed and
        progress.business_details_completed
    ):
        progress.overall_status = "completed"

    try:
        db.session.commit()
        flash("Progress updated successfully!", category="success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating progress: {str(e)}", category="error")

    return redirect(url_for('spachainview.update_progress', user=current_user))



# registration form for the main owner - excludes the spaza shop detaiils and the leasee details
@spachainauth.route('/owner-details/<int:user_id>', methods=['GET', 'POST'])
@login_required
def owner_details(user_id):
    
    user = UserProfile.query.get(user_id)
    
    if not owner:
        flash('no owner details , ensure your registration is completed.', category='error')
        return redirect(url_for('spachainauth.sign_up'))

    if request.method == 'POST':
        id_number = request.form.get('id_number')
        address = request.form.get('address')
        lesee_name = request.form.get('lesee_name')
        store_name = request.form.get('store_name')

        # Check if owner details already exist for the user
        owner = SpazaOwner.query.filter_by(user_id=user.id).first()
        if user:
            flash('Owner details already exist.', category='error')
            return redirect(url_for('spachainauth.owner_details', owner_id=owner.id))

        # Add new owner details
        new_owner = SpazaOwner(
            user_id=user.id,
            id_number=id_number,
            address=address,
            lesee_name=lesee_name,
            store_name=store_name
        )
        db.session.add(new_owner)
        db.session.commit()
        flash('Owner details saved successfully!', category='success')
        return redirect(url_for('spachainauth.owner_details', owner_id=new_owner.id))

    return render_template("owner_details.html", user=user,owner=owner)

@spachainauth.route('/register_store', methods=['GET', 'POST'])
@login_required
def register_store():
    if request.method == 'POST':
        # Extract common store fields
        owner_id = current_user.id
        storetype = request.form.get('storetype')
        store_name = request.form.get('store_name')
        storevolume = request.form.get('storevolume')
        cicpno = request.form.get('cicpno')
        sarsno = request.form.get('sarsno')
        permitid = request.form.get('permitid')
        zonecertno = request.form.get('zonecertno')
        #compstatus = request.form.get('compstatus')
        ownershipstatus = request.form.get('ownershipstatus')
        storeaddress = request.form.get('storeaddress')
        city = request.form.get('city')
        postal_code = request.form.get('postal_code')
        province = request.form.get('province')
        district_mnc = request.form.get('municipality')

        # Extract Lessee fields if ownership status is Rented
        leseefname = request.form.get('leseefname')
        leseelname = request.form.get('leseelname')
        lesee_id = request.form.get('lesee_id')

        # Validate missing store fields
        required_fields = {
            "Store Type": storetype, "Store Name": store_name, "Store Volume": storevolume,
            "CIPC Number": cicpno, "SARS Number": sarsno, "Permit ID": permitid,
            "Zoning Certification": zonecertno, 
            "Ownership Status": ownershipstatus, "Store Address": storeaddress,
            "City": city, "Postal Code": postal_code, "Province": province, "District": district_mnc
        }

        print(f"Store details: {required_fields}")

        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            flash(f"Store related Data missing. Please provide values for: {', '.join(missing_fields)}", category='error')
            return redirect(url_for('spachainauth.register_store'))
         
        # Validate missing lessee fields
        required_lessee_fields = {"Lessee First Name": leseefname, "Lessee Last Name": leseelname, "Lessee ID": lesee_id}
        missing_lessee_fields = [field for field, value in required_lessee_fields.items() if not value]

        print(f"Lesee details: {required_lessee_fields}")
        
        # If ownership status is rented, lessee details are required
        """if ownershipstatus == "Rented":
            if missing_lessee_fields:
                flash(f"Please provide the Store Renter's details: {', '.join(missing_lessee_fields)}", category='error')
                return redirect(url_for('spachainauth.register_store'))"""



        # get the current user profile first
        user_id = current_user.id
        user_profile = UserProfile.query.get(user_id)
        if not user_profile:
            flash('No user profile found. Please complete your profile first.', category='error')
            return redirect(url_for('spachainauth.sign_up'))
        
        #step 2 : check for the owner details
        spaza_owner = SpazaOwner.query.filter_by(user_id=user_id).first()
        if not spaza_owner:
            flash('No owner details found. Please complete owner details first.', category='error')
            return redirect(url_for('spachainauth.owner_details', user_id=user_id))


        # Create store record
        try:
    
            store = StoreDetails(
                storetype=storetype.strip(),
                store_name=store_name.strip(),
                storevolume=storevolume.strip(),
                cicpno=cicpno.strip(),
                sarsno=sarsno.strip(),
                permitid=permitid.strip(),
                zonecertno=zonecertno.strip(),
                compstatus="draft status",
                ownershipstatus=ownershipstatus.strip(),
                storeaddress=storeaddress.strip(),
                city=city.strip(),
                postal_code=postal_code.strip(),
                province=province.strip(),
                district_mnc=district_mnc.strip(),
                owner_id=spaza_owner.id
            )
            db.session.add(store)
            db.session.commit() # commit to generate store.id
            flash("Store details saved successfully!", category="success")

        # Create Lessee record if ownership status is Rented
            if ownershipstatus == "Rented":
                if missing_lessee_fields:
                    flash(f"Please provide the Store Renter's details: {', '.join(missing_lessee_fields)}", category='error')
                    return redirect(url_for('spachainauth.register_store'))
                else:
                            new_lesee = Lesee(
                                leseefname=leseefname.strip(),
                                leseelname=leseelname.strip(),
                                lesee_id=lesee_id.strip(),
                                leseeemail="draft@example.com",
                                leseeaddress="draft address",
                                leseestoreid=store.id,  # Link to the newly created store
                                spazaownerid=spaza_owner.id  # Link to the spaza owner
                            )
                            db.session.add(new_lesee)
                            db.session.commit()      # create a new lessee record using the store.id             
                            flash("Lesee details saved successfully!", category="success")
                            
            return redirect(url_for('spachainview.home',user=current_user))
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving lessee details: {str(e)}", category="error")
            return redirect(url_for('spachainview.register_store',user=current_user))

    # Handle non-POST requests
    return redirect(url_for('spachainview.home', user=current_user))


# tracking the registratin progress 

@spachainauth.route('/store-details/<int:owner_id>', methods=['GET', 'POST'])
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

# upodate registration details in case soem details have been misssed or enetered wrong
@spachainauth.route('/update_registration', methods=['GET', 'POST'])
@login_required
def update_registration():
    registration = RegistrationForm.query.filter_by(user_id=current_user.id).first()

    # Identify missing fields
    missing_fields = []
    if not registration.first_name:
        missing_fields.append('firstName')
    if not registration.last_name:
        missing_fields.append('lastName')
    if not registration.dob:
        missing_fields.append('dob')
    if not registration.gender:
        missing_fields.append('gender')
    if not registration.id_number and registration.citizenship == 'South Africa':
        missing_fields.append('saId')
    if not registration.passport_number and registration.citizenship != 'South Africa':
        missing_fields.append('passportNo')
    if not registration.street_address:
        missing_fields.append('streetAddress')
    if not registration.city:
        missing_fields.append('city')
    if not registration.postal_code:
        missing_fields.append('postcode')
    if not registration.province:
        missing_fields.append('province')

    if request.method == 'POST':
        # Update only fields that are provided in the form
        if 'firstName' in request.form:
            registration.first_name = request.form.get('firstName')
        if 'lastName' in request.form:
            registration.last_name = request.form.get('lastName')
        if 'dob' in request.form:
            registration.dob = request.form.get('dob')
        if 'gender' in request.form:
            registration.gender = request.form.get('gender')
        if 'saId' in request.form and registration.citizenship == 'South Africa':
            registration.id_number = request.form.get('saId')
        if 'passportNo' in request.form and registration.citizenship != 'South Africa':
            registration.passport_number = request.form.get('passportNo')
        if 'streetAddress' in request.form:
            registration.street_address = request.form.get('streetAddress')
        if 'city' in request.form:
            registration.city = request.form.get('city')
        if 'postcode' in request.form:
            registration.postal_code = request.form.get('postcode')
        if 'province' in request.form:
            registration.province = request.form.get('province')

        # Update status based on completeness
        registration.status = 'completed' if not missing_fields else 'submitted'

        try:
            db.session.commit()
            flash('Registration details updated successfully!', category='success')
            return redirect(url_for('spachainauth.reg_detail'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating registration: {str(e)}', category='error')

    return render_template('update_registration.html', registration=registration, missing_fields=missing_fields)



@spachainauth.route('/home', methods=['GET', 'POST'])
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
@spachainauth.route('/profile', methods=['GET', 'POST'])
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
@spachainauth.route('/reg_detail', methods=['GET', 'POST'])
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

# done for showing customer compliance tracking progress
@spachainauth.route('/spusers', methods=['GET', 'POST'])
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
@spachainauth.route('/services')
def services():
    return render_template("services.html", user=current_user)
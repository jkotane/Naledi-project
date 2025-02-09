import re
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from naledi.naledimodels import UserProfile, SpazaOwner, StoreDetails, RegistrationForm, RegistrationProgress, Lesee, FoodItems,HealthCompliance,Document
from datetime import datetime
from naledi import oauth
from naledi import db, os
from google.cloud import storage
from naledi.utils import allowed_file, upload_to_gcs



spachainauth = Blueprint('spachainauth', __name__)

#google = oauth.google

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

# For users with a user profile , they can now register their spaza shop
# registration form for the main owner with a user profile  - excludes the spaza shop detaiils and the leasee details

@spachainauth.route('/register', methods=['GET', 'POST'])
@login_required
def spachainauth_register():
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
            return redirect(url_for('naledi.naledi_sign_up'))
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
            return redirect(url_for('spachainauth.spachainauth_register'))

        # Check if registration already exists
        existing_registration = RegistrationForm.query.filter_by(user_id=user_id).first()
        if existing_registration:
            flash('You are already registered. Please update your details if needed.', category='info')
            return redirect(url_for('naledi.naledi_home'))

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
            return redirect(url_for('naledi.naledi_home'))  # Redirect to home after successful registration
        except    Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", category='error')
            return redirect(url_for('spachainauth.spachainauth_register'))
    return render_template('spachainauth_register.html', title='Spaza Owner Registration')
   
# owner details for the spaza shop owner
@spachainauth.route('/owner-details/<int:user_id>', methods=['GET', 'POST'])
@login_required
def spachainauth_owner_details(user_id):
    # Get the user profile
    user = UserProfile.query.get(user_id)
    
    # If the user doesn't exist, redirect with an error message
    if not user:
        flash('No user profile exists. Ensure your registration is completed.', category='error')
        return redirect(url_for('naledi.naledi_sign_up'))

    # Initialize owner variable to None
    owner = None

    if request.method == 'POST':
        id_number = request.form.get('id_number')
        address = request.form.get('address')
        lesee_name = request.form.get('lesee_name')
        store_name = request.form.get('store_name')

        # Check if owner details already exist for the user
        owner = SpazaOwner.query.filter_by(user_id=user.id).first()
        if owner:
            flash('Owner details already exist.', category='error')
            return redirect(url_for('spachainauth.spachainauth_owner_details', user_id=owner.user_id))

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
        return redirect(url_for('spachainauth.spachainauth_owner_details', user_id=new_owner.user_id))

    # If it's a GET request, try to get the existing owner details
    owner = SpazaOwner.query.filter_by(id=user.id).first()

    # Render the template and pass the user and owner details
    return render_template("spachainauth_owner_details.html", user=user, owner=owner)





# route for the owner to be able to regisyte the store details
@spachainauth.route('/store', methods=['GET', 'POST'])
@login_required
def spachainauth_store():
    if request.method == 'POST':
        # Extract common store fields
        user_id = current_user.id
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
            return redirect(url_for('spachainauth.spachainauth_store'))
         
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
        user_profile = UserProfile.query.filter_by(id=user_id).first()
        if not user_profile:
            flash('No user profile found. Please complete your profile first.', category='error')
            return redirect(url_for('naledi.naledi_sign_up'))
        
        #step 2 : check for the owner details
        spaza_owner = SpazaOwner.query.filter_by(user_id=user_id).first()
        if not spaza_owner:
            flash('No owner details found. Please complete owner details first.', category='error')
            return redirect(url_for('spachainauth.spachainauth_owner_details', user_id=user_id))


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
                    return redirect(url_for('spachainauth.spachainauth_store'))
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
                            
            return redirect(url_for('naledi.naledi_home',user=current_user))
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving lessee details: {str(e)}", category="error")
            return redirect(url_for('spachainauth.spachainauth_store',user=current_user))

    # Handle non-POST requests
    return render_template('spachainauth_store.html', title='Spaza Owner Registration')


# Route to capture food list items for the store 
# the route to handle food items selected by the store owner
@spachainauth.route('/food_items', methods=['GET', 'POST'])
@login_required
def spachainauth_food_items():
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
            return redirect(url_for('naledi.naledi_home',user=current_user))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving your food items.', category='error')
            print(f'Error: {e}')

    return render_template('spachainauth_food_items.html',user=current_user)

# The route for health compliance for the store owner
@spachainauth.route('/health_self_check', methods=['GET', 'POST'])
@login_required
def spachainauth_health_self_check():
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
            return redirect(url_for('naledi.naledi_home',user=current_user))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving the data.', category='error')
            print(f'Error: {e}')
            return redirect(url_for('spachainauth.spachainauth_health_self_check',owner=owner,user=current_user))

    return render_template('spachainauth_health_self_check.html',user=current_user)


@spachainauth.route('/update_profile', methods=['GET', 'POST'])
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
    #return render_template("services.html", user=current_user)
    return render_template("services.html", user=current_user)


# Route to displace compliance actions for the store owner
@spachainauth.route('/compliance_actions')
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
@spachainauth.route('/compliance/fire', methods=['GET', 'POST'])
@login_required
def spachainauth_fire():
    #return render_template("services.html", user=current_user)
    return render_template("spachainauth_fire.html", user=current_user)

# Route to display  zoning by laws alignment for the store 
@spachainauth.route('/compliance/zoning', methods=['GET', 'POST'])
@login_required
def spachainauth_zoning():
    #return render_template("services.html", user=current_user)
    return render_template("spachainauth_zoning.html", user=current_user)

# Route to display  electrical compliance  by laws alignment for the store 
@spachainauth.route('/compliance/electrical', methods=['GET', 'POST'])
@login_required
def spachainauth_electrical():
    #return render_template("services.html", user=current_user)
    return render_template("spachainauth_electrical.html", user=current_user)

# Route to display  building plans alignment  by laws alignment for the store 
@spachainauth.route('/compliance/building', methods=['GET', 'POST'])
@login_required
def spachainauth_building():
    #return render_template("services.html", user=current_user)
    return render_template("spachainauth_building.html", user=current_user)



@spachainauth.route('/upload_docs', methods=['GET', 'POST'])
@login_required
def spachainauth_upload_docs():
    if request.method == 'POST':
        # List of document types and corresponding field names
        document_types = {
            'id_passport_visa': 'ID/Passport/Visa',
            'cipc': 'CIPC',
            'sars': 'SARS Tax Clearance',
            'permit': 'Permit',
            'building_plans': 'Building Plans'
        }

        # Loop through the document types and process the files
        for field_name, document_type in document_types.items():
            file = request.files.get(field_name)
            if file and allowed_file(file.filename):
                # Secure the filename to prevent path traversal
                filename = secure_filename(file.filename)
                destination_blob_name = f'{current_user.id}/{document_type}_{filename}'
                
                # Upload file to Google Cloud Storage
                file_url = upload_to_gcs(file, destination_blob_name)
                
                # Store the document in the database
                document = Document(
                    user_id=current_user.id,
                    document_type=document_type,
                    file_url=file_url,
                    filename=filename
                )
                db.session.add(document)
                db.session.commit()

        return 'Documents uploaded successfully!', 200

    return render_template('spachainauth_upload_docs.html')
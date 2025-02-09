# this route ( to be included in the spachainview looks for all key registration tables - Registration form , store , and documents uploaded to check any missing fields )

# For instance when the registration in submitted state - the user is redirected to the registration page with pre-filled data
# The user can now be able to register their store details
# after the register stoire details , thet can upload documents required for registration


@spachainauth.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    # Fetch existing registration
    registration = RegistrationForm.query.filter_by(user_id=current_user.id).first()

    # Determine missing fields
    required_fields = ['business_type', 'first_name', 'last_name', 'dob', 'gender', 'id_number', 'street_address', 'city', 'province', 'postal_code']
    missing_fields = [field for field in required_fields if not getattr(registration, field, None)]

    if request.method == 'POST':
        # Handle form submission
        # Update fields and commit to the database
        pass

    return render_template('register.html', user=current_user, registration=registration, missing_fields=missing_fields)
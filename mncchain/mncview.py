from flask import Blueprint, render_template, request, flash, jsonify, session
#from flask_login import login_required, current_user
from flask_login import login_user, logout_user, login_required, current_user
#from .modelspdb import Note
from naledi import db
import json
from naledi.naledimodels import SpazaOwner, RegistrationForm
from naledi import azure,official_login_manager  # Import the Azure OAuth instance
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from naledi.naledimodels import db, MncUser, MncDepartment, StoreDetails, Municipal,  HealthCompliance, UserProfile, SpazaOwner,Document
from functools import wraps
from naledi import official_login_manager, exchange_id_token_for_access_token, get_storage_client
from naledi.utils import fetch_data, generate_dashboard_layout, allowed_file, upload_to_gcs , generate_signed_url,get_access_token, generate_temporary_download_url
import dash
import dash_bootstrap_components as dbc
import plotly.express as px
from datetime import datetime, timedelta   
import os
from google.cloud import storage
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from sqlalchemy import select



mncview = Blueprint('mncview', __name__,url_prefix='/mncauth',template_folder='templates')  # ✅ Explicitly set template folder)


# decorator and official login manager 

# user loader define for the official user
@official_login_manager.user_loader
def load_official(user_id):
    """Loads an offcial  user from the database using Flask-Login."""
    print(f"🔹 Loading official User: {user_id}")

    # Query using mnc_user_id instead of default id
    user = MncUser.query.get(int(user_id))  # ✅ Use `id` instead of `mnc_user_id`
    
    print(f"🔹 User: {user}" )
    #print(f"🔹 is this an official ? : {user.is_official}" )


    if user and user.is_official:
        print(f"✅ official User Loaded: {user.mncfname} {user.mnclname}")
        return user

    print(f"🚨 User {user_id} is not an admin or does not exist!")
    return None  # Return None if not an admin


# ✅ Ensure only authenticated Offcials can access routes
def official_required(f):
    """Ensure the user is an authenticated admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"🔹 Checking admin access for user: {current_user}")

        print(f"🔹 User is authenticated: {current_user.is_authenticated}")

        if not current_user.is_authenticated:
            print("❌ User is NOT authenticated. Redirecting to login.")
            flash("Please log in first.", "warning")
            return redirect(url_for('mncauth.official_login'))

        if not isinstance(current_user, MncUser):
            print("❌ User is not an instance of MncUser.")
            flash("Unauthorized access.", "error")
            return redirect(url_for('mncauth.official_login'))

        if not current_user.is_official:
            print("❌ User is not an official.")
            flash("You do not have official  privileges.", "error")
            return redirect(url_for('mncauth.official_login'))

        print("✅ offcial  check passed.")
        return f(*args, **kwargs)
    
    return decorated_function



# generate a dashboard to show spazalytics
def create_dashboard(flask_app):
    """Initialize Dash inside the correct app context"""
    with flask_app.app_context():
        dashboard_app = dash.Dash(
            __name__,
            server=flask_app,
            url_base_pathname="/naledi/official/dashboard/",
            external_stylesheets=[dbc.themes.BOOTSTRAP]
        )
        dashboard_app.layout = generate_dashboard_layout()
        return dashboard_app




#route for the mncview  home
@mncview.route('/')
@login_required
@official_required
def official_view_home():
    """Official Home Page."""        
    print("Reached the official home route.")
    return render_template("official_view_home.html")




#route dashbiard route for the official
@mncview.route('/dashboard')
def official_dashboard():
    print("Reached the official dashboard route.")
    #return render_template("official_dashboard.html")   
    
    df = fetch_data()
  
    print("fetching the data")
     
    # Generate Dash components
    pie_chart = px.pie(df, names="ownershipstatus", title="Store Ownership Distribution").to_html()
    bar_chart = px.bar(df, x="city", y="store_name", title="Stores by City").to_html()
    
    # Convert DataFrame to HTML table
    data_table = df.to_html(classes="table table-striped table-bordered", index=False)

    return render_template(
        "official_dashboard.html",
        pie_chart=pie_chart,
        bar_chart=bar_chart,
        data_table=data_table,
        total_stores=len(df),
        compliant_stores=len(df[df["compstatus"] == "Compliant"]),
        non_compliant_stores=len(df[df["compstatus"] != "Compliant"]),
    )



# route for registered stores an official can view 
# ✅ Admin Dashboard
@mncview.route('/store_dashboard')
@login_required
@official_required
def official_store_dashboard():
    """Store dashboard: View Candidate stores."""
    print(f"🚀 Reached Store dashboard route! User: {current_user}")

    if not current_user.is_authenticated:
        print("❌ User is NOT authenticated. Redirecting to login.")
        return redirect(url_for('mncauth.official_login'))

    if not isinstance(current_user, MncUser):
        print("❌ Current user is NOT an instance of MncUser.")
        return redirect(url_for('mncauth.official_login'))

    if not current_user.is_official:
        print("❌ Current user is NOT an admin.")
        return redirect(url_for('mncauth.official_login'))

    official_municipality = current_user.municipalid

    if not official_municipality:
        flash("No official-municipality assignment data found.", "error")
        return redirect(url_for('mncauth.official_login'))

    # ✅ Fetch all active stores in the municipality
    active_stores = (
    db.session.query(
        StoreDetails.store_id,
        StoreDetails.store_name,
        HealthCompliance.compliance_status,
        HealthCompliance.updated_at
    )
    .outerjoin(HealthCompliance, StoreDetails.store_id == HealthCompliance.store_id)
    .join(Municipal, StoreDetails.district_mnc == Municipal.mncname)
    .filter(Municipal.id == official_municipality)
    .order_by(HealthCompliance.updated_at.desc())  # ✅ Ensure latest compliance is fetched
    .all()
     )  
    print(f"✅ Active Stores: {active_stores}")
    return render_template('official_store_dashboard.html',  active_stores=active_stores)


# route for the official to view the store details
@mncview.route('/health_review/<int:store_id>', methods=['GET', 'POST'])
@login_required
@official_required
def official_health_review(store_id):
    """Handles health compliance reviews for a store."""

    print(f"🚀 Reached official_health_review route! User: {current_user}")
    print(f"🔹 Store ID: {store_id}")

    store = StoreDetails.query.filter_by(store_id=store_id).first_or_404()

    # ✅ Fetch SpazaOwner record
    spaza_owner = SpazaOwner.query.filter_by(id=store.owner_id).first()

    if not spaza_owner:
      flash('Error: Store owner not found.', category='error')
      return redirect(url_for('mncview.official_store_dashboard'))   

    official_id = current_user.id  # ✅ Health Official ID
    user_id = spaza_owner.user_id  # ✅ Spaza Owner ID

    print(f"🔹 Store Health Review for Store ID: {store_id} by Official ID: {official_id}")


     # ✅ Check if the store has a review for the current 2-week cycle
    today = datetime.utcnow().date()
    cycle_start = today - timedelta(days=today.weekday() % 14)  # Start of the cycle
    cycle_end = cycle_start + timedelta(days=13)  # End of the cycle

    # check if a review already exists

    existing_review = HealthCompliance.query.filter(
        HealthCompliance.store_id == store.store_id,
        HealthCompliance.review_cycle_start == cycle_start
    ).first()

    if request.method == 'POST':
        # ✅ Capture form data (preserves your previous logic)
        sanitary_facilities = {"status": "compliant" if request.form.getlist('sanitary_facilities') else "pending",
                               "details": request.form.getlist('sanitary_facilities')}
        cleaning_facilities = {"status": "compliant" if request.form.getlist('cleaning_facilities') else "pending",
                               "details": request.form.getlist('cleaning_facilities')}
        handwashing_stations = {"status": "compliant" if request.form.getlist('handwashing_stations') else "pending",
                                "details": request.form.getlist('handwashing_stations')}
        waste_disposal = {"status": "compliant" if request.form.getlist('waste_disposal') else "pending",
                          "details": request.form.getlist('waste_disposal')}
        food_handling = {"status": "compliant" if request.form.getlist('food_handling') else "pending",
                         "details": request.form.getlist('food_handling')}
        food_storage = {"status": "compliant" if request.form.getlist('food_storage') else "pending",
                        "details": request.form.getlist('food_storage')}
        food_preparation = {"status": "compliant" if request.form.getlist('food_preparation') else "pending",
                            "details": request.form.getlist('food_preparation')}
        food_prep_tools = {"status": "compliant" if request.form.getlist('food_prep_tools') else "pending",
                           "details": request.form.getlist('food_prep_tools')}
        employees = {"men": request.form.get('men-employed'),
                     "women": request.form.get('women-employed'),
                     "total": request.form.get('total-employed')}


                    # ✅ Capture form data and check compliance for each category
            # ✅ Define All Compliance Categories
        compliance_categories = {
            "sanitary_facilities": request.form.getlist('sanitary_facilities'),
            "cleaning_facilities": request.form.getlist('cleaning_facilities'),
            "handwashing_stations": request.form.getlist('handwashing_stations'),
            "waste_disposal": request.form.getlist('waste_disposal'),
            "food_handling": request.form.getlist('food_handling'),
            "food_storage": request.form.getlist('food_storage'),
            "food_preparation": request.form.getlist('food_preparation'),
            "food_prep_tools": request.form.getlist('food_prep_tools'),
        }

        # ✅ Count total categories checked
        total_criteria = len(compliance_categories)
        compliant_count = sum(1 for category, details in compliance_categories.items() if details and len(details) > 0)

        # ✅ Calculate compliance percentage
        compliance_percentage = (compliant_count / total_criteria) * 100 if total_criteria > 0 else 0

        # ✅ Assign Compliance Status
        if compliance_percentage >= 90:
            compliance_status = "compliant"
        elif 70 <= compliance_percentage < 90:
            compliance_status = "amber"
        else:
            compliance_status = "non-compliant"

        print(f"✅ Compliance Score - Total Criteria: {total_criteria}, Percentage: {compliance_percentage:.2f}%")
        print(f"🔹 Compliance Status: {compliance_status}")


       # compliance_status = "compliant" if request.form.get('compliance_status') == 'compliant' else "non-compliant"

        if existing_review:
            # ✅ Update existing review
            existing_review.sanitary_facilities = sanitary_facilities
            existing_review.cleaning_facilities = cleaning_facilities
            existing_review.handwashing_stations = handwashing_stations
            existing_review.waste_disposal = waste_disposal
            existing_review.food_handling = food_handling
            existing_review.food_storage = food_storage
            existing_review.food_preparation = food_preparation
            existing_review.food_prep_tools = food_prep_tools
            existing_review.employees = employees
            existing_review.compliance_status = compliance_status
            existing_review.updated_at = datetime.utcnow()
        else:
            # ✅ Create new compliance entry for the cycle
            new_review = HealthCompliance(
                store_id=store.store_id,
                user_id=user_id,
                official_id=official_id,
                sanitary_facilities=sanitary_facilities,
                cleaning_facilities=cleaning_facilities,
                handwashing_stations=handwashing_stations,
                waste_disposal=waste_disposal,
                food_handling=food_handling,
                food_storage=food_storage,
                food_preparation=food_preparation,
                food_prep_tools=food_prep_tools,
                employees=employees,
                compliance_status=compliance_status,
                review_cycle_start=cycle_start,
                review_cycle_end=cycle_end
            )
            db.session.add(new_review)

        try:
            db.session.commit()
            flash('Health compliance review saved successfully!', category='success')
            return redirect(url_for('mncview.official_store_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving the data.', category='error')
            print(f'❌ Error: {e}')
            return redirect(url_for('mncview.official_health_review', store_id=store_id))

    return render_template('official_health_review.html', store=store, store_id=store_id, existing_review=existing_review)


# define the route for the health official to view / update health compliance for stores

@mncview.route('/view_compliance/<int:store_id>', methods=['GET'])
@login_required
@official_required
def view_compliance(store_id):
    """Load existing health compliance record for viewing/updating."""
    store = StoreDetails.query.filter_by(store_id=store_id).first_or_404()
    compliance_record = HealthCompliance.query.filter_by(store_id=store_id).order_by(HealthCompliance.created_at.desc()).first()

    if not compliance_record:
        flash("No compliance record found for this store.", "warning")
        return redirect(url_for('mncview.official_store_dashboard'))

    return render_template('offcial_view_compliance.html', store=store, compliance_record=compliance_record)


#define the route that verifies document status at store level

@mncview.route('/doc_verify_status', methods=['GET'])
@login_required
def doc_verify_status():
    """Fetches submitted and missing documents for the user."""
    
    document_types = {
        'id_passport_visa': 'ID/Passport/Visa [Required for all owners]',
        'proof_of_address': 'Proof of Address [ Utility Bill or Letter from Municipality]',
        'permit': 'Permit [Municipal Trading Permit]',
        'health_certificate': 'Certificate of Acceptability [ Issued by the Environmental Health Department of the municipality ]',
        'zoning_certificate': 'Zoning certificate or Special Consent Approval [To be obtained from the Municipality]',
        'building_plans': 'Building plans [Required for any building alterations or new buildings]',
        'title_deed_or_lease_agreement': 'Title deed or Lease Agreement',
        'banking_confirmation': 'Banking confirmation [ Proof of your South African Bank Account]',
        'cipc': 'CIPC [ Company Registration Certificate]',
        'sars': 'SARS Tax Clearance [ This can be obtained from SARS to show you don’t have outstanding taxes]',
        'affidavit': 'Affidavit [Proof that you are not engaged in illegal trading of goods]'   
    }

    # Fetch existing documents for the current user
    existing_docs = {doc.document_type for doc in Document.query.filter_by(user_id=current_user.id).all()}

    # Determine missing documents
    submitted_docs = {key: value for key, value in document_types.items() if key in existing_docs}
    missing_docs = {key: value for key, value in document_types.items() if key not in existing_docs}

    return jsonify({
        "submitted_documents": submitted_docs,
        "missing_documents": missing_docs
    })


# route for the official to view the documents uploaded by the store owner
""" @mncview.route('/official_view_documents/<int:store_id>', methods=['GET', 'POST'])
@login_required
@official_required
def official_view_documents(store_id):
    """ """Official Route: View, Inspect & Approve Uploaded Documents""" """"
    
    print(f"🚀 Official Document Review Route! User: {current_user}")
    print(f"🔹 Store ID: {store_id}")

    # Fetch store details
    store = StoreDetails.query.filter_by(store_id=store_id).first_or_404()
    
    # Ensure store owner exists
    spaza_owner = SpazaOwner.query.filter_by(id=store.owner_id).first()
    if not spaza_owner:
        flash("Store owner not found.", "error")
        return redirect(url_for("mncview.mncview.official_view_home")) 
    

    official_id = current_user.id
    user_id = spaza_owner.user_id

    # Fetch documents for this store owner
    documents = Document.query.filter_by(user_id=user_id).all()

    if request.method == 'POST':
        doc_id = request.form.get("doc_id")  # ✅ Get Document ID from the form
        action = request.form.get("action")  # ✅ Get Action (approve/reject)

        document = Document.query.get_or_404()
        if action == "approve":
            document.status = "approved"
            document.reviewed_by = current_user.id
            document.reviewed_at = datetime.utcnow()
            db.session.commit()
            flash("Document approved successfully!", "success")
        elif action == "reject":
            document.status = "rejected"
            document.reviewed_by = current_user.id
            document.reviewed_at = datetime.utcnow()
            db.session.commit()
            flash("Document rejected!", "warning")

        return redirect(url_for("mncview.official_view_documents"))

    # ✅ Fetch all uploaded documents (Pending Approval or Already Reviewed)
   # documents = Document.query.all()

    return render_template("official_view_documents.html",store=store, documents=documents)
    """

# route for registered stores's document dasgbard for officials
# ✅ Admin Dashboard
@mncview.route('/doc_dashboard')
@login_required
@official_required
def official_doc_dashboard():
    """Document dashboard: View Candidate stores documents uploaded"""
    print(f"🚀 Reached Store document dashboard route! User: {current_user}")

    #file_list = list_files_with_manual_token() previouslt used this function
    #file_list = list_files_with_token()

    file_list = list_files_for_officials()
    print("📂 Files in GCS bucket:", file_list)

    if not current_user.is_authenticated:
        print("❌ User is NOT authenticated. Redirecting to login.")
        return redirect(url_for('mncauth.official_login'))

    if not isinstance(current_user, MncUser):
        print("❌ Current user is NOT an instance of MncUser.")
        return redirect(url_for('mncauth.official_login'))

    if not current_user.is_official:
        print("❌ Current user is NOT an official.")
        return redirect(url_for('mncauth.official_login'))

    official_municipality = current_user.municipalid
    print(f"🔹 Official Municipality: {official_municipality}"  )

    if not official_municipality:
        flash("No official-municipality assignment data found.", "error")
        return redirect(url_for('mncauth.official_login'))

    # ✅ Fetch all stores with their documents, grouped by store
    store_documents = {}

    # Step 1: Subquery for provinces that exist in municipal
    """province_subquery = (
       select(StoreDetails.province)
       .join(Municipal, StoreDetails.province == Municipal.mncprov)
    .filter(Municipal.id == official_municipality)
     )
    """
    results = (
    db.session.query(
        StoreDetails.store_id,
        StoreDetails.store_name,
        Document.document_type,
        Document.uploaded_at.label("uploaded_at"),
        Document.reviewed_status,
        Document.approved_status,
        Document.file_url
    )
    .join(SpazaOwner, StoreDetails.owner_id == SpazaOwner.id)  # ✅ Join on owner_id → SpazaOwner.id
    .outerjoin(Document, SpazaOwner.user_id == Document.user_id)  # ✅ Join SpazaOwner → Document via user_id
    .join(Municipal, StoreDetails.district_mnc == Municipal.mncname)
    .filter(Municipal.id == official_municipality)
    .order_by(StoreDetails.store_id, Document.uploaded_at.desc())
    .all()
) 

    # Step 2: Main query with filter by provinces from the subquery
    """ results = (
        db.session.query(
            StoreDetails.store_id,
            StoreDetails.store_name,
            Document.document_type,
            Document.uploaded_at.label("uploaded_at"),
            Document.reviewed_status,
            Document.approved_status,
            Document.file_url
        )
        .join(Document, StoreDetails.owner_id == Document.user_id)
        .filter(StoreDetails.province.in_(province_subquery))  # ✅ now properly formed
        .order_by(StoreDetails.store_id, Document.uploaded_at.desc())
        .all()
     )
    """


    # ✅ Process query results and group by store

    file_list = list_files_for_officials() # ✅ Now pass it here   
    
    for row in results:
        store_id = row.store_id
        store_name = row.store_name

        # Initialize list for each store if not exists
        if store_id not in store_documents:
            store_documents[store_id] = {
                "store_name": store_name,
                "documents": []  # List of docs for this store
            }

    # if this does not work - the previous sort of working route will be used and the view access will have to be fixed
    file_url = None
    if row.file_url:
        bucket_name = os.getenv("GCS_BUCKET_NAME").replace("gs://", "")
         # Detect if row.file_url is a URL or a blob path
       # if row.file_url.startswith("http"):
        # Already a URL – use as-is (but append token if needed)


        id_token = session.get("azure_id_token")
        if not id_token:
          raise Exception("No ID token in session.")

        access_token = exchange_id_token_for_access_token(id_token)

        if "storage.googleapis.com" in row.file_url:     # assume its a full URL , extract the blob path
           
            try: 
               blob_name = row.file_url.split(f"{bucket_name}/")[-1]  # Extract blob path from URL
            except IndexError as e:  
                print(f"⚠️ Could not extract blob_name from URL: {row.file_url}")
                blob_name = None 
        else:
        # Not a URL – assume blob path like "43/filename"
          blob_name = row.file_url


        if blob_name and blob_name in file_list:
           print(f"✅ Match found in GCS for blob: {blob_name}")
        else:
          print(f"❌ Blob {blob_name} not found in GCS file list.")
   

        # only build URL if the blobname is valid
        if blob_name:
           file_url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}?access_token={access_token}"
           print(f"✅ Final File URL: {file_url}")
        else:
            file_url = None


        """ id_token = session.get("azure_id_token")
        if not id_token:
          raise Exception("No ID token in session.")

        access_token = exchange_id_token_for_access_token(id_token) """

            # ✅ Manual signed URL
       # file_url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}?access_token={access_token}"
        print(f"✅ file URLs: {file_url}")
        
        # Append document details
        store_documents[store_id]["documents"].append({
            "document_type": row.document_type,
            "uploaded_at": row.uploaded_at,
            "reviewed_status": row.reviewed_status,
            "approved_status": row.approved_status,
            "file_url": file_url  # Use the temporary download URL
        })

    print(f"✅ file URLs: {file_url}")

    return render_template('official_doc_dashboard.html', store_documents=store_documents)

@mncview.route('/update_doc_status', methods=['POST'])
@login_required
@official_required
def update_doc_status():
    file_url = request.form.get('file_url')
    doc_type = request.form.get('doc_type')
    action = request.form.get('action')  # 'approve' or 'reject'

    document = Document.query.filter_by(file_url=file_url, document_type=doc_type).first()
    if document:
        if action == 'approve':
            document.approved_status = 'approved'
            document.reviewed_status = 'reviewed'
        elif action == 'reject':
            document.approved_status = 'rejected'
            document.reviewed_status = 'reviewed'
        db.session.commit()
        flash(f'Document {action}d successfully.', 'success')
    else:
        flash('Document not found.', 'error')

    return redirect(url_for('mncview.official_doc_dashboard'))


# define the route to list files in the buckeet

@mncview.route('/list-files')
def list_files():
    bucket_name = os.getenv("GCS_BUCKET_NAME").replace("gs://", "")  # Remove gs:// prefix
    storage_client = get_storage_client()  # Use the shared client
    blobs = storage_client.list_blobs(bucket_name)
    files = [blob.name for blob in blobs]
    return jsonify({"files": files})


def list_files_with_token(access_token):
    """List files in a GCS bucket using a valid access token (STS exchange)."""
    creds = Credentials(token=access_token)

    # ❌ DO NOT refresh this credential – just use it
    storage_client = storage.Client(credentials=creds)

    bucket_name = os.getenv("GCS_BUCKET_NAME").replace("gs://", "")
    blobs = storage_client.list_blobs(bucket_name)
    files = [blob.name for blob in blobs]
    return files

def list_files_for_officials():
    """List ALL files in GCS bucket using token from Azure session."""
    id_token = session.get("azure_id_token")
    if not id_token:
        raise Exception("No ID token in session.")

    access_token = exchange_id_token_for_access_token(id_token)
    creds = Credentials(token=access_token)
    storage_client = storage.Client(credentials=creds)

    bucket_name = os.getenv("GCS_BUCKET_NAME").replace("gs://", "")
    bucket = storage_client.bucket(bucket_name)

    print(f"📂 Accessing bucket: {bucket_name}")

    # List ALL blobs in the bucket (ensure pagination handled)
    blobs_iterator = storage_client.list_blobs(bucket)
    file_list = []
    for blob in blobs_iterator:
        print(f"📁 Found blob: {blob.name}")
        file_list.append(blob.name)

    print(f"📂 Total files found: {len(file_list)}")
    return file_list




# naledi/utils.py
import re
from google.cloud import storage
from google.auth.transport.requests import Request
from google.auth import identity_pool
from google.auth import credentials
from datetime import timedelta

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}



# Validation helper function for email
def is_valid_email(email):
    """Validate email format."""
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email)


# Validation helper function for cell number
def is_valid_cellno(cellno):
    """Validate South African cell number format."""
    regex = r'^(0|\+27)[6-8][0-9]{8}$'
    return re.match(regex, cellno)


# Validation helper function for password
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

# heloer file to upload documets to Google cloud storage
def upload_to_gcs(file, destination_blob_name):
    """Uploads a file to Google Cloud Storage and returns the file URL."""
    # Initialize a GCS client
    storage_client = storage.Client()

    # The name of your GCS bucket
    bucket_name = 'your-gcs-bucket-name'  # Replace this with your actual bucket name
    bucket = storage_client.bucket(bucket_name)

    # Upload the file to GCS
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(file)

    # Get the public URL of the file
    file_url = blob.public_url
    return file_url

def allowed_file(filename):
    """
    Check if a file is allowed based on its extension.
    
    :param filename: The name of the file
    :param allowed_extensions: A set of allowed file extensions
    :return: True if file extension is allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# utils.py (if you are using this for GCS upload)
from google.cloud import storage

def upload_to_gcs(file, destination_blob_name):
    """Uploads a file to Google Cloud Storage and returns a signed URL for authenticated users."""
    
    # Authenticate with Workload Identity or ADC
    storage_client = storage.Client()

    bucket_name = "spaza-docs-bucket"  # Change to your bucket name
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Upload the file
    blob.upload_from_file(file)

    # Generate a signed URL (Valid for 15 minutes)
    #signed_url = blob.generate_signed_url(expiration=timedelta(minutes=15))

    return f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"

def get_storage_client():
    """
    Get a Google Cloud Storage client using Workload Identity Federation.
    """

    # Define the identity pool and provider you set up in Google Cloud
    identity_pool_id = 'your-identity-pool-id'
    provider_id = 'your-identity-provider-id'

    # Federation with Workload Identity Federation (without using service account key)
    credentials, project = identity_pool.Credentials.from_identity_pool(
        identity_pool_id, provider_id
    )

    # Initialize the GCS client with federated credentials
    storage_client = storage.Client(credentials=credentials, project=project)
    
    return storage_client
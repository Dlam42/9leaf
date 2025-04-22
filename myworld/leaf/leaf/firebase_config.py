import firebase_admin
from firebase_admin import credentials, firestore, storage # Import storage
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use the specific storage bucket name provided
storage_bucket_url = "leaf-3578c.firebasestorage.app"

# Initialize Firebase Admin with service account
cred = credentials.Certificate({
    "type": os.getenv('FIREBASE_TYPE'),
    "project_id": os.getenv('FIREBASE_PROJECT_ID'),
    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
    "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n') if os.getenv('FIREBASE_PRIVATE_KEY') else None,
    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
    "client_id": os.getenv('FIREBASE_CLIENT_ID'),
    "auth_uri": os.getenv('FIREBASE_AUTH_URI'),
    "token_uri": os.getenv('FIREBASE_TOKEN_URI'),
    "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL'),
    "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL')
})

# Initialize the app with Firestore and Storage
if storage_bucket_url:
    firebase_admin.initialize_app(cred, {
        'storageBucket': storage_bucket_url
    })
    print(f"Firebase Admin initialized with Storage Bucket: {storage_bucket_url}")
else:
    firebase_admin.initialize_app(cred)
    print("Firebase Admin initialized (Storage Bucket URL not provided)")

# Get Firestore database instance
db = firestore.client()

# Get Storage bucket instance (optional, can also get it dynamically via storage.bucket())
# bucket = storage.bucket() # You can get the bucket instance here if needed globally
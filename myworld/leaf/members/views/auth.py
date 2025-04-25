# Authentication related views (register, login, logout)
import os
import uuid
import threading
from django.shortcuts import render, redirect
from django.template import loader
from django.contrib import messages
from firebase_admin import auth, firestore, storage
import requests
from dotenv import load_dotenv

from leaf.firebase_config import db
# Import the background geocoding function from utils
from .utils import geocode_and_update_user 

# Load environment variables
load_dotenv()

# Firebase configuration from environment variables
FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')
# FIREBASE_AUTH_DOMAIN = os.getenv('FIREBASE_AUTH_DOMAIN') # Not directly used in these views, can be removed if not needed elsewhere

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["pwd"]
        password_2 = request.POST["pwd2"]
        email = request.POST["email"]
        phone_num = request.POST["phone_num"]
        address = request.POST["address"]
        city = request.POST["city"]
        state = request.POST["state"]
        unit_num = request.POST["unit_num"]
        zip_code = request.POST["zip_code"]
        profile_image = request.FILES.get("profile_image") # Get the uploaded file

        if password != password_2:
            messages.info(request, 'Password not matching...')
            return redirect("register")

        user = None # Initialize user to None
        try:
            print("Starting user registration process...")
            # Create user in Firebase Auth
            user = auth.create_user(
                email=email,
                password=password,
                display_name=username
            )
            print(f"Firebase Auth user created with UID: {user.uid}")

            profile_image_url = None # Default profile image URL
            if profile_image:
                try:
                    print(f"Attempting to upload profile image for user {user.uid}")
                    # Get the default storage bucket
                    bucket = storage.bucket() # Ensure your firebase_config initializes storage
                    # Create a unique filename using UUID and preserve extension
                    file_extension = os.path.splitext(profile_image.name)[1]
                    blob_name = f"profile_images/{user.uid}/{uuid.uuid4()}{file_extension}"
                    blob = bucket.blob(blob_name)

                    # Upload the file
                    blob.upload_from_file(profile_image, content_type=profile_image.content_type)

                    # Make the blob publicly viewable (adjust permissions as needed)
                    blob.make_public()

                    # Get the public URL
                    profile_image_url = blob.public_url
                    print(f"Profile image uploaded successfully: {profile_image_url}")
                except Exception as storage_e:
                    print(f"Error uploading profile image: {storage_e}")
                    # Decide if this error should prevent registration or just skip the image
                    # For now, we'll proceed without the image URL
                    profile_image_url = None # Reset to None on error

            # --- Start: Modified Section ---
            # Set default geo_location immediately
            default_geo_location = "0.0/0.0"
            print(f"Using default geo_location initially: {default_geo_location}")

            # Store initial user data in Firestore (without blocking for geocoding)
            user_data = {
                'username': username,
                'email': email,
                'phone_num': phone_num,
                'address': address,
                'city': city,
                'state': state,
                'geo_location': default_geo_location, # Use default for now
                'unit_apt_num': unit_num,
                'zip_code': zip_code,
                'profile_image_url': profile_image_url, # Add profile image URL
                'payment_option': "Paypal",
                'identification': "none",
                'dark_mode': False,
                'language': "English",
                'created_at': firestore.SERVER_TIMESTAMP
            }

            print("Attempting to save initial user data to Firestore...")
            db.collection('users').document(user.uid).set(user_data)
            print("Initial user data successfully saved to Firestore")

            # Start background task for geocoding
            geocoding_thread = threading.Thread(
                target=geocode_and_update_user,
                args=(user.uid, address, city, state)
            )
            geocoding_thread.start()
            print(f"Started background geocoding thread for user {user.uid}")

            # --- End: Modified Section ---

            # Set session variables
            request.session["user_id"] = user.uid
            request.session["username"] = username
            request.session["is_authenticated"] = True
            request.session["profile_image_url"] = profile_image_url
            
            print("Registration complete, redirecting to dashboard")
            return redirect('dashboard')
                
        # Keep the outer exception handling for Auth creation or initial Firestore save errors
        except Exception as e:
            print(f"Registration error: {str(e)}")
            # Attempt to delete Auth user if Firestore save failed or other critical error occurred
            if user: # Check if user object was created
                 try:
                     auth.delete_user(user.uid)
                     print(f"Deleted Auth user {user.uid} due to registration error: {str(e)}")
                 except Exception as delete_e:
                     print(f"Failed to delete Auth user {user.uid} after registration error: {str(delete_e)}")

            messages.info(request, f"Registration failed: {str(e)}")
            return redirect('register')

    # Get site settings for logo
    site_settings = {}
    try:
        site_settings_ref = db.collection('site_settings').document('general').get()
        if site_settings_ref.exists:
            site_settings = site_settings_ref.to_dict()
    except Exception as e:
        print(f"Error retrieving site settings: {e}")
        
    return render(request, "register.html", {
        'site_settings': site_settings
    })

def login_page(request):
    # Get site settings for logo
    site_settings = {}
    try:
        site_settings_ref = db.collection('site_settings').document('general').get()
        if site_settings_ref.exists:
            site_settings = site_settings_ref.to_dict()
    except Exception as e:
        print(f"Error retrieving site settings: {e}")
        
    return render(request, "login.html", {
        'site_settings': site_settings
    })

def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("pwd")
        
        try:
            # Query Firestore to find user by username using the filter keyword
            users_ref = db.collection('users')
            # Updated query using filter keyword argument
            query = users_ref.where(filter=firestore.FieldFilter('username', '==', username)).limit(1).get()
            
            if not query:
                messages.info(request, 'Invalid username or password')
                return redirect("login_page")
            
            user_doc = query[0]
            user_data = user_doc.to_dict()
            email = user_data.get('email')
            
            try:
                # Sign in with email/password using Firebase REST API
                sign_in_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
                sign_in_data = {
                    "email": email,
                    "password": password,
                    "returnSecureToken": True
                }
                response = requests.post(sign_in_url, json=sign_in_data)
                response_data = response.json()
                
                if response.status_code == 200:
                    # Successfully signed in
                    user = auth.get_user(user_doc.id)
                    
                    # Update last sign in time in Firestore
                    current_time = firestore.SERVER_TIMESTAMP
                    user_ref = db.collection('users').document(user.uid)
                    user_ref.update({
                        'last_sign_in': current_time,
                        'sign_in_count': firestore.Increment(1)
                    })
                    
                    # --- Corrected Session Setting ---
                    # Use the username from Firestore data, not the form input
                    db_username = user_data.get('username', username) # Fallback to input username if not in DB
                    
                    # Store user info in session
                    request.session["user_id"] = user.uid
                    request.session["username"] = db_username # Use the username from the database
                    request.session["is_authenticated"] = True
                    request.session["profile_image_url"] = user_data.get('profile_image_url', '/static/default_profile.png')
                    
                    # Check if user is an admin and set session variable
                    request.session["is_admin"] = user_data.get('is_admin', False)

                    print(f"Login successful for user: {db_username}, redirecting to dashboard")
                    return redirect("dashboard")
                else:
                    error_message = response_data.get('error', {}).get('message', 'Invalid credentials')
                    print(f"Firebase Auth sign-in failed: {response_data}")
                    messages.info(request, error_message)
                    return redirect("login_page")
                
            except Exception as e:
                print(f"Firebase Auth error: {str(e)}")
                messages.info(request, 'Invalid credentials')
                return redirect("login_page")
            
        except Exception as e:
            print(f"Login error: {str(e)}")
            messages.info(request, 'Invalid credentials')
            return redirect("login_page")
    
    return render(request, "login.html")

def logout(request):
    request.session.flush()
    return redirect('login_page')

# Add change password functionality
def change_password(request):
    """Allow users to change their password"""
    if not request.session.get("is_authenticated"):
        return redirect('login_page')
        
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "User session not found. Please log in again.")
        return redirect('login_page')
        
    # Get site settings for logo
    site_settings = {}
    try:
        site_settings_ref = db.collection('site_settings').document('general').get()
        if site_settings_ref.exists:
            site_settings = site_settings_ref.to_dict()
    except Exception as e:
        print(f"Error retrieving site settings: {e}")
        
    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        
        # Basic validation
        if not current_password or not new_password or not confirm_password:
            messages.error(request, "All fields are required.")
            return render(request, "change_password.html")
            
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return render(request, "change_password.html")
            
        try:
            # Get user email from Firestore
            user_doc = db.collection('users').document(user_id).get()
            if not user_doc.exists:
                messages.error(request, "User not found. Please log in again.")
                request.session.flush()
                return redirect('login_page')
                
            user_data = user_doc.to_dict()
            email = user_data.get('email')
            
            # Verify current password using Firebase Auth REST API
            sign_in_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
            sign_in_data = {
                "email": email,
                "password": current_password,
                "returnSecureToken": True
            }
            
            response = requests.post(sign_in_url, json=sign_in_data)
            
            if response.status_code != 200:
                messages.error(request, "Current password is incorrect.")
                return render(request, "change_password.html")
                
            # Change password with Firebase Auth
            update_url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={FIREBASE_API_KEY}"
            id_token = response.json().get('idToken')
            
            update_data = {
                "idToken": id_token,
                "password": new_password,
                "returnSecureToken": True
            }
            
            update_response = requests.post(update_url, json=update_data)
            
            if update_response.status_code != 200:
                error_message = update_response.json().get('error', {}).get('message', 'Password change failed')
                messages.error(request, f"Error changing password: {error_message}")
                return render(request, "change_password.html")
                
            messages.success(request, "Password changed successfully! Please log in with your new password.")
            request.session.flush()  # Log the user out for security
            return redirect('login_page')
            
        except Exception as e:
            print(f"Password change error: {str(e)}")
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, "change_password.html")
    
    return render(request, "change_password.html")
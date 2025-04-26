# Utility functions 
import re
import threading
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut # Import the specific timeout exception
from firebase_admin import auth, firestore
from leaf.firebase_config import db
from datetime import datetime, timezone, timedelta # Import timezone and timedelta

# Define the background geocoding function
def geocode_and_update_user(user_id, address, city, state):
    try:
        print(f"Background geocoding started for user: {user_id}")
        geolocator = Nominatim(user_agent="background_geo_coding", timeout=10)
        full_address = f"{address}, {city}, {state}"
        location = None

        try:
            # First attempt with the full address
            print(f"Attempting geocode with full address: {full_address}")
            location = geolocator.geocode(full_address)
        except GeocoderTimedOut:
            print(f"Geocoding timed out for full address: {full_address}")
            # Allow proceeding to simplified address attempt or handle as needed
        except Exception as e:
            print(f"Error geocoding full address {full_address}: {str(e)}")

        # If the first attempt failed, try simplifying the address
        if not location:
            # Basic simplification: remove common unit designators and numbers after them
            # This is a simple example; more robust parsing might be needed for edge cases
            simplified_address_str = re.sub(r'(apt|unit|suite|ste|#|spc).*$', '', address, flags=re.IGNORECASE).strip()
            # Remove trailing commas or spaces if any resulted from the substitution
            simplified_address_str = simplified_address_str.rstrip(', ')
            
            if simplified_address_str != address: # Only try again if simplification changed the address
                simplified_full_address = f"{simplified_address_str}, {city}, {state}"
                print(f"Full address failed, attempting geocode with simplified address: {simplified_full_address}")
                try:
                    location = geolocator.geocode(simplified_full_address)
                except GeocoderTimedOut:
                     print(f"Geocoding timed out for simplified address: {simplified_full_address}")
                except Exception as e:
                    print(f"Error geocoding simplified address {simplified_full_address}: {str(e)}")
            else:
                print("Address simplification did not change the address, skipping second attempt.")

        # Update Firestore if a location was found
        if location:
            geo_location = f"{location.latitude}/{location.longitude}"
            print(f"Background geocoding successful for {user_id}: {geo_location}")
            user_ref = db.collection('users').document(user_id)
            user_ref.update({'geo_location': geo_location})
            print(f"Firestore updated for user {user_id} with new geo_location.")
        else:
            print(f"Background geocoding failed for {user_id}: Address not found or geocoding error for address: {full_address}")
            # Optionally update Firestore with a specific 'failed' status or leave default

    # Catch timeout specifically for the whole process if needed, though inner catches handle specific attempts
    except GeocoderTimedOut:
        print(f"Background geocoding process timed out for user {user_id}")
    except Exception as e:
        print(f"Error during background geocoding process for user {user_id}: {str(e)}")


# Function to create a dummy admin account for demonstration purposes
def create_admin_account():
    """Create a dummy admin account with the credentials leaf_admin:admin123"""
    try:
        # Check if admin user already exists by username
        users_ref = db.collection('users')
        query = users_ref.where(filter=firestore.FieldFilter('username', '==', 'leaf_admin')).limit(1).get()
        
        if query:
            print("Admin account already exists")
            # Make sure it's marked as admin if it exists
            user_doc = query[0]
            user_ref = db.collection('users').document(user_doc.id)
            user_ref.update({'is_admin': True})
            
            # Make sure a messages collection exists (won't create duplicate data)
            messages_ref = db.collection('messages')
            messages_list = messages_ref.limit(1).get()
            if not messages_list:
                print("Creating example message")
                # Create a welcome message for the admin
                welcome_message = {
                    'sender_id': 'system',
                    'sender_name': 'Leaf System',
                    'receiver_id': user_doc.id,
                    'receiver_name': 'leaf_admin',
                    'subject': 'Welcome to Leaf Message System',
                    'content': 'This is a sample message. Users can now communicate with admins through this messaging system.',
                    'timestamp': firestore.SERVER_TIMESTAMP,
                    'is_read': False
                }
                messages_ref.add(welcome_message)
                
            return
        
        # Create admin user in Firebase Auth
        user = auth.create_user(
            email="admin@leaf.com",
            password="admin123",
            display_name="leaf_admin"
        )
        
        # Store admin user data in Firestore with is_admin=True
        user_data = {
            'username': 'leaf_admin',
            'email': 'admin@leaf.com',
            'phone_num': '555-ADMIN',
            'address': 'Admin Building',
            'city': 'Admin City',
            'state': 'Admin State',
            'geo_location': '0.0/0.0',
            'unit_apt_num': 'Admin',
            'zip_code': '00000',
            'profile_image_url': None,
            'payment_option': 'Paypal',
            'identification': 'admin',
            'dark_mode': False,
            'language': 'English',
            'is_admin': True,
            'created_at': firestore.SERVER_TIMESTAMP
        }
        
        db.collection('users').document(user.uid).set(user_data)
        print("Admin account created successfully")
        
        # Create a welcome message for the admin
        welcome_message = {
            'sender_id': 'system',
            'sender_name': 'Leaf System',
            'receiver_id': user.uid,
            'receiver_name': 'leaf_admin',
            'subject': 'Welcome to Leaf Message System',
            'content': 'This is a sample message. Users can now communicate with admins through this messaging system.',
            'timestamp': firestore.SERVER_TIMESTAMP,
            'is_read': False
        }
        db.collection('messages').add(welcome_message)
        
    except Exception as e:
        print(f"Error creating admin account: {str(e)}")

# Call this function to create the dummy admin account when the server starts
# NOTE: This call should be moved to the app's startup logic (e.g., apps.py ready() method or manage.py)
# For now, we leave it here but commented out, as calling it directly in views/utils.py might have side effects.
# create_admin_account() 
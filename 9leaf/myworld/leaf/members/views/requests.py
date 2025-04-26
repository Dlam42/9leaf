# Job request views
import random
import string
from django.shortcuts import render, redirect
from django.contrib import messages
from firebase_admin import firestore

from members.custom_wrappers import is_logged_in
from leaf.firebase_config import db
# Import the geocoding service
from members.geocoding_utils import geocoding_service

def generate_job_number():
    """Generate a unique job number in format LF-XXXXX"""
    chars = string.ascii_uppercase + string.digits
    while True:
        job_number = 'LF-' + ''.join(random.choice(chars) for _ in range(5))
        
        # Check if this job number already exists in Firestore
        existing = db.collection('requests').where(filter=firestore.FieldFilter('job_number', '==', job_number)).limit(1).get()
        if not existing:
            return job_number

@is_logged_in
def new_request(request):
    if request.method == 'POST':
        user_id = request.session.get("user_id")
        job_title = request.POST.get("job_title")  # Get the job title
        description = request.POST.get("job_description")
        address = request.POST.get("address", "")
        city = request.POST.get("city", "")
        state = request.POST.get("state", "")
        unit_apt_num = request.POST.get("unit_apt_num", "")
        zip_code = request.POST.get("zip_code", "")
        tools = request.POST.get("tools")
        start_time = request.POST.get("start_time")
        duration = request.POST.get("duration")
        job_price = request.POST.get("job_price")
        personal_business = request.POST.get("personal_business")
        sizes = request.POST.get("sizes")
        amt_people = request.POST.get("amt_people")

        # Basic validation (add more as needed)
        if not all([job_title, description, address, city, state, zip_code, duration, job_price, personal_business, sizes, amt_people]):
            messages.error(request, "Please fill in all required fields.")
            # Re-render form with existing data? Or just redirect?
            return redirect('new_request')

        try:
            # Use the real geocoding service instead of placeholder
            coordinates = geocoding_service.geocode(address, city, state, zip_code)
            
            if coordinates:
                # Coordinates found successfully
                latitude, longitude = coordinates
                geo_location = f"{latitude}/{longitude}"
                print(f"Geocoding successful: {geo_location}")
            else:
                # Geocoding failed, inform the user
                messages.warning(request, "Could not accurately geocode the address provided. Your request will still be submitted but location features may not work correctly.")
                geo_location = "0.0/0.0"
            
            # Generate unique job number
            job_number = generate_job_number()
            
            # Create new request document in Firestore
            request_ref = db.collection('requests').document()
            request_data = {
                'user_id': user_id,
                'request_name': job_title,  # Use the job title as request_name
                'job_number': job_number,  # Add the job number
                'start_time': start_time,
                'tool': tools,
                'request_description': description,
                'request_price': job_price,
                'address': address,
                'city': city,
                'state': state,
                'geo_location': geo_location,
                'unit_apt_num': unit_apt_num,
                'zip_code': zip_code,
                'duration': duration,
                'personal_business': personal_business,
                'request_size': sizes,
                'people_amount': amt_people,
                'status': 'pending',
                'created_at': firestore.SERVER_TIMESTAMP
            }
            request_ref.set(request_data)
            print(f"Request submitted successfully for user {user_id}")
            
            messages.success(request, f"Your request has been submitted with job number {job_number} and is pending admin approval.")
            return redirect("dashboard")
            
        except Exception as e:
            print(f"Error creating new request: {str(e)}")
            messages.error(request, f"Error submitting request: {str(e)}")
            # Consider passing form data back to template on error
            return redirect('new_request')

    # Render the form for GET requests
    return render(request, "new_request.html")
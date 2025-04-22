# Profile related views (dashboard, settings, etc.)
import os
import uuid
import json
import threading
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from firebase_admin import firestore, storage
from haversine import haversine, Unit

from members.custom_wrappers import is_logged_in # Import the decorator
from leaf.firebase_config import db
from .utils import geocode_and_update_user # Import the geocoding function

@is_logged_in
def dashboard(request):
    user_id = request.session.get("user_id")
    print(f"Dashboard request received for user_id: {user_id}")
    
    if not user_id:
        print("No user_id in session, redirecting to login")
        # Should be caught by decorator, but safe fallback
        return redirect('login_page') 
    
    try:
        # Get user data from Firestore
        user_doc = db.collection('users').document(user_id).get()
        
        if not user_doc.exists:
            print(f"No user document found for ID: {user_id}")
            # User exists in session but not DB? Log out.
            request.session.flush()
            messages.error(request, "User data not found. Please log in again.")
            return redirect('login_page')
            
        user_data = user_doc.to_dict()
        print(f"User data retrieved: {user_data.get('username')}")
        
        # Get all active jobs to display on the dashboard (exclude 'done' jobs)
        jobs = []
        try:
            # Only fetch jobs with 'active' status - don't show 'done' jobs
            jobs_ref = db.collection('jobs').where(filter=firestore.FieldFilter('status', '==', 'active')).get()
            for job_doc in jobs_ref:
                job_data = job_doc.to_dict()
                # Add job ID to the data for reference in templates
                job_data['job_id'] = job_doc.id
                # Add job to the list
                jobs.append(job_data)
        except Exception as e:
            print(f"Error fetching jobs: {e}")
            # Optionally, inform the user jobs couldn't be loaded
            messages.warning(request, "Could not load available jobs at this time.")
        
        # Initialize map variables safely
        latitude = None
        longitude = None
        map_markers = []
        user_loc_1 = None
        geo_location = user_data.get('geo_location', '')
        
        if geo_location:
            try:
                location_parts = geo_location.split("/")
                if len(location_parts) == 2:
                    latitude = float(location_parts[0])
                    longitude = float(location_parts[1])
                    user_loc_1 = (latitude, longitude)
            except ValueError as e:
                print(f"Error parsing user geo_location '{geo_location}': {e}")
                # Reset lat/lon if parsing fails
                latitude = None
                longitude = None
                user_loc_1 = None
        
        # Calculate distances and prepare map markers if user location is valid
        if user_loc_1:
            try:
                miles = 20 # Search radius for map jobs
                for job in jobs:
                    job_geo_location = job.get('geo_location', '')
                    if job_geo_location:
                        try:
                            pos = job_geo_location.find("/")
                            if pos != -1: 
                                job_lat = float(job_geo_location[0:pos])
                                job_lon = float(job_geo_location[pos+1:])
                                job_loc = (job_lat, job_lon)
                                
                                distance = haversine(user_loc_1, job_loc, unit=Unit.MILES)
                                if distance <= miles:
                                    map_markers.append({
                                        "latitude": job_lat,
                                        "longitude": job_lon,
                                        "title": job.get('job_title', 'Job'),
                                        "job_id": job.get('job_id') # Assuming job dict already contains job_id
                                    })
                        except ValueError as e:
                             print(f"Error parsing job geo_location '{job_geo_location}' for job ID {job.get('job_id')}: {e}")
                        except Exception as e:
                            print(f"Error processing job {job.get('job_id')} for map: {e}")
            except Exception as e:
                # Don't fail the whole function if location processing fails
                print(f"Error processing location data for map: {e}")
                map_markers = [] # Clear markers if there was an error
        
        print("Rendering dashboard with user data and jobs")
        return render(request, "dashboard.html", {
            'user': user_data,
            'jobs': jobs,
            'latitude': latitude,
            'longitude': longitude,
            'map_markers': map_markers
        })
        
    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        messages.error(request, "An error occurred loading your dashboard.")
        # Redirect to login as a safe fallback
        return redirect('login_page')

@is_logged_in
def get_dashboard_updates(request):
    """API endpoint to provide dashboard updates for auto-refresh functionality"""
    user_id = request.session.get("user_id")
    
    if not user_id:
        return JsonResponse({'error': 'User not authenticated'}, status=401)
    
    try:
        # Get all active jobs to display on the dashboard
        jobs = []
        try:
            # Only fetch jobs with 'active' status - don't show 'done' jobs
            jobs_ref = db.collection('jobs').where(filter=firestore.FieldFilter('status', '==', 'active')).get()
            for job_doc in jobs_ref:
                job_data = job_doc.to_dict()
                job_data['job_id'] = job_doc.id
                # Convert any non-serializable objects (like Firestore timestamps) to strings
                for key, value in job_data.items():
                    if isinstance(value, (firestore.SERVER_TIMESTAMP.__class__)):
                        job_data[key] = str(value)
                jobs.append(job_data)
        except Exception as e:
            print(f"Error fetching jobs for updates: {e}")
            return JsonResponse({'error': 'Error fetching jobs'}, status=500)
        
        # Get updated user data
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            return JsonResponse({'error': 'User not found'}, status=404)
            
        user_data = user_doc.to_dict()
        
        # Check for unread messages count (optional feature)
        unread_count = 0
        try:
            messages_ref = db.collection('messages')
            unread_query = messages_ref.where(
                filter=firestore.FieldFilter('receiver_id', '==', user_id)
            ).where(
                filter=firestore.FieldFilter('is_read', '==', False)
            ).count()
            unread_count = unread_query.get()[0][0].value
        except Exception as e:
            print(f"Error counting unread messages: {e}")
            # Continue even if message count fails
        
        # Calculate map markers (similar to dashboard view)
        map_markers = []
        geo_location = user_data.get('geo_location', '')
        
        if geo_location and '/' in geo_location:
            try:
                location_parts = geo_location.split("/")
                latitude = float(location_parts[0])
                longitude = float(location_parts[1])
                user_loc = (latitude, longitude)
                
                miles = 20  # Search radius
                for job in jobs:
                    job_geo_location = job.get('geo_location', '')
                    if job_geo_location and '/' in job_geo_location:
                        try:
                            pos = job_geo_location.find("/")
                            job_lat = float(job_geo_location[0:pos])
                            job_lon = float(job_geo_location[pos+1:])
                            job_loc = (job_lat, job_lon)
                            
                            distance = haversine(user_loc, job_loc, unit=Unit.MILES)
                            if distance <= miles:
                                map_markers.append({
                                    "latitude": job_lat,
                                    "longitude": job_lon,
                                    "title": job.get('job_title', 'Job'),
                                    "job_id": job.get('job_id')
                                })
                        except Exception as e:
                            print(f"Error processing job location: {e}")
            except Exception as e:
                print(f"Error processing user location: {e}")
        
        return JsonResponse({
            'success': True,
            'jobs': jobs,
            'unread_messages': unread_count,
            'map_markers': map_markers,
            'user': {
                'username': user_data.get('username'),
                'profile_image_url': user_data.get('profile_image_url'),
                'geo_location': geo_location
            }
        })
    
    except Exception as e:
        print(f"Error fetching dashboard updates: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@is_logged_in
def settings(request):
    user_id = request.session.get("user_id")
    # Decorator handles check, but another layer just in case.
    if not user_id:
        return redirect('login_page')

    try:
        user_doc = db.collection('users').document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            # Ensure profile_image_url is passed, default handled in template if needed
            user_data['profile_image_url'] = user_data.get('profile_image_url') 
        else:
            # Handle case where user doc doesn't exist but session does
            request.session.flush()
            messages.error(request, "User data not found. Please log in again.")
            return redirect('login_page')

        return render(request, "settings.html", {'user': user_data})

    except Exception as e:
        print(f"Error loading settings page for user {user_id}: {str(e)}")
        messages.error(request, "Could not load settings page.")
        return redirect('dashboard') # Redirect to dashboard on error

@is_logged_in
def change_password(request):
    # Assuming this just renders a template, actual logic might be elsewhere or needs adding
    return render(request, "change_password.html")

@is_logged_in
def get_user_coordinates(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({'error': 'User not logged in'}, status=401)

    try:
        user_doc = db.collection('users').document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            geo_location = user_data.get('geo_location', '0.0/0.0') # Provide default
            # Validate format before returning?
            if '/' not in geo_location:
                print(f"Invalid geo_location format for user {user_id}: {geo_location}. Returning default.")
                geo_location = '0.0/0.0'
            return JsonResponse({'geo_location': geo_location})
        else:
            # User in session but not DB? Log them out.
            request.session.flush()
            return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        print(f"Error fetching coordinates for user {user_id}: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@is_logged_in
def upload_profile_image(request):
    if request.method == 'POST':
        user_id = request.session.get("user_id")
        profile_image = request.FILES.get("profile_image")

        if not user_id:
            messages.error(request, "User session not found. Please log in again.")
            return redirect('login_page')

        if profile_image:
            try:
                print(f"Attempting to upload new profile image for user {user_id}")
                bucket = storage.bucket()
                # Determine file extension
                file_extension = os.path.splitext(profile_image.name)[1]
                # Use UUID to avoid caching issues, user_id for organization
                blob_name = f"profile_images/{user_id}/{uuid.uuid4()}{file_extension}"
                blob = bucket.blob(blob_name)

                # Upload the file
                blob.upload_from_file(profile_image, content_type=profile_image.content_type)
                blob.make_public() # Ensure this permission is appropriate
                profile_image_url = blob.public_url
                print(f"New profile image uploaded successfully: {profile_image_url}")

                # Update Firestore
                user_ref = db.collection('users').document(user_id)
                user_ref.update({'profile_image_url': profile_image_url})
                
                # Update the session as well
                request.session['profile_image_url'] = profile_image_url
                
                messages.success(request, "Profile picture updated successfully!")

            except Exception as e:
                print(f"Error uploading profile image for user {user_id}: {e}")
                messages.error(request, f"Failed to upload profile picture: {e}")
        else:
            messages.warning(request, "No image file selected.")

        # Redirect back to settings page after upload attempt
        return redirect('settings') 
    else:
        # If accessed via GET, just redirect to settings
        return redirect('settings')

@is_logged_in
def update_contact_info(request):
    """Update user contact information (phone number, address, etc.)"""
    if request.method == 'POST':
        user_id = request.session.get("user_id")
        
        if not user_id:
            messages.error(request, "User session not found. Please log in again.")
            return redirect('login_page')
        
        try:
            # Get form data
            phone_num = request.POST.get("phone_num", "")
            address = request.POST.get("address", "")
            city = request.POST.get("city", "")
            state = request.POST.get("state", "")
            unit_apt_num = request.POST.get("unit_apt_num", "")
            zip_code = request.POST.get("zip_code", "")
            
            # Basic validation
            if not all([phone_num, address, city, state, zip_code]):
                messages.warning(request, "Please fill in all required contact fields.")
                return redirect('settings')
            
            # Update user data in Firestore
            user_ref = db.collection('users').document(user_id)
            updates = {
                'phone_num': phone_num,
                'address': address,
                'city': city,
                'state': state,
                'unit_apt_num': unit_apt_num,
                'zip_code': zip_code
            }
            
            user_ref.update(updates)
            
            # Start a background thread to geocode the new address
            # This will update the geo_location field asynchronously
            geocode_thread = threading.Thread(
                target=geocode_and_update_user,
                args=(user_id, address, city, state)
            )
            geocode_thread.daemon = True
            geocode_thread.start()
            
            messages.success(request, "Contact information updated successfully!")
            
        except Exception as e:
            print(f"Error updating contact info for user {user_id}: {str(e)}")
            messages.error(request, f"An error occurred: {str(e)}")
        
    return redirect('settings')

# Job management views
@is_logged_in
def mark_job_done(request, job_id):
    """Mark a job as completed (only job owner or admin can mark a job as done)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    user_id = request.session.get('user_id')
    is_admin = request.session.get('is_admin', False)
    
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    
    try:
        # Get the job from Firestore
        job_ref = db.collection('jobs').document(job_id)
        job_doc = job_ref.get()
        
        if not job_doc.exists:
            return JsonResponse({'success': False, 'error': 'Job not found'})
            
        job_data = job_doc.to_dict()
        
        # Check if the user is the job owner or an admin
        if job_data.get('user_id') != user_id and not is_admin:
            return JsonResponse({'success': False, 'error': 'Not authorized to mark this job as done'})
        
        # Check if the job is already done
        if job_data.get('status') == 'done':
            return JsonResponse({'success': False, 'error': 'Job is already marked as done'})
        
        # Update the job status
        job_ref.update({
            'status': 'done',
            'completed_at': firestore.SERVER_TIMESTAMP
        })
        
        # Send notification to the worker if there is one assigned
        worker_id = job_data.get('worker_id')
        if worker_id:
            try:
                # Get job owner name for the message
                user_ref = db.collection('users').document(user_id)
                user_doc = user_ref.get()
                user_name = user_doc.to_dict().get('username', 'Job Owner') if user_doc.exists else 'Job Owner'
                
                # Send message to worker
                message_ref = db.collection('messages').document()
                message_data = {
                    'message_id': message_ref.id,
                    'sender_id': user_id,
                    'sender_name': user_name,
                    'receiver_id': worker_id,
                    'subject': f"Job Marked as Done: {job_data.get('job_title', 'Job')}",
                    'content': f"The job '{job_data.get('job_title', 'Job')}' has been marked as completed. Thank you for your work!",
                    'timestamp': firestore.SERVER_TIMESTAMP,
                    'is_read': False,
                    'folder': 'inbox'
                }
                message_ref.set(message_data)
                print(f"Notification sent to worker {worker_id} for completed job {job_id}")
            except Exception as e:
                print(f"Error sending notification to worker: {str(e)}")
                # Continue even if notification fails
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        print(f"Error marking job as done: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@is_logged_in
def accept_job(request, job_id):
    """Accept a job as a worker. This decreases the people needed count and assigns the current user as a worker."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    user_id = request.session.get('user_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    
    try:
        # Get the job from Firestore
        job_ref = db.collection('jobs').document(job_id)
        job_doc = job_ref.get()
        
        if not job_doc.exists:
            return JsonResponse({'success': False, 'error': 'Job not found'})
            
        job_data = job_doc.to_dict()
        
        # Check if the user is the job owner (they can't accept their own job)
        if job_data.get('user_id') == user_id:
            return JsonResponse({'success': False, 'error': 'You cannot accept your own job', 'is_owner': True})
        
        # Check if the user already accepted this job
        if job_data.get('accepted_workers') and user_id in job_data['accepted_workers']:
            return JsonResponse({'success': False, 'error': 'You have already accepted this job'})
        
        # Check if the job still needs workers
        people_needed = int(job_data.get('people_amount', 0))
        if people_needed <= 0:
            return JsonResponse({'success': False, 'error': 'This job does not need any more workers'})
            
        # Decrease the people needed count
        new_people_needed = people_needed - 1
        
        # Initialize or update the accepted_workers array
        accepted_workers = job_data.get('accepted_workers', [])
        if not accepted_workers:
            accepted_workers = []
        accepted_workers.append(user_id)
        
        # Get user information to include in job
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            worker_name = user_data.get('username', 'Unknown Worker')
        else:
            worker_name = 'Unknown Worker'
        
        # Update the job data
        updates = {
            'people_amount': str(new_people_needed),
            'accepted_workers': accepted_workers
        }
        
        # If this is the first worker, update main worker_id and name
        if not job_data.get('worker_id'):
            updates['worker_id'] = user_id
            updates['worker_name'] = worker_name
        
        # If no more workers needed, update job status to "in progress"
        if new_people_needed <= 0:
            updates['workers_needed'] = False
        else:
            updates['workers_needed'] = True
        
        # Update the job in Firestore
        job_ref.update(updates)
        
        # Send notification to the job owner
        try:
            owner_id = job_data.get('user_id')
            job_title = job_data.get('job_title', 'Job')
            
            # Create a message for the job owner
            message_ref = db.collection('messages').document()
            message_data = {
                'message_id': message_ref.id,
                'sender_id': user_id,
                'sender_name': worker_name,
                'receiver_id': owner_id,
                'subject': f"Worker Accepted: {job_title}",
                'content': f"{worker_name} has accepted your job '{job_title}'. {new_people_needed} worker(s) still needed.",
                'timestamp': firestore.SERVER_TIMESTAMP,
                'is_read': False,
                'folder': 'inbox'
            }
            message_ref.set(message_data)
            print(f"Notification sent to job owner {owner_id} for job {job_id} acceptance")
        except Exception as e:
            print(f"Error sending notification to job owner: {str(e)}")
            # Continue even if notification fails
        
        # Return success response with updated job data
        return JsonResponse({
            'success': True, 
            'people_needed': new_people_needed,
            'all_workers_assigned': new_people_needed <= 0
        })
    
    except Exception as e:
        print(f"Error accepting job: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@is_logged_in
def cancel_assigned_job(request, job_id):
    """Cancel an assigned job. This removes the user from the job's accepted workers
    and makes the job available again on the dashboard."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    user_id = request.session.get('user_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    
    try:
        # Get the job from Firestore
        job_ref = db.collection('jobs').document(job_id)
        job_doc = job_ref.get()
        
        if not job_doc.exists:
            return JsonResponse({'success': False, 'error': 'Job not found'})
            
        job_data = job_doc.to_dict()
        
        # Check if the user is assigned to this job
        accepted_workers = job_data.get('accepted_workers', [])
        if user_id not in accepted_workers:
            return JsonResponse({'success': False, 'error': 'You are not assigned to this job'})
        
        # Check if the job is still active
        if job_data.get('status') != 'active':
            return JsonResponse({'success': False, 'error': 'This job is no longer active'})
        
        # Get user information for notification
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        worker_name = "Unknown Worker"
        if user_doc.exists:
            user_data = user_doc.to_dict()
            worker_name = user_data.get('username', 'Unknown Worker')
        
        # Remove user from accepted workers
        accepted_workers.remove(user_id)
        
        # Increment the people needed count
        current_people_needed = int(job_data.get('people_amount', 0))
        new_people_needed = current_people_needed + 1
        
        # Prepare updates
        updates = {
            'people_amount': str(new_people_needed),
            'accepted_workers': accepted_workers,
            'workers_needed': True  # Job now needs more workers
        }
        
        # If this user was the primary worker, remove that assignment
        if job_data.get('worker_id') == user_id:
            updates['worker_id'] = None
            updates['worker_name'] = None
            
            # Assign a new primary worker if any remain
            if accepted_workers:
                new_primary_worker = accepted_workers[0]
                new_worker_ref = db.collection('users').document(new_primary_worker)
                new_worker_doc = new_worker_ref.get()
                
                if new_worker_doc.exists:
                    new_worker_data = new_worker_doc.to_dict()
                    updates['worker_id'] = new_primary_worker
                    updates['worker_name'] = new_worker_data.get('username', 'Worker')
        
        # Update the job
        job_ref.update(updates)
        
        # Send notification to the job owner
        try:
            owner_id = job_data.get('user_id')
            job_title = job_data.get('job_title', 'Job')
            
            if owner_id:
                message_ref = db.collection('messages').document()
                message_data = {
                    'message_id': message_ref.id,
                    'sender_id': user_id,
                    'sender_name': worker_name,
                    'receiver_id': owner_id,
                    'subject': f"Worker Canceled: {job_title}",
                    'content': f"{worker_name} has canceled their assignment to your job '{job_title}'. The job is now available for others.",
                    'timestamp': firestore.SERVER_TIMESTAMP,
                    'is_read': False,
                    'folder': 'inbox'
                }
                message_ref.set(message_data)
        except Exception as e:
            print(f"Error sending notification for job cancellation: {str(e)}")
            # Continue even if notification fails
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        print(f"Error canceling assigned job: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@is_logged_in
def job_details(request, job_id):
    """View for displaying job details with options to edit or cancel the job."""
    user_id = request.session.get("user_id")
    is_admin = request.session.get('is_admin', False)
    
    if not user_id:
        return redirect('login_page')
    
    try:
        # Get the job from Firestore
        job_ref = db.collection('jobs').document(job_id)
        job_doc = job_ref.get()
        
        if not job_doc.exists:
            messages.error(request, "Job not found")
            return redirect('my_account')
            
        job_data = job_doc.to_dict()
        job_data['job_id'] = job_id
        
        # Check if the user is the job owner or an admin
        is_owner = job_data.get('user_id') == user_id
        can_edit = is_owner or is_admin
        
        # Get client information if needed
        if not is_owner and 'user_id' in job_data:
            try:
                client_doc = db.collection('users').document(job_data['user_id']).get()
                if client_doc.exists:
                    client_data = client_doc.to_dict()
                    job_data['client_name'] = client_data.get('username', 'Unknown')
                else:
                    job_data['client_name'] = 'Unknown Client'
            except Exception as e:
                print(f"Error fetching client data for job {job_id}: {e}")
                job_data['client_name'] = 'Unknown Client'
        
        # Get user data for profile display
        user_data = {}
        try:
            user_doc = db.collection('users').document(user_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
            else:
                print(f"User document not found for ID: {user_id}")
        except Exception as e:
            print(f"Error fetching user data for profile display: {e}")
        
        # Handle form submission for editing or canceling
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'cancel' and can_edit:
                # Cancel the job
                job_ref.update({
                    'status': 'canceled',
                    'canceled_at': firestore.SERVER_TIMESTAMP
                })
                messages.success(request, "Job has been canceled successfully")
                return redirect('my_account')
                
            elif action == 'edit' and can_edit:
                # Update job details
                updates = {}
                
                # Process form data for fields that can be edited
                job_title = request.POST.get('job_title')
                if job_title:
                    updates['job_title'] = job_title
                
                description = request.POST.get('description')
                if description:
                    updates['description'] = description
                
                price = request.POST.get('price')
                if price:
                    updates['price'] = price
                
                # Add other fields as needed
                start_time = request.POST.get('start_time')
                if start_time:
                    updates['start_time'] = start_time
                
                duration = request.POST.get('duration')
                if duration:
                    updates['duration'] = duration
                
                tools = request.POST.get('tools')
                if tools:
                    updates['tool'] = tools
                
                # Change status to pending for admin review (same as new_request)
                updates['status'] = 'pending'
                updates['edit_timestamp'] = firestore.SERVER_TIMESTAMP
                
                # Update the job in Firestore
                if updates:
                    job_ref.update(updates)
                    
                    messages.success(request, "Job details have been updated and are pending admin approval")
                    return redirect('my_account')
            
        return render(request, "job_details.html", {
            'job': job_data,
            'is_owner': is_owner,
            'can_edit': can_edit,
            'is_admin': is_admin,
            'user': user_data  # Add user data to template context
        })
        
    except Exception as e:
        print(f"Error in job_details view for job {job_id}: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('my_account')
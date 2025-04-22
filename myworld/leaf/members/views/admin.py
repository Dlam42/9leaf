# Admin specific views
import traceback
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from firebase_admin import firestore
from datetime import datetime, timezone, timedelta

from members.custom_wrappers import admin_required # Import the decorator
from leaf.firebase_config import db

@admin_required
def admin_dashboard(request):
    """View for the admin dashboard"""
    try:
        # Get all users
        users_ref = db.collection('users').stream() # Use stream for potentially large collections
        users = []
        for user_doc in users_ref:
            user_data = user_doc.to_dict()
            user_data['user_id'] = user_doc.id  # Add the document ID as user_id
            users.append(user_data)
        
        # Get pending requests - only fetch pending status requests
        requests_ref = db.collection('requests').where(filter=firestore.FieldFilter('status', '==', 'pending')).stream()
        pending_requests = []
        for request_doc in requests_ref:
            request_data = request_doc.to_dict()
            request_data['request_id'] = request_doc.id  # Add the document ID as request_id
            
            # Add username to request by looking up the user
            user_id_for_request = request_data.get('user_id')
            if user_id_for_request:
                try:
                    user_ref = db.collection('users').document(user_id_for_request).get()
                    if user_ref.exists:
                        requesting_user_data = user_ref.to_dict()
                        # Store user info dictionary instead of overwriting user_id
                        request_data['requesting_user'] = {
                            'user_id': user_id_for_request,
                            'user_name': requesting_user_data.get('username', 'Unknown')
                        }
                    else:
                         request_data['requesting_user'] = {'user_name': 'User Not Found'} 
                except Exception as user_fetch_e:
                    print(f"Error fetching user {user_id_for_request} for request {request_data['request_id']}: {user_fetch_e}")
                    request_data['requesting_user'] = {'user_name': 'Error Fetching User'}
            else:
                request_data['requesting_user'] = {'user_name': 'Unknown User'}
            
            pending_requests.append(request_data)
            
        # Get pending jobs (edited jobs waiting for approval)
        pending_jobs_ref = db.collection('jobs').where(filter=firestore.FieldFilter('status', '==', 'pending')).stream()
        for job_doc in pending_jobs_ref:
            job_data = job_doc.to_dict()
            job_id = job_doc.id
            
            # Format as a request for display in the request management tab
            job_request = {
                'request_id': job_id,  # Use job ID since we'll handle approval differently
                'job_id': job_id,  # Include this to identify it as a job object
                'request_name': job_data.get('job_title', 'Untitled Job'),
                'job_number': job_data.get('job_number', 'N/A'),
                'request_description': job_data.get('description', 'No description'),
                'status': 'pending',
                'is_edited_job': True,  # Flag to identify this as an edited job
                'edit_timestamp': job_data.get('edit_timestamp')
            }
            
            # Add user information
            user_id_for_job = job_data.get('user_id')
            if user_id_for_job:
                try:
                    user_ref = db.collection('users').document(user_id_for_job).get()
                    if user_ref.exists:
                        user_data = user_ref.to_dict()
                        job_request['requesting_user'] = {
                            'user_id': user_id_for_job,
                            'user_name': user_data.get('username', 'Unknown')
                        }
                    else:
                        job_request['requesting_user'] = {'user_name': 'User Not Found'}
                except Exception as e:
                    print(f"Error fetching user {user_id_for_job} for edited job {job_id}: {e}")
                    job_request['requesting_user'] = {'user_name': 'Error Fetching User'}
            else:
                job_request['requesting_user'] = {'user_name': 'Unknown User'}
                
            # Add to pending requests list for display in Request Management tab
            pending_requests.append(job_request)
        
        # Get all jobs (active, inactive, and jobs from rejected requests)
        jobs_ref = db.collection('jobs').stream()
        active_inactive_jobs = []
        
        # Get rejected requests to create job representations for them
        rejected_requests_ref = db.collection('requests').where(filter=firestore.FieldFilter('status', '==', 'rejected')).stream()
        rejected_request_jobs = []
        
        # Process rejected requests into job-like objects for display
        for request_doc in rejected_requests_ref:
            request_data = request_doc.to_dict()
            request_data['request_id'] = request_doc.id
            
            # Create a job-like representation from rejected request
            rejected_job = {
                'job_id': f"rejected_{request_doc.id}",  # Special ID to identify as rejected request
                'job_title': request_data.get('request_name', 'Untitled Request'),
                'price': request_data.get('request_price', 'N/A'),
                'status': 'rejected',  # Special status for rejected requests
                'user_id': request_data.get('user_id'),
                'description': request_data.get('request_description', 'No description'),
                'rejection_reason': request_data.get('rejection_reason', 'No reason provided'),
                'address': request_data.get('address', ''),
                'city': request_data.get('city', ''),
                'state': request_data.get('state', ''),
                'start_time': request_data.get('start_time', ''),
                'duration': request_data.get('duration', ''),
                'tools': request_data.get('tool', ''),
                'request_id': request_doc.id
            }
            
            # Add username to job by looking up the user
            user_id_for_job = rejected_job.get('user_id')
            if user_id_for_job:
                try:
                    user_ref = db.collection('users').document(user_id_for_job).get()
                    if user_ref.exists:
                        job_poster_data = user_ref.to_dict()
                        rejected_job['user_name'] = job_poster_data.get('username', 'Unknown')
                    else:
                        rejected_job['user_name'] = 'User Not Found'
                except Exception as user_fetch_e:
                    print(f"Error fetching user {user_id_for_job} for rejected request {request_doc.id}: {user_fetch_e}")
                    rejected_job['user_name'] = 'Error Fetching User'
            else:
                rejected_job['user_name'] = 'Unknown User'
                
            rejected_request_jobs.append(rejected_job)
        
        # Process active and inactive jobs
        for job_doc in jobs_ref:
            job_data = job_doc.to_dict()
            job_data['job_id'] = job_doc.id  # Add the document ID as job_id
            
            # Add username to job by looking up the user
            user_id_for_job = job_data.get('user_id')
            if user_id_for_job:
                try:
                    user_ref = db.collection('users').document(user_id_for_job).get()
                    if user_ref.exists:
                        job_poster_data = user_ref.to_dict()
                        job_data['user_name'] = job_poster_data.get('username', 'Unknown')
                    else:
                        job_data['user_name'] = 'User Not Found'
                except Exception as user_fetch_e:
                    print(f"Error fetching user {user_id_for_job} for job {job_data['job_id']}: {user_fetch_e}")
                    job_data['user_name'] = 'Error Fetching User'
            else:
                job_data['user_name'] = 'Unknown User'
                
            # If job has a worker assigned, get their name too
            worker_id = job_data.get('worker_id')
            if worker_id:
                try:
                    worker_ref = db.collection('users').document(worker_id).get()
                    if worker_ref.exists:
                        worker_data = worker_ref.to_dict()
                        job_data['worker_name'] = worker_data.get('username', 'Unknown Worker')
                except Exception as worker_fetch_e:
                    print(f"Error fetching worker {worker_id} for job {job_data['job_id']}: {worker_fetch_e}")
                    job_data['worker_name'] = 'Error Fetching Worker'
            
            active_inactive_jobs.append(job_data)
        
        # Combine active/inactive jobs and rejected request jobs
        all_jobs = active_inactive_jobs + rejected_request_jobs
            
        # Get all messages sent to the admin
        admin_user_id = request.session.get('user_id') # Get current admin's ID
        messages_ref = db.collection('messages')
        
        # Fetch messages efficiently
        received_query = messages_ref.where(filter=firestore.FieldFilter('receiver_id', '==', admin_user_id)).stream()
        
        admin_messages = []
        utc_minus_7 = timezone(timedelta(hours=-7)) # Define timezone once

        # Helper for timestamp conversion
        def format_timestamp(timestamp):
            if not timestamp:
                return "No date"
            try:
                # Firestore Timestamp to datetime (assume UTC)
                if hasattr(timestamp, 'ToDatetime'): 
                    utc_dt = timestamp.ToDatetime().replace(tzinfo=timezone.utc)
                # Python datetime (assume UTC if naive)
                elif isinstance(timestamp, datetime):
                    utc_dt = timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp
                else:
                     return "Invalid Date Format"
                # Convert to target timezone
                local_dt = utc_dt.astimezone(utc_minus_7)
                return local_dt.strftime('%b %d, %Y') # Format as needed
            except Exception as date_e:
                print(f"Error converting timestamp {timestamp}: {date_e}")
                return "Invalid Date"

        for doc in received_query:
            try:
                message_data = doc.to_dict()
                message_data['message_id'] = doc.id
                message_data['timestamp_display'] = format_timestamp(message_data.get('timestamp'))
                
                # Mark message as read if it's not already
                if not message_data.get('is_read', False):
                    doc.reference.update({'is_read': True}) # Update Firestore
                    message_data['is_read'] = True # Update local data
                    
                admin_messages.append(message_data)
            except Exception as msg_proc_e:
                 print(f"Error processing message {doc.id}: {msg_proc_e}")
        
        # Sort messages by timestamp in Python (descending order)
        def get_timestamp_seconds(msg):
            timestamp = msg.get('timestamp')
            if hasattr(timestamp, 'seconds'):
                return timestamp.seconds
            elif isinstance(timestamp, datetime):
                 # Convert datetime to comparable value (e.g., epoch seconds)
                 return timestamp.timestamp() 
            return 0 # Default for sorting if timestamp is missing/invalid
            
        admin_messages.sort(key=get_timestamp_seconds, reverse=True)
        
        context = {
            'users': users,
            'requests': pending_requests,
            'jobs': all_jobs,
            'messages': admin_messages,
             # Pass admin user info if needed by template
            'admin_user': {'user_id': admin_user_id, 'username': request.session.get('username')}
        }
        
        return render(request, 'admin/admin_dashboard.html', context)
    
    except Exception as e:
        print(f"Admin dashboard error: {traceback.format_exc()}")
        messages.error(request, f"Error loading admin dashboard: {str(e)}")
        return redirect('dashboard') # Redirect non-admin dashboard

@admin_required
def promote_user(request, user_id):
    """Promote a regular user to admin"""
    if request.method == 'POST':
        try:
            # Update user in Firestore to be an admin
            user_ref = db.collection('users').document(user_id)
            # Check if user exists before updating
            user_doc = user_ref.get()
            if user_doc.exists:
                 user_ref.update({'is_admin': True})
                 messages.success(request, f"User {user_doc.to_dict().get('username', user_id)} promoted to admin successfully")
            else:
                messages.error(request, f"User with ID {user_id} not found.")
        except Exception as e:
            print(f"Error promoting user {user_id}: {str(e)}")
            messages.error(request, f"Error promoting user: {str(e)}")
    else:
         messages.error(request, "Invalid request method.")
    
    return redirect('admin_dashboard')

@admin_required
def demote_user(request, user_id):
    """Demote an admin to regular user"""
    # Prevent admin from demoting themselves?
    current_admin_id = request.session.get('user_id')
    if user_id == current_admin_id:
        messages.error(request, "Admins cannot demote themselves.")
        return redirect('admin_dashboard')

    if request.method == 'POST':
        try:
            # Update user in Firestore to be a regular user
            user_ref = db.collection('users').document(user_id)
            user_doc = user_ref.get()
            if user_doc.exists:
                 user_ref.update({'is_admin': False})
                 messages.success(request, f"User {user_doc.to_dict().get('username', user_id)} demoted to regular user successfully")
            else:
                 messages.error(request, f"User with ID {user_id} not found.")
        except Exception as e:
            print(f"Error demoting user {user_id}: {str(e)}")
            messages.error(request, f"Error demoting user: {str(e)}")
    else:
         messages.error(request, "Invalid request method.")

    return redirect('admin_dashboard')

@admin_required
def approve_request(request, request_id):
    """Approve a pending request and create a job listing"""
    if request.method == 'POST':
        try:
            # Use a transaction for atomicity if desired, but simple update for now
            request_ref = db.collection('requests').document(request_id)
            request_doc = request_ref.get()
            
            if not request_doc.exists:
                messages.error(request, "Request not found")
                return redirect('admin_dashboard')
                
            request_data = request_doc.to_dict()

            # Check if already processed
            if request_data.get('status') != 'pending':
                messages.warning(request, f'Request has already been {request_data.get("status")}.')
                return redirect('admin_dashboard')
            
            # Update request status
            request_ref.update({'status': 'approved'})
            print(f"Request {request_id} status updated to approved.")
            
            # Create a new job listing document based on the request
            job_ref = db.collection('jobs').document() # Auto-generate ID
            job_data = {
                'job_id': job_ref.id, # Store the auto-generated ID
                'request_id': request_id,
                'user_id': request_data.get('user_id'),
                'job_title': request_data.get('request_name', 'Untitled Job'), # Default title
                'job_number': request_data.get('job_number'),  # Copy the job number from the request
                'description': request_data.get('request_description'),
                'price': request_data.get('request_price'),
                'start_time': request_data.get('start_time'),
                'duration': request_data.get('duration'),
                'tools': request_data.get('tool'),
                'address': request_data.get('address'),
                'city': request_data.get('city'),
                'state': request_data.get('state'),
                'zip_code': request_data.get('zip_code'),
                'unit_apt_num': request_data.get('unit_apt_num'),
                'geo_location': request_data.get('geo_location'),
                'personal_business': request_data.get('personal_business'),
                'job_size': request_data.get('request_size'),
                'people_amount': request_data.get('people_amount'),
                'status': 'active', # Job status is active
                'created_at': firestore.SERVER_TIMESTAMP
            }
            
            # Save the job listing to Firestore
            job_ref.set(job_data)
            print(f"Job {job_ref.id} created from request {request_id}.")

            # --- Send Approval Notification --- 
            try:
                admin_uid = request.session.get('user_id')
                submitter_uid = request_data.get('user_id')
                request_name = job_data['job_title'] # Use the job title

                if admin_uid and submitter_uid:
                    message_content = f"Congratulations! Your request '{request_name}' has been approved and is now listed as a job."
                    # Function to send message (could be moved to messaging.py or utils.py)
                    send_system_message(admin_uid, submitter_uid, f"Request Approved: {request_name}", message_content)
                    print(f"Approval notification sent for request {request_id}")
                else:
                    print(f"Warning: Could not send approval notification for request {request_id}. Missing admin_uid or submitter_uid.")
            except Exception as msg_e:
                 print(f"Error sending approval notification for request {request_id}: {msg_e}")
            # --- End Approval Notification ---
            
            messages.success(request, "Request approved and job listing created successfully")
        except Exception as e:
            print(f"Error approving request {request_id}: {traceback.format_exc()}")
            messages.error(request, f"Error approving request: {str(e)}")
    else:
         messages.error(request, "Invalid request method.")

    return redirect('admin_dashboard')

@admin_required
def reject_request(request, request_id):
    if request.method == 'POST':
        reason = request.POST.get('reason')
        if not reason:
            messages.error(request, 'Rejection reason is required.')
            # Consider redirecting back to a modal or specific rejection form?
            return redirect('admin_dashboard') 

        try:
            request_ref = db.collection('requests').document(request_id)
            request_doc = request_ref.get()

            if not request_doc.exists:
                messages.error(request, "Request not found")
                return redirect('admin_dashboard')

            request_data = request_doc.to_dict()
            request_name = request_data.get('request_name', '[Unknown Request]') 

            # Check if already processed
            if request_data.get('status') != 'pending':
                 messages.warning(request, f'Request "{request_name}" has already been {request_data.get("status")}.')
                 return redirect('admin_dashboard')

            # Get the Firebase UID of the user who submitted the request
            submitter_uid = request_data.get('user_id') 
            if not submitter_uid:
                 # This case should ideally not happen if data is consistent
                 messages.error(request, f'Submitter User ID not found in request data for request {request_id}')
                 # Log this as a potential data integrity issue
                 print(f"Critical: Submitter UID missing for request {request_id}")
                 return redirect('admin_dashboard')

            # Get the admin's Firebase UID from the session
            admin_uid = request.session.get('user_id')
            if not admin_uid:
                 messages.error(request, 'Admin user session not found. Please log in again.')
                 return redirect('login_page') # Redirect to login if admin session lost

            # Update Firestore Document
            request_ref.update({
                'status': 'rejected',
                'rejection_reason': reason
            })
            print(f"Request {request_id} status updated to rejected.")

            # Send rejection message via Firestore
            try:
                message_content = f"Your request '{request_name}' has been rejected for the following reason:\n\n{reason}"
                send_system_message(admin_uid, submitter_uid, f"Request Rejected: {request_name}", message_content)
                print(f"Rejection notification sent for request {request_id}")
            except Exception as msg_e:
                 print(f"Error sending rejection notification for request {request_id}: {msg_e}")

            messages.success(request, f'Request "{request_name}" has been rejected and the user notified.')

        except Exception as e:
            messages.error(request, f'An error occurred while rejecting the request: {str(e)}')
            print(f"Error in reject_request for {request_id}: {traceback.format_exc()}")

        return redirect('admin_dashboard')
    else:
        messages.error(request, "Invalid request method.")
        return redirect('admin_dashboard')

@admin_required
def get_job_details(request, job_id):
    """API endpoint to fetch detailed job information for admin panel"""
    try:
        job_ref = db.collection('jobs').document(job_id)
        job_doc = job_ref.get()
        
        if not job_doc.exists:
            return JsonResponse({'success': False, 'error': 'Job not found'})
            
        job_data = job_doc.to_dict()
        job_data['job_id'] = job_id  # Add the document ID
        
        # Get poster's username if not already included
        if 'user_name' not in job_data and 'user_id' in job_data:
            try:
                user_ref = db.collection('users').document(job_data['user_id']).get()
                if user_ref.exists:
                    job_data['user_name'] = user_ref.to_dict().get('username', 'Unknown')
            except Exception as e:
                print(f"Error fetching username for job {job_id}: {e}")
                job_data['user_name'] = 'Error Fetching User'
        
        # Get worker's username if assigned and not already included
        if 'worker_id' in job_data and 'worker_name' not in job_data:
            try:
                worker_ref = db.collection('users').document(job_data['worker_id']).get()
                if worker_ref.exists:
                    job_data['worker_name'] = worker_ref.to_dict().get('username', 'Unknown Worker')
            except Exception as e:
                print(f"Error fetching worker name for job {job_id}: {e}")
                job_data['worker_name'] = 'Error Fetching Worker'
                
        return JsonResponse({
            'success': True,
            'job': job_data
        })
        
    except Exception as e:
        print(f"Error in get_job_details for {job_id}: {traceback.format_exc()}")
        return JsonResponse({'success': False, 'error': str(e)})

@admin_required
def activate_job(request, job_id):
    """Activate a job listing"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
        
    try:
        job_ref = db.collection('jobs').document(job_id)
        job_doc = job_ref.get()
        
        if not job_doc.exists:
            return JsonResponse({'success': False, 'error': 'Job not found'})
            
        job_data = job_doc.to_dict()
        job_title = job_data.get('job_title', 'Untitled Job')
        user_id = job_data.get('user_id')
        
        # Update job status to active
        job_ref.update({'status': 'active'})
        
        # Notify the job poster
        if user_id:
            admin_id = request.session.get('user_id')
            message = f"Your job listing '{job_title}' has been activated and is now visible to potential workers."
            send_system_message(admin_id, user_id, f"Job Activated: {job_title}", message)
        
        # Check if request is from the admin dashboard approve button (Accept-Requested header check)
        is_html_request = request.META.get('HTTP_ACCEPT', '').startswith('text/html')
        
        # If coming from admin dashboard UI, redirect back to dashboard
        if is_html_request:
            messages.success(request, f"Job '{job_title}' has been approved and activated successfully")
            return redirect('admin_dashboard')
        
        # Otherwise return JSON response (for API/AJAX calls)
        return JsonResponse({'success': True})
        
    except Exception as e:
        print(f"Error in activate_job for {job_id}: {traceback.format_exc()}")
        
        # Check if request was from the admin dashboard
        is_html_request = request.META.get('HTTP_ACCEPT', '').startswith('text/html')
        if is_html_request:
            messages.error(request, f"Error activating job: {str(e)}")
            return redirect('admin_dashboard')
            
        return JsonResponse({'success': False, 'error': str(e)})

@admin_required
def deactivate_job(request, job_id):
    """Deactivate a job listing"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
        
    try:
        job_ref = db.collection('jobs').document(job_id)
        job_doc = job_ref.get()
        
        if not job_doc.exists:
            return JsonResponse({'success': False, 'error': 'Job not found'})
            
        # Update job status to inactive
        job_ref.update({'status': 'inactive'})
        
        # Notify the job poster
        job_data = job_doc.to_dict()
        job_title = job_data.get('job_title', 'Untitled Job')
        user_id = job_data.get('user_id')
        
        if user_id:
            admin_id = request.session.get('user_id')
            message = f"Your job listing '{job_title}' has been deactivated and is no longer visible to potential workers."
            send_system_message(admin_id, user_id, f"Job Deactivated: {job_title}", message)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        print(f"Error in deactivate_job for {job_id}: {traceback.format_exc()}")
        return JsonResponse({'success': False, 'error': str(e)})

# Helper function to send messages (could be in utils.py or messaging.py)
def send_system_message(sender_id, receiver_id, subject, content):
    """Sends a message via Firestore, typically from admin or system."""
    message_data = {
        'sender_id': sender_id,
        'receiver_id': receiver_id,
        'subject': subject,
        'content': content,
        'timestamp': firestore.SERVER_TIMESTAMP,
        'is_read': False
    }
    # Add sender/receiver names if easily available (enhance user experience)
    try:
        sender_doc = db.collection('users').document(sender_id).get()
        if sender_doc.exists:
            message_data['sender_name'] = sender_doc.to_dict().get('username', 'System/Admin')
        else: 
            message_data['sender_name'] = 'System/Admin' # Default if sender not found
        
        receiver_doc = db.collection('users').document(receiver_id).get()
        if receiver_doc.exists:
            message_data['receiver_name'] = receiver_doc.to_dict().get('username', 'User')
        else:
            message_data['receiver_name'] = 'User' # Default if receiver not found
    except Exception as name_fetch_e:
        print(f"Warning: Could not fetch sender/receiver names for system message: {name_fetch_e}")
    
    db.collection('messages').add(message_data) # Use add() to auto-generate ID
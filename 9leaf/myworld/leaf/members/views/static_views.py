# Simple static page views 
from django.shortcuts import render, redirect
from django.contrib import messages
from firebase_admin import firestore
from members.custom_wrappers import is_logged_in
from leaf.firebase_config import db
# from django.template import loader # loader.get_template not used if using render shortcut

def members(request):
    # Get site settings for logo
    site_settings = {}
    try:
        site_settings_ref = db.collection('site_settings').document('general').get()
        if site_settings_ref.exists:
            site_settings = site_settings_ref.to_dict()
    except Exception as e:
        print(f"Error retrieving site settings: {e}")
         
    return render(request, "members_page.html", {
        'site_settings': site_settings
    })

def app(request):
    # Redirect to dashboard which has all the functionality
    return redirect('dashboard')

def services_FAQ(request):
    # These need their own templates eventually
    return redirect('members')

def about_us(request):
    return redirect('members')

def language(request):
    return redirect('members')

def new_job(request):
    # Use the dedicated new request page
    return redirect('new_request')

def job_list(request):
    # Jobs are shown on dashboard
    return redirect('dashboard')

@is_logged_in
def my_account(request):
    user_id = request.session.get("user_id")
    
    if not user_id:
        # Should be caught by decorator, but safe fallback
        return redirect('login_page') 
    
    try:
        # Get user data from Firestore
        user_doc = db.collection('users').document(user_id).get()
        
        if not user_doc.exists:
            # User exists in session but not DB? Log out.
            request.session.flush()
            messages.error(request, "User data not found. Please log in again.")
            return redirect('login_page')
            
        user_data = user_doc.to_dict()

        # Get site settings for logo
        site_settings = {}
        try:
            site_settings_ref = db.collection('site_settings').document('general').get()
            if site_settings_ref.exists:
                site_settings = site_settings_ref.to_dict()
        except Exception as e:
            print(f"Error retrieving site settings: {e}")
        
        # Ensure phone_number is available, using phone_num if it exists
        if 'phone_num' in user_data and 'phone_number' not in user_data:
            user_data['phone_number'] = user_data['phone_num']
        
        # Get all jobs posted by the user
        posted_jobs = []
        try:
            # Query jobs created by this user
            jobs_ref = db.collection('jobs').where(filter=firestore.FieldFilter('user_id', '==', user_id)).get()
            for job_doc in jobs_ref:
                job_data = job_doc.to_dict()
                job_data['job_id'] = job_doc.id
                posted_jobs.append(job_data)
        except Exception as e:
            print(f"Error fetching user's posted jobs: {e}")
            messages.warning(request, "Could not load your job listings.")
        
        # Get all requests posted by the user
        requests_data = []
        try:
            # Query requests created by this user 
            requests_ref = db.collection('requests').where(filter=firestore.FieldFilter('user_id', '==', user_id)).get()
            for request_doc in requests_ref:
                request_data = request_doc.to_dict()
                request_data['request_id'] = request_doc.id
                requests_data.append(request_data)
        except Exception as e:
            print(f"Error fetching user's requests: {e}")
            messages.warning(request, "Could not load your requests.")
        
        # Get all jobs where user is the worker
        assigned_jobs = []
        try:
            # Query jobs where this user is in the accepted_workers array
            # Use this query if your Firestore database supports array-contains
            jobs_ref_accepted = db.collection('jobs').where(
                filter=firestore.FieldFilter('accepted_workers', 'array_contains', user_id)
            ).get()
            
            # Also query direct worker_id assignment for backward compatibility
            jobs_ref_worker = db.collection('jobs').where(
                filter=firestore.FieldFilter('worker_id', '==', user_id)
            ).get()
            
            # Keep track of job IDs to avoid duplicates
            processed_job_ids = set()
            
            # Process jobs from accepted_workers query
            for job_doc in jobs_ref_accepted:
                job_data = job_doc.to_dict()
                job_data['job_id'] = job_doc.id
                processed_job_ids.add(job_doc.id)
                
                # Get client information
                client_id = job_data.get('user_id')
                if client_id:
                    try:
                        client_doc = db.collection('users').document(client_id).get()
                        if client_doc.exists:
                            client_data = client_doc.to_dict()
                            job_data['client_name'] = client_data.get('username', 'Unknown')
                        else:
                            job_data['client_name'] = 'Unknown Client'
                    except Exception as client_e:
                        print(f"Error fetching client data for job {job_doc.id}: {client_e}")
                        job_data['client_name'] = 'Unknown Client'
                
                assigned_jobs.append(job_data)
            
            # Process jobs from worker_id query (only if not already processed)
            for job_doc in jobs_ref_worker:
                if job_doc.id not in processed_job_ids:
                    job_data = job_doc.to_dict()
                    job_data['job_id'] = job_doc.id
                    
                    # Get client information
                    client_id = job_data.get('user_id')
                    if client_id:
                        try:
                            client_doc = db.collection('users').document(client_id).get()
                            if client_doc.exists:
                                client_data = client_doc.to_dict()
                                job_data['client_name'] = client_data.get('username', 'Unknown')
                            else:
                                job_data['client_name'] = 'Unknown Client'
                        except Exception as client_e:
                            print(f"Error fetching client data for job {job_doc.id}: {client_e}")
                            job_data['client_name'] = 'Unknown Client'
                    
                    assigned_jobs.append(job_data)
        except Exception as e:
            print(f"Error fetching user's assigned jobs: {e}")
            messages.warning(request, "Could not load jobs you're working on.")
        
        return render(request, "my_account.html", {
            'user': user_data,
            'posted_jobs': posted_jobs,
            'requests': requests_data,
            'assigned_jobs': assigned_jobs,
            'site_settings': site_settings  # Add site_settings to the context
        })
        
    except Exception as e:
        print(f"My account error: {str(e)}")
        messages.error(request, "An error occurred loading your account details.")
        return redirect('dashboard')

@is_logged_in
def dashboard(request):
    """View for the main user dashboard"""
    user_id = request.session.get("user_id")
    
    try:
        # Get user data
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            # User session exists but user data doesn't? Force logout
            request.session.flush()
            messages.error(request, "User data not found. Please log in again.")
            return redirect('login_page')
            
        user_data = user_doc.to_dict()
        
        # Get active jobs and requests (pending approval becomes job after approval)
        jobs = []
        
        # Get all active jobs
        jobs_ref = db.collection('jobs').where(filter=firestore.FieldFilter('status', '==', 'active')).stream()
        for job_doc in jobs_ref:
            job_data = job_doc.to_dict()
            job_data['job_id'] = job_doc.id
            # Make sure we have a job title for display
            job_data['job_title'] = job_data.get('job_name', 'Unnamed Job')
            jobs.append(job_data)
        
        # Get all requests (including pending ones if the user is admin)
        requests_ref = db.collection('requests').stream()
        for req_doc in requests_ref:
            req_data = req_doc.to_dict()
            req_data['job_id'] = req_doc.id
            # Format job data for display in the same format as jobs
            req_data['job_title'] = req_data.get('request_name', 'Unnamed Request')
            if req_data.get('job_number'):
                req_data['job_title'] = f"{req_data['job_title']} (#{req_data['job_number']})"
            
            # Add people amount to display
            people_needed = req_data.get('people_amount', 'Unknown')
            req_data['people_needed'] = people_needed
            
            # Only admins see pending requests, everyone sees approved ones
            if req_data.get('status') == 'approved' or request.session.get('is_admin'):
                jobs.append(req_data)
        
        return render(request, "dashboard.html", {
            'user': user_data,
            'jobs': jobs
        })
        
    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        messages.error(request, "An error occurred loading the dashboard.")
        # If we can't load the dashboard, log the user out
        request.session.flush()
        return redirect('login_page')

@is_logged_in
def settings(request):
    """View for user settings page"""
    user_id = request.session.get("user_id")
    
    try:
        # Get user data
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            request.session.flush()
            messages.error(request, "User data not found. Please log in again.")
            return redirect('login_page')
            
        user_data = user_doc.to_dict()
        
        return render(request, "settings.html", {
            'user': user_data
        })
        
    except Exception as e:
        print(f"Settings page error: {str(e)}")
        messages.error(request, "An error occurred loading settings.")
        return redirect('dashboard')
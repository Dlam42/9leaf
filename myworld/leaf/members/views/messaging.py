# Messaging views
import traceback
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from firebase_admin import firestore
from datetime import datetime, timezone, timedelta

from members.custom_wrappers import is_logged_in
from leaf.firebase_config import db

# --- Helper Functions --- (Could also be in utils.py)

def format_timestamp(timestamp, format_str='%b %d, %Y', detail_format_str='%B %d, %Y at %I:%M %p', use_detail_format=False):
    """Formats a Firestore timestamp or Python datetime into a readable string."""
    if not timestamp:
        return "No date"
    
    # Define target timezone (e.g., UTC-7)
    target_tz = timezone(timedelta(hours=-7)) 

    try:
        utc_dt = None
        # Convert Firestore Timestamp to aware UTC datetime
        if hasattr(timestamp, 'ToDatetime'): 
            utc_dt = timestamp.ToDatetime().replace(tzinfo=timezone.utc)
        # Convert Python datetime to aware UTC datetime (assume naive is UTC)
        elif isinstance(timestamp, datetime):
            utc_dt = timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp.astimezone(timezone.utc)
        
        if utc_dt:
            # Convert to target timezone
            local_dt = utc_dt.astimezone(target_tz)
            chosen_format = detail_format_str if use_detail_format else format_str
            return local_dt.strftime(chosen_format)
        else:
             print(f"Timestamp type not recognized: {type(timestamp)}")
             return "Invalid Date Format"

    except Exception as date_e:
        print(f"Error converting timestamp {timestamp}: {date_e}")
        return "Invalid Date"

def get_timestamp_sort_key(msg):
    """Provides a sortable key (epoch seconds) from a message's timestamp."""
    timestamp = msg.get('timestamp')
    if hasattr(timestamp, 'seconds'): # Firestore Timestamp
        return timestamp.seconds
    elif isinstance(timestamp, datetime): # Python datetime
         return timestamp.timestamp() 
    return 0 # Default for sorting if timestamp is missing/invalid

# --- Main Views --- 

@is_logged_in
def messages_page(request):
    """View for the user's messages page (inbox and sent items)."""
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    is_admin_user = request.session.get('is_admin', False)
    profile_image_url = request.session.get('profile_image_url', '/static/default_profile.png') # Get profile image URL

    # Should be handled by decorator, but double-check
    if not user_id:
        return redirect('login_page')
    
    try:
        # Get site settings for logo
        site_settings = {}
        try:
            site_settings_ref = db.collection('site_settings').document('general').get()
            if site_settings_ref.exists:
                site_settings = site_settings_ref.to_dict()
        except Exception as e:
            print(f"Error retrieving site settings: {e}")
        
        messages_ref = db.collection('messages')
        
        # Fetch sent messages
        sent_query = messages_ref.where(filter=firestore.FieldFilter('sender_id', '==', user_id)).stream()
        sent_messages = []
        for doc in sent_query:
            msg = doc.to_dict()
            msg['message_id'] = doc.id
            msg['timestamp_display'] = format_timestamp(msg.get('timestamp'))
            sent_messages.append(msg)
        sent_messages.sort(key=get_timestamp_sort_key, reverse=True)
        
        # Fetch received messages
        received_query = messages_ref.where(filter=firestore.FieldFilter('receiver_id', '==', user_id)).stream()
        received_messages = []
        unread_count = 0
        for doc in received_query:
            msg = doc.to_dict()
            msg['message_id'] = doc.id
            msg['timestamp_display'] = format_timestamp(msg.get('timestamp'))
            
            # Mark message as read if needed
            if not msg.get('is_read', False):
                unread_count += 1
                # Consider marking read only when explicitly opened via get_message?
                # For now, mark read on loading the inbox page.
                # doc.reference.update({'is_read': True}) 
                # msg['is_read'] = True # Update local dict too
            
            received_messages.append(msg)
        received_messages.sort(key=get_timestamp_sort_key, reverse=True)
        
        # Get potential recipients (Admins for regular users, all users for Admins)
        users_ref = db.collection('users')
        recipients = []
        try:
            if is_admin_user:
                # Admins can message anyone - get all users
                all_users_query = users_ref.stream()
                for doc in all_users_query:
                    if doc.id != user_id:  # Exclude self
                        udata = doc.to_dict()
                        recipients.append({'user_id': doc.id, 'username': udata.get('username', 'Unknown')})
            else:
                # Regular users can message anyone - get all users
                all_users_query = users_ref.stream()
                for doc in all_users_query:
                    if doc.id != user_id:  # Exclude self
                        udata = doc.to_dict()
                        is_admin = udata.get('is_admin', False)
                        # Use a different variable name here to avoid overwriting the session username
                        recipient_username = udata.get('username', 'Unknown') 
                        # Add "(Admin)" label for admin users
                        display_name = f"{recipient_username} (Admin)" if is_admin else recipient_username
                        recipients.append({'user_id': doc.id, 'username': display_name})
        except Exception as user_fetch_e:
            print(f"Error fetching users: {user_fetch_e}")
            # Fall back to empty recipients list if needed

        # Sort recipients alphabetically by username for display
        recipients.sort(key=lambda x: x['username'])

        context = {
            'user': {
                # Ensure we use the original username from the session
                'username': request.session.get('username'), # Explicitly get from session again, or use a correctly scoped variable
                'profile_image_url': profile_image_url, # Use the profile image URL retrieved
                'is_admin': is_admin_user
            },
            'sent_messages': sent_messages,
            'received_messages': received_messages,
            'unread_count': unread_count, # Pass unread count to template
            'recipients': recipients, # Renamed from 'admins' for clarity
            'site_settings': site_settings # Pass site settings to template
        }
        
        return render(request, 'messages.html', context)
    
    except Exception as e:
        print(f"Error loading messages page for user {user_id}: {traceback.format_exc()}")
        messages.error(request, f"Error loading messages: {str(e)}")
        return redirect('dashboard')

@is_logged_in
def send_message(request):
    """Handles the POST request to send a new message."""
    if request.method == 'POST':
        sender_id = request.session.get('user_id')
        sender_name = request.session.get('username', 'Unknown User') # Get sender name from session
        receiver_id = request.POST.get('receiver')
        subject = request.POST.get('subject', '(No Subject)') # Default subject
        content = request.POST.get('content', '')

        # Basic Validation
        if not receiver_id or not content:
             messages.error(request, "Recipient and message content are required.")
             return redirect('messages_page') # Corrected redirect
        
        if not sender_id:
             messages.error(request, "Your session seems to have expired. Please log in again.")
             return redirect('login_page')
             
        # Prevent sending message to self? (Optional)
        # if sender_id == receiver_id:
        #    messages.error(request, "You cannot send a message to yourself.")
        #    return redirect('messages_page') # Corrected redirect (if uncommented)
            
        try:
            # Verify receiver exists and get their name
            receiver_doc = db.collection('users').document(receiver_id).get()
            if not receiver_doc.exists:
                messages.error(request, "Recipient not found.")
                return redirect('messages_page') # Corrected redirect
            receiver_name = receiver_doc.to_dict().get('username', 'Unknown User')
            
            # Create new message document in Firestore
            # Use add() to let Firestore generate the document ID
            message_ref = db.collection('messages').add({
                'sender_id': sender_id,
                'sender_name': sender_name,
                'receiver_id': receiver_id,
                'receiver_name': receiver_name,
                'subject': subject.strip(), # Strip whitespace
                'content': content.strip(), # Strip whitespace
                'timestamp': firestore.SERVER_TIMESTAMP,
                'is_read': False
            })
            
            print(f"Message sent from {sender_id} to {receiver_id}, doc ID: {message_ref[1].id}")
            messages.success(request, "Message sent successfully!")

        except Exception as e:
            print(f"Error sending message from {sender_id} to {receiver_id}: {traceback.format_exc()}")
            messages.error(request, f"An error occurred while sending the message: {str(e)}")
        
        return redirect('messages_page') # Corrected redirect
    
    # If not POST, redirect back to the messages page
    messages.error(request, "Invalid request method.")
    return redirect('messages_page') # Corrected redirect

@is_logged_in
def get_message(request, message_id):
    """API view to fetch details of a single message (e.g., for a modal)."""
    user_id = request.session.get('user_id')
    print(f"Attempting to get message with ID: {message_id} for user: {user_id}")

    if not user_id:
         return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)

    try:
        message_doc_ref = db.collection('messages').document(str(message_id))
        message_doc = message_doc_ref.get()
        
        if not message_doc.exists:
            print(f"Message document not found for ID: {message_id}")
            return JsonResponse({'success': False, 'error': 'Message not found'}, status=404)
            
        print(f"Message document found for ID: {message_id}")
        message_data = message_doc.to_dict()
        
        # Authorization check: Ensure user is sender or receiver
        sender_id = message_data.get('sender_id')
        receiver_id = message_data.get('receiver_id')
        print(f"Message sender: {sender_id}, receiver: {receiver_id}. Current user: {user_id}")
        
        if sender_id != user_id and receiver_id != user_id:
            print(f"Permission denied for user {user_id} to view message {message_id}")
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        # Mark message as read if the current user is the receiver and it's unread
        is_read = message_data.get('is_read', False)
        if receiver_id == user_id and not is_read:
            print(f"Marking message {message_id} as read for user {user_id}")
            try:
                 message_doc_ref.update({'is_read': True})
                 is_read = True # Update the status we return
            except Exception as update_e:
                 print(f"Error marking message {message_id} as read: {update_e}")
                 # Proceed with returning data, but log the error

        # Format timestamp using the helper function with detail format
        formatted_timestamp = format_timestamp(message_data.get('timestamp'), use_detail_format=True)
        print(f"Formatted timestamp: {formatted_timestamp}")
        
        # Prepare response data
        response_data = {
            'success': True,
            'message': {
                'message_id': message_id,
                'sender_id': sender_id,
                'sender_name': message_data.get('sender_name', 'Unknown'),
                'receiver_id': receiver_id,
                'receiver_name': message_data.get('receiver_name', 'Unknown'),
                'subject': message_data.get('subject', '(No Subject)'),
                'content': message_data.get('content', ''),
                'timestamp': formatted_timestamp,
                'is_read': is_read
            }
        }
        print(f"Returning success response for message {message_id}")
        return JsonResponse(response_data)

    except Exception as e:
        print(f"Exception caught in get_message for ID {message_id}: {traceback.format_exc()}")
        return JsonResponse({'success': False, 'error': 'An unexpected error occurred.'}, status=500)
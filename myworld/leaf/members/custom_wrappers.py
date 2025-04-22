from django.shortcuts import redirect
from functools import wraps

def is_logged_in(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('is_authenticated'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # First check if user is logged in
        if not request.session.get('is_authenticated'):
            return redirect('login')
        
        # Then check if user is an admin
        if not request.session.get('is_admin'):
            return redirect('dashboard')  # Redirect to user dashboard if not admin
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

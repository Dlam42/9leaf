from django.urls import path
from . import views
from .views import admin, auth, messaging, profile, requests, static_views, utils

from django.conf import settings
from django.conf.urls.static import static as static_url

urlpatterns = [
    # Static views
    path('', static_views.members, name='members'),
    path('members/', static_views.members, name='members'),
    path('app/', static_views.app, name="app"),
    path('services_FAQ/', static_views.services_FAQ, name='services_FAQ'),
    path('about_us/', static_views.about_us, name="about_us"),
    path('language/', static_views.language, name='language'),
    path('new_job/', static_views.new_job, name='new_job'),
    path('job_list/', static_views.job_list, name="job_list"),
    path('my_account/', static_views.my_account, name='my_account'),

    # Auth views
    path('register/', auth.register, name="register"),
    path('login/', auth.login, name="login_user"),
    path('login_page/', auth.login_page, name="login_page"),
    path('logout/', auth.logout, name="logout"),
    
    # Profile views
    path('dashboard/', profile.dashboard, name="dashboard"),
    path('upload_profile_image/', profile.upload_profile_image, name='upload_profile_image'),
    path('update_contact_info/', profile.update_contact_info, name='update_contact_info'),
    path('settings/', profile.settings, name="settings"),
    path('change_password/', auth.change_password, name="change_password"),
    path('get-coordinates/', profile.get_user_coordinates, name='get_coordinates'),
    path('mark_job_done/<str:job_id>/', profile.mark_job_done, name='mark_job_done'),
    path('get-dashboard-updates/', profile.get_dashboard_updates, name='get_dashboard_updates'),
    path('accept_job/<str:job_id>/', profile.accept_job, name='accept_job'),
    path('cancel_assigned_job/<str:job_id>/', profile.cancel_assigned_job, name='cancel_assigned_job'),
    path('job_details/<str:job_id>/', profile.job_details, name='job_details'),

    # Request views
    path('new_request/', requests.new_request, name='new_request'),
    
    # Messages URLs
    path('messages/', messaging.messages_page, name='messages_page'),
    path('send_message/', messaging.send_message, name='send_message'),
    path('get_message/<str:message_id>/', messaging.get_message, name='get_message_details'),
    
    # Admin dashboard URLs
    path('admin_dashboard/', admin.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/', admin.admin_dashboard, name='admin_dashboard_hyphen'),  # Add hyphen version for compatibility
    path('promote_user/<str:user_id>/', admin.promote_user, name='promote_user'),
    path('demote_user/<str:user_id>/', admin.demote_user, name='demote_user'),
    path('approve_request/<str:request_id>/', admin.approve_request, name='approve_request'),
    path('reject_request/<str:request_id>/', admin.reject_request, name='reject_request'),
    path('get_job_details/<str:job_id>/', admin.get_job_details, name='get_job_details'),
    path('activate_job/<str:job_id>/', admin.activate_job, name='activate_job'),
    path('deactivate_job/<str:job_id>/', admin.deactivate_job, name='deactivate_job'),
    path('upload_logo/', admin.upload_logo, name='upload_logo'),
    path('reset_logo/', admin.reset_logo, name='reset_logo'),
] + static_url(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
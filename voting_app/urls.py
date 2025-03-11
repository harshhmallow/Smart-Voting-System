from django.urls import path
from . import views

urlpatterns = [
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('vote/', views.vote, name='vote'),  # Ensure this renders the vote.html page
    path('register_voter/', views.register_voter, name='register_voter'),
    path('register/', views.register_page, name='register_page'),
    path('verify_voter/', views.verify_voter, name='verify_voter'),  # Endpoint for face verification
    # Add any new endpoints here as needed
]

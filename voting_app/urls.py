from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path
from . import views
from .views import admin_dashboard 
from voting_app.views import register_voter 
from voting_app.views import register_page

urlpatterns = [
    path('admin_dashboard/', staff_member_required(admin_dashboard), name='admin_dashboard'),
    path('vote/', views.vote, name='vote'),  # Ensure this renders the vote.html page
    path('register_voter/', views.register_voter, name='register_voter'),
    path('register/', views.register_page, name='register_page'),
    path('verify_voter/', views.verify_voter, name='verify_voter'),  # Endpoint for face verification
    path('api/get_vote_counts/', views.get_vote_counts, name='get_vote_counts'),  # Add trailing slash
    # Add any new endpoints here as needed
    path('live-voting-stats/', views.live_voting_statistics, name='live_voting_statistics'),
    path('voter-list/', views.voter_list, name='voter_list'),

]

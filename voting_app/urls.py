from django.urls import path
from . import views

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('vote/', views.vote, name='vote'),
    path('register-voter/', views.register_voter, name='register_voter'),
    path('register/', views.register_page, name='register_page'),
]

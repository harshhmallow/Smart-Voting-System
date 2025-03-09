from django.urls import path
from . import views
from .views import check_face_data

urlpatterns = [
    path('register/', views.register_voter, name='register_voter'),
    path('vote/', views.vote, name='vote'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('check-face-data/', check_face_data, name='check_face_data'),
]
from django.db import models
from django.shortcuts import render
from .models import Vote

def admin_dashboard(request):
    vote_counts = Vote.objects.values('candidate').annotate(count=models.Count('candidate'))
    return render(request, 'admin_dashboard.html', {'vote_counts': vote_counts})
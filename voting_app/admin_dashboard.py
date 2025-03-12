from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from voting_app.models import Voter, Vote
from voting_app.forms import VoterForm  # Ensure you have a VoterForm in forms.py
from voting_app.views import register_voter

@login_required
def admin_dashboard(request):
    voters = Voter.objects.all()
    votes = Vote.objects.all()
    
    # Live vote counting per candidate
    candidates = dict(Vote.CANDIDATE_CHOICES)
    vote_data = []
    for key, name in candidates.items():
        candidate_votes = Vote.objects.filter(candidate=key).count()
        vote_data.append({
            'name': name,
            'votes': candidate_votes,
        })
    
    # Election status
    election_status = "Ongoing" if votes.count() < voters.count() else "Completed"
    
    # Add new voter functionality
    if request.method == "POST":
        form = VoterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = VoterForm()
    
    context = {
        'voters': voters,
        'votes': votes,
        'vote_data': vote_data,
        'election_status': election_status,
        'form': form,
    }
    return render(request, 'admin_dashboard.html', context)

urlpatterns = [
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
]

admin.site.site_header = "Smart Voting System Admin"
admin.site.site_title = "Smart Voting System"
admin.site.index_title = "Admin Dashboard"

class VoterAdmin(admin.ModelAdmin):
    list_display = ('id', 'ktu_id', 'has_voted')
    search_fields = ('ktu_id',)
    list_filter = ('has_voted',)

class VoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'voter', 'candidate', 'timestamp')
    search_fields = ('voter__ktu_id', 'candidate')
    list_filter = ('timestamp',)

admin.site.register(Voter, VoterAdmin)
admin.site.register(Vote, VoteAdmin)

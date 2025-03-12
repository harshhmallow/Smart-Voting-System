from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from voting_app.models import Voter, Vote

@login_required
def admin_dashboard(request):
    voters_count = Voter.objects.count()
    votes_count = Vote.objects.count()

    # Calculate vote percentage for each candidate
    candidates = dict(Vote.CANDIDATE_CHOICES)
    vote_data = []
    for key, name in candidates.items():
        candidate_votes = Vote.objects.filter(candidate=key).count()
        vote_percentage = (candidate_votes / votes_count * 100) if votes_count > 0 else 0
        vote_data.append({
            'name': name,
            'votes': candidate_votes,
            'percentage': round(vote_percentage, 2)
        })
    
    # Determine election status
    election_status = "Ongoing" if votes_count < voters_count else "Completed"
    
    context = {
        'voters_count': voters_count,
        'votes_count': votes_count,
        'vote_data': vote_data,
        'election_status': election_status,
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

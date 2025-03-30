from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db.models import Count
from .models import Vote

class VoteAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'voter')  # Customize the list view
    search_fields = ('candidate', 'voter__ktu_id')  # Enable search by candidate or voter ID

    def get_urls(self):
        # Add a custom URL for the admin dashboard
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_site.admin_view(self.admin_dashboard), name='vote_dashboard'),
        ]
        return custom_urls + urls

    def admin_dashboard(self, request):
        # Calculate vote counts for each candidate
        vote_counts = Vote.objects.values('candidate').annotate(count=Count('candidate'))
        context = {
            'vote_counts': vote_counts,
            'opts': self.model._meta,  # Required for admin template
        }
        return render(request, 'admin/vote_dashboard.html', context)

admin.site.register(Vote, VoteAdmin)
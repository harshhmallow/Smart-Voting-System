from django.db import models
from django.shortcuts import render
from .models import Vote,Voter
from django.http import JsonResponse

from django.core.paginator import Paginator

def get_voters(request):
    page = request.GET.get('page', 1)
    voters = Voter.objects.all()
    paginator = Paginator(voters, 10)  # Show 10 voters per page
    voters_page = paginator.get_page(page)
    data = [{'ktu_id': voter.ktu_id, 'has_voted': voter.has_voted} for voter in voters_page]
    return JsonResponse({'voters': data, 'has_next': voters_page.has_next()})
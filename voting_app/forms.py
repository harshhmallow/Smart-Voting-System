from django import forms
from voting_app.models import Voter

class VoterForm(forms.ModelForm):
    class Meta:
        model = Voter
        fields = ['ktu_id', 'has_voted']  # Include only necessary fields
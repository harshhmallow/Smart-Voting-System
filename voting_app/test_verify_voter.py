import json
from django.test import TestCase
from django.urls import reverse
from .models import Voter

class VoterTests(TestCase):
    def setUp(self):
        # Create a voter object with encrypted face data
        self.voter = Voter.objects.create(
            ktu_id='TVE22CS001',
            encrypted_face_data=b'some_encrypted_data',  # Placeholder for actual encrypted data
            has_voted=False
        )

    def test_decrypt_valid_voter(self):
        """Test decryption for a valid voter ID."""
        response = self.client.post(reverse('verify_voter'), {
            'ktu_id': 'TVE22CS001',
            'frame_data': 'base64_encoded_frame_data'  # Placeholder for actual frame data
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('Voter verified successfully.', response.json()['message'])

    def test_decrypt_invalid_voter(self):
        """Test decryption for an invalid voter ID."""
        response = self.client.post(reverse('verify_voter'), {
            'ktu_id': 'TVE22CS999',  # Invalid ID
            'frame_data': 'base64_encoded_frame_data'  # Placeholder for actual frame data
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Decryption failed for voter ID', response.json()['message'])

    def test_missing_ktu_id(self):
        """Test handling of missing KTU ID."""
        response = self.client.post(reverse('verify_voter'), {
            'frame_data': 'base64_encoded_frame_data'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('KTU ID and face data are required.', response.json()['message'])

    def test_missing_frame_data(self):
        """Test handling of missing frame data."""
        response = self.client.post(reverse('verify_voter'), {
            'ktu_id': 'TVE22CS001'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('KTU ID and face data are required.', response.json()['message'])

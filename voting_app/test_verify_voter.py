import json
from django.test import TestCase
from django.urls import reverse
from .models import Voter, Vote

class VoterTests(TestCase):
    def setUp(self):
        # Create a voter object in the database
        self.voter = Voter.objects.create(ktu_id='TVE22CS001')

        # Set up the URLs for voting, registering, and verifying voter
        self.vote_url = reverse('vote')
        self.register_url = reverse('register_voter')
        self.verify_url = reverse('verify_voter')

        # Define a valid base64 image string for testing
        self.valid_base64_image = 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAAAAAAAD/2wBDAAoHBwkJCAoLCwoODQsOEw8QFx4kGyMtKxwbKkpEKycrPzEoPLdAQD5//2wBDAQ8PGh8p5jE0Pjs/zDhK4vE+MIAwLfnkt6kXKg3VXE7HSeP3ZQNmJ0zVZGGzAWN3zmkwC3gFR9Yf2c7JozlJtHax8DkwLg0XCuI12EGQwXwMZmzBlw60UuBlLPVrgf1wF5RYtoUUSNrKldY6s8YWJ6kD53i55OdntcGRdw/xMHiA3+wYZV4Q=4Q=='

    def test_register_voter(self):
        # Test registration of voter with a base64 image
        response = self.client.post(self.register_url, json.dumps({
            'ktu_id': 'TVE22CS001',
            'frames_data': [self.valid_base64_image]
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Registration successful!', response.json()['message'])

    def test_verify_voter_success(self):
        # Test successful verification
        response = self.client.post(self.verify_url, json.dumps({
            'ktu_id': 'TVE22CS001',
            'frame_data': self.valid_base64_image
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Voter verified successfully.', response.json()['message'])

    def test_verify_voter_missing_ktu_id(self):
        # Test verification with missing KTU ID
        response = self.client.post(self.verify_url, json.dumps({
            'frame_data': self.valid_base64_image
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('KTU ID and face data are required.', response.json()['message'])

    def test_verify_voter_missing_frame_data(self):
        # Test verification with missing frame data
        response = self.client.post(self.verify_url, json.dumps({
            'ktu_id': 'TVE22CS001'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('KTU ID and face data are required.', response.json()['message'])

    def test_verify_voter_invalid_image(self):
        # Test verification with an invalid base64 image
        response = self.client.post(self.verify_url, json.dumps({
            'ktu_id': 'TVE22CS001',
            'frame_data': 'invalid_base64_image'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid JSON data.', response.json()['message'])

    def test_vote(self):
        # Test voting functionality
        response = self.client.post(self.vote_url, json.dumps({
            'ktu_id': 'TVE22CS001',
            'candidate': 'KSU'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Vote for KSU recorded successfully.', response.json()['message'])

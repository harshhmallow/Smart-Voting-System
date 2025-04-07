from django.http import JsonResponse
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
import requests
import json
import base64
import logging
import numpy as np
import cv2
import pickle
from .models import Voter, Vote
from .face_recognition import FaceRecognition
from voting_app.forms import VoterForm
from cryptography.fernet import Fernet

face_recognition = FaceRecognition()  # Initialize face recognition

logger = logging.getLogger(__name__)

def get_vote_counts(request):
    # Define colors for each candidate
    candidate_colors = {
        'KSU': '#00A9E0',  # Light blue
        'SFI': '#FF0000',  # Red
        'ABVP': '#FFA500',  # Orange
        'NOTA': '#FFC0CB',  # Pink
    }

    try:
        # Count the number of votes for each candidate (grouping by candidate)
        vote_data = Vote.objects.values('candidate').annotate(vote_count=Count('candidate')).order_by('candidate')

        # If no votes exist, return an empty response with a message
        if not vote_data:
            return JsonResponse({'message': 'No votes found.'}, status=404)

        # Convert the queryset to a dictionary, adding color data
        formatted_data = {
            vote['candidate']: {
                'vote_count': vote['vote_count'],
                'color': candidate_colors.get(vote['candidate'], '#000000')  # Default to black if not found
            }
            for vote in vote_data
        }

        return JsonResponse(formatted_data)

    except Exception as e:
        # Log any exceptions for debugging
        logger.error(f"Error in get_vote_counts: {str(e)}")
        return JsonResponse({'message': 'An error occurred while fetching vote counts.'}, status=500)
# Ensure that face recognition is only loaded when needed to avoid circular imports

@csrf_exempt
def verify_voter(request):
    """Handles voter face recognition to verify identity before voting."""
    if request.method == 'POST':
        logger.debug(f"Received POST request to verify_voter with body: {request.body.decode('utf-8')}")

        try:
            # Decode the JSON data from the request body
            data = json.loads(request.body.decode('utf-8'))  # Ensure proper decoding

            ktu_id = data.get('ktu_id')
            frame_data = data.get('frame_data')  # Base64-encoded image

            logger.debug(f"Extracted KTU ID: {ktu_id}, Frame Data Length: {len(frame_data) if frame_data else 0}")

            # Check for missing KTU ID or frame data
            if not ktu_id or not frame_data:
                logger.warning(f"Missing KTU ID: {ktu_id}, or frame data: {len(frame_data) if frame_data else 'None'}")
                return JsonResponse({'message': 'KTU ID and face data are required.'}, status=400)

            # Decode the Base64 image
            try:
                image_data = base64.b64decode(frame_data)
                nparr = np.frombuffer(image_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            except Exception as e:
                logger.error(f"Base64 decoding failed: {e}, Frame Data Length: {len(frame_data) if frame_data else 'None'}")
                return JsonResponse({'message': 'Invalid image data.'}, status=400)

            # Check if the decoded frame is empty or invalid
            if frame is None or frame.size == 0:
                logger.warning("Decoded frame is empty or invalid.")
                return JsonResponse({'message': 'Invalid image data.'}, status=400)

            logger.debug("Successfully decoded base64 image. Proceeding with face recognition.")

            # Check if the voter exists
            try:
                voter = Voter.objects.get(ktu_id=ktu_id)
                face_data = voter.get_face_data()
            except Voter.DoesNotExist:
                logger.error(f"Voter with KTU ID {ktu_id} does not exist.")
                return JsonResponse({'message': 'Voter not found.'}, status=404)

            # Recognize the voter based on the face in the image
            recognized_ktu_id = face_recognition.recognize_voter(frame)

            # Compare recognized voter ID with the provided KTU ID
            if recognized_ktu_id == ktu_id:
                logger.info(f"Voter {ktu_id} verified successfully.")
                return JsonResponse({'message': 'Voter verified successfully.', 'verified': True})

            else:
                logger.warning(f"Face does not match the KTU ID: {ktu_id}.")
                return JsonResponse({'message': 'Face does not match the KTU ID.', 'verified': False}, status=400)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error: {str(e)}")
            return JsonResponse({'message': 'Invalid JSON data.'}, status=400)

    # Handle invalid HTTP methods (only POST is allowed)
    return JsonResponse({'message': 'Invalid request method.'}, status=405)

ENCRYPTION_KEY = b'e2SFWo_JW88JOSQvYbhAAQGjzdunUg2Bzrdb4oJX4sY='  
cipher = Fernet(ENCRYPTION_KEY)

@csrf_exempt
def register_voter(request):
    """ Endpoint for registering or updating a voter. """
    if request.method == 'POST':
        logger.debug(f"Received POST request to register_voter with body: {request.body}")
        try:
            data = json.loads(request.body)
            ktu_id = data.get('ktu_id')
            frames_data = data.get('frames_data')  # List of base64-encoded frames

            if not ktu_id or not frames_data:
                return JsonResponse({'message': 'KTU ID and frames data are required.'}, status=400)

            face_data_list = []
            for frame_data in frames_data:
                if ',' in frame_data:
                    image_data = base64.b64decode(frame_data.split(',')[1])
                    nparr = np.frombuffer(image_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if frame is None or frame.size == 0:
                        continue  # Skip empty frames

                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                    faces = facedetect.detectMultiScale(gray, 1.3, 5)

                    for (x, y, w, h) in faces:
                        crop_img = frame[y:y+h, x:x+w]
                        resized_img = cv2.resize(crop_img, (50, 50))
                        face_data_list.append(resized_img.tolist())

            if face_data_list:
                # Encrypt serialized face data
                serialized_data = pickle.dumps(face_data_list)  # Serialize face data
                encrypted_face_data = cipher.encrypt(serialized_data)  # Encrypt it

                # Save voter data with encrypted face data
                voter, created = Voter.objects.update_or_create(
                    ktu_id=ktu_id,
                    defaults={'encrypted_face_data': encrypted_face_data}  # Store encrypted data
                )

                if created:
                    return JsonResponse({'message': 'Registration successful! Your face data has been saved.'})
                else:
                    return JsonResponse({'message': 'Voter data updated successfully!'})

            return JsonResponse({'message': 'No valid face data detected in any frame.'}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in register_voter: {str(e)}", exc_info=True)
            return JsonResponse({'message': f'An error occurred: {str(e)}'}, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)


def register_page(request):
    """ Renders the voter registration page. """
    return render(request, 'register.html')


@staff_member_required
def admin_dashboard(request):
    """ Admin dashboard to display vote statistics and manage voters """
    voters = Voter.objects.all()
    voters_count = voters.count()
    votes_count = Vote.objects.count()

    election_status = "Ongoing" if votes_count < voters_count else "Completed"

    # Fetch vote statistics from the API
    response = requests.get('http://localhost:8000/api/get_vote_counts')  # Replace with your API URL
    if response.status_code == 200:
        vote_data = response.json()
    else:
        vote_data = {}

    context = {
        'vote_data': vote_data,
        'voters_count': voters_count,
        'votes_count': votes_count,
        'election_status': election_status,
        'voters': voters,
    }

    return render(request, 'admin_dashboard.html', context)
@staff_member_required
def live_voting_statistics(request):
    voters_count = Voter.objects.count()
    votes_count = Vote.objects.count()
    election_status = "Ongoing"  # Replace with actual logic if you have it

    leaderboard = (
        Vote.objects
        .values('candidate')
        .annotate(vote_count=Count('candidate'))
        .order_by('-vote_count')
    )

    context = {
        'voters_count': voters_count,
        'votes_count': votes_count,
        'election_status': election_status,
        'leaderboard': leaderboard,
    }

    return render(request, 'live_voting_statistics.html', context)

@staff_member_required
def voter_list(request):
    voters = Voter.objects.all()
    context = {
        'voters': voters,
    }
    return render(request, 'voter_list.html', context)



@csrf_exempt
def vote(request):
    """Handles the voting process for a candidate."""
    if request.method == 'POST':
        ktu_id = request.POST.get('ktu_id')
        candidate = request.POST.get('candidate')

        if not ktu_id or not candidate:
            return JsonResponse({'message': 'KTU ID and candidate are required.'}, status=400)

        # Check if the voter exists
        voter = Voter.objects.filter(ktu_id=ktu_id).first()
        if not voter:
            return JsonResponse({'message': 'Voter not found.'}, status=404)

        # Prevent duplicate votes
        if voter.has_voted:
            return JsonResponse({'message': 'You have already voted.'}, status=400)

        # Validate candidate
        valid_candidates = ['KSU', 'SFI', 'ABVP', 'NOTA']
        if candidate not in valid_candidates:
            return JsonResponse({'message': 'Invalid candidate.'}, status=400)

        # Record the vote
        Vote.objects.create(voter=voter, candidate=candidate)

        # Mark the voter as having voted
        voter.has_voted = True
        voter.save()

        return JsonResponse({'message': f'Vote for {candidate} recorded successfully.'})

    return render(request, 'vote.html')

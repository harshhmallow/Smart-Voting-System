from django.http import JsonResponse
from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
import json
import base64
import logging
import numpy as np
import cv2
from .models import Voter, Vote
from .face_recognition import FaceRecognition
from voting_app.forms import VoterForm


face_recognition = FaceRecognition()  # Initialize face recognition

logger = logging.getLogger(__name__)

@csrf_exempt
def verify_voter(request):
    """ Handles voter face recognition to verify identity before voting. """
    if request.method == 'POST':
        logger.debug(f"Received POST request to verify_voter with body: {request.body}")
        try:
            data = json.loads(request.body)
            ktu_id = data.get('ktu_id')
            frame_data = data.get('frame_data')  # Base64-encoded image frame

            logger.debug(f"KTU ID: {ktu_id}, Frame Data: {frame_data}")

            if not ktu_id or not frame_data or ',' not in frame_data:
                logger.warning("Missing KTU ID or frame data in the request.")
                return JsonResponse({'message': 'KTU ID and face data are required.'}, status=400)

            # Decode the base64 image
            try:
                image_data = base64.b64decode(frame_data)  # Remove the split to check data integrity
            except Exception as e:
                logger.error(f"Base64 decoding failed: {e}")
                return JsonResponse({'message': 'Invalid image data.'}, status=400)

            nparr = np.frombuffer(image_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None or frame.size == 0:
                logger.warning("Empty frame detected, cannot process.")
                return JsonResponse({'message': 'Invalid image data.'}, status=400)

            logger.debug("Decoding base64 image data for face recognition.")
            recognized_ktu_id = face_recognition.recognize_voter(frame)

            if recognized_ktu_id == ktu_id:
                logger.info(f"Voter {ktu_id} verified successfully.")
                return JsonResponse({'message': 'Voter verified successfully.', 'verified': True})

            else:
                logger.warning(f"Face does not match the KTU ID: {ktu_id}.")
                return JsonResponse({'message': 'Face does not match the KTU ID.', 'verified': False}, status=400)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error: {str(e)}")
            return JsonResponse({'message': 'Invalid JSON data.'}, status=400)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def register_voter(request):
    """ Endpoint for registering a new voter. """
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
                voter = Voter(ktu_id=ktu_id)
                voter.save_face_data(face_data_list)
                return JsonResponse({'message': 'Registration successful! Your face data has been saved.'})
            else:
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
    votes = Vote.objects.all()
    vote_counts = votes.values('candidate').annotate(count=Count('candidate'))
    voters_count = voters.count()
    votes_count = votes.count()

    election_status = "Ongoing" if votes_count < voters_count else "Completed"
    vote_data = [{'name': vote['candidate'], 'votes': vote['count']} for vote in vote_counts]
    
    if request.method == "POST":
        form = VoterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('register_page')  # Redirects to voter registration page
    else:
        form = VoterForm()
    
    context = {
        'vote_data': vote_data,
        'voters_count': voters_count,
        'votes_count': votes_count,
        'election_status': election_status,
        'voters': voters,
        'form': form,
    }
    return render(request, 'admin_dashboard.html', context)


@csrf_exempt
def vote(request):
    """ Handles the voting process for a candidate. """
    if request.method == 'POST':
        ktu_id = request.POST.get('ktu_id')
        candidate = request.POST.get('candidate')

        if not ktu_id or not candidate:
            return JsonResponse({'message': 'KTU ID and candidate are required.'}, status=400)

        # Check if the voter exists in the database
        voter = get_object_or_404(Voter, ktu_id=ktu_id)

        # Check if the voter has already voted
        if voter.has_voted:
            return JsonResponse({'message': 'You have already voted.'}, status=400)

        # Validate the candidate against the list of valid candidates
        valid_candidates = ['KSU', 'SFI', 'ABVP', 'NOTA']
        if candidate not in valid_candidates:
            return JsonResponse({'message': 'Invalid candidate.'}, status=400)

        # Save the vote
        Vote.objects.create(voter=voter, candidate=candidate)

        # Mark the voter as having voted
        voter.has_voted = True
        voter.save()

        return JsonResponse({'message': f'Vote for {candidate} recorded successfully.'})

    # Render the voting form for GET requests
    return render(request, 'vote.html')

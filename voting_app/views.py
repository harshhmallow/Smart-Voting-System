from django.http import JsonResponse
from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import json
import base64
import numpy as np
import cv2
from .models import Voter, Vote

def admin_dashboard(request):
    # Calculate vote counts for each candidate
    vote_counts = Vote.objects.values('candidate').annotate(count=Count('candidate'))
    context = {
        'vote_counts': vote_counts,
    }
    return render(request, 'admin_dashboard.html', context)


def vote(request):
    if request.method == 'POST':
        ktu_id = request.POST.get('ktu_id')
        candidate = request.POST.get('candidate')

        if not ktu_id or not candidate:
            return JsonResponse({'message': 'KTU ID and candidate are required.'}, status=400)

        # Check if the voter exists
        voter = get_object_or_404(Voter, ktu_id=ktu_id)

        # Check if the voter has already voted
        if voter.has_voted:
            return JsonResponse({'message': 'You have already voted.'}, status=400)

        # Validate the candidate
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

@csrf_exempt  # Temporarily disable CSRF for testing
@csrf_exempt
def register_voter(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            ktu_id = data.get('ktu_id')
            frames_data = data.get('frames_data')  # List of base64-encoded frames

            if not ktu_id or not frames_data:
                return JsonResponse({'message': 'KTU ID and frames data are required.'}, status=400)

            # Decode and process each frame
            face_data_list = []
            for frame_data in frames_data:
                # Decode the base64 image data
                image_data = base64.b64decode(frame_data.split(',')[1])
                nparr = np.frombuffer(image_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                # Perform face detection
                facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = facedetect.detectMultiScale(gray, 1.3, 5)

                if len(faces) == 0:
                    continue  # Skip frames with no face detected

                # Extract the face region
                for (x, y, w, h) in faces:
                    crop_img = frame[y:y+h, x:x+w]
                    resized_img = cv2.resize(crop_img, (50, 50))
                    face_data_list.append(resized_img.tolist())  # Convert to list for JSON serialization

            # Save face data to the database
            if len(face_data_list) > 0:
                voter = Voter(ktu_id=ktu_id)
                voter.save_face_data(face_data_list)
                return JsonResponse({'message': 'Face data captured and saved successfully.'})
            else:
                return JsonResponse({'message': 'No valid face data detected in any frame.'}, status=400)

        except Exception as e:
            return JsonResponse({'message': f'An error occurred: {str(e)}'}, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def check_face_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ktu_id = data.get('ktu_id')

            if not ktu_id:
                return JsonResponse({'error': 'KTU ID is required.'}, status=400)

            # Query the database for the voter with the given KTU ID
            voter = Voter.objects.filter(ktu_id=ktu_id).first()

            if voter:
                return JsonResponse({
                    'ktu_id': voter.ktu_id,
                    'face_data': voter.face_data,  # Ensure this is a base64-encoded image
                    'created_at': voter.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            else:
                return JsonResponse({'error': 'No face data found for the given KTU ID.'}, status=404)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)
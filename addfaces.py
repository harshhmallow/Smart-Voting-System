import cv2
import pickle
import numpy as np
import os

# Create a directory to store the data if it doesn't exist
if not os.path.exists('data/'):
    os.makedirs('data/')

# Initialize the video capture from the webcam (0 indicates the default camera)
video = cv2.VideoCapture(0)

# Load the pre-trained face detection model
facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Initialize an empty list to store face images
face_data = []
i = 0

# Get the user input for the KTU registration number
regno = input('Enter your KTU registation number:  ')

# Set the total number of frames to capture for face data
framesTotal = 51
# Set how frequently to capture frames (every 2nd frame)
captureAfterFrame = 2

# Loop to capture frames from the video feed
while True:
    ret, frame = video.read()  # Capture a frame from the video
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert the frame to grayscale
    faces = facedetect.detectMultiScale(gray, 1.3, 5)  # Detect faces in the grayscale image

    # Loop through the detected faces
    for (x, y, w, h) in faces:
        # Crop the detected face from the frame
        crop_image = frame[y:y + h, x:x + w]
        # Resize the cropped face to 50x50 pixels
        resize_image = cv2.resize(crop_image, (50, 50))
        
        # Capture the frame if we haven't yet reached the total number of frames
        # and if the frame is selected based on the capture rate (every 2nd frame)
        if len(face_data) <= framesTotal and i % captureAfterFrame == 0:
            face_data.append(resize_image)
        
        i += 1
        
        # Display the number of captured face images on the screen
        cv2.putText(frame, str(len(face_data)), (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 255), 1)
        # Draw a rectangle around the detected face
        cv2.rectangle(frame, (x, y), (x + w, y + h), (50, 50, 255), 1)

    # Display the frame with detected faces
    cv2.imshow('Add your face', frame)

    # Wait for the user to press 'q' to exit or stop if enough frames are captured
    k = cv2.waitKey(1)
    if k == ord('q') or len(face_data) >= framesTotal:
        break

# Release the video capture and close the windows
video.release()
cv2.destroyAllWindows()

# Print the total number of captured face data frames
print(len(face_data))

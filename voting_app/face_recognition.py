import cv2
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from .models import Voter

class FaceRecognition:  # Class for handling face recognition functionality

    def __init__(self):
        self.model = KNeighborsClassifier(n_neighbors=5)  # Initialize KNN classifier with 5 neighbors

        self.facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.faces = []  # Initialize faces
        self.labels = []  # Initialize labels
        self.load_training_data()

    def load_training_data(self):
        self.faces = []
        self.labels = []
        for voter in Voter.objects.all():
            face_data = voter.get_face_data()  # Assuming this returns an image
            if face_data is not None and isinstance(face_data, (np.ndarray, list)) and (isinstance(face_data, np.ndarray) and face_data.shape[0] > 0 or isinstance(face_data, list) and len(face_data) > 0):

                if isinstance(face_data, list):
                    face_data = np.array(face_data)  # Convert to NumPy array if it's a list
                print(f"Face data received for voter ID: {voter.ktu_id}, shape: {face_data.shape}" if isinstance(face_data, np.ndarray) else f"Face data received for voter ID: {voter.ktu_id}, length: {len(face_data)}")

                # Resize to a consistent size (e.g., 50x50)
                try:
                    if isinstance(face_data, np.ndarray) and face_data.ndim == 4:
                        for i in range(face_data.shape[0]):
                            face_data_resized = cv2.resize(face_data[i], (50, 50))
                            self.faces.append(face_data_resized.flatten())
                    else:
                        face_data_resized = cv2.resize(face_data, (50, 50))
                        self.faces.append(face_data_resized.flatten())
                except Exception as e:
                    print(f"Error resizing face data for voter ID: {voter.ktu_id}, error: {e}")

                for _ in range(face_data.shape[0]):  # Append label for each face sample
                    self.labels.append(voter.ktu_id)  


            else:
                print(f"No face data for voter with ID: {voter.ktu_id}")

        print(f"Faces shape: {len(self.faces)}, Labels shape: {len(self.labels)}")  # Debugging statement for loaded faces and labels

        if self.faces and self.labels:  # Check if both lists are populated
            if len(self.faces) != len(self.labels):
                raise ValueError(f"Inconsistent number of samples: Faces: {len(self.faces)}, Labels: {len(self.labels)}")
            # Convert to numpy arrays
            self.faces = np.array(self.faces)
            self.labels = np.array(self.labels)
            self.model.fit(self.faces, self.labels)

    def recognize_voter(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.facedetect.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            crop_img = frame[y:y+h, x:x+w]
            resized_img = cv2.resize(crop_img, (50, 50)).flatten().reshape(1, -1)
            prediction = self.model.predict(resized_img)
            return prediction[0]  # Return the predicted label
        return None  # Return None if no face is detected in the frame

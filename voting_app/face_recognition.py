import cv2
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from .models import Voter

class FaceRecognition:
    def __init__(self):
        self.model = KNeighborsClassifier(n_neighbors=3)  # Initialize KNN classifier
        self.facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.faces = []
        self.labels = []
        self.load_training_data()  # Load and train model on initialization

    def load_training_data(self):
        self.faces = []
        self.labels = []
        num_voters = Voter.objects.count()

        for voter in Voter.objects.all():
            face_data = voter.get_face_data()  # Fetch face data

            if face_data is None or not isinstance(face_data, (np.ndarray, list)) or (isinstance(face_data, np.ndarray) and face_data.size == 0):
                print(f"Skipping voter {voter.ktu_id}: No valid face data")
                continue

            if isinstance(face_data, list):
                face_data = np.array(face_data)  # Convert lists to NumPy arrays

            try:
                if isinstance(face_data, np.ndarray) and face_data.ndim == 4:
                    for i in range(face_data.shape[0]):
                        face_resized = cv2.resize(face_data[i], (50, 50)).flatten()
                        self.faces.append(face_resized)
                        self.labels.append(voter.ktu_id)
                else:
                    face_resized = cv2.resize(face_data, (50, 50)).flatten()
                    self.faces.append(face_resized)
                    self.labels.append(voter.ktu_id)
            except Exception as e:
                print(f"Error processing face data for voter {voter.ktu_id}: {e}")

        print(f"Loaded {len(self.faces)} face(s) with {len(self.labels)} label(s)")

        if self.faces and self.labels:  # Train only if valid data exists
            self.faces = np.array(self.faces)
            self.labels = np.array(self.labels)

            if len(self.faces) != len(self.labels):
                raise ValueError(f"Inconsistent data: {len(self.faces)} faces, {len(self.labels)} labels")

            self.model.fit(self.faces, self.labels)  # Train the KNN model
        else:
            print("Warning: No face data available for training. Model will not be trained.")

    def recognize_voter(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Dynamically adjust scaleFactor and minNeighbors based on voter count
        num_voters = Voter.objects.count()
        scaleFactor = 1.1 + (0.005 * min(num_voters, 50))
        minNeighbors = 3 if num_voters < 10 else (4 if num_voters < 50 else 5)

        print(f"Detecting faces with scaleFactor={scaleFactor}, minNeighbors={minNeighbors}")
        faces = self.facedetect.detectMultiScale(gray, scaleFactor=scaleFactor, minNeighbors=minNeighbors)

        if len(faces) == 0:
            print("No face detected in the frame.")
            return None

        for (x, y, w, h) in faces:
            cropped_face = frame[y:y+h, x:x+w]
            resized_face = cv2.resize(cropped_face, (50, 50)).flatten().reshape(1, -1)

            try:
                if hasattr(self.model, "classes_"):  # Check if model is trained
                    prediction = self.model.predict(resized_face)
                    return prediction[0]  # Return recognized voter ID
                else:
                    print("Face recognition model is not trained yet.")
                    return None
            except Exception as e:
                print(f"Error during prediction: {e}")
                return None

        return None
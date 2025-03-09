import cv2
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from .models import Voter

class FaceRecognition:
    def __init__(self):
        self.model = KNeighborsClassifier(n_neighbors=5)
        self.facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.load_training_data()

    def load_training_data(self):
        self.faces = []
        self.labels = []
        for voter in Voter.objects.all():
            face_data = voter.get_face_data()
            self.faces.append(face_data)
            self.labels.append(voter.ktu_id)
        if self.faces:
            self.model.fit(np.array(self.faces), np.array(self.labels))

    def recognize_voter(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.facedetect.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            crop_img = frame[y:y+h, x:x+w]
            resized_img = cv2.resize(crop_img, (50, 50)).flatten().reshape(1, -1)
            prediction = self.model.predict(resized_img)
            return prediction[0]
        return None
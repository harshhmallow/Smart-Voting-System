from django.db import models
from django.core.validators import RegexValidator
from cryptography.fernet import Fernet, InvalidToken
import pickle
import logging
from django.db.models.signals import pre_save
from django.dispatch import receiver

# Load encryption key from environment variable
ENCRYPTION_KEY ="e2SFWo_JW88JOSQvYbhAAQGjzdunUg2Bzrdb4oJX4sY="
print("ENCRYPTION_KEY:", ENCRYPTION_KEY)
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

logger=logging.getLogger(__name__)

# Face Registration Model
class Voter(models.Model):
    ktu_id = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^TVE22CS\d{3}$',  # Regex for TVE22CS followed by 3 digits
                message='KTU ID must be in the format TVE22CS followed by 3 digits (e.g., TVE22CS001).',
            ),
        ],
        help_text="Enter the KTU ID in the format TVE22CS followed by 3 digits (e.g., TVE22CS001).",
    )
    encrypted_face_data = models.BinaryField(
        help_text="Encrypted face data of the voter.",
    )
    has_voted = models.BooleanField(
        default=False,
        help_text="Indicates whether the voter has cast a vote.",
    )

    def save_face_data(self, face_data):
        """
        Encrypt and save multiple frames of face data.
        """
        from voting_app.face_recognition import FaceRecognition
        face_data_serialized = pickle.dumps(face_data)
        logger.debug(f"Face data before encryption for voter {self.ktu_id}: {face_data_serialized}")
        encrypted_data = cipher_suite.encrypt(face_data_serialized)
        self.encrypted_face_data = encrypted_data
        self.save()

        #  Retrain Face Recognition Model After New Voter Registration
        logger.info(f"Retraining face recognition model after registering voter {self.ktu_id}")
        FaceRecognition().load_training_data()


    def get_face_data(self):
        try:
            return pickle.loads(cipher_suite.decrypt(self.encrypted_face_data))
        
        except InvalidToken as e:
            logger.error(f"Decryption failed for voter {self.ktu_id}. Invalid token error: {e}. Encrypted data length: {len(self.encrypted_face_data) if self.encrypted_face_data else 'None'}")
            return None
    
        except Exception as e:
            logger.error(f"Unexpected error while decrypting face data for voter {self.ktu_id}: {e}")
            return None


    def can_vote(self):
        """
        Check if the voter is eligible to vote.
        """
        return not self.has_voted

    def __str__(self):
        return f"Voter: {self.ktu_id}"

# Vote Storage Model
class Vote(models.Model):
    CANDIDATE_CHOICES = [
        ('KSU', 'KSU'),
        ('SFI', 'SFI'),
        ('ABVP', 'ABVP'),
        ('NOTA', 'NOTA'),
    ]

    voter = models.OneToOneField(
        Voter,
        on_delete=models.CASCADE,
        help_text="The voter who cast this vote.",
    )
    candidate = models.CharField(
        max_length=10,
        choices=CANDIDATE_CHOICES,
        help_text="The candidate for whom the vote was cast.",
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="The time when the vote was cast.",
    )

    def save(self, *args, **kwargs):
        if Vote.objects.filter(voter=self.voter).exists():
            raise ValueError("This voter has already cast a vote.")
        
        super().save(*args, **kwargs)  # Ensure correct placement inside the class

    def __str__(self):
        return f"Vote by {self.voter.ktu_id} for {self.candidate}"

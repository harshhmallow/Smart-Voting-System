import cv2
import pickle
import numpy as np
import os

if not os.path.exists('data/'):
    os.makedirs('data/')

video=cv2.VideoCapture(0)
facedetect=cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

face_data=[]
i=0

regno=input('Enter your KTU registation number:  ')
framesTotal=51
captureAfterFrame=2

while True:
    ret,frame=video.read()
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    faces=facedetect.detectMultiScale(gray,1.3,5)

    for (x,y,w,h) in faces:
        crop_image=frame[y:y+h,x:x+w]
        resize_image=cv2.resize(crop_image,(50,50))
        if len(face_data)<=framesTotal and i%captureAfterFrame==0:
            face_data.append(resize_image)
        i+=1
        cv2.putText(frame,str(len(face_data)),(50,50),cv2.FONT_HERSHEY_COMPLEX,1,(50,50,255),1)
        cv2.rectangle(frame,(x,y),(x+w,y+h),(50,50,255),1)

    cv2.imshow('Add your face',frame)
    k=cv2.waitKey(1)
    if k==ord('q') or len(face_data)>=framesTotal:
        break
video.release()
cv2.destroyAllWindows()

print(len(face_data))


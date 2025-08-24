import face_recognition
import cv2
import pickle
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
# importin the studnets images into list 
folderModePath = 'Images'
pathList = os.listdir(folderModePath)
# print (pathList)
imgList =[]
studentsIds = []
for path in pathList :
    imgList.append(cv2.imread(os.path.join(folderModePath,path)))
    studentsIds.append(os.path.splitext(path)[0])
    # print (path)
    # print (os.path.splitext(path)[0])

print (len(imgList))
   
   
def findEncodings (imagesList) :
    encodeList = []
    for img in imagesList :
        img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
        
    return encodeList
print ('Encoding start ....')
encodeListKnown = findEncodings(imgList)
encodeListKnownWithIds =[encodeListKnown, studentsIds]
print(encodeListKnown)
print ('Encoding completed')

file = open ("EncodeFile.p" , 'wb')
pickle.dump (encodeListKnownWithIds, file)
file.close()
print ("file saved")
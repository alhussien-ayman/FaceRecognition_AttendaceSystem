import cv2
import os
import pickle
import face_recognition
import numpy as np
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred , {
    'databaseURL' : 'https://faceattendacnerealtime-f717b-default-rtdb.firebaseio.com/'
})

cap = cv2.VideoCapture(0)
cap.set(3,640)
cap.set(4,480)

imgBackground = cv2.imread('Resources/background.png')

# importing the modes images into list 
folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList =[]
for path in modePathList :
    imgModeList.append(cv2.imread(os.path.join(folderModePath,path)))

# Path for student images - Images/{id}.png format
studentImagesPath = 'Images'

# Create the directory if it doesn't exist
if not os.path.exists(studentImagesPath):
    os.makedirs(studentImagesPath)
    print(f"Created directory: {studentImagesPath}")
else:
    print(f"Student images directory exists: {studentImagesPath}")
    # List existing images
    if os.listdir(studentImagesPath):
        print("Found images:", os.listdir(studentImagesPath))
    else:
        print("No images found in the directory")
    
# load encoding file 
print ("loading encode file ..")
file = open('EncodeFile.p', 'rb')
encodeListKnownWithIds =pickle.load(file)
file.close()
encodeListKnown, studentsIds = encodeListKnownWithIds
print(studentsIds)
print ("Done loaded")

modeType = 0
counter = 0
id = -1
imgStudent = None
attendanceMarked = False  # Flag to prevent multiple attendance marking
lastRecognizedId = None   # Track last recognized student
recognitionCooldown = 0   # Cooldown counter to prevent immediate re-recognition

def loadStudentImage(studentId):
    """Load student image from Images/{id}.png"""
    try:
        # Construct the exact path: Images/{id}.png
        imgPath = f'Images/{studentId}.png'
        print(f"Looking for image at: {imgPath}")
        
        if os.path.exists(imgPath):
            print(f"Found image at: {imgPath}")
            img = cv2.imread(imgPath)
            if img is not None:
                # Resize to fit the UI area (216x216)
                resized_img = cv2.resize(img, (216, 216))
                print(f"✅ Successfully loaded and resized image for student {studentId}")
                return resized_img
            else:
                print(f"❌ Failed to read image at {imgPath} - file may be corrupted")
        else:
            print(f"❌ Image not found at: {imgPath}")
        
        return None
        
    except Exception as e:
        print(f"❌ Error loading student image: {e}")
        return None

while True:
    success, img = cap.read()
    
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    
    faceCurrentFrame = face_recognition.face_locations(imgS)
    encodeCurrentFrame = face_recognition.face_encodings(imgS, faceCurrentFrame)
    
    imgBackground[162:162+480, 55:55+640] = img
    imgBackground[44:44+633, 808:808+414] = imgModeList[modeType]
    
    # Decrease cooldown counter
    if recognitionCooldown > 0:
        recognitionCooldown -= 1
    
    if faceCurrentFrame:
        for encodeFace, faceLoc in zip(encodeCurrentFrame, faceCurrentFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            
            matchIndex = np.argmin(faceDis)
            
            if matches[matchIndex] and faceDis[matchIndex] < 0.50:  # Added distance threshold
                # Draw bounding box
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1*4, x2*4, y2*4, x1*4
                bbox = 55+x1, 162+y1, x2-x1, y2-y1
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                
                currentId = studentsIds[matchIndex]
                
                # Check if this is a new recognition or cooldown period is over
                if (not attendanceMarked or currentId != lastRecognizedId) and recognitionCooldown == 0:
                    id = currentId
                    counter = 1
                    modeType = 1
                    attendanceMarked = True
                    lastRecognizedId = currentId
                    recognitionCooldown = 30  # 30 frames cooldown (~1 second at 30fps)
    else:
        # No face detected, reset after some time
        if counter == 0:
            attendanceMarked = False
            lastRecognizedId = None
    
    if counter != 0:
        if counter == 1:
            # Get the data from database
            try:
                studentInfo = db.reference(f'Students/{id}').get()
                print(f"Student Info: {studentInfo}")
                
                if studentInfo:
                    # Update attendance data
                    ref = db.reference(f'Students/{id}')
                    studentInfo['total_attendance'] += 1
                    
                    # Update last attendance time
                    datetimeObject = datetime.now()
                    studentInfo['last_attendance_time'] = datetimeObject.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Update in database
                    ref.child('total_attendance').set(studentInfo['total_attendance'])
                    ref.child('last_attendance_time').set(studentInfo['last_attendance_time'])
                    
                    # Load student image from Images/{id}.png
                    imgStudent = loadStudentImage(id)
                    if imgStudent is None:
                        # Create a placeholder if no image found
                        imgStudent = np.zeros((216, 216, 3), dtype=np.uint8)
                        cv2.putText(imgStudent, "No Photo", (40, 108), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                        print(f"❌ Using placeholder for student ID: {id}")
                    
                    # datetimeObject = datetime.strptime(studentInfo['last_attendance_time'],'%Y-%m-%d %H:%M:%S')
                    # secondElaspsed = (datetime.now() - datetimeObject).total_seconds()
                    # print()
                else:
                    print(f"No student data found for ID: {id}")
                    counter = 0
                    modeType = 0
                    continue
                    
            except Exception as e:
                print(f"Database error: {e}")
                counter = 0
                modeType = 0
                continue
        
        # Display student image - happens every frame while counter > 0
        if imgStudent is not None:
            try:
                print(f"📸 Displaying image for student {id}, counter: {counter}")
                # Ensure correct size
                if imgStudent.shape[:2] != (216, 216):
                    imgStudent = cv2.resize(imgStudent, (216, 216))
                # Display the image in the UI
                imgBackground[175:175+216, 909:909+216] = imgStudent
            except Exception as e:
                print(f"❌ Error displaying student image: {e}")
                # Show error placeholder
                placeholder = np.zeros((216, 216, 3), dtype=np.uint8)
                cv2.putText(placeholder, "Error", (70, 108), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                imgBackground[175:175+216, 909:909+216] = placeholder
        
        if 10 < counter < 20:
            modeType = 2
            imgBackground[44:44+633, 808:808+414] = imgModeList[modeType]
        
        if counter <= 10:
            # Display student information
            if 'studentInfo' in locals() and studentInfo:
                cv2.putText(imgBackground, str(studentInfo['total_attendance']), (861, 125), 
                           cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                cv2.putText(imgBackground, str(studentInfo['major']), (1006, 550), 
                           cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(imgBackground, str(id), (1006, 493), 
                           cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(imgBackground, str(studentInfo['standing']), (910, 625), 
                           cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                cv2.putText(imgBackground, str(studentInfo['year']), (1025, 625), 
                           cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                cv2.putText(imgBackground, str(studentInfo['starting_year']), (1125, 625), 
                           cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                
                # Center the name text
                (w, h), _ = cv2.getTextSize(studentInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                offset = (414 - w) // 2
                cv2.putText(imgBackground, str(studentInfo['name']), (808 + offset, 445), 
                           cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)
        
        counter += 1
        
        if counter >= 20:
            counter = 0
            modeType = 0 
            studentInfo = None
            imgStudent = None
            attendanceMarked = False
            imgBackground[44:44+633, 808:808+414] = imgModeList[modeType]
    
    cv2.imshow('Face Attendance', imgBackground)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):  # Press 'q' to quit
        break

cap.release()
cv2.destroyAllWindows()
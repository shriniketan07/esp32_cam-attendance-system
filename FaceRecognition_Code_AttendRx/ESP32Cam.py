import cv2
import numpy as np
import face_recognition
import os
import csv
from datetime import datetime, timedelta
import requests
import urllib

# ESP32-CAM IP address
esp32cam_url = 'http://192.168.31.154/cam-hi.jpg'


# Function to fetch images from ESP32-CAM
def get_esp32cam_image():
    try:
        response = requests.get(esp32cam_url, timeout=10)
        if response.status_code == 200:
            img_array = np.array(bytearray(response.content), dtype=np.uint8)
            img = cv2.imdecode(img_array, -1)
            return img
    except Exception as e:
        print(f"Error fetching image from ESP32-CAM: {str(e)}")
    return None


path = 'Images_Basic'
images = []
classNames = []
mylist = os.listdir(path)
print(mylist)
for cl in mylist:
    curImg = cv2.imread(f'{path}/{cl}')
    images.append(curImg)
    classNames.append(os.path.splitext(cl)[0])
print(classNames)


def find_encodings(images):
    encodeList = []
    i = 0
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
        print(f'Encoding {i}/{len(mylist)} done!')
        i=i+1
    return encodeList


def markAttendance(name):
    filename = 'Attendance.csv'
    
    # Read existing data
    try:
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)  # Read all rows into a list
            nameList = [row[0] for row in rows if row]  # Extract names from the first column
    except FileNotFoundError:
        rows = []  # If the file doesn't exist, start with an empty list
        nameList = []

    # Check if the name is already in the list
    if name in nameList:
        # Find the last entry for this name
        last_entry = None
        for row in reversed(rows):
            if row[0] == name:
                last_entry = row
                break
        
        if last_entry:
            # Extract the date and time from the last entry
            last_date = last_entry[1]
            last_time = last_entry[2]
            last_datetime_str = f"{last_date} {last_time}"
            last_datetime = datetime.strptime(last_datetime_str, '%Y-%m-%d %H:%M:%S')
            
            # Calculate the time difference
            now = datetime.now()
            time_difference = now - last_datetime
            
            # Check if 15 minutes have passed
            if time_difference < timedelta(minutes=15):
                return

    # If the name is not in the list or 15 minutes have passed, mark attendance
    now = datetime.now()
    dateString = now.strftime('%Y-%m-%d')  # Format: YYYY-MM-DD
    timeString = now.strftime('%H:%M:%S')  # Format: HH:MM:SS
    
    # Append the new entry
    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([name, dateString, timeString])


encodelistknown = find_encodings(images)
print('Encoding Complete!')

while True:
    # Capture an image from ESP32-CAM
    img = get_esp32cam_image()

    if img is not None:
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodesCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        for encodeFace, faceLoc in zip(encodesCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodelistknown, encodeFace)
            faceDis = face_recognition.face_distance(encodelistknown, encodeFace)
            print(faceDis)
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                name = classNames[matchIndex].upper()
                print(name)
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                markAttendance(name)

        cv2.imshow('ESP32-CAM', img)
        cv2.waitKey(1)

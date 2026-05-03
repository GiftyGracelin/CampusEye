#========================================================================================================================================================================
#                                     Completed Attendance App Code Name & Current Time With (Co-ordinate's as a Dataset) 
#========================================================================================================================================================================

import cv2
import numpy as np
import os
from tkinter import *
from PIL import Image, ImageTk
from datetime import datetime
import mysql.connector

root = Tk()
root.title("Attendance System")
root.geometry("1280x720")

background_image = Image.open("Resources/background.png")
background_image = background_image.resize((1280, 720), Image.Resampling.LANCZOS)
background_photo = ImageTk.PhotoImage(background_image)

canvas = Canvas(root, width=1280, height=720)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, anchor=NW, image=background_photo)

video_label = Label(root, bg='white')
canvas.create_window(50, 150, anchor=NW, window=video_label, width=640, height=495)

info_label = Label(root, text="Information will be displayed here.",
                   font=("Helvetica", 15), bg='white', justify=CENTER, anchor='nw')
canvas.create_window(820, 150, anchor=NW, window=info_label, width=400, height=495)

video_capture = cv2.VideoCapture(0)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def get_lbph_recognizer():
    try:
        return cv2.face.LBPHFaceRecognizer_create()
    except Exception:
        pass
    try:
        return cv2.createLBPHFaceRecognizer()
    except Exception:
        pass
    try:
        from cv2 import face as cv2face
        return cv2face.LBPHFaceRecognizer_create()
    except Exception:
        pass
    raise RuntimeError("LBPHFaceRecognizer not available. Install opencv-contrib-python: pip install opencv-contrib-python")

recognizer = get_lbph_recognizer()
recognizer.read("trainer.yml")
label_map = np.load("labels.npy", allow_pickle=True).item()

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Gifty@2411",
        database="attendance_system"
    )

def mark_attendance(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    
    cursor.execute(
        "SELECT time FROM attendance WHERE name=%s AND date=%s ORDER BY time DESC LIMIT 1",
        (name, date_str)
    )
    result = cursor.fetchone()

    if result:
        last_time = datetime.strptime(f"{date_str} {result[0]}", "%Y-%m-%d %H:%M:%S")
        diff_minutes = (now - last_time).total_seconds() / 60.0
        if diff_minutes < 60:  
            cursor.close()
            conn.close()
            info_label.config(
                text=f"\nName: {name}\nATTENDANCE ALREADY MARKED\nLast: {last_time.strftime('%H:%M:%S')}\nTry after 1 hour."
            )
            return

    
    cursor.execute(
        "INSERT INTO attendance (name, date, time) VALUES (%s, %s, %s)",
        (name, date_str, time_str)
    )
    conn.commit()
    cursor.close()
    conn.close()

    info_label.config(
        text=f"\nName: {name}\nATTENDANCE MARKED\nTime: {time_str}\nHave a Great Day!"
    )

def looks_like_screen(frame, x, y, w, h):
    roi = frame[y:y+h, x:x+w]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    avg_brightness = np.mean(hsv[:, :, 2])
    edges = cv2.Canny(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY), 100, 200)
    edge_density = np.sum(edges > 0) / (roi.shape[0] * roi.shape[1])
    return avg_brightness > 180 and edge_density < 0.02

def process_frame():
    ret, frame = video_capture.read()
    if not ret:
        return

    frame = cv2.resize(frame, (640, 495))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

    for (x, y, w, h) in faces:
        if looks_like_screen(frame, x, y, w, h):
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0,0,255), 2)
            cv2.putText(frame, "Fake Face", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)
            info_label.config(text="Fake face detected! Please show real face.")
            continue

        roi_gray = gray[y:y+h, x:x+w]
        label, confidence = recognizer.predict(roi_gray)

        if confidence < 50: 
            recognized_name = [name for name, id in label_map.items() if id == label][0]
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
            cv2.putText(frame, recognized_name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

            
            mark_attendance(recognized_name)
        else:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0,0,255), 2)
            cv2.putText(frame, "Unknown", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)

    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)
    image = ImageTk.PhotoImage(image)
    video_label.imgtk = image
    video_label.configure(image=image)
    video_label.after(10, process_frame)

process_frame()
root.mainloop()


#========================================================================================================================================================================
#                                        Completed Attendance App Code Name & Current Time With (Image's as a Dataset) 
#========================================================================================================================================================================


# import cv2
# import numpy as np
# import os
# from tkinter import *
# from tkinter import messagebox
# from PIL import Image, ImageTk
# from datetime import datetime

# # Initialize tkinter
# root = Tk()
# root.title("Attendance System")

# # Load the background image
# background_image = Image.open("Resources/background.png")
# background_image = background_image.resize((1280, 720), Image.Resampling.LANCZOS)
# background_photo = ImageTk.PhotoImage(background_image)

# # Load the image to display after marking attendance
# marked_image_path = "Resources/3.png"
# marked_image = Image.open(marked_image_path)

# # Create a white background of 640x495 pixels
# background = Image.new('RGB', (640, 495), (255, 255, 255))

# # Calculate the position to paste the marked image at the center
# marked_image_width, marked_image_height = marked_image.size
# center_x = (640 - marked_image_width) // 2
# center_y = (495 - marked_image_height) // 2

# # Paste the marked image onto the background at the center
# background.paste(marked_image, (center_x, center_y))

# marked_photo = ImageTk.PhotoImage(background)

# # Set up the GUI elements
# canvas = Canvas(root, width=1280, height=720)
# canvas.pack()
# canvas.create_image(0, 0, anchor=NW, image=background_photo)

# # Adjust positions for the elements
# video_label = Label(root)
# canvas.create_window(50, 150, anchor=NW, window=video_label)

# # Title label
# title_label = Label(root, text="WELCOME TO PUG-ARCH TECHNOLOGY", font=("Algerian",15, "bold"), bg='white', fg='black')
# canvas.create_window(1007, 75, anchor="center", window=title_label)

# # Info label
# info_label = Label(root, text="Information will be displayed here.", font=("Helvetica", 16), bg='white')
# canvas.create_window(820, 150, anchor=NW, window=info_label)

# # Initialize webcam
# video_capture = cv2.VideoCapture(0)

# # Load the known faces and train the recognizer
# recognizer = cv2.face.LBPHFaceRecognizer_create()
# face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# def train_recognizer():
#     faces = []
#     labels = []
#     label_map = {}
#     current_label = 0

#     for filename in os.listdir('known_faces'):
#         if filename.endswith(".jpg") or filename.endswith(".png"):
#             image_path = os.path.join('known_faces', filename)
#             image = cv2.imread(image_path)
#             gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#             faces_detected = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
#             for (x, y, w, h) in faces_detected:
#                 face_roi = gray[y:y+h, x:x+w]
#                 faces.append(face_roi)
#                 labels.append(current_label)
#             person_name = os.path.splitext(filename)[0]
#             label_map[current_label] = person_name
#             current_label += 1

#     recognizer.train(faces, np.array(labels))
#     return label_map

# def load_person_info():
#     person_info = {}
#     try:
#         with open('person_info.txt', 'r') as file:
#             for line in file:
#                 if ':' in line:
#                     name, info = line.split(':', 1)
#                     person_info[name.strip()] = info.strip()
#     except FileNotFoundError:
#         print("person_info.txt not found.")
#     return person_info

# label_map = train_recognizer()
# person_info = load_person_info()

# unrecognized_shown = False  # Flag to show error message only once
# attendance_marked = False  # Flag to track if attendance is already marked

# def mark_attendance(name):
#     with open("attendance.txt", "a") as f:
#         f.write(f"{name}, {datetime.now()}\n")

# def process_frame():
#     global unrecognized_shown, attendance_marked, video_capture

#     ret, frame = video_capture.read()
#     if not ret:
#         return

#     frame = cv2.resize(frame, (640, 495))

#     if attendance_marked:
#         # Stop the webcam feed
#         video_capture.release()
#         cv2.destroyAllWindows()
        
#         # Display the marked image
#         video_label.imgtk = marked_photo
#         video_label.configure(image=marked_photo)
#         return  # Skip the face detection part

#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

#     face_names = []
#     for (x, y, w, h) in faces:
#         face_roi = gray[y:y+h, x:x+w]
#         label, confidence = recognizer.predict(face_roi)
#         name = label_map[label] if confidence < 60 else "Unknown" # Adjust threshold for better accuracy
#         face_names.append(name)

#         cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
#         cv2.rectangle(frame, (x, y+h-35), (x+w, y+h), (0, 255, 0), cv2.FILLED)
#         font = cv2.FONT_HERSHEY_DUPLEX
#         cv2.putText(frame, name, (x + 6, y+h - 6), font, 1.0, (255, 255, 255), 1)

#         if name != "Unknown":
#             info = person_info.get(name, None)
#             if info:
#                 info_label.config(text=f"\n\nName: {name}\n\n\tTime: {datetime.now().strftime('%H:%M:%S')}\n\n{info}\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nHave a Nice Day!")
#             else:
#                 info_label.config(text=f"\n\nName: {name}\n\nTime: {datetime.now().strftime('%H:%M:%S')}\n\n\n\n\n\n\n\n\n\n\n\n\n\n\t\tHave a Nice Day!")
#             mark_attendance(name)
#             attendance_marked = True  # Set the flag when a face is recognized
#             unrecognized_shown = False  # Reset the flag when a face is recognized
#         else:
#             if not unrecognized_shown:
#                 messagebox.showerror("Error", "Face not recognized!")
#                 unrecognized_shown = True  # Set the flag to prevent multiple pop-ups

#     # Display the resulting frame
#     image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     image = Image.fromarray(image)
#     image = ImageTk.PhotoImage(image)
#     video_label.imgtk = image
#     video_label.configure(image=image)

#     video_label.after(10, process_frame)

# # Start the frame processing
# process_frame()

# # Start the GUI event loop
# root.mainloop()
'''#========================================================================================================================================================================
#                                     Completed Attendance App Code Name & Current Time With (Co-ordinate's as a Dataset) 
#========================================================================================================================================================================

import cv2
import numpy as np
import os
import json
from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
from datetime import datetime
import mysql.connector

root = Tk()
root.title("Attendance System")

background_image = Image.open("Resources/background.png")
background_image = background_image.resize((1280, 720), Image.Resampling.LANCZOS)
background_photo = ImageTk.PhotoImage(background_image)

marked_image_path = "Resources/3.png"
marked_image = Image.open(marked_image_path)

background = Image.new('RGB', (640, 495), (255, 255, 255))

marked_image_width, marked_image_height = marked_image.size
center_x = (640 - marked_image_width) // 2
center_y = (495 - marked_image_height) // 2

background.paste(marked_image, (center_x, center_y))

marked_photo = ImageTk.PhotoImage(background)

canvas = Canvas(root, width=1280, height=720)
canvas.pack()
canvas.create_image(0, 0, anchor=NW, image=background_photo)

video_label = Label(root)
canvas.create_window(50, 150, anchor=NW, window=video_label)

title_label = Label(root, text="Attendance Status", font=("Algerian", 15, "bold"), bg='white', fg='black')
canvas.create_window(1007, 75, anchor="center", window=title_label)

info_label = Label(root, text="Information will be displayed here.", font=("Helvetica", 16), bg='white')
canvas.create_window(820, 150, anchor=NW, window=info_label)

video_capture = cv2.VideoCapture(0)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Gifty@2411",
        database="attendance_system"
    )

def load_face_coordinates():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, x, y, w, h FROM face_coordinates")
    data = {}
    for name, x, y, w, h in cursor.fetchall():
        coords = [x, y, w, h]
        if name not in data:
            data[name] = []
        data[name].append(coords)
    cursor.close()
    conn.close()
    return data

face_coordinates = load_face_coordinates()

def load_person_info():
    person_info = {}
    try:
        with open('person_info.txt', 'r') as file:
            for line in file:
                if ':' in line:
                    name, info = line.split(':', 1)
                    person_info[name.strip()] = info.strip()
    except FileNotFoundError:
        print("person_info.txt not found.")
    return person_info

person_info = load_person_info()

unrecognized_shown = False  
attendance_marked = False 

attendance_marked_users = set()  # Track users whose attendance is marked

def mark_attendance(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    cursor.execute(
        "INSERT INTO attendance (name, date, time) VALUES (%s, %s, %s)",
        (name, date_str, time_str)
    )
    conn.commit()
    cursor.close()
    conn.close()

def process_frame():
    global unrecognized_shown, video_capture

    ret, frame = video_capture.read()
    if not ret:
        return

    frame = cv2.resize(frame, (640, 495))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    detected_names = []

    for (x, y, w, h) in faces:
        recognized_name = None
        for name, coords_list in face_coordinates.items():
            for coords in coords_list:
                cx, cy, cw, ch = coords
                if (abs(x - cx) < 20 and abs(y - cy) < 20 and
                    abs(w - cw) < 20 and abs(h - ch) < 20):
                    recognized_name = name
                    break
            if recognized_name:
                break

        if recognized_name:
            detected_names.append(recognized_name)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, recognized_name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
            if recognized_name not in attendance_marked_users:
                info = person_info.get(recognized_name, "")
                info_label.config(text=f"\n\nName: {recognized_name}\n\nTime: {datetime.now().strftime('%H:%M:%S')}\n\n{info}\n\nHave a Nice Day!")
                mark_attendance(recognized_name)
                attendance_marked_users.add(recognized_name)
        else:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
            cv2.putText(frame, "Unknown", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)

    if not detected_names and not unrecognized_shown:
        messagebox.showerror("Error", "Face not recognized!")
        unrecognized_shown = True

    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)
    image = ImageTk.PhotoImage(image)
    video_label.imgtk = image
    video_label.configure(image=image)

    video_label.after(10, process_frame)

process_frame()

root.mainloop()
'''


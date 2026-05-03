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

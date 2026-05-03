import cv2
from ultralytics import YOLO
import mysql.connector
import time
import os
import numpy as np
from datetime import datetime, timedelta

PHONE_CLASS_ID = 67
model = YOLO('yolov8n.pt')

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Gifty@2411",
        database="attendance_system"
    )

def get_present_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT name FROM attendance
        WHERE TIMESTAMP(CONCAT(date, ' ', time)) >= NOW() - INTERVAL 1 HOUR
    """)
    students = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return students

def save_phone_detection(name, phone_minutes):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS phone_detection (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            phone_detected VARCHAR(10),
            phone_count INT,
            detected_date DATE,
            detected_time TIME
        )
    """)
    conn.commit()
    cursor.execute("""
        INSERT INTO phone_detection (name, phone_detected, phone_count, detected_date, detected_time)
        VALUES (%s, %s, %s, CURDATE(), CURTIME())
    """, (name, "Yes", phone_minutes))
    conn.commit()
    cursor.close()
    conn.close()


def save_behaviour(name, behaviour, count):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_behaviour (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            behaviour VARCHAR(50),
            count INT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.execute("""
        INSERT INTO student_behaviour (name, behaviour, count)
        VALUES (%s, %s, %s)
    """, (name, behaviour, count))
    conn.commit()
    cursor.close()
    conn.close()

def get_closest_face(phone_box, faces):
    px, py, px2, py2 = phone_box
    phone_center = ((px + px2) // 2, (py + py2) // 2)
    min_dist = float('inf')
    closest_face = None
    for (x, y, w, h, name) in faces:
        face_center = (x + w // 2, y + h // 2)
        dist = ((phone_center[0] - face_center[0]) ** 2 + (phone_center[1] - face_center[1]) ** 2) ** 0.5
        if dist < min_dist:
            min_dist = dist
            closest_face = name
    return closest_face

def main():
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("trainer.yml")

    label_map = np.load("labels.npy", allow_pickle=True).item()
    id_to_name = {v: k for k, v in label_map.items()}

    present_students = get_present_students()
    print(f"Students present in class (last 1 hr): {present_students}")

    cap = cv2.VideoCapture(0)

    detected_students = {}
    sleepy_frames = {}
    sleepy_minutes = {}

    phone_frames = {}
    phone_minutes = {}

    start_time = time.time()
    duration = 60 * 5
    minute_start = time.time()

    while (time.time() - start_time) < duration:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))

        face_list = []

        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            roi_gray = cv2.resize(roi_gray, (200, 200))
            roi_gray = cv2.equalizeHist(roi_gray)

            id_, confidence = recognizer.predict(roi_gray)

            if confidence < 60:
                name = id_to_name.get(id_)
                if name not in present_students:
                    continue

                if name not in detected_students:
                    detected_students[name] = 0
                    sleepy_frames[name] = 0
                    sleepy_minutes[name] = 0
                    phone_frames[name] = 0
                    phone_minutes[name] = 0

                face_list.append((x, y, w, h, name))
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                cv2.putText(frame, name, (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

                eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 8)
                if len(eyes) == 0:
                    sleepy_frames[name] += 1
                    cv2.putText(frame, f"{name} eyes closed",
                                (x, y+h+25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

        if (time.time() - minute_start) >= 60:
            for name in sleepy_frames:
                if sleepy_frames[name] > 60:
                    sleepy_minutes[name] += 1
                sleepy_frames[name] = 0

            for name in phone_frames:
                if phone_frames[name] > 60:
                    phone_minutes[name] += 1
                phone_frames[name] = 0

            minute_start = time.time()

        results = model(frame, verbose=False)
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                conf = float(box.conf[0])

                if class_id == PHONE_CLASS_ID and conf > 0.5:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255,0,0), 2)
                    cv2.putText(frame, "Phone", (x1, y1-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,0,0), 2)

                    closest_name = get_closest_face((x1, y1, x2, y2), face_list)
                    if closest_name:
                        detected_students[closest_name] += 1
                        phone_frames[closest_name] += 1
                        cv2.putText(frame, f"{closest_name} using phone!",
                                    (x1, y2+20),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

        cv2.imshow("Phone + Sleepiness Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    print("\n--- FINAL SUMMARY ---")

    for name in detected_students:
        print(f"{name} phone detections (frames): {detected_students[name]}")
        print(f"{name} phone usage minutes: {phone_minutes[name]}")
        print(f"{name} sleepy minutes: {sleepy_minutes[name]}")

        if phone_minutes[name] >= 4:
            save_phone_detection(name, phone_minutes[name])
            print(f"Phone usage saved for {name}")

        if sleepy_minutes[name] >= 4:
            save_behaviour(name, "sleepy", sleepy_minutes[name])
            print(f"Sleepiness saved for {name}")


if __name__ == "__main__":
    main()
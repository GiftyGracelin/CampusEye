import cv2
import mediapipe as mp
import numpy as np
import mysql.connector
import os
import time
from datetime import datetime

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

def save_posture(name, count):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posture_detection (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            posture VARCHAR(50),
            count INT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.execute("""
        INSERT INTO posture_detection (name, posture, count)
        VALUES (%s, %s, %s)
    """, (name, "lying", count))
    conn.commit()
    cursor.close()
    conn.close()

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer.yml")

label_map = np.load("labels.npy", allow_pickle=True).item()
id_to_name = {v: k for k, v in label_map.items()}

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.4, min_tracking_confidence=0.4)

cap = cv2.VideoCapture(0)
present_students = get_present_students()
print(f"Students present (last 1 hour): {present_students}")

lying_frames = {}
lying_detected = {}
lying_minutes = {}

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

start_time = time.time()
duration = 60 * 5
minute_start = time.time()

while (time.time() - start_time) < duration:
    ret, frame = cap.read()
    if not ret:
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    results = pose.process(frame_rgb)

    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
    recognized_name = None

    for (x, y, w, h) in faces:
        roi_gray = gray[y:y+h, x:x+w]
        id_, confidence = recognizer.predict(roi_gray)

        if confidence < 60:
            name = id_to_name.get(id_)
            if name in present_students:
                recognized_name = name

                if name not in lying_frames:
                    lying_frames[name] = 0
                    lying_detected[name] = 0
                    lying_minutes[name] = 0

                cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                cv2.putText(frame, name, (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        else:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0,0,255), 2)
            cv2.putText(frame, "Unknown", (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

    if recognized_name and results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark
        nose = landmarks[mp_pose.PoseLandmark.NOSE]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]

        avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        head_y = nose.y

        if abs(head_y - avg_shoulder_y) < 0.2:
            lying_frames[recognized_name] += 1
            cv2.putText(frame,
                        f"{recognized_name} lying posture detected",
                        (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0,0,255),
                        2)

        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    if (time.time() - minute_start) >= 60:
        for name in lying_frames:
            if lying_frames[name] > 60:
                lying_minutes[name] += 1
            lying_frames[name] = 0
        minute_start = time.time()

    cv2.imshow("Posture Detection (Mediapipe)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print("\n--- FINAL POSTURE SUMMARY ---")

for name in lying_minutes:
    print(f"{name} lying minutes: {lying_minutes[name]}")

    if lying_minutes[name] >= 4:
        save_posture(name, lying_minutes[name])
        print(f"Posture saved for {name}")
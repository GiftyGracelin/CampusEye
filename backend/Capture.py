#========================================================================================================================================================================
#                 Detecting the face from Web-Cam and Storing it into MySQL in simple list Format... [ Multiple Data of one Person ]
#========================================================================================================================================================================

import cv2
import os
import numpy as np
from tkinter import Tk, simpledialog

dataset_path = "dataset"
if not os.path.exists(dataset_path):
    os.makedirs(dataset_path)

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

def get_name():
    root = Tk()
    root.withdraw()
    name = simpledialog.askstring("Input", "Enter name of the person:")
    root.destroy()
    return name

def capture_faces(name, num_samples=10):
    cam = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    count = 0
    while count < num_samples:
        ret, frame = cam.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face_img = gray[y:y+h, x:x+w]
            img_path = os.path.join(dataset_path, f"{name}_{count}.jpg")
            cv2.imwrite(img_path, face_img)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            count += 1
            cv2.putText(frame, f"Capturing {count}/{num_samples}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,0,0), 2)

        cv2.imshow("Capture Faces", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()

def train_model():
    recognizer = get_lbph_recognizer()
    faces = []
    labels = []
    label_map = {}
    current_label = 0

    for file in os.listdir(dataset_path):
        if file.endswith(".jpg"):
            path = os.path.join(dataset_path, file)
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            name = file.split("_")[0]
            if name not in label_map:
                label_map[name] = current_label
                current_label += 1
            faces.append(img)
            labels.append(label_map[name])

    recognizer.train(faces, np.array(labels))
    recognizer.save("trainer.yml")
    # Save label map
    np.save("labels.npy", label_map)
    print("Training complete! LBPH model saved as trainer.yml")

if __name__ == "__main__":
    name = get_name()
    if name:
        capture_faces(name, num_samples=10)
        train_model()












''' import cv2
import numpy as np
from tkinter import Tk, simpledialog
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Gifty@2411",
        database="attendance_system"
    )

def save_coordinates(name, coords):
    conn = get_db_connection()
    cursor = conn.cursor()
    x, y, w, h = int(coords['x']), int(coords['y']), int(coords['w']), int(coords['h'])
    cursor.execute(
        "INSERT INTO face_coordinates (name, x, y, w, h) VALUES (%s, %s, %s, %s, %s)",
        (name, x, y, w, h)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_name():
    root = Tk()
    root.withdraw() 
    name = simpledialog.askstring("Input", "Enter name for the detected face:")
    root.destroy()
    return name

def main():
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    video_capture = cv2.VideoCapture(0)
    coordinates_saved = False 

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Failed to grab frame.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) > 0 and not coordinates_saved:
            x, y, w, h = faces[0]
            coords = {'x': x, 'y': y, 'w': w, 'h': h}

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"({x}, {y}, {w}, {h})", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            if cv2.waitKey(1) & 0xFF == ord('s'):
                name = get_name()
                if name:
                    save_coordinates(name, coords)
                    print(f"Coordinates saved for {name}: ({x}, {y}, {w}, {h})")
                    coordinates_saved = True

        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q') or coordinates_saved:
            coordinates_saved = False 
            break

    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() '''
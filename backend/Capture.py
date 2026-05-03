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

# 🎓 CampusEye – Smart Classroom Monitoring System

CampusEye is an AI-powered classroom monitoring system designed to automate attendance tracking and analyze student behaviour in real time using computer vision techniques.

The system integrates face recognition, object detection, and posture analysis to provide insights into student engagement inside a classroom environment.

---

## 📌 Project Overview

CampusEye enables educational institutions to digitally monitor classroom activities by:

- Automatically marking attendance using face recognition  
- Detecting mobile phone usage during class hours  
- Identifying student behaviour such as sleepiness  
- Monitoring posture (e.g., lying or inattentive positions)  
- Providing dashboards for students, staff, and administrators  

The system ensures efficient classroom management and helps improve student discipline and engagement through data-driven insights.

---

## 👥 User Roles

### 👨‍🎓 Student
- View attendance records (monthly & overall)  
- Track behaviour through calendar visualization  
- Submit leave requests  

### 👨‍🏫 Staff
- Monitor assigned students  
- View attendance and behaviour statistics  
- Manage and approve leave requests  

### 🛠️ Admin
- Approve and manage users  
- Assign students to staff  
- Monitor classroom activity  
- Control AI-based detection modules  

---

## 🤖 Core Functionalities

### Face Recognition Attendance System
- Detects and recognizes student faces  
- Automatically logs attendance with timestamp  

### Phone Detection
- Identifies mobile phone usage using object detection (YOLO)  

### Sleepiness Detection
- Detects closed eyes to identify drowsiness  

### Posture Detection
- Uses body landmarks to detect improper posture (e.g., lying)  

### Behaviour Tracking
- Stores and visualizes behaviour data for analysis  

---

## 🧰 Technologies Used

### 💻 Backend
- Python  
- FastAPI  

### 🌐 Frontend
- HTML  
- CSS  
- JavaScript  
- Chart.js  

### 🗄️ Database
- MySQL  

### 🤖 AI / Computer Vision
- OpenCV (Face Detection & Recognition - LBPH)  
- YOLOv8 (Object Detection for phone usage)  
- MediaPipe (Posture Detection)  
- NumPy  

---

## 🎯 Key Highlights

- Real-time AI-based monitoring system  
- Multi-user role-based architecture  
- Integrated attendance and behaviour analytics  
- Combination of multiple computer vision techniques  
- Practical application of AI in education systems  

---

## 📌 Conclusion

CampusEye demonstrates how artificial intelligence and computer vision can be effectively applied to automate classroom management tasks. It provides a scalable foundation for building smart educational environments with enhanced monitoring and analytics capabilities.

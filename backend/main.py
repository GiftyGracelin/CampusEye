from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
import subprocess, sys, os
import calendar

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Gifty@2411",
        database="attendance_system"
    )


def ensure_behaviour_tables(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS phone_detection (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            phone_detected VARCHAR(10),
            phone_count INT,
            detected_date DATE,
            detected_time TIME
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS posture_detection (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            posture VARCHAR(50),
            count INT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_behaviour (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            behaviour VARCHAR(50),
            count INT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


# ---------------- AUTH ----------------
@app.post("/login")
def login(data: dict):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT role, approved FROM users WHERE username=%s AND password=%s",
                (data["username"], data["password"]))
    res = cur.fetchone()
    cur.close(); conn.close()
    if not res:
        return {"status": "fail"}
    role, approved = res
    if approved == 0:
        return {"status": "not approved"}
    return {"status": "ok", "role": role}


@app.post("/register")
def register(data: dict):
    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username,password,role,approved,assigned_staff) VALUES(%s,%s,%s,0,NULL)",
                (data["username"], data["password"], data["role"]))
    conn.commit()
    cur.close(); conn.close()
    return {"msg": "waiting"}


# ---------------- ADMIN ----------------
@app.get("/pending")
def pending():
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT username, role FROM users WHERE approved=0")
    data = cur.fetchall()
    cur.close(); conn.close()
    return data


@app.get("/staffs")
def staffs():
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE role='staff' AND approved=1")
    data = cur.fetchall()
    cur.close(); conn.close()
    return data


@app.post("/approve")
def approve(data: dict):
    conn = db(); cur = conn.cursor()
    cur.execute("UPDATE users SET approved=1, assigned_staff=%s WHERE username=%s",
                (data.get("staff"), data["username"]))
    if data.get("staff"):
        cur.execute("INSERT IGNORE INTO mapping (student, staff) VALUES(%s,%s)",
                    (data["username"], data["staff"]))
    conn.commit()
    cur.close(); conn.close()
    return {"msg": "approved"}


# ---------------- STUDENT ----------------
@app.get("/student-home/{user}")
def student_home(user: str):
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT assigned_staff FROM users WHERE username=%s", (user,))
    staff = cur.fetchone()
    cur.close(); conn.close()
    return {"staff": staff[0] if staff else "Not assigned"}


@app.get("/attendance/{user}")
def attendance(user: str):
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM attendance WHERE name=%s", (user,))
    present = cur.fetchone()[0] or 0
    total = 30
    cur.close(); conn.close()
    return {"present": present, "absent": max(total - present, 0)}


@app.get("/attendance-month/{user}")
def attendance_month(user: str, month: int, year: int):
    conn = db(); cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM attendance WHERE name=%s AND MONTH(date)=%s AND YEAR(date)=%s",
        (user, month, year),
    )
    present = cur.fetchone()[0] or 0
    total = calendar.monthrange(year, month)[1]
    cur.close(); conn.close()
    return {"present": present, "absent": max(total - present, 0)}


@app.get("/attendance-table/{user}")
def attendance_table(user: str):
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT date, time FROM attendance WHERE name=%s ORDER BY date, time", (user,))
    data = cur.fetchall()
    cur.close(); conn.close()
    return data


@app.get("/behaviour-calendar/{user}")
def behaviour_calendar(user: str, month: int = None, year: int = None):
    conn = db(); cur = conn.cursor()
    ensure_behaviour_tables(cur)

    month_filter = ""
    params = [user]
    if month and year:
        month_filter = " AND MONTH(detected_date)=%s AND YEAR(detected_date)=%s"
        params.extend([month, year])

    query = f"""
        SELECT DATE(detected_date) AS event_date, 'phone' AS category, COUNT(*) AS total
        FROM phone_detection
        WHERE name=%s{month_filter}
        GROUP BY DATE(detected_date)
        UNION ALL
        SELECT DATE(detected_at) AS event_date, 'posture' AS category, COUNT(*) AS total
        FROM posture_detection
        WHERE name=%s{month_filter.replace('detected_date', 'detected_at')}
        GROUP BY DATE(detected_at)
        UNION ALL
        SELECT DATE(detected_at) AS event_date, 'behaviour' AS category, COUNT(*) AS total
        FROM student_behaviour
        WHERE name=%s{month_filter.replace('detected_date', 'detected_at')}
        GROUP BY DATE(detected_at)
        ORDER BY event_date DESC, category
    """
    if month and year:
        params.extend([user, month, year, user, month, year])
    else:
        params = [user, user, user]

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [{"date": str(row[0]), "category": row[1], "total": row[2]} for row in rows]


# ---------------- LEAVE ----------------
@app.post("/leave")
def leave(data: dict):
    conn = db(); cur = conn.cursor()
    cur.execute("INSERT INTO leave_requests(user, reason, status) VALUES(%s,%s,'pending')",
                (data["user"], data["reason"]))
    conn.commit()
    cur.close(); conn.close()
    return {"msg": "sent"}


@app.get("/student-leaves/{user}")
def student_leaves(user: str):
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT id, reason, status, created_at FROM leave_requests WHERE user=%s ORDER BY created_at DESC", (user,))
    data = cur.fetchall()
    cur.close(); conn.close()
    return data


@app.get("/leaves")
def leaves():
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT id, user, reason, status, created_at FROM leave_requests ORDER BY created_at DESC")
    data = cur.fetchall()
    cur.close(); conn.close()
    return data


@app.post("/approve-leave")
def approve_leave(data: dict):
    conn = db(); cur = conn.cursor()
    cur.execute("UPDATE leave_requests SET status='approved' WHERE id=%s", (data["id"],))
    conn.commit()
    cur.close(); conn.close()
    return {"msg": "ok"}


# ---------------- STAFF ----------------
@app.get("/staff-students/{staff}")
def staff_students(staff: str):
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT student FROM mapping WHERE staff=%s", (staff,))
    students = [row[0] for row in cur.fetchall()]
    data = []
    for student in students:
        cur.execute("SELECT COUNT(*) FROM attendance WHERE name=%s", (student,))
        present = cur.fetchone()[0] or 0
        total = 30
        cur.execute("SELECT COUNT(*) FROM student_behaviour WHERE name=%s", (student,))
        sleepiness_count = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM phone_detection WHERE name=%s", (student,))
        phone_events = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM posture_detection WHERE name=%s", (student,))
        posture_events = cur.fetchone()[0] or 0
        data.append({
            "student": student,
            "present": present,
            "absent": max(total - present, 0),
            "sleepiness_count": sleepiness_count,
            "phone_events": phone_events,
            "posture_events": posture_events,
        })
    cur.close(); conn.close()
    return data


# ---------------- MONITOR CLASSROOM ----------------
@app.get("/run-capture")
def run_capture():
    try:
        subprocess.Popen([sys.executable, "Capture.py"], cwd=os.path.dirname(__file__))
        return {"msg": "capture started"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/run-attendance-ai")
def run_attendance_ai():
    try:
        subprocess.Popen([sys.executable, "attendance_system.py"], cwd=os.path.dirname(__file__))
        return {"msg": "attendance started"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/run-behaviour")
def run_behaviour():
    try:
        subprocess.Popen([sys.executable, "phone_detection.py"], cwd=os.path.dirname(__file__))
        subprocess.Popen([sys.executable, "posture_detection.py"], cwd=os.path.dirname(__file__))
        return {"msg": "behaviour started"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/run-phone-detection")
def run_phone_detection():
    try:
        subprocess.Popen([sys.executable, "phone_detection.py"], cwd=os.path.dirname(__file__))
        return {"msg": "phone detection started"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/run-posture-detection")
def run_posture_detection():
    try:
        subprocess.Popen([sys.executable, "posture_detection.py"], cwd=os.path.dirname(__file__))
        return {"msg": "posture detection started"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/all-staff")
def all_staff():
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE role='staff'")
    staff = cur.fetchall()
    cur.close(); conn.close()
    return [s[0] for s in staff]


@app.get("/all-students")
def all_students():
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE role='student'")
    students = cur.fetchall()
    cur.close(); conn.close()
    return [s[0] for s in students]


@app.get("/staff-students-admin")
def staff_students_admin():
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE role='staff'")
    staff_list = [s[0] for s in cur.fetchall()]
    result = []
    for staff in staff_list:
        cur.execute("SELECT username FROM users WHERE role='student' AND assigned_staff=%s", (staff,))
        students = [s[0] for s in cur.fetchall()]
        result.append({"staff": staff, "students": students})
    cur.close(); conn.close()
    return result


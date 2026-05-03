const apiRoot = "http://127.0.0.1:8000";
const user = localStorage.getItem("user");
let attendanceChartInstance = null;

function getById(id) {
  return document.getElementById(id);
}

function ensureAuthPage() {
  if (!user) {
    window.location.href = "index.html";
    return false;
  }
  return true;
}

function fetchJson(url, options) {
  return fetch(url, options).then((res) => res.json());
}

function populateMonthYearSelects() {
  const monthNames = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December",
  ];
  const attendanceMonth = getById("attendanceMonth");
  const attendanceYear = getById("attendanceYear");
  const behaviourMonth = getById("behaviourMonth");
  const behaviourYear = getById("behaviourYear");

  if (!attendanceMonth || !attendanceYear || !behaviourMonth || !behaviourYear) return;

  const today = new Date();
  const currentYear = today.getFullYear();
  const currentMonth = today.getMonth();

  attendanceMonth.innerHTML = monthNames
    .map((name, index) => `<option value="${index + 1}" ${index === currentMonth ? "selected" : ""}>${name}</option>`)
    .join("");
  behaviourMonth.innerHTML = attendanceMonth.innerHTML;

  const yearOptions = Array.from({ length: 5 }, (_, i) => currentYear - i)
    .map((year) => `<option value="${year}">${year}</option>`)
    .join("");
  attendanceYear.innerHTML = yearOptions;
  behaviourYear.innerHTML = yearOptions;
}

function loadAttendanceMonth() {
  if (!ensureAuthPage()) return;
  const month = getById("attendanceMonth")?.value;
  const year = getById("attendanceYear")?.value;
  if (!month || !year) return;

  fetchJson(`${apiRoot}/attendance-month/${user}?month=${month}&year=${year}`)
    .then((data) => {
      const chartEl = getById("attendanceChart");
      const labels = ["Present", "Absent"];
      const values = [data.present, data.absent];

      if (attendanceChartInstance) {
        attendanceChartInstance.destroy();
      }
      attendanceChartInstance = new Chart(chartEl, {
        type: "pie",
        data: {
          labels,
          datasets: [{
            data: values,
            backgroundColor: ["#1cc88a", "#e74a3b"],
          }],
        },
        options: {
          responsive: true,
          plugins: {
            legend: { position: "bottom" },
          },
        },
      });

      getById("attendanceStats").innerHTML = `
        <h3>${getById("attendanceMonth").selectedOptions[0].text} ${year}</h3>
        <p><strong>Present:</strong> ${data.present}</p>
        <p><strong>Absent:</strong> ${data.absent}</p>
      `;
    });
}

function loadBehaviourCalendar() {
  if (!ensureAuthPage()) return;
  const month = getById("behaviourMonth")?.value;
  const year = getById("behaviourYear")?.value;
  if (!month || !year) return;

  fetchJson(`${apiRoot}/behaviour-calendar/${user}?month=${month}&year=${year}`).then((events) => {
    const calendar = getById("calendar");
    const summary = getById("calendarSummary");
    const eventMap = {};
    events.forEach((item) => {
      if (!eventMap[item.date]) eventMap[item.date] = [];
      eventMap[item.date].push(item);
    });

    const monthIndex = parseInt(month, 10) - 1;
    const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();

    let html = "";
    for (let day = 1; day <= daysInMonth; day++) {
      const isoDate = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
      const row = eventMap[isoDate] || [];
      const badges = row
        .map((event) => `<span class="badge ${event.category}">${event.category}</span>`)
        .join(" ");
      html += `
        <div class="calendar-day ${row.length ? "marked" : ""}">
          <strong>${day}</strong>
          <div>${badges || "No events"}</div>
        </div>`;
    }
    calendar.innerHTML = html;

    const totals = events.reduce((acc, item) => {
      acc[item.category] = (acc[item.category] || 0) + item.total;
      return acc;
    }, {});
    summary.innerHTML = `
      <h3>${getById("behaviourMonth").selectedOptions[0].text} ${year} Summary</h3>
      <p><strong>Phone Events:</strong> ${totals.phone || 0}</p>
      <p><strong>Posture Events:</strong> ${totals.posture || 0}</p>
      <p><strong>Sleepiness Events:</strong> ${totals.behaviour || 0}</p>
    `;
  });
}

function login() {
  const username = getById("u")?.value;
  const password = getById("p")?.value;
  if (!username || !password) return alert("Enter username and password.");

  fetchJson(`${apiRoot}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  }).then((data) => {
    if (data.status === "ok") {
      localStorage.setItem("user", username);
      if (data.role === "student") window.location.href = "student.html";
      if (data.role === "staff") window.location.href = "staff.html";
      if (data.role === "admin") window.location.href = "admin.html";
    } else {
      alert(data.status);
    }
  });
}

function register() {
  const username = getById("u")?.value;
  const password = getById("p")?.value;
  const role = getById("r")?.value;
  if (!username || !password || !role) return alert("Enter all registration details.");

  fetchJson(`${apiRoot}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, role }),
  }).then(() => alert("Registration submitted. Wait for approval."));
}

function logout() {
  localStorage.clear();
  window.location.href = "index.html";
}

function scrollToSection(id) {
  const section = getById(id);
  if (section) section.scrollIntoView({ behavior: "smooth", block: "start" });
}

function pending() {
  fetchJson(`${apiRoot}/pending`).then((pendingUsers) => {
    fetchJson(`${apiRoot}/staffs`).then((staffs) => {
      const html = pendingUsers
        .map(([username, role]) => {
          const dropdown =
            role === "student"
              ? `<select id="s_${username}">${staffs
                  .map((s) => `<option>${s[0]}</option>`)
                  .join("")}</select>`
              : "";
          return `<div class="card">
            <strong>${username}</strong> (${role})
            ${dropdown}
            <button onclick="approveUser('${username}','${role}')">Approve</button>
          </div>`;
        })
        .join("");
      getById("adminData").innerHTML = html || "<p>No pending users.</p>";
    });
  });
}

function approveUser(username, role) {
  let staff = null;
  if (role === "student") {
    staff = getById(`s_${username}`)?.value || null;
  }
  fetchJson(`${apiRoot}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, staff }),
  }).then(() => pending());
}

function runCapture() {
  fetchJson(`${apiRoot}/run-capture`).then((data) => {
    getById("adminMessage").innerText = data.msg || data.error || "Capture started.";
  });
}

function runAttendanceAI() {
  fetchJson(`${apiRoot}/run-attendance-ai`).then((data) => {
    getById("adminMessage").innerText = data.msg || data.error || "Attendance started.";
  });
}

function runBehaviour() {
  fetchJson(`${apiRoot}/run-behaviour`).then((data) => {
    getById("adminMessage").innerText = data.msg || data.error || "Behaviour started.";
  });
}

function runPhoneDetection() {
  fetchJson(`${apiRoot}/run-phone-detection`).then((data) => {
    getById("adminMessage").innerText = data.msg || data.error || "Phone detection started.";
  });
}

function runPostureDetection() {
  fetchJson(`${apiRoot}/run-posture-detection`).then((data) => {
    getById("adminMessage").innerText = data.msg || data.error || "Posture detection started.";
  });
}

function loadAllUsers() {
  fetchJson(`${apiRoot}/staff-students-admin`).then((data) => {
    getById("staffStudentsTable").innerHTML = data.length
      ? `<table>
           <thead><tr><th>Staff</th><th>Students</th></tr></thead>
           <tbody>${data.map(item => `<tr><td>${item.staff}</td><td>${item.students.join(", ")}</td></tr>`).join("")}</tbody>
         </table>`
      : "<p>No staff found.</p>";
  });
}

function loadHome() {
  if (!ensureAuthPage()) return;
  fetchJson(`${apiRoot}/student-home/${user}`).then((data) => {
    getById("homeInfo").innerHTML = `
      <h2>Welcome ${user}</h2>
      <p><strong>Assigned Staff:</strong> ${data.staff || "Not assigned"}</p>
    `;
  });
}

function loadAttendanceSummary() {
  if (!ensureAuthPage()) return;
  fetchJson(`${apiRoot}/attendance/${user}`).then((data) => {
    getById("attendanceStats").innerHTML = `
      <h3>Attendance Summary</h3>
      <p><strong>Present:</strong> ${data.present}</p>
      <p><strong>Absent:</strong> ${data.absent}</p>
    `;
  });
}

function loadAttendanceTable() {
  if (!ensureAuthPage()) return;
  fetchJson(`${apiRoot}/attendance-table/${user}`).then((rows) => {
    getById("attendanceTable").innerHTML = rows.length
      ? `<h3>Attendance Records</h3>
         <table>
           <thead><tr><th>Date</th><th>Time</th></tr></thead>
           <tbody>${rows
             .map((row) => `<tr><td>${row[0]}</td><td>${row[1]}</td></tr>`)
             .join("")}</tbody>
         </table>`
      : "<p>No attendance records found.</p>";
  });
}

function leave() {
  if (!ensureAuthPage()) return;
  const reason = getById("reason")?.value;
  if (!reason) return alert("Enter a leave reason.");

  fetchJson(`${apiRoot}/leave`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user, reason }),
  }).then(() => {
    getById("reason").value = "";
    loadLeaveHistory();
  });
}

function loadLeaveHistory() {
  if (!ensureAuthPage()) return;
  fetchJson(`${apiRoot}/student-leaves/${user}`).then((rows) => {
    getById("leaveHistory").innerHTML = rows.length
      ? rows
          .map(
            (row) => `<div class="card">
              <p><strong>Reason:</strong> ${row[1]}</p>
              <p><strong>Status:</strong> ${row[2]}</p>
              <p><strong>Date:</strong> ${row[3]}</p>
            </div>`
          )
          .join("")
      : "<p>No leave requests found.</p>";
  });
}

function loadStaffStudents() {
  if (!ensureAuthPage()) return;
  fetchJson(`${apiRoot}/staff-students/${user}`).then((students) => {
    getById("data").innerHTML = students.length
      ? `<table>
           <thead>
             <tr>
               <th>Student</th>
               <th>Present</th>
               <th>Absent</th>
               <th>Sleepiness Detected Count</th>
               <th>Phone Detected Count</th>
               <th>Lying Down Count</th>
             </tr>
           </thead>
           <tbody>${students
             .map(
               (student) => `<tr>
                 <td>${student.student}</td>
                 <td>${student.present}</td>
                 <td>${student.absent}</td>
                 <td>${student.sleepiness_count}</td>
                 <td>${student.phone_events}</td>
                 <td>${student.posture_events}</td>
               </tr>`
             )
             .join("")}</tbody>
         </table>`
      : "<p>No assigned students found.</p>";
  });
}

function loadLeaves() {
  if (!ensureAuthPage()) return;
  fetchJson(`${apiRoot}/leaves`).then((rows) => {
    getById("leaveData").innerHTML = rows.length
      ? rows
          .map(
            (row) => `<div class="card">
              <p><strong>User:</strong> ${row[1]}</p>
              <p><strong>Reason:</strong> ${row[2]}</p>
              <p><strong>Status:</strong> ${row[3]}</p>
              <p><strong>Date:</strong> ${row[4]}</p>
              <button onclick="approveLeave(${row[0]})">Approve</button>
            </div>`
          )
          .join("")
      : "<p>No leave requests found.</p>";
  });
}

function approveLeave(id) {
  fetchJson(`${apiRoot}/approve-leave`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id }),
  }).then(() => loadLeaves());
}

window.addEventListener("DOMContentLoaded", () => {
  const page = window.location.pathname.split("/").pop();
  if (page === "student.html") {
    populateMonthYearSelects();
    loadHome();
    loadAttendanceMonth();
    loadBehaviourCalendar();
    loadLeaveHistory();
  }
  if (page === "staff.html") {
    loadStaffStudents();
    loadLeaves();
  }
  if (page === "admin.html") {
    pending();
  }
});

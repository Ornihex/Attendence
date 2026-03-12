const state = {
  apiBase: `${window.location.origin}/api/v1`,
  token: "",
  role: "",
  userId: null,
  selectedClassId: null,
  attendanceEditClassId: null,
};

const el = (id) => document.getElementById(id);
const excusedReasons = [
  "Болезнь",
  "Семейные обстоятельства",
  "Официальное мероприятие",
  "Другое",
];

const toast = (message, isError = false) => {
  const node = el("toast");
  node.textContent = message;
  node.classList.remove("hidden", "error");
  if (isError) node.classList.add("error");
  setTimeout(() => node.classList.add("hidden"), 3200);
};

const request = async (path, options = {}) => {
  const headers = options.headers || {};
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const res = await fetch(`${state.apiBase}${path}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.message || `HTTP ${res.status}`);
  }
  return data;
};

const setRoleVisibility = () => {
  document.querySelectorAll(".admin-only").forEach((node) => {
    node.classList.toggle("hidden", state.role !== "admin");
  });
};

const activateTab = (id) => {
  document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach((v) => v.classList.remove("active"));
  document.querySelector(`[data-tab="${id}"]`)?.classList.add("active");
  el(id).classList.add("active");
};

const renderItems = (containerId, items, formatter) => {
  const container = el(containerId);
  container.innerHTML = "";
  if (!items || items.length === 0) {
    container.innerHTML = `<div class="item muted">Нет данных</div>`;
    return;
  }
  items.forEach((item) => {
    const node = document.createElement("div");
    node.className = "item";
    node.innerHTML = formatter(item);
    container.appendChild(node);
  });
};

const loadUsers = async () => {
  if (state.role !== "admin") return;
  const users = await request("/users");
  populateTeacherSelects(users);
  populateRoleUserSelect(users);
  renderItems(
    "usersList",
    users,
    (u) =>
      `<b>#${u.id}</b> ${u.login} <span class="mono">(${u.role})</span><br><span class="muted">classId: ${
        u.classId ?? "-"
      }, promotedBy: ${u.promotedBy ?? "-"}</span>`
  );
};

const populateRoleUserSelect = (users) => {
  const select = el("roleUserId");
  const prev = select.value;
  select.innerHTML = ['<option value="">Выберите пользователя</option>']
    .concat(users.map((u) => `<option value="${u.id}">#${u.id} - ${u.login} (${u.role})</option>`))
    .join("");
  if (prev && users.some((u) => String(u.id) === prev)) {
    select.value = prev;
  }
};

const populateTeacherSelects = (users) => {
  const teachers = users.filter((u) => u.role === "teacher");
  const ids = ["classTeacherId", "credTeacherId"];
  ids.forEach((id) => {
    const select = el(id);
    const prev = select.value;
    select.innerHTML = ['<option value="">Выберите учителя</option>']
      .concat(teachers.map((t) => `<option value="${t.id}">#${t.id} - ${t.login}</option>`))
      .join("");
    if (prev && teachers.some((t) => String(t.id) === prev)) {
      select.value = prev;
    }
  });
};

const populateAttendanceClassSelect = (classes) => {
  const classSelectIds = ["attendanceEditClassId", "attendanceClassId", "statsClassId"];
  classSelectIds.forEach((id) => {
    const select = el(id);
    const previousValue = select.value;
    const options = ['<option value="">Выберите класс</option>'].concat(
      classes.map((c) => `<option value="${c.id}">#${c.id} - ${c.name}</option>`)
    );
    select.innerHTML = options.join("");
    if (previousValue && classes.some((c) => String(c.id) === previousValue)) {
      select.value = previousValue;
    } else if (state.selectedClassId && classes.some((c) => c.id === state.selectedClassId)) {
      select.value = String(state.selectedClassId);
    }
  });
};

const populateDashboardClassSelect = (classes) => {
  const select = el("dashboardClassSelect");
  const previousValue = select.value;
  select.innerHTML = ['<option value="">Выберите класс</option>']
    .concat(classes.map((c) => `<option value="${c.id}">#${c.id} - ${c.name}</option>`))
    .join("");
  if (previousValue && classes.some((c) => String(c.id) === previousValue)) {
    select.value = previousValue;
  } else if (state.selectedClassId && classes.some((c) => c.id === state.selectedClassId)) {
    select.value = String(state.selectedClassId);
  }
};

const loadClasses = async () => {
  const classes = await request("/classes");
  populateDashboardClassSelect(classes);
  populateAttendanceClassSelect(classes);
};

const applySelectedClass = async (classIdValue) => {
  if (!classIdValue) return;
  state.selectedClassId = Number(classIdValue);
  el("selectedClassInfo").textContent = `Выбран classId: ${state.selectedClassId}`;
  el("attendanceEditClassId").value = String(state.selectedClassId);
  el("attendanceClassId").value = String(state.selectedClassId);
  el("statsClassId").value = String(state.selectedClassId);
  await loadStudents();
};

const loadStudents = async () => {
  if (!state.selectedClassId) return;
  const students = await request(`/classes/${state.selectedClassId}/students`);
  const select = el("updateStudentId");
  const previousValue = select.value;
  select.innerHTML = ['<option value="">Выберите ученика</option>']
    .concat(students.map((s) => `<option value="${s.id}">#${s.id} - ${s.fullName}</option>`))
    .join("");
  if (previousValue && students.some((s) => String(s.id) === previousValue)) {
    select.value = previousValue;
  }
  renderItems(
    "studentsList",
    students,
    (s) => `<b>#${s.id}</b> ${s.fullName} <span class="muted">active: ${s.isActive ? "yes" : "no"}</span>`
  );
};

const renderAttendanceTable = (block) => {
  const filledLabel = block.isFilled ? "Заполнено" : "Не заполнено";
  const filledClass = block.isFilled ? "" : "warn";
  const unexcused = block.absentUnexcused || [];
  const excused = block.absentExcused || [];
  const unexcusedRows = unexcused
    .map((r) => `<tr><td>${r.studentId}</td><td>${r.fullName}</td><td>неуваж.</td></tr>`)
    .join("");
  const excusedRows = excused
    .map((r) => `<tr><td>${r.studentId}</td><td>${r.fullName}</td><td>${r.reason || "уваж."}</td></tr>`)
    .join("");
  const rows = `${unexcusedRows}${excusedRows}`;
  return `<div class="item"><b>Class #${block.classId}</b> <span class="muted">${block.date}</span> <span class="fill-flag ${filledClass}">${filledLabel}</span><div class="muted">Всего: ${block.totalStudents}, присутствуют: ${block.presentCount}</div><table class="attendance-table"><thead><tr><th>ID</th><th>Ученик</th><th>Причина</th></tr></thead><tbody>${rows}</tbody></table></div>`;
};

const loadAttendance = async () => {
  const dateValue = el("attendanceDate").value;
  const classIdValue = el("attendanceClassId").value;
  const allClasses = el("attendanceAllClasses").checked && state.role === "admin";
  const query = allClasses
    ? `?date=${dateValue}`
    : `?date=${dateValue}${classIdValue ? `&classId=${classIdValue}` : ""}`;
  const data = await request(`/attendance${query}`);
  const container = el("attendanceResult");
  container.innerHTML = "";
  if (Array.isArray(data)) {
    container.innerHTML = data.map(renderAttendanceTable).join("");
  } else {
    container.innerHTML = renderAttendanceTable(data);
  }
};

const renderAttendanceEditor = (block) => {
  const unexcusedMap = new Set((block.absentUnexcused || []).map((r) => r.studentId));
  const excusedMap = new Map((block.absentExcused || []).map((r) => [r.studentId, r.reason || ""]));
  const table = document.createElement("table");
  table.className = "attendance-table";
  table.innerHTML = `
    <thead>
      <tr>
        <th>ID</th>
        <th>Ученик</th>
        <th>Неуваж.</th>
        <th>Уважительная причина</th>
      </tr>
    </thead>
    <tbody>
      ${block.studentList
        .map(
          (r) => `
        <tr>
          <td>${r.studentId}</td>
          <td>${r.fullName}</td>
          <td>
            <input type="checkbox" class="attendance-unexcused" data-student-id="${r.studentId}" ${unexcusedMap.has(r.studentId) ? "checked" : ""} />
          </td>
          <td>
            <select class="attendance-excused" data-student-id="${r.studentId}">
              <option value="">—</option>
              ${excusedReasons
                .map(
                  (reason) =>
                    `<option value="${reason}" ${excusedMap.get(r.studentId) === reason ? "selected" : ""}>${reason}</option>`
                )
                .join("")}
            </select>
          </td>
        </tr>
      `
        )
        .join("")}
    </tbody>
  `;
  const box = el("attendanceEditTable");
  box.innerHTML = "";
  box.appendChild(table);
  el("attendanceEditInfo").textContent = `Class #${block.classId}, date ${block.date}`;
  el("attendanceSaveBtn").classList.remove("hidden");
  el("attendanceBulkActions").classList.remove("hidden");

  document.querySelectorAll(".attendance-unexcused").forEach((box) => {
    box.addEventListener("change", () => {
      if (box.checked) {
        const selector = document.querySelector(
          `.attendance-excused[data-student-id="${box.dataset.studentId}"]`
        );
        if (selector) selector.value = "";
      }
    });
  });
  document.querySelectorAll(".attendance-excused").forEach((select) => {
    select.addEventListener("change", () => {
      if (select.value) {
        const box = document.querySelector(
          `.attendance-unexcused[data-student-id="${select.dataset.studentId}"]`
        );
        if (box) box.checked = false;
      }
    });
  });
};

const loadAttendanceForEdit = async () => {
  const dateValue = el("attendanceEditDate").value;
  let classIdValue = el("attendanceEditClassId").value;
  if (!classIdValue && state.selectedClassId) {
    classIdValue = String(state.selectedClassId);
    el("attendanceEditClassId").value = classIdValue;
  }
  const query = classIdValue ? `?date=${dateValue}&classId=${classIdValue}` : `?date=${dateValue}`;
  const data = await request(`/attendance${query}`);
  if (Array.isArray(data)) {
    throw new Error("Для редактирования укажите конкретный classId");
  }
  const studentList = (data.absentUnexcused || [])
    .concat(data.absentExcused || [])
    .reduce((acc, _) => acc, []);
  const students = await request(`/classes/${data.classId}/students`);
  const block = {
    ...data,
    studentList: students.map((s) => ({ studentId: s.id, fullName: s.fullName })),
  };
  state.attendanceEditClassId = data.classId;
  renderAttendanceEditor(block);
};

const saveAttendanceEdit = async () => {
  const dateValue = el("attendanceEditDate").value;
  const classId = Number(state.attendanceEditClassId || el("attendanceEditClassId").value);
  if (!dateValue || !classId) {
    throw new Error("Укажите дату и classId");
  }
  const unexcused = new Set(
    Array.from(document.querySelectorAll(".attendance-unexcused"))
      .filter((node) => node.checked)
      .map((node) => Number(node.dataset.studentId))
  );
  const excused = Array.from(document.querySelectorAll(".attendance-excused"))
    .filter((node) => node.value)
    .map((node) => ({ studentId: Number(node.dataset.studentId), reason: node.value }));
  const excusedIds = new Set(excused.map((r) => r.studentId));
  for (const id of unexcused) {
    if (excusedIds.has(id)) {
      throw new Error("Нельзя одновременно указать неуваж. и уважительную причину");
    }
  }
  await request(`/attendance?date=${dateValue}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      classId,
      unexcusedStudentIds: Array.from(unexcused),
      excused,
    }),
  });
};

const setAllUnexcused = () => {
  document.querySelectorAll(".attendance-unexcused").forEach((node) => {
    node.checked = true;
  });
  document.querySelectorAll(".attendance-excused").forEach((node) => {
    node.value = "";
  });
};

const clearAllAttendance = () => {
  document.querySelectorAll(".attendance-unexcused").forEach((node) => {
    node.checked = false;
  });
  document.querySelectorAll(".attendance-excused").forEach((node) => {
    node.value = "";
  });
};

const renderWeeklyStats = (block) => {
  return `<div class="item"><b>Class #${block.classId}</b> <span class="muted">${block.from} .. ${block.to}</span><div class="muted">Всего: ${block.totalStudents}, присутствуют: ${block.presentCount}, заполнено дней: ${block.filledDays}</div></div>`;
};

const loadStats = async () => {
  const startDate = el("statsStartDate").value;
  const classIdValue = el("statsClassId").value;
  const allClasses = el("statsAllClasses").checked && state.role === "admin";
  const query = allClasses
    ? `?startDate=${startDate}`
    : `?startDate=${startDate}${classIdValue ? `&classId=${classIdValue}` : ""}`;
  const data = await request(`/statistics/weekly${query}`);
  const container = el("statsResult");
  container.innerHTML = "";
  if (Array.isArray(data)) {
    container.innerHTML = data.map(renderWeeklyStats).join("");
  } else {
    container.innerHTML = renderWeeklyStats(data);
  }
};

const initSession = () => {
  const saved = localStorage.getItem("attendance_session");
  if (!saved) return;
  try {
    const parsed = JSON.parse(saved);
    state.apiBase = parsed.apiBase || state.apiBase;
    state.token = parsed.token || "";
    state.role = parsed.role || "";
    state.userId = parsed.userId || null;
    if (state.token) {
      el("apiBase").value = state.apiBase;
      openAppView();
    }
  } catch {
    localStorage.removeItem("attendance_session");
  }
};

const persistSession = () => {
  localStorage.setItem(
    "attendance_session",
    JSON.stringify({
      apiBase: state.apiBase,
      token: state.token,
      role: state.role,
      userId: state.userId,
    })
  );
};

const clearSession = () => {
  state.token = "";
  state.role = "";
  state.userId = null;
  localStorage.removeItem("attendance_session");
};

const openAppView = async () => {
  el("loginView").classList.add("hidden");
  el("appView").classList.remove("hidden");
  el("sessionInfo").textContent = `role: ${state.role}, userId: ${state.userId}`;
  setRoleVisibility();
  activateTab("classesTab");
  await loadClasses();
  if (state.role === "admin") await loadUsers();
};

const bindEvents = () => {
  el("apiBase").value = state.apiBase;
  el("attendanceDate").valueAsDate = new Date();
  el("attendanceEditDate").valueAsDate = new Date();
  el("statsStartDate").valueAsDate = new Date();

  el("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      state.apiBase = el("apiBase").value.trim().replace(/\/$/, "");
      const data = await request("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          login: el("login").value.trim(),
          password: el("password").value,
        }),
      });
      state.token = data.accessToken;
      state.role = data.role;
      state.userId = data.userId;
      persistSession();
      await openAppView();
      toast("Успешный вход");
    } catch (err) {
      toast(err.message, true);
    }
  });

  el("logoutBtn").addEventListener("click", () => {
    clearSession();
    window.location.reload();
  });

  document.querySelectorAll(".tab").forEach((t) => {
    t.addEventListener("click", () => activateTab(t.dataset.tab));
  });

  el("refreshClasses").addEventListener("click", async () => {
    try {
      await loadClasses();
      toast("Классы обновлены");
    } catch (err) {
      toast(err.message, true);
    }
  });

  el("dashboardClassSelect").addEventListener("change", async (e) => {
    try {
      await applySelectedClass(e.target.value);
    } catch (err) {
      toast(err.message, true);
    }
  });

  el("refreshUsers")?.addEventListener("click", async () => {
    try {
      await loadUsers();
      toast("Список учителей обновлен");
    } catch (err) {
      toast(err.message, true);
    }
  });

  el("createTeacherForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await request("/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          login: el("teacherLogin").value.trim(),
          password: el("teacherPassword").value,
        }),
      });
      await loadUsers();
      e.target.reset();
      toast("Учитель создан");
    } catch (err) {
      toast(err.message, true);
    }
  });

  el("updateCredentialsForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const payload = {};
      const login = el("credLogin").value.trim();
      const password = el("credPassword").value;
      if (login) payload.login = login;
      if (password) payload.password = password;
      await request(`/users/${el("credTeacherId").value}/credentials`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      e.target.reset();
      await loadUsers();
      toast("Credentials обновлены");
    } catch (err) {
      toast(err.message, true);
    }
  });

  el("selfCredentialsForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const payload = {};
      const login = el("selfLogin").value.trim();
      const password = el("selfPassword").value;
      if (login) payload.login = login;
      if (password) payload.password = password;
      await request("/profile/credentials", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      e.target.reset();
      await loadUsers();
      toast("Собственные credentials обновлены");
    } catch (err) {
      toast(err.message, true);
    }
  });

  el("updateRoleForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await request(`/users/${el("roleUserId").value}/role`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: el("roleValue").value }),
      });
      await loadUsers();
      e.target.reset();
      toast("Роль обновлена");
    } catch (err) {
      toast(err.message, true);
    }
  });

  el("createClassForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await request("/classes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: el("className").value.trim(),
          teacherId: Number(el("classTeacherId").value),
        }),
      });
      e.target.reset();
      await loadClasses();
      toast("Класс создан");
    } catch (err) {
      toast(err.message, true);
    }
  });

  el("addStudentForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!state.selectedClassId) return toast("Сначала выберите класс", true);
    try {
      await request(`/classes/${state.selectedClassId}/students`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fullName: el("studentFullName").value.trim() }),
      });
      e.target.reset();
      await loadStudents();
      toast("Ученик добавлен");
    } catch (err) {
      toast(err.message, true);
    }
  });

  el("updateStudentForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const payload = {};
      const fullName = el("updateStudentName").value.trim();
      const isActive = el("updateStudentActive").value;
      if (fullName) payload.fullName = fullName;
      if (isActive) payload.isActive = isActive === "true";
      await request(`/students/${el("updateStudentId").value}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      e.target.reset();
      await loadStudents();
      toast("Ученик обновлен");
    } catch (err) {
      toast(err.message, true);
    }
  });

  el("attendanceLoadForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await loadAttendance();
      toast("Посещаемость загружена");
    } catch (err) {
      toast(err.message, true);
    }
  });

  el("attendanceEditForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await loadAttendanceForEdit();
      toast("Список для редактирования загружен");
    } catch (err) {
      toast(err.message, true);
    }
  });

  el("attendanceSaveBtn").addEventListener("click", async () => {
    try {
      await saveAttendanceEdit();
      await loadAttendance();
      toast("Посещаемость сохранена");
    } catch (err) {
      toast(err.message, true);
    }
  });

  el("setAllUnexcused").addEventListener("click", () => setAllUnexcused());
  el("clearAllAttendance").addEventListener("click", () => clearAllAttendance());

  el("statsForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await loadStats();
      toast("Статистика загружена");
    } catch (err) {
      toast(err.message, true);
    }
  });
};

bindEvents();
initSession();

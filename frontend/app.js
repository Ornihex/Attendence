const state = {
  apiBase: `${window.location.origin}/api/v1`,
  token: "",
  role: "",
  userId: null,
  selectedClassId: null,
  attendanceEditClassId: null,
  attendanceLoadRequestId: 0,
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
      `<b>#${u.id}</b> ${u.login} <span class="mono">(${u.role})</span><br><span class="muted">класс: ${
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
  el("attendanceEditClassId").value = String(state.selectedClassId);
  el("attendanceClassId").value = String(state.selectedClassId);
  el("statsClassId").value = String(state.selectedClassId);
  if (el("attendanceTab").classList.contains("active")) {
    await loadAttendanceForEdit();
  }
};

const renderAttendanceTable = (block) => {
  const filledLabel = block.isFilled ? "Заполнено" : "Не заполнено";
  const filledClass = block.isFilled ? "" : "warn";
  const unexcused = block.absentUnexcused || [];
  const excused = block.absentExcused || [];
  const unexcusedRows = unexcused
    .map((r) => `<tr><td>${r.fullName}</td><td>неуваж.</td></tr>`)
    .join("");
  const excusedRows = excused
    .map((r) => `<tr><td>${r.fullName}</td><td>${r.reason || "уваж."}</td></tr>`)
    .join("");
  const rows = `${unexcusedRows}${excusedRows}`;
  return `<div class="item"><b>Класс #${block.classId}</b> <span class="muted">${block.date}</span> <span class="fill-flag ${filledClass}">${filledLabel}</span><div class="muted">Всего: ${block.totalStudents}, присутствуют: ${block.presentCount}</div><table class="attendance-table"><thead><tr><th>Фамилия</th><th>Причина</th></tr></thead><tbody>${rows}</tbody></table></div>`;
};

const collectAbsenceData = () => {
  const absentUnexcused = Array.from(document.querySelectorAll(".unexcused-name"))
    .map((node) => node.value.trim())
    .filter((value) => value);
  const absentExcused = Array.from(document.querySelectorAll("#excusedList .absence-row"))
    .map((row) => {
      const name = row.querySelector(".excused-name")?.value.trim() || "";
      const reason = row.querySelector(".absence-reason")?.value || "";
      return name ? { fullName: name, reason } : null;
    })
    .filter((item) => item);
  return { absentUnexcused, absentExcused };
};

const updateAttendanceMismatchHint = () => {
  if (!el("attendanceMismatchHint") || !el("attendanceTotalStudents") || !el("attendancePresentCount")) return;
  const totalStudents = Number(el("attendanceTotalStudents").value || 0);
  const presentCount = Number(el("attendancePresentCount").value || 0);
  const expectedAbsent = Math.max(totalStudents - presentCount, 0);
  const { absentUnexcused, absentExcused } = collectAbsenceData();
  const enteredAbsent = absentUnexcused.length + absentExcused.length;
  const hint = el("attendanceMismatchHint");
  hint.textContent = `Ожидается отсутствующих: ${expectedAbsent}. Введено: ${enteredAbsent}.`;
  hint.classList.toggle("hint-error", expectedAbsent !== enteredAbsent);
};

const setAttendanceEditorStatus = (message, isError = false) => {
  const info = el("attendanceEditInfo");
  if (!info) return;
  info.textContent = message;
  info.classList.toggle("hint-error", isError);
};

const setAttendanceSaveEnabled = (enabled) => {
  const saveButton = el("attendanceSaveBtn");
  if (!saveButton) return;
  saveButton.disabled = !enabled;
};

const resetAttendanceEditor = (statusMessage = "Выберите класс и дату") => {
  state.attendanceEditClassId = null;
  if (el("attendanceTotalStudents")) el("attendanceTotalStudents").value = 0;
  if (el("attendancePresentCount")) el("attendancePresentCount").value = 0;
  if (el("unexcusedList")) el("unexcusedList").innerHTML = "";
  if (el("excusedList")) el("excusedList").innerHTML = "";
  setAttendanceEditorStatus(statusMessage);
  setAttendanceSaveEnabled(false);
  updateAttendanceMismatchHint();
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

const addUnexcusedRow = (name = "") => {
  const container = el("unexcusedList");
  const row = document.createElement("div");
  row.className = "item absence-row";
  const input = document.createElement("input");
  input.type = "text";
  input.placeholder = "Фамилия";
  input.className = "absence-name unexcused-name";
  input.value = name;
  const removeBtn = document.createElement("button");
  removeBtn.type = "button";
  removeBtn.className = "ghost-btn remove-absence";
  removeBtn.textContent = "Удалить";
  removeBtn.addEventListener("click", () => {
    row.remove();
    updateAttendanceMismatchHint();
  });
  input.addEventListener("input", () => updateAttendanceMismatchHint());
  row.append(input, removeBtn);
  container.appendChild(row);
  updateAttendanceMismatchHint();
};

const addExcusedRow = (name = "", reason = "") => {
  const container = el("excusedList");
  const row = document.createElement("div");
  row.className = "item absence-row";
  const input = document.createElement("input");
  input.type = "text";
  input.placeholder = "Фамилия";
  input.className = "absence-name excused-name";
  input.value = name;
  const select = document.createElement("select");
  select.className = "absence-reason";
  const options = ['<option value="">—</option>']
    .concat(excusedReasons.map((r) => `<option value="${r}">${r}</option>`))
    .join("");
  select.innerHTML = options;
  select.value = reason;
  const removeBtn = document.createElement("button");
  removeBtn.type = "button";
  removeBtn.className = "ghost-btn remove-absence";
  removeBtn.textContent = "Удалить";
  removeBtn.addEventListener("click", () => {
    row.remove();
    updateAttendanceMismatchHint();
  });
  input.addEventListener("input", () => updateAttendanceMismatchHint());
  select.addEventListener("change", () => updateAttendanceMismatchHint());
  row.append(input, select, removeBtn);
  container.appendChild(row);
  updateAttendanceMismatchHint();
};

const renderAttendanceEditor = (block) => {
  setAttendanceEditorStatus(`Данные загружены: класс #${block.classId}, дата ${block.date}`);
  setAttendanceSaveEnabled(true);
  el("attendanceTotalStudents").value = block.totalStudents ?? 0;
  el("attendancePresentCount").value = block.presentCount ?? 0;

  el("unexcusedList").innerHTML = "";
  el("excusedList").innerHTML = "";
  (block.absentUnexcused || []).forEach((item) => addUnexcusedRow(item.fullName || ""));
  (block.absentExcused || []).forEach((item) => addExcusedRow(item.fullName || "", item.reason || ""));
  updateAttendanceMismatchHint();
};

const loadAttendanceForEdit = async () => {
  const requestId = ++state.attendanceLoadRequestId;
  const dateValue = el("attendanceEditDate").value;
  let classIdValue = el("attendanceEditClassId").value;
  if (!classIdValue && state.selectedClassId) {
    classIdValue = String(state.selectedClassId);
    el("attendanceEditClassId").value = classIdValue;
  }
  if (!classIdValue || !dateValue) {
    resetAttendanceEditor("Выберите класс и дату");
    return;
  }
  setAttendanceEditorStatus("Загрузка...");
  setAttendanceSaveEnabled(false);
  const query = `?date=${dateValue}&classId=${classIdValue}`;
  try {
    const data = await request(`/attendance${query}`);
    if (requestId !== state.attendanceLoadRequestId) return;
    if (Array.isArray(data)) {
      throw new Error("Для редактирования укажите конкретный класс");
    }
    state.attendanceEditClassId = data.classId;
    renderAttendanceEditor(data);
  } catch (err) {
    if (requestId !== state.attendanceLoadRequestId) return;
    resetAttendanceEditor("Не удалось загрузить данные");
    setAttendanceEditorStatus(err.message || "Не удалось загрузить данные", true);
  }
};

const saveAttendanceEdit = async () => {
  const dateValue = el("attendanceEditDate").value;
  const classId = Number(state.attendanceEditClassId || el("attendanceEditClassId").value);
  if (!dateValue || !classId) {
    throw new Error("Укажите дату и класс");
  }
  const totalStudents = Number(el("attendanceTotalStudents").value);
  const presentCount = Number(el("attendancePresentCount").value);
  if (Number.isNaN(totalStudents) || Number.isNaN(presentCount)) {
    throw new Error("Укажите численность и присутствующих");
  }
  if (totalStudents < 0 || presentCount < 0 || presentCount > totalStudents) {
    throw new Error("Проверьте значения по списку/присутствуют");
  }
  const { absentUnexcused, absentExcused } = collectAbsenceData();
  if (absentExcused.some((item) => !item.reason)) {
    throw new Error("Укажите причину для каждого уважительного отсутствия");
  }
  const normalizedUnexcused = absentUnexcused.map((name) => name.toLocaleLowerCase("ru-RU"));
  const normalizedExcused = absentExcused.map((item) => item.fullName.toLocaleLowerCase("ru-RU"));
  const allNames = normalizedUnexcused.concat(normalizedExcused);
  if (new Set(allNames).size !== allNames.length) {
    throw new Error("В списках отсутствующих есть дубликаты фамилий");
  }
  const expectedAbsent = totalStudents - presentCount;
  if (absentUnexcused.length + absentExcused.length !== expectedAbsent) {
    throw new Error("Количество отсутствующих должно совпадать с totalStudents - presentCount");
  }
  await request(`/attendance?date=${dateValue}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      classId,
      totalStudents,
      presentCount,
      absentUnexcused,
      absentExcused,
    }),
  });
};

const renderDailyStats = (statsBlocks) => {
  const blocks = Array.isArray(statsBlocks) ? statsBlocks : [statsBlocks];
  const reportDate = blocks[0]?.date || "";
  const absentItems = blocks.flatMap((block) => block.absent || []);
  const rows = absentItems
    .map(
      (item) =>
        `<tr><td>${item.fullName}</td><td>${item.className || `#${item.classId}`}</td><td>${item.reason}</td></tr>`
    )
    .join("");
  const body = rows || '<tr><td colspan="3" class="muted">Отсутствующих нет</td></tr>';
  return `<div class="item"><b>Отсутствующие за ${reportDate}</b><div class="muted">Всего отсутствуют: ${absentItems.length}</div><table class="attendance-table"><thead><tr><th>Фамилия</th><th>Класс</th><th>Причина</th></tr></thead><tbody>${body}</tbody></table></div>`;
};

const loadStats = async () => {
  const selectedDate = el("statsDate").value;
  const classIdValue = el("statsClassId").value;
  const allClasses = el("statsAllClasses").checked && state.role === "admin";
  const query = allClasses
    ? `?date=${selectedDate}`
    : `?date=${selectedDate}${classIdValue ? `&classId=${classIdValue}` : ""}`;
  const data = await request(`/statistics/daily${query}`);
  const container = el("statsResult");
  container.innerHTML = "";
  container.innerHTML = renderDailyStats(data);
};

const loadUnfilledClasses = async () => {
  const selectedDate = el("statsDate").value;
  const data = await request(`/attendance/unfilled-classes?date=${selectedDate}`);
  renderItems(
    "unfilledClassesResult",
    data,
    (row) => `<b>#${row.id}</b> ${row.name} <span class="muted">teacherId: ${row.teacherId}</span>`
  );
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
  el("statsDate").valueAsDate = new Date();
  el("attendanceTotalStudents")?.addEventListener("input", () => updateAttendanceMismatchHint());
  el("attendancePresentCount")?.addEventListener("input", () => updateAttendanceMismatchHint());
  resetAttendanceEditor();

  el("loginForm")?.addEventListener("submit", async (e) => {
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

  el("logoutBtn")?.addEventListener("click", () => {
    clearSession();
    window.location.reload();
  });

  document.querySelectorAll(".tab").forEach((t) => {
    t.addEventListener("click", async () => {
      activateTab(t.dataset.tab);
      if (t.dataset.tab === "attendanceTab") {
        await loadAttendanceForEdit();
      }
    });
  });

  el("dashboardClassSelect")?.addEventListener("change", async (e) => {
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


  el("attendanceLoadForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await loadAttendance();
      toast("Посещаемость загружена");
    } catch (err) {
      toast(err.message, true);
    }
  });

  el("attendanceEditDate")?.addEventListener("change", async () => {
    await loadAttendanceForEdit();
  });
  el("attendanceEditClassId")?.addEventListener("change", async () => {
    await loadAttendanceForEdit();
  });

  el("attendanceSaveBtn")?.addEventListener("click", async () => {
    try {
      await saveAttendanceEdit();
      await loadAttendance();
      toast("Посещаемость сохранена");
    } catch (err) {
      toast(err.message, true);
    }
  });

  el("addUnexcused")?.addEventListener("click", () => addUnexcusedRow());
  el("addExcused")?.addEventListener("click", () => addExcusedRow());

  el("statsForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await loadStats();
      toast("Статистика загружена");
    } catch (err) {
      toast(err.message, true);
    }
  });

  el("unfilledClassesBtn")?.addEventListener("click", async () => {
    try {
      await loadUnfilledClasses();
      toast("Незаполненные классы загружены");
    } catch (err) {
      toast(err.message, true);
    }
  });
};

bindEvents();
initSession();

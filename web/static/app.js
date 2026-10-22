// Веб-интерфейс «Библиотеки». Все данные берутся из REST API через nginx: /api/...
"use strict";

const API = "/api";

// Описание 5 сущностей: какие поля показывать в форме и в таблице
const ENTITIES = {
  authors: {
    title: "Авторы", one: "автора", label: "full_name",
    fields: [
      { name: "full_name", label: "ФИО", required: true },
      { name: "country", label: "Страна" },
      { name: "city", label: "Город" },
      { name: "birth_year", label: "Год рождения", type: "number" },
    ],
  },
  genres: {
    title: "Жанры", one: "жанр", label: "name",
    fields: [
      { name: "name", label: "Название", required: true },
      { name: "description", label: "Описание" },
    ],
  },
  books: {
    title: "Книги", one: "книгу", label: "title",
    fields: [
      { name: "title", label: "Название", required: true },
      { name: "year", label: "Год издания", type: "number" },
      { name: "isbn", label: "ISBN" },
      { name: "copies", label: "Экземпляров", type: "number", value: 1, required: true },
      { name: "author_id", label: "Автор", ref: "authors", required: true },
      { name: "genre_id", label: "Жанр", ref: "genres" },
    ],
  },
  readers: {
    title: "Читатели", one: "читателя", label: "full_name",
    fields: [
      { name: "full_name", label: "ФИО", required: true },
      { name: "email", label: "E-mail", type: "email", required: true },
      { name: "phone", label: "Телефон" },
    ],
  },
  loans: {
    title: "Выдачи", one: "выдачу", label: "id",
    fields: [
      { name: "book_id", label: "Книга", ref: "books", required: true },
      { name: "reader_id", label: "Читатель", ref: "readers", required: true },
      { name: "loan_date", label: "Дата выдачи", type: "date", required: true },
      { name: "due_date", label: "Вернуть до", type: "date", required: true },
      { name: "returned", label: "Возвращена", type: "checkbox" },
    ],
  },
};

const state = { entity: "authors", editId: null, cache: {} };
const $ = (id) => document.getElementById(id);

// ---------- запросы к API ----------
async function request(method, path, body, quiet = false) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  let res, data = null;
  try {
    res = await fetch(API + path, opts);
  } catch (e) {
    if (!quiet) showStatus(method, path, 0, "Сервер недоступен: " + e.message);
    throw e;
  }
  const text = await res.text();
  if (text) { try { data = JSON.parse(text); } catch { data = text; } }
  if (!quiet) showStatus(method, path, res.status, res.ok ? summary(data) : errorText(data));
  return { status: res.status, ok: res.ok, data };
}

const STATUS_TEXT = { 200: "OK", 201: "Created", 204: "No Content", 404: "Not Found", 409: "Conflict", 422: "Unprocessable Entity", 502: "Bad Gateway" };

function showStatus(method, path, code, text) {
  const el = $("status");
  el.className = "status " + (code >= 200 && code < 300 ? "ok" : code >= 500 || code === 0 ? "err" : "warn");
  el.replaceChildren();
  el.append(`${method} ${API}${path}  →  `);
  const c = document.createElement("span");
  c.className = "code";
  c.textContent = code ? `${code} ${STATUS_TEXT[code] || ""}` : "нет ответа";
  el.append(c);
  if (text) el.append("\n" + text);
}

function summary(data) {
  if (Array.isArray(data)) return `получено записей: ${data.length}`;
  if (data && typeof data === "object") return JSON.stringify(data, null, 0);
  return "";
}

function errorText(data) {
  if (!data) return "";
  const d = data.detail ?? data;
  if (Array.isArray(d)) {
    return d.map((e) => `• ${(e.loc || []).filter((x) => x !== "body").join(".")}: ${e.msg}`).join("\n");
  }
  const text = typeof d === "string" ? d : JSON.stringify(d);
  const low = text.toLowerCase();
  if (low.includes("foreign key")) return "Ссылочная целостность: на запись ссылаются другие данные или указан несуществующий id\n(" + text + ")";
  if (low.includes("unique") || low.includes("duplicate key")) return "Такое значение уже есть в базе — поле должно быть уникальным\n(" + text + ")";
  return text;
}

// ---------- справочники для выпадающих списков ----------
async function loadRef(name) {
  const res = await fetch(`${API}/${name}?limit=1000`);
  state.cache[name] = res.ok ? await res.json() : [];
  return state.cache[name];
}

function refLabel(name, id) {
  if (id === null || id === undefined) return "—";
  const ent = ENTITIES[name];
  const item = (state.cache[name] || []).find((x) => x.id === id);
  if (!item) return `#${id}`;
  return ent.label === "id" ? `#${id}` : `${item[ent.label]} (#${id})`;
}

// ---------- вкладки ----------
function renderTabs() {
  const nav = $("tabs");
  nav.replaceChildren();
  for (const [key, ent] of Object.entries(ENTITIES)) {
    const b = document.createElement("button");
    b.type = "button";
    b.setAttribute("role", "tab");
    b.textContent = ent.title;
    b.setAttribute("aria-selected", key === state.entity);
    b.onclick = () => { state.entity = key; location.hash = key; showEntity(); };
    nav.append(b);
  }
}

// ---------- форма ----------
async function renderForm(item) {
  const ent = ENTITIES[state.entity];
  state.editId = item ? item.id : null;
  $("form-title").textContent = item ? `Изменить ${ent.one} #${item.id}` : `Добавить ${ent.one}`;
  $("submit").textContent = item ? "Сохранить (PUT)" : "Добавить (POST)";
  $("cancel").hidden = !item;

  const refs = [...new Set(ent.fields.filter((f) => f.ref).map((f) => f.ref))];
  await Promise.all(refs.map(loadRef));

  const form = $("form");
  form.replaceChildren();
  for (const f of ent.fields) {
    const label = document.createElement("label");
    let input;
    if (f.ref) {
      input = document.createElement("select");
      input.append(new Option(f.required ? "— выберите —" : "— не указан —", ""));
      for (const r of state.cache[f.ref]) input.append(new Option(refLabel(f.ref, r.id), r.id));
    } else {
      input = document.createElement("input");
      input.type = f.type || "text";
    }
    input.name = f.name;
    const val = item ? item[f.name] : f.value;
    if (f.type === "checkbox") {
      input.checked = Boolean(val);
      label.className = "check";
      label.append(input, f.label);
    } else {
      if (val !== undefined && val !== null) input.value = val;
      if (f.required) input.required = true;
      const cap = document.createElement("span");
      cap.textContent = f.label;
      if (f.required) { const s = document.createElement("span"); s.className = "req"; s.textContent = " *"; cap.append(s); }
      label.append(cap, input);
    }
    form.append(label);
  }
}

function readForm() {
  const ent = ENTITIES[state.entity];
  const form = $("form");
  const body = {};
  for (const f of ent.fields) {
    const el = form.elements[f.name];
    if (f.type === "checkbox") { body[f.name] = el.checked; continue; }
    const raw = el.value.trim();
    if (raw === "") {
      if (state.editId) body[f.name] = null; // при изменении пустое поле очищается
      continue;
    }
    body[f.name] = f.type === "number" || f.ref ? Number(raw) : raw;
  }
  return body;
}

async function submitForm(ev) {
  ev.preventDefault();
  const body = readForm();
  const path = state.editId ? `/${state.entity}/${state.editId}` : `/${state.entity}`;
  const res = await request(state.editId ? "PUT" : "POST", path, body);
  if (res.ok) {
    await renderForm(null);
    await renderTable(res.data.id, true);
  }
}

// ---------- таблица ----------
// quiet = true: обновить таблицу, не затирая результат предыдущего запроса (POST/PUT/DELETE)
async function renderTable(highlightId, quiet = false) {
  const ent = ENTITIES[state.entity];
  $("table-title").textContent = ent.title;
  const refs = [...new Set(ent.fields.filter((f) => f.ref).map((f) => f.ref))];
  await Promise.all(refs.map(loadRef));
  const res = await request("GET", `/${state.entity}`, undefined, quiet);
  const rows = res.ok ? res.data : [];
  state.cache[state.entity] = rows;

  const table = $("table");
  table.replaceChildren();
  const head = table.createTHead().insertRow();
  for (const t of ["id", ...ent.fields.map((f) => f.label), ""]) {
    const th = document.createElement("th");
    th.textContent = t;
    head.append(th);
  }
  const tbody = table.createTBody();
  for (const item of rows) {
    const tr = tbody.insertRow();
    if (item.id === highlightId) tr.className = "hl";
    tr.insertCell().textContent = item.id;
    for (const f of ent.fields) {
      let v = item[f.name];
      if (f.ref) v = refLabel(f.ref, v);
      else if (f.type === "checkbox") v = v ? "✓ да" : "нет";
      else if (v === null || v === undefined || v === "") v = "—";
      tr.insertCell().textContent = v;
    }
    const act = tr.insertCell();
    act.className = "actions";
    const edit = document.createElement("button");
    edit.className = "small";
    edit.textContent = "Изменить";
    edit.onclick = async () => {
      const r = await request("GET", `/${state.entity}/${item.id}`);
      if (r.ok) { await renderForm(r.data); await renderTable(r.data.id, true); }
    };
    const del = document.createElement("button");
    del.className = "small danger";
    del.textContent = "Удалить";
    del.onclick = async () => {
      const r = await request("DELETE", `/${state.entity}/${item.id}`);
      if (r.ok) { if (state.editId === item.id) renderForm(null); renderTable(undefined, true); }
    };
    act.append(edit, del);
  }
  $("empty").hidden = rows.length > 0;
}

async function findById(ev) {
  ev.preventDefault();
  const id = $("find-id").value;
  if (!id) return;
  const r = await request("GET", `/${state.entity}/${id}`);
  if (r.ok) { await renderForm(r.data); await renderTable(r.data.id, true); }
}

// ---------- информация о развёрнутой сборке ----------
const SERVICES = ["catalog", "readers", "loans"];

async function loadInfo() {
  const foot = $("foot");
  const pods = $("pods");
  // каждый запрос nginx отправляет в Service, а тот — в один из подов (реплик) сервиса
  const infos = await Promise.all(SERVICES.map(async (svc) => {
    try {
      const res = await fetch(`${API}/svc/${svc}/info`, { cache: "no-store" });
      return res.ok ? await res.json() : { service: svc, pod: `ошибка ${res.status}` };
    } catch {
      return { service: svc, pod: "недоступен" };
    }
  }));
  const main = infos.find((i) => i.version) || {};
  foot.replaceChildren();
  const env = document.createElement("span");
  env.className = "badge " + (main.environment || "");
  env.textContent = main.environment || "нет связи с API";
  foot.append(env);
  const parts = [["Версия", main.version], ["Сборка Jenkins", main.build ? "#" + main.build : "—"],
                 ["Коммит", main.commit], ["База данных", main.database]];
  for (const [k, v] of parts) {
    const s = document.createElement("span");
    s.append(k + ": ");
    const b = document.createElement("b");
    b.textContent = v ?? "—";
    s.append(b);
    foot.append(s);
  }
  pods.replaceChildren();
  for (const i of infos) {
    const s = document.createElement("span");
    s.className = "pod";
    s.textContent = i.pod || i.service;
    pods.append(s);
  }
}

async function showEntity() {
  renderTabs();
  await renderForm(null);
  await renderTable();
}

$("form").addEventListener("submit", submitForm);
$("cancel").onclick = () => renderForm(null);
$("find").addEventListener("submit", findById);
$("refresh").onclick = () => renderTable();
$("pods-refresh").onclick = () => loadInfo();

const fromHash = location.hash.slice(1);
if (ENTITIES[fromHash]) state.entity = fromHash;
showEntity();
loadInfo();

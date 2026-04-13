// ============================================================
// NextRound — Frontend (v2, auth-gated)
// ============================================================

// ---------- State ----------
const state = {
  token: localStorage.getItem("token") || null,
  user: null,
  companies: [],
  experiences: [],
  activeTab: null,
};

// ---------- API helper ----------
const api = async (path, options = {}) => {
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  if (state.token) headers["Authorization"] = `Bearer ${state.token}`;

  const res = await fetch(path, { ...options, headers });
  if (res.status === 401) {
    logout();
    throw new Error("Session expired. Please sign in again.");
  }
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      msg = data.detail || JSON.stringify(data);
    } catch {}
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  return res.json();
};

// ---------- DOM helpers ----------
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);
const el = (tag, cls = "", html = "") => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html) e.innerHTML = html;
  return e;
};
const esc = (s) =>
  String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");

// ---------- Auth state helpers ----------
function isAuthed() {
  return !!(state.token && state.user);
}

function setNavVisible(visible) {
  const nav = $("#main-nav");
  if (visible) {
    nav.classList.remove("hidden");
    nav.classList.add("md:flex");
  } else {
    nav.classList.add("hidden");
    nav.classList.remove("md:flex");
  }
}

// ---------- Tab switching ----------
function showTab(name) {
  const protectedTabs = ["companies", "experiences", "ai", "profile"];
  if (protectedTabs.includes(name) && !isAuthed()) {
    showAuthView();
    return;
  }
  state.activeTab = name;
  $$(".tab").forEach((t) => t.classList.add("hidden"));
  const target = $(`#tab-${name}`);
  if (target) target.classList.remove("hidden");
  $$(".tab-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.tab === name);
  });
}

function showAuthView() {
  state.activeTab = "auth";
  $$(".tab").forEach((t) => t.classList.add("hidden"));
  $("#tab-auth").classList.remove("hidden");
  $$(".tab-btn").forEach((b) => b.classList.remove("active"));
}

// ---------- Auth actions ----------
async function doLogin(email, password) {
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Login failed");
  }
  const data = await res.json();
  state.token = data.access_token;
  state.user = data.user;
  localStorage.setItem("token", state.token);
}

async function doRegister(payload) {
  await api("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  await doLogin(payload.email, payload.password);
}

async function fetchMe() {
  if (!state.token) return null;
  try {
    state.user = await api("/api/auth/me");
    return state.user;
  } catch (e) {
    state.token = null;
    state.user = null;
    localStorage.removeItem("token");
    return null;
  }
}

function logout() {
  state.token = null;
  state.user = null;
  state.companies = [];
  state.experiences = [];
  localStorage.removeItem("token");
  updateUserArea();
  setNavVisible(false);
  showAuthView();
}

function updateUserArea() {
  const area = $("#user-area");
  area.innerHTML = "";
  if (isAuthed()) {
    area.innerHTML = `
      <span class="text-sm text-slate-600 hidden sm:inline">Hi, <b>${esc(state.user.name)}</b></span>
      <button id="logout-btn" class="px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-100 text-sm">Sign out</button>
    `;
    $("#logout-btn").onclick = logout;
  } else {
    area.innerHTML = `<button id="login-btn" class="px-3 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 text-sm">Sign in</button>`;
    $("#login-btn").onclick = showAuthView;
  }
}

// ---------- Health / demo badge ----------
async function checkHealth() {
  try {
    const h = await api("/api/health");
    if (h.demo_mode) $("#demo-badge").classList.remove("hidden");
  } catch (e) {
    console.warn("Health check failed", e);
  }
}

// ---------- Companies ----------
async function loadCompanies() {
  state.companies = await api("/api/companies");
  renderCompanies();
  fillCompanyDropdowns();
}

function diffClass(d) {
  if (d === "easy") return "difficulty-easy";
  if (d === "hard") return "difficulty-hard";
  return "difficulty-medium";
}

function renderCompanies() {
  const grid = $("#companies-grid");
  grid.innerHTML = "";
  state.companies.forEach((c) => {
    const card = el(
      "button",
      "text-left bg-white rounded-2xl border border-slate-200 p-5 hover:shadow-md hover:border-indigo-300 transition"
    );
    const ctc =
      c.ctc_min != null && c.ctc_max != null
        ? `₹${c.ctc_min}–${c.ctc_max} LPA`
        : "CTC N/A";
    card.innerHTML = `
      <div class="flex items-start justify-between mb-2">
        <h3 class="font-bold text-slate-900">${esc(c.name)}</h3>
        <span class="${diffClass(c.difficulty)} text-xs px-2 py-0.5 rounded-full capitalize">${esc(c.difficulty || "medium")}</span>
      </div>
      <p class="text-xs text-slate-500 mb-2">${esc(c.sector || "")}</p>
      <div class="text-sm text-slate-700 mb-3">${ctc}</div>
      <div class="text-xs text-slate-500">Eligibility: CGPA ≥ ${c.eligibility_cgpa ?? "—"}</div>
      <div class="flex flex-wrap gap-1 mt-3">
        ${(c.topics || [])
          .slice(0, 4)
          .map((t) => `<span class="text-xs px-2 py-0.5 bg-slate-100 rounded-full">${esc(t)}</span>`)
          .join("")}
      </div>
    `;
    card.onclick = () => openCompanyModal(c.id);
    grid.appendChild(card);
  });
}

async function openCompanyModal(id) {
  const detail = await api(`/api/companies/${id}`);
  $("#modal-name").textContent = detail.name;
  const body = $("#modal-body");
  const ctc =
    detail.ctc_min != null && detail.ctc_max != null
      ? `₹${detail.ctc_min}–${detail.ctc_max} LPA`
      : "CTC N/A";
  body.innerHTML = `
    <p class="text-sm text-slate-500 mb-2">${esc(detail.sector || "")}</p>
    <p class="text-slate-700 mb-4">${esc(detail.description || "")}</p>
    <div class="grid grid-cols-2 gap-3 mb-5 text-sm">
      <div class="bg-slate-50 rounded-lg p-3"><div class="text-xs text-slate-500">CTC</div><div class="font-semibold">${ctc}</div></div>
      <div class="bg-slate-50 rounded-lg p-3"><div class="text-xs text-slate-500">Eligibility</div><div class="font-semibold">CGPA ≥ ${detail.eligibility_cgpa ?? "—"}</div></div>
      <div class="bg-slate-50 rounded-lg p-3"><div class="text-xs text-slate-500">Difficulty</div><div class="font-semibold capitalize">${esc(detail.difficulty || "medium")}</div></div>
      <div class="bg-slate-50 rounded-lg p-3"><div class="text-xs text-slate-500">Rounds</div><div class="font-semibold">${(detail.rounds || []).length}</div></div>
    </div>
    <div class="mb-4">
      <h4 class="font-semibold mb-2">Interview rounds</h4>
      <ol class="list-decimal pl-5 text-sm space-y-1">
        ${(detail.rounds || []).map((r) => `<li>${esc(r)}</li>`).join("") || '<li class="text-slate-400">No data</li>'}
      </ol>
    </div>
    <div class="mb-5">
      <h4 class="font-semibold mb-2">Topics tested</h4>
      <div class="flex flex-wrap gap-1">
        ${(detail.topics || []).map((t) => `<span class="text-xs px-2 py-1 bg-indigo-50 text-indigo-700 rounded-full">${esc(t)}</span>`).join("")}
      </div>
    </div>
    <div>
      <h4 class="font-semibold mb-2">Senior experiences (${(detail.experiences || []).length})</h4>
      <div class="space-y-2">
        ${(detail.experiences || []).map((e) => `
          <div class="border border-slate-200 rounded-lg p-3 text-sm">
            <div class="flex justify-between mb-1">
              <span class="font-medium">${esc(e.role)} · ${esc(String(e.year))}</span>
              <span class="text-xs px-2 py-0.5 rounded-full ${e.verdict === "selected" ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"}">${esc(e.verdict)}</span>
            </div>
            <p class="text-slate-700">${esc(e.rounds_description)}</p>
            <p class="text-slate-500 text-xs mt-2"><b>Tip:</b> ${esc(e.tips)}</p>
          </div>
        `).join("") || '<p class="text-sm text-slate-400">No experiences yet. Be the first to share.</p>'}
      </div>
    </div>
  `;
  $("#company-modal").classList.remove("hidden");
}

// ---------- Experiences ----------
async function loadExperiences(companyId = "") {
  const q = companyId ? `?company_id=${companyId}` : "";
  state.experiences = await api(`/api/experiences${q}`);
  renderExperiences();
}

function renderExperiences() {
  const list = $("#experiences-list");
  list.innerHTML = "";
  if (!state.experiences.length) {
    list.innerHTML = '<p class="text-sm text-slate-400 p-8 text-center bg-white rounded-xl border border-slate-200">No experiences to show.</p>';
    return;
  }
  state.experiences.forEach((e) => {
    const comp = state.companies.find((c) => c.id === e.company_id);
    const card = el("div", "bg-white rounded-xl border border-slate-200 p-4");
    card.innerHTML = `
      <div class="flex justify-between items-start mb-2">
        <div>
          <div class="font-semibold">${esc(comp?.name || "Company")} · ${esc(e.role)}</div>
          <div class="text-xs text-slate-500">Year ${esc(String(e.year))} · Difficulty ${esc(String(e.difficulty_rating))}/5</div>
        </div>
        <span class="text-xs px-2 py-0.5 rounded-full ${e.verdict === "selected" ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"}">${esc(e.verdict)}</span>
      </div>
      <p class="text-sm text-slate-700 mt-2">${esc(e.rounds_description)}</p>
      <p class="text-sm text-slate-500 mt-2"><b>Tip:</b> ${esc(e.tips)}</p>
    `;
    list.appendChild(card);
  });
}

// ---------- Share experience ----------
function openShareModal() {
  const sel = $("#share-company");
  sel.innerHTML = state.companies.map((c) => `<option value="${c.id}">${esc(c.name)}</option>`).join("");
  $("#share-modal").classList.remove("hidden");
}

async function submitShare(ev) {
  ev.preventDefault();
  const payload = {
    company_id: parseInt($("#share-company").value, 10),
    role: $("#share-role").value,
    verdict: $("#share-verdict").value,
    year: parseInt($("#share-year").value, 10),
    rounds_description: $("#share-rounds").value,
    tips: $("#share-tips").value,
    difficulty_rating: parseInt($("#share-rating").value, 10),
  };
  try {
    await api("/api/experiences", { method: "POST", body: JSON.stringify(payload) });
    $("#share-modal").classList.add("hidden");
    ev.target.reset();
    loadExperiences($("#exp-filter").value);
  } catch (e) {
    alert("Failed: " + e.message);
  }
}

// ---------- AI Prep ----------
function fillCompanyDropdowns() {
  const opts = state.companies.map((c) => `<option value="${c.id}">${esc(c.name)}</option>`).join("");
  $("#ai-company").innerHTML = opts;
  $("#exp-filter").innerHTML = '<option value="">All companies</option>' + opts;
  $("#p-targets").innerHTML = opts;
}

function aiResultCard(title, body, color = "indigo") {
  const colors = {
    indigo: "border-indigo-200 bg-indigo-50",
    emerald: "border-emerald-200 bg-emerald-50",
  };
  return `
    <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
      <div class="inline-block px-3 py-1 rounded-full text-xs font-medium mb-3 ${colors[color] || colors.indigo} border">${esc(title)}</div>
      ${body}
    </div>
  `;
}

function setAILoading(label) {
  $("#ai-results").innerHTML = `
    <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
      <div class="flex items-center gap-3 text-slate-600">
        <div class="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <span>${esc(label)}</span>
      </div>
    </div>
  `;
}

async function generatePlan() {
  if (!isAuthed()) return showAuthView();
  const companyId = parseInt($("#ai-company").value, 10);
  if (!companyId) return;
  setAILoading("Generating your personalized study plan…");
  try {
    const plan = await api("/api/ai/study-plan", { method: "POST", body: JSON.stringify({ company_id: companyId }) });
    const weeksHtml = (plan.weeks || []).map((w) => `
      <details class="border border-slate-200 rounded-lg p-3 mb-2" ${w.week_number === 1 ? "open" : ""}>
        <summary class="font-semibold">Week ${esc(String(w.week_number))}: ${esc(w.focus || "")}</summary>
        <div class="mt-2 text-sm text-slate-700 space-y-2">
          <div><b>Topics:</b> ${esc((w.topics || []).join(", ") || "—")}</div>
          <div><b>Resources:</b> ${esc((w.resources || []).join(", ") || "—")}</div>
          <div><b>Practice goal:</b> ${esc(w.practice_goal || "—")}</div>
        </div>
      </details>
    `).join("");
    $("#ai-results").innerHTML = aiResultCard("📅 Your Study Plan", weeksHtml || '<p class="text-slate-400">No plan generated.</p>');
  } catch (e) {
    $("#ai-results").innerHTML = `<div class="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">Failed: ${esc(e.message)}</div>`;
  }
}

async function generateScore() {
  if (!isAuthed()) return showAuthView();
  const companyId = parseInt($("#ai-company").value, 10);
  if (!companyId) return;
  setAILoading("Analyzing your readiness…");
  try {
    const r = await api("/api/ai/readiness-score", { method: "POST", body: JSON.stringify({ company_id: companyId }) });
    const scoreColor = r.score >= 75 ? "emerald" : r.score >= 50 ? "amber" : "rose";
    const scoreColors = { emerald: "text-emerald-600", amber: "text-amber-600", rose: "text-rose-600" };
    const body = `
      <div class="grid md:grid-cols-3 gap-4">
        <div class="text-center md:border-r md:border-slate-200 md:pr-4">
          <div class="text-5xl font-bold ${scoreColors[scoreColor]}">${esc(String(r.score))}<span class="text-2xl text-slate-400">/100</span></div>
          <div class="text-xs text-slate-500 mt-1">Readiness Score</div>
        </div>
        <div>
          <div class="text-xs font-medium text-emerald-700 mb-1">✓ STRENGTHS</div>
          <ul class="text-sm space-y-1">
            ${(r.strengths || []).map((s) => `<li>• ${esc(s)}</li>`).join("") || '<li class="text-slate-400">—</li>'}
          </ul>
        </div>
        <div>
          <div class="text-xs font-medium text-rose-700 mb-1">✗ GAPS</div>
          <ul class="text-sm space-y-1">
            ${(r.gaps || []).map((g) => `<li>• ${esc(g)}</li>`).join("") || '<li class="text-slate-400">—</li>'}
          </ul>
        </div>
      </div>
      <div class="mt-5 pt-4 border-t border-slate-200">
        <div class="text-xs font-medium text-slate-500 mb-2">ACTION ITEMS</div>
        <ol class="list-decimal pl-5 text-sm space-y-1">
          ${(r.action_items || []).map((a) => `<li>${esc(a)}</li>`).join("") || '<li class="text-slate-400">—</li>'}
        </ol>
      </div>
    `;
    $("#ai-results").innerHTML = aiResultCard("📊 Readiness Analysis", body, "emerald");
  } catch (e) {
    $("#ai-results").innerHTML = `<div class="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">Failed: ${esc(e.message)}</div>`;
  }
}

// ---------- Chat ----------
function appendChat(role, text) {
  const log = $("#chat-log");
  const div = el("div", "flex", `<div class="${role === "user" ? "chat-msg-user" : "chat-msg-assistant"}">${esc(text)}</div>`);
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

async function sendChat(ev) {
  ev.preventDefault();
  if (!isAuthed()) return showAuthView();
  const input = $("#chat-input");
  const message = input.value.trim();
  if (!message) return;
  appendChat("user", message);
  input.value = "";

  const thinking = el("div", "flex", '<div class="chat-msg-assistant italic text-slate-400">Thinking…</div>');
  $("#chat-log").appendChild(thinking);

  try {
    const companyId = parseInt($("#ai-company").value, 10) || null;
    const r = await api("/api/ai/chat", { method: "POST", body: JSON.stringify({ message, company_id: companyId }) });
    thinking.remove();
    appendChat("assistant", r.reply);
  } catch (e) {
    thinking.remove();
    appendChat("assistant", "Error: " + e.message);
  }
}

// ---------- Profile ----------
async function loadProfile() {
  const p = await api("/api/profile");
  $("#p-name").value = p.name || "";
  $("#p-dept").value = p.department || "";
  $("#p-cgpa").value = p.cgpa ?? "";
  $("#p-year").value = p.year ?? "";
  $("#p-skills").value = (p.skills || []).join(", ");
  const targets = new Set((p.target_companies || []).map(Number));
  $$("#p-targets option").forEach((o) => {
    o.selected = targets.has(parseInt(o.value, 10));
  });
}

async function saveProfile(ev) {
  ev.preventDefault();
  const selectedTargets = Array.from($$("#p-targets option")).filter((o) => o.selected).map((o) => parseInt(o.value, 10));
  const payload = {
    name: $("#p-name").value,
    department: $("#p-dept").value,
    cgpa: parseFloat($("#p-cgpa").value) || 0,
    year: parseInt($("#p-year").value, 10) || 3,
    skills: $("#p-skills").value.split(",").map((s) => s.trim()).filter(Boolean),
    target_companies: selectedTargets,
  };
  try {
    await api("/api/profile", { method: "PUT", body: JSON.stringify(payload) });
    $("#profile-msg").textContent = "✓ Saved";
    setTimeout(() => ($("#profile-msg").textContent = ""), 2000);
  } catch (e) {
    $("#profile-msg").textContent = "Error: " + e.message;
  }
}

// ---------- Wiring ----------
function wireEvents() {
  $$(".tab-btn").forEach((btn) => {
    btn.onclick = async () => {
      const tab = btn.dataset.tab;
      if (!isAuthed()) return showAuthView();
      showTab(tab);
      try {
        if (tab === "companies") await loadCompanies();
        if (tab === "experiences") await loadExperiences($("#exp-filter").value);
        if (tab === "profile") await loadProfile();
      } catch (e) {
        console.error(e);
      }
    };
  });

  $$(".auth-tab").forEach((b) => {
    b.onclick = () => {
      const mode = b.dataset.auth;
      $$(".auth-tab").forEach((x) => {
        const active = x.dataset.auth === mode;
        x.classList.toggle("active", active);
        x.classList.toggle("bg-indigo-600", active);
        x.classList.toggle("text-white", active);
        x.classList.toggle("bg-slate-100", !active);
        x.classList.toggle("text-slate-700", !active);
      });
      $("#login-form").classList.toggle("hidden", mode !== "login");
      $("#register-form").classList.toggle("hidden", mode !== "register");
      $("#auth-error").textContent = "";
    };
  });

  $("#login-form").onsubmit = async (ev) => {
    ev.preventDefault();
    $("#auth-error").textContent = "";
    try {
      await doLogin($("#login-email").value.trim(), $("#login-password").value);
      await onAuthSuccess();
    } catch (e) {
      $("#auth-error").textContent = e.message;
    }
  };

  $("#register-form").onsubmit = async (ev) => {
    ev.preventDefault();
    $("#auth-error").textContent = "";
    try {
      await doRegister({
        name: $("#reg-name").value.trim(),
        email: $("#reg-email").value.trim(),
        password: $("#reg-password").value,
        cgpa: parseFloat($("#reg-cgpa").value) || 0,
        year: parseInt($("#reg-year").value, 10) || 3,
      });
      await onAuthSuccess();
    } catch (e) {
      $("#auth-error").textContent = e.message;
    }
  };

  const topLogin = $("#login-btn");
  if (topLogin) topLogin.onclick = showAuthView;

  $("#modal-close").onclick = () => $("#company-modal").classList.add("hidden");
  $("#company-modal").onclick = (e) => {
    if (e.target.id === "company-modal") $("#company-modal").classList.add("hidden");
  };
  $("#share-close").onclick = () => $("#share-modal").classList.add("hidden");
  $("#share-modal").onclick = (e) => {
    if (e.target.id === "share-modal") $("#share-modal").classList.add("hidden");
  };
  $("#share-exp-btn").onclick = () => {
    if (!isAuthed()) return showAuthView();
    openShareModal();
  };
  $("#share-form").onsubmit = submitShare;

  $("#exp-filter").onchange = (e) => loadExperiences(e.target.value);

  $("#btn-plan").onclick = generatePlan;
  $("#btn-score").onclick = generateScore;
  $("#chat-form").onsubmit = sendChat;

  $("#profile-form").onsubmit = saveProfile;
}

async function onAuthSuccess() {
  updateUserArea();
  setNavVisible(true);
  await loadCompanies();
  showTab("companies");
}

// ---------- Boot ----------
(async function init() {
  wireEvents();
  await checkHealth();
  const me = await fetchMe();
  updateUserArea();
  if (me) {
    setNavVisible(true);
    try {
      await loadCompanies();
    } catch (e) {
      console.error(e);
    }
    showTab("companies");
  } else {
    setNavVisible(false);
    showAuthView();
  }
})();
// ============================================================
// NextRound — Frontend
// Roles: student | alumni | placement_officer
// Features: companies (read-only), experiences (add), AI prep,
//           daily challenge (refreshable), profile (resume upload),
//           admin (officer), custom study plan weeks
// ============================================================

const state = {
  token: localStorage.getItem("token") || null,
  user: null,
  companies: [],
  experiences: [],
  activeTab: null,
  challengeSelected: null,
  currentChallenge: null,  // current challenge data object
  practiceMode: false,     // true if viewing a practice question (no streak)
};

// ── API helper ──────────────────────────────────────────────
const api = async (path, options = {}) => {
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  if (state.token) headers["Authorization"] = `Bearer ${state.token}`;
  const res = await fetch(path, { ...options, headers });
  if (res.status === 401) { logout(); throw new Error("Session expired. Please sign in again."); }
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { const d = await res.json(); msg = d.detail || JSON.stringify(d); } catch {}
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  return res.json();
};

const $  = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);
const el = (tag, cls = "", html = "") => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html) e.innerHTML = html;
  return e;
};
const esc = (s) =>
  String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
                 .replace(/"/g,"&quot;").replace(/'/g,"&#39;");

// ── Role helpers ─────────────────────────────────────────────
const isAuthed  = () => !!(state.token && state.user);
const isStudent = () => state.user?.role === "student";
const isAlumni  = () => state.user?.role === "alumni";
const isOfficer = () => state.user?.role === "placement_officer";

// ── Navigation ───────────────────────────────────────────────
function setNavVisible(v) {
  const nav = $("#main-nav");
  nav.classList.toggle("hidden", !v);
  nav.classList.toggle("md:flex", v);
}

function updateRoleVisibility() {
  if (!state.user) return;

  // shared-nav: visible to students AND alumni (not officers)
  $$(".shared-nav").forEach(b => b.classList.toggle("hidden", isOfficer()));
  // student-nav: only students
  $$(".student-nav").forEach(b => b.classList.toggle("hidden", !isStudent()));
  // officer-nav: only placement officers
  $$(".officer-nav").forEach(b => b.classList.toggle("hidden", !isOfficer()));

  const banner = $("#streak-banner");
  if (banner) banner.classList.toggle("hidden", !isStudent());

  const streakCard    = $("#profile-streak-card");
  const resumeSection = $("#profile-resume-section");
  const targetsSection = $("#profile-targets-section");
  if (streakCard)     streakCard.classList.toggle("hidden",     !isStudent());
  if (resumeSection)  resumeSection.classList.toggle("hidden",  !isStudent());
  if (targetsSection) targetsSection.classList.toggle("hidden", !isStudent());
}

function defaultTabForRole() {
  if (isOfficer()) return "admin";
  return "companies"; // students and alumni both land on companies
}

function showTab(name) {
  const allProtected = ["companies","experiences","challenge","ai","profile","admin"];
  if (allProtected.includes(name) && !isAuthed()) return showAuthView();

  // Role guards
  if (name === "admin"     && !isOfficer()) return showTab("companies");
  if (name === "challenge" && !isStudent()) return showTab("companies");
  if (name === "ai"        && !isStudent()) return showTab("companies");
  // Officers don't get shared tabs — send them to admin
  if (["companies","experiences","profile","challenge","ai"].includes(name) && isOfficer()) return showTab("admin");

  state.activeTab = name;
  $$(".tab").forEach(t => t.classList.add("hidden"));
  const target = $(`#tab-${name}`);
  if (target) target.classList.remove("hidden");
  $$(".tab-btn").forEach(b => b.classList.toggle("active", b.dataset.tab === name));
}

function showAuthView() {
  state.activeTab = "auth";
  $$(".tab").forEach(t => t.classList.add("hidden"));
  $("#tab-auth").classList.remove("hidden");
  $$(".tab-btn").forEach(b => b.classList.remove("active"));
}

// ── Auth ─────────────────────────────────────────────────────
async function doLogin(email, password) {
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || "Login failed"); }
  const data = await res.json();
  state.token = data.access_token;
  state.user  = data.user;
  localStorage.setItem("token", state.token);
}

async function doRegister(payload) {
  await api("/api/auth/register", { method: "POST", body: JSON.stringify(payload) });
  await doLogin(payload.email, payload.password);
}

async function fetchMe() {
  if (!state.token) return null;
  try { state.user = await api("/api/auth/me"); return state.user; }
  catch { state.token = null; state.user = null; localStorage.removeItem("token"); return null; }
}

function logout() {
  state.token = null; state.user = null;
  state.companies = []; state.experiences = [];
  localStorage.removeItem("token");
  updateUserArea(); setNavVisible(false); showAuthView();
}

function updateUserArea() {
  const area = $("#user-area");
  area.innerHTML = "";
  if (isAuthed()) {
    const roleLabel = isOfficer() ? "🏛️ Officer" : isAlumni() ? "🎓 Alumni" : "🎯 Student";
    area.innerHTML = `
      <span class="text-sm text-slate-600 hidden sm:inline">${esc(roleLabel)} · <b>${esc(state.user.name)}</b></span>
      <button id="logout-btn" class="px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-100 text-sm">Sign out</button>
    `;
    $("#logout-btn").onclick = logout;
  } else {
    area.innerHTML = `<button id="login-btn" class="px-3 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 text-sm">Sign in</button>`;
    $("#login-btn").onclick = showAuthView;
  }
}

async function checkHealth() {
  try { const h = await api("/api/health"); if (h.demo_mode) $("#demo-badge").classList.remove("hidden"); }
  catch {}
}

// ── Companies ────────────────────────────────────────────────
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
  if (!grid) return;
  const sector = $("#company-sector-filter")?.value || "";
  const diff   = $("#company-diff-filter")?.value   || "";
  const filtered = state.companies.filter(c =>
    (!sector || c.sector === sector) &&
    (!diff   || c.difficulty === diff)
  );
  grid.innerHTML = "";
  filtered.forEach(c => {
    const card = el("button","text-left bg-white rounded-2xl border border-slate-200 p-5 hover:shadow-md hover:border-indigo-300 transition");
    const ctc  = c.ctc_min != null && c.ctc_max != null ? `₹${c.ctc_min}–${c.ctc_max} LPA` : "CTC N/A";
    card.innerHTML = `
      <div class="flex items-start justify-between mb-2">
        <h3 class="font-bold text-slate-900">${esc(c.name)}</h3>
        <span class="${diffClass(c.difficulty)} text-xs px-2 py-0.5 rounded-full capitalize">${esc(c.difficulty||"medium")}</span>
      </div>
      <p class="text-xs text-slate-500 mb-2">${esc(c.sector||"")}</p>
      <div class="text-sm text-slate-700 mb-3">${ctc}</div>
      <div class="text-xs text-slate-500">Eligibility: CGPA ≥ ${c.eligibility_cgpa ?? "—"}</div>
      <div class="flex flex-wrap gap-1 mt-3">
        ${(c.topics||[]).slice(0,4).map(t=>`<span class="text-xs px-2 py-0.5 bg-slate-100 rounded-full">${esc(t)}</span>`).join("")}
      </div>`;
    card.onclick = () => openCompanyModal(c.id);
    grid.appendChild(card);
  });
  if (!filtered.length) {
    grid.innerHTML = '<p class="text-slate-400 text-center col-span-3 py-12">No companies match your filters.</p>';
  }
}

async function openCompanyModal(id) {
  const detail = await api(`/api/companies/${id}`);
  $("#modal-name").textContent = detail.name;
  const ctc = detail.ctc_min != null && detail.ctc_max != null ? `₹${detail.ctc_min}–${detail.ctc_max} LPA` : "CTC N/A";
  $("#modal-body").innerHTML = `
    <p class="text-sm text-slate-500 mb-2">${esc(detail.sector||"")}</p>
    <p class="text-slate-700 mb-4">${esc(detail.description||"")}</p>
    <div class="grid grid-cols-2 gap-3 mb-5 text-sm">
      <div class="bg-slate-50 rounded-lg p-3"><div class="text-xs text-slate-500">CTC</div><div class="font-semibold">${ctc}</div></div>
      <div class="bg-slate-50 rounded-lg p-3"><div class="text-xs text-slate-500">Eligibility</div><div class="font-semibold">CGPA ≥ ${detail.eligibility_cgpa??'—'}</div></div>
      <div class="bg-slate-50 rounded-lg p-3"><div class="text-xs text-slate-500">Difficulty</div><div class="font-semibold capitalize">${esc(detail.difficulty||"medium")}</div></div>
      <div class="bg-slate-50 rounded-lg p-3"><div class="text-xs text-slate-500">Rounds</div><div class="font-semibold">${(detail.rounds||[]).length}</div></div>
    </div>
    <div class="mb-4">
      <h4 class="font-semibold mb-2">Interview rounds</h4>
      <ol class="list-decimal pl-5 text-sm space-y-1">
        ${(detail.rounds||[]).map(r=>`<li>${esc(r)}</li>`).join("")||'<li class="text-slate-400">No data</li>'}
      </ol>
    </div>
    <div class="mb-5">
      <h4 class="font-semibold mb-2">Topics tested</h4>
      <div class="flex flex-wrap gap-1">
        ${(detail.topics||[]).map(t=>`<span class="text-xs px-2 py-1 bg-indigo-50 text-indigo-700 rounded-full">${esc(t)}</span>`).join("")}
      </div>
    </div>
    <div>
      <h4 class="font-semibold mb-2">Senior experiences (${(detail.experiences||[]).length})</h4>
      <div class="space-y-2">
        ${(detail.experiences||[]).map(e=>`
          <div class="border border-slate-200 rounded-lg p-3 text-sm">
            <div class="flex justify-between mb-1">
              <span class="font-medium">${esc(e.role)} · ${esc(String(e.year))}</span>
              <span class="text-xs px-2 py-0.5 rounded-full ${e.verdict==="selected"?"bg-emerald-100 text-emerald-700":"bg-rose-100 text-rose-700"}">${esc(e.verdict)}</span>
            </div>
            <p class="text-slate-700">${esc(e.rounds_description)}</p>
            <p class="text-slate-500 text-xs mt-2"><b>Tip:</b> ${esc(e.tips)}</p>
          </div>`).join("")||'<p class="text-sm text-slate-400">No experiences yet.</p>'}
      </div>
    </div>`;
  $("#company-modal").classList.remove("hidden");
}

// ── Experiences ───────────────────────────────────────────────
async function loadExperiences(companyId = "") {
  const q = companyId ? `?company_id=${companyId}` : "";
  state.experiences = await api(`/api/experiences${q}`);
  renderExperiences();
}

function renderExperiences() {
  const list = $("#experiences-list");
  if (!list) return;
  list.innerHTML = "";
  if (!state.experiences.length) {
    list.innerHTML = '<p class="text-sm text-slate-400 p-8 text-center bg-white rounded-xl border border-slate-200">No experiences to show.</p>';
    return;
  }
  state.experiences.forEach(e => {
    const comp = state.companies.find(c => c.id === e.company_id);
    const card = el("div","bg-white rounded-xl border border-slate-200 p-4");
    card.innerHTML = `
      <div class="flex justify-between items-start mb-2">
        <div>
          <div class="font-semibold">${esc(comp?.name||"Company")} · ${esc(e.role)}</div>
          <div class="text-xs text-slate-500">Year ${esc(String(e.year))} · Difficulty ${esc(String(e.difficulty_rating))}/5</div>
        </div>
        <span class="text-xs px-2 py-0.5 rounded-full ${e.verdict==="selected"?"bg-emerald-100 text-emerald-700":"bg-rose-100 text-rose-700"}">${esc(e.verdict)}</span>
      </div>
      <p class="text-sm text-slate-700 mt-2">${esc(e.rounds_description)}</p>
      <p class="text-sm text-slate-500 mt-2"><b>Tip:</b> ${esc(e.tips)}</p>`;
    list.appendChild(card);
  });
}

function openShareModal() {
  const sel = $("#share-company");
  sel.innerHTML = state.companies.map(c => `<option value="${c.id}">${esc(c.name)}</option>`).join("");
  $("#share-modal").classList.remove("hidden");
}

async function submitShare(ev) {
  ev.preventDefault();
  const payload = {
    company_id:        parseInt($("#share-company").value, 10),
    role:              $("#share-role").value,
    verdict:           $("#share-verdict").value,
    year:              parseInt($("#share-year").value, 10),
    rounds_description:$("#share-rounds").value,
    tips:              $("#share-tips").value,
    difficulty_rating: parseInt($("#share-rating").value, 10),
  };
  try {
    await api("/api/experiences", { method: "POST", body: JSON.stringify(payload) });
    $("#share-modal").classList.add("hidden");
    ev.target.reset();
    loadExperiences($("#exp-filter").value);
  } catch(e) { alert("Failed: " + e.message); }
}

function fillCompanyDropdowns() {
  const opts = state.companies.map(c => `<option value="${c.id}">${esc(c.name)}</option>`).join("");
  const aiC = $("#ai-company"); if (aiC) aiC.innerHTML = opts;
  const expF = $("#exp-filter"); if (expF) expF.innerHTML = '<option value="">All companies</option>' + opts;
  const pT = $("#p-targets");   if (pT)  pT.innerHTML = opts;
}

// ── AI Prep ───────────────────────────────────────────────────
function aiResultCard(title, body, color = "indigo") {
  const colors = { indigo:"border-indigo-200 bg-indigo-50", emerald:"border-emerald-200 bg-emerald-50" };
  return `<div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
    <div class="inline-block px-3 py-1 rounded-full text-xs font-medium mb-3 ${colors[color]||colors.indigo} border">${esc(title)}</div>
    ${body}</div>`;
}

function setAILoading(label) {
  $("#ai-results").innerHTML = `
    <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
      <div class="flex items-center gap-3 text-slate-600">
        <div class="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <span>${esc(label)}</span>
      </div>
    </div>`;
}

async function generatePlan() {
  if (!isAuthed()) return showAuthView();
  const companyId = parseInt($("#ai-company").value, 10);
  if (!companyId) return;
  const weeks = parseInt($("#ai-weeks").value, 10) || 4;
  setAILoading(`Generating your personalised ${weeks}-week study plan…`);
  try {
    const plan = await api("/api/ai/study-plan", {
      method:"POST",
      body: JSON.stringify({ company_id: companyId, weeks })
    });
    const weeksHtml = (plan.weeks||[]).map(w => `
      <details class="border border-slate-200 rounded-lg p-3 mb-2" ${w.week_number===1?"open":""}>
        <summary class="font-semibold">Week ${esc(String(w.week_number))}: ${esc(w.focus||"")}</summary>
        <div class="mt-2 text-sm text-slate-700 space-y-2">
          <div><b>Topics:</b> ${esc((w.topics||[]).join(", ")||"—")}</div>
          <div><b>Resources:</b> ${esc((w.resources||[]).join(", ")||"—")}</div>
          <div><b>Practice goal:</b> ${esc(w.practice_goal||"—")}</div>
        </div>
      </details>`).join("");
    $("#ai-results").innerHTML = aiResultCard(
      `📅 Your ${weeks}-Week Study Plan`,
      weeksHtml||'<p class="text-slate-400">No plan generated.</p>'
    );
  } catch(e) {
    $("#ai-results").innerHTML = `<div class="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">Failed: ${esc(e.message)}</div>`;
  }
}

async function generateScore() {
  if (!isAuthed()) return showAuthView();
  const companyId = parseInt($("#ai-company").value, 10);
  if (!companyId) return;
  setAILoading("Analysing your readiness…");
  try {
    const r = await api("/api/ai/readiness-score", { method:"POST", body:JSON.stringify({ company_id:companyId }) });
    const sc = r.score >= 75 ? "emerald" : r.score >= 50 ? "amber" : "rose";
    const scCls = { emerald:"text-emerald-600", amber:"text-amber-600", rose:"text-rose-600" };
    const body = `
      <div class="grid md:grid-cols-3 gap-4">
        <div class="text-center md:border-r md:border-slate-200 md:pr-4">
          <div class="text-5xl font-bold ${scCls[sc]}">${esc(String(r.score))}<span class="text-2xl text-slate-400">/100</span></div>
          <div class="text-xs text-slate-500 mt-1">Readiness Score</div>
        </div>
        <div>
          <div class="text-xs font-medium text-emerald-700 mb-1">✓ STRENGTHS</div>
          <ul class="text-sm space-y-1">${(r.strengths||[]).map(s=>`<li>• ${esc(s)}</li>`).join("")||'<li class="text-slate-400">—</li>'}</ul>
        </div>
        <div>
          <div class="text-xs font-medium text-rose-700 mb-1">✗ GAPS</div>
          <ul class="text-sm space-y-1">${(r.gaps||[]).map(g=>`<li>• ${esc(g)}</li>`).join("")||'<li class="text-slate-400">—</li>'}</ul>
        </div>
      </div>
      <div class="mt-5 pt-4 border-t border-slate-200">
        <div class="text-xs font-medium text-slate-500 mb-2">ACTION ITEMS</div>
        <ol class="list-decimal pl-5 text-sm space-y-1">${(r.action_items||[]).map(a=>`<li>${esc(a)}</li>`).join("")||'<li class="text-slate-400">—</li>'}</ol>
      </div>`;
    $("#ai-results").innerHTML = aiResultCard("📊 Readiness Analysis", body, "emerald");
  } catch(e) {
    $("#ai-results").innerHTML = `<div class="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">Failed: ${esc(e.message)}</div>`;
  }
}

function appendChat(role, text) {
  const log = $("#chat-log");
  const div = el("div","flex",`<div class="${role==="user"?"chat-msg-user":"chat-msg-assistant"}">${esc(text)}</div>`);
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
  const thinking = el("div","flex",'<div class="chat-msg-assistant italic text-slate-400">Thinking…</div>');
  $("#chat-log").appendChild(thinking);
  try {
    const companyId = parseInt($("#ai-company").value, 10) || null;
    const r = await api("/api/ai/chat", { method:"POST", body:JSON.stringify({ message, company_id:companyId }) });
    thinking.remove();
    appendChat("assistant", r.reply);
  } catch(e) { thinking.remove(); appendChat("assistant","Error: "+e.message); }
}

// ── Daily Challenge ───────────────────────────────────────────
function _renderChallenge(c) {
  state.currentChallenge = c;
  state.challengeSelected = null;

  $("#chal-topic").textContent  = c.topic + (c.practice_mode ? " · Practice" : "");
  $("#chal-title").textContent  = c.title;
  $("#chal-desc").textContent   = c.description;
  $("#chal-date").textContent   = (c.practice_mode ? "Practice mode · " : "Today · ") + c.today;

  const choices = $("#chal-choices");
  choices.innerHTML = "";
  c.choices.forEach((ch, i) => {
    const btn = el("button",
      "w-full text-left px-4 py-3 rounded-xl border-2 border-slate-200 hover:border-violet-400 hover:bg-violet-50 transition text-sm font-medium",
      `<span class="inline-block w-6 h-6 rounded-full bg-slate-100 text-center text-xs leading-6 mr-2 font-bold">${String.fromCharCode(65+i)}</span>${esc(ch)}`
    );
    btn.dataset.idx = i;
    btn.onclick = () => selectChoice(i);
    choices.appendChild(btn);
  });

  $("#chal-submit").disabled = true;
  $("#chal-submit").onclick  = () => submitChallenge();

  $("#challenge-loading").classList.add("hidden");
  $("#challenge-content").classList.remove("hidden");
  $("#challenge-result").classList.add("hidden");
  $("#challenge-done").classList.add("hidden");

  const mini = $("#challenge-streak-mini");
  if (mini) {
    mini.classList.remove("hidden");
    const sv = $("#chal-streak-val");
    if (sv) sv.textContent = state.user?.current_streak || 0;
  }
}

async function loadChallenge() {
  state.challengeSelected = null;
  state.practiceMode = false;
  $("#challenge-loading").classList.remove("hidden");
  $("#challenge-content").classList.add("hidden");
  $("#challenge-result").classList.add("hidden");
  $("#challenge-done").classList.add("hidden");

  try {
    const c = await api("/api/streak/challenge");

    if (c.already_solved) {
      $("#challenge-loading").classList.add("hidden");
      $("#challenge-done").classList.remove("hidden");
      startCountdown();
      return;
    }

    _renderChallenge(c);
  } catch(e) {
    $("#challenge-loading").textContent = "Failed to load challenge: " + e.message;
  }
}

async function loadNewChallenge() {
  // Fetch a fresh random question (practice mode)
  state.practiceMode = true;
  $("#challenge-loading").classList.remove("hidden");
  $("#challenge-content").classList.add("hidden");
  $("#challenge-result").classList.add("hidden");
  try {
    const c = await api("/api/streak/challenge/new");
    _renderChallenge(c);
  } catch(e) {
    $("#challenge-loading").textContent = "Failed: " + e.message;
    $("#challenge-loading").classList.remove("hidden");
  }
}

function selectChoice(idx) {
  state.challengeSelected = idx;
  $$("#chal-choices button").forEach((btn, i) => {
    const active = i === idx;
    btn.classList.toggle("border-violet-500", active);
    btn.classList.toggle("bg-violet-50", active);
    btn.classList.toggle("border-slate-200", !active);
  });
  $("#chal-submit").disabled = false;
}

async function submitChallenge() {
  if (state.challengeSelected === null || !state.currentChallenge) return;
  $("#chal-submit").disabled = true;

  try {
    const r = await api("/api/streak/challenge/submit", {
      method: "POST",
      body: JSON.stringify({
        choice_index: state.challengeSelected,
        challenge_id: state.currentChallenge.id,
      }),
    });

    $("#challenge-content").classList.add("hidden");
    $("#challenge-result").classList.remove("hidden");

    if (r.correct) {
      $("#chal-result-icon").textContent  = "🎉";
      $("#chal-result-title").textContent = "Correct! Well done!";
      $("#chal-result-title").className   = "text-xl font-bold text-emerald-600 mb-2";
    } else {
      $("#chal-result-icon").textContent  = "❌";
      $("#chal-result-title").textContent = "Not quite — here's why:";
      $("#chal-result-title").className   = "text-xl font-bold text-rose-600 mb-2";
    }

    const selectedText = state.currentChallenge.choices[state.challengeSelected];
    $("#chal-result-answer").textContent = r.correct
      ? `Your answer: ${selectedText} ✓`
      : `Your answer: ${selectedText} ✗  |  Correct: ${r.correct_answer}`;
    $("#chal-explanation").textContent = r.explanation;

    if (r.streak_updated) {
      $("#chal-streak-update").textContent =
        `🔥 Streak updated! Now ${r.current_streak} days · Consistency: ${r.consistency_score}/100`;
      try { await loadStreak(); } catch {}
    } else if (r.correct && state.practiceMode) {
      $("#chal-streak-update").textContent = "Practice mode — streak not updated (already counted today).";
    } else if (r.correct) {
      $("#chal-streak-update").textContent = "Already counted for today — streak safe!";
    } else {
      $("#chal-streak-update").textContent = state.practiceMode ? "Practice mode — keep going!" : "";
    }
  } catch(e) { alert("Submit failed: " + e.message); $("#chal-submit").disabled = false; }
}

function startCountdown() {
  const countEl = $("#chal-countdown");
  if (!countEl) return;
  function tick() {
    const now  = new Date();
    const next = new Date(now);
    next.setUTCHours(24, 0, 0, 0);
    const diff = Math.max(0, Math.floor((next - now) / 1000));
    const h = String(Math.floor(diff / 3600)).padStart(2,"0");
    const m = String(Math.floor((diff % 3600) / 60)).padStart(2,"0");
    const s = String(diff % 60).padStart(2,"0");
    countEl.textContent = `${h}:${m}:${s}`;
  }
  tick();
  setInterval(tick, 1000);
}

// ── Profile ───────────────────────────────────────────────────
async function loadProfile() {
  const p = await api("/api/profile");
  $("#p-name").value  = p.name || "";
  $("#p-dept").value  = p.department || "";
  $("#p-cgpa").value  = p.cgpa ?? "";
  $("#p-year").value  = p.year ?? "";
  $("#p-skills").value = (p.skills || []).join(", ");
  if (isStudent()) {
    const targets = new Set((p.target_companies || []).map(Number));
    $$("#p-targets option").forEach(o => { o.selected = targets.has(parseInt(o.value, 10)); });
  }
}

async function saveProfile(ev) {
  ev.preventDefault();
  const payload = {
    name:       $("#p-name").value,
    department: $("#p-dept").value,
    cgpa:       parseFloat($("#p-cgpa").value) || 0,
    year:       parseInt($("#p-year").value, 10) || 3,
    skills:     $("#p-skills").value.split(",").map(s=>s.trim()).filter(Boolean),
  };
  if (isStudent()) {
    payload.target_companies = Array.from($$("#p-targets option"))
      .filter(o => o.selected).map(o => parseInt(o.value, 10));
  }
  try {
    await api("/api/profile", { method:"PUT", body:JSON.stringify(payload) });
    $("#profile-msg").textContent = "✓ Saved";
    setTimeout(() => ($("#profile-msg").textContent = ""), 2000);
  } catch(e) { $("#profile-msg").textContent = "Error: " + e.message; }
}

// ── Resume Upload ─────────────────────────────────────────────
async function uploadResume(ev) {
  ev.preventDefault();
  const fileInput = $("#resume-file");
  const msg = $("#resume-msg");
  if (!fileInput.files[0]) { msg.textContent = "Please select a PDF."; msg.className="text-sm mt-2 text-rose-600"; return; }
  msg.textContent = "⏳ Parsing your resume with AI...";
  msg.className = "text-sm mt-2 text-slate-600";
  const fd = new FormData();
  fd.append("file", fileInput.files[0]);
  try {
    const res = await fetch("/api/resume/upload", {
      method:"POST", headers:{ Authorization:`Bearer ${state.token}` }, body:fd,
    });
    if (!res.ok) { const err = await res.json().catch(()=>({})); throw new Error(err.detail||"Upload failed"); }
    const data = await res.json();
    msg.textContent = `✅ ${data.message}`;
    msg.className = "text-sm mt-2 text-emerald-600";
    const ex = data.extracted;
    $("#resume-extracted").classList.remove("hidden");
    $("#resume-extracted").innerHTML = `
      <div class="bg-white p-3 rounded-lg border border-slate-200">
        <div class="font-medium text-slate-700 mb-1">AI Summary</div>
        <div class="text-slate-600 italic">${esc(ex.summary||"—")}</div>
      </div>
      <div class="bg-white p-3 rounded-lg border border-slate-200">
        <div class="font-medium text-slate-700 mb-1">Skills Detected (${ex.skills.length})</div>
        <div class="flex flex-wrap gap-1">${ex.skills.map(s=>`<span class="text-xs px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full">${esc(s)}</span>`).join("")}</div>
      </div>
      ${ex.projects.length?`<div class="bg-white p-3 rounded-lg border border-slate-200"><div class="font-medium text-slate-700 mb-1">Projects</div><ul class="list-disc pl-5 space-y-1">${ex.projects.map(p=>`<li>${esc(p)}</li>`).join("")}</ul></div>`:""}
      ${ex.certifications.length?`<div class="bg-white p-3 rounded-lg border border-slate-200"><div class="font-medium text-slate-700 mb-1">Certifications</div><ul class="list-disc pl-5 space-y-1">${ex.certifications.map(c=>`<li>${esc(c)}</li>`).join("")}</ul></div>`:""}`;
    await loadProfile();
  } catch(e) { msg.textContent = "❌ " + e.message; msg.className="text-sm mt-2 text-rose-600"; }
}

// ── Admin ─────────────────────────────────────────────────────
async function loadAdminDashboard() {
  await Promise.all([loadAdminStats(), loadAdminStudents(), loadAdminCompanies()]);
}

async function loadAdminStats() {
  try {
    const s = await api("/api/admin/stats");
    $("#admin-stats").innerHTML = `
      ${statCard("Students",    s.total_students,            "indigo")}
      ${statCard("Placed",      s.placed_students,           "emerald")}
      ${statCard("Unplaced",    s.unplaced_students,         "amber")}
      ${statCard("Companies",   s.total_companies,           "slate")}
      ${statCard("Placement %", s.placement_percentage + "%","rose")}`;
  } catch(e) {
    $("#admin-stats").innerHTML = `<div class="col-span-5 p-3 bg-red-50 text-red-700 rounded-lg text-sm">Failed: ${esc(e.message)}</div>`;
  }
}

function statCard(label, value, color) {
  const cls = {
    indigo:"bg-indigo-50 text-indigo-700", emerald:"bg-emerald-50 text-emerald-700",
    amber:"bg-amber-50 text-amber-700",    slate:"bg-slate-50 text-slate-700",
    rose:"bg-rose-50 text-rose-700",
  };
  return `<div class="${cls[color]||cls.slate} rounded-xl p-3 text-center">
    <div class="text-2xl font-bold">${esc(String(value))}</div>
    <div class="text-xs mt-0.5">${esc(label)}</div></div>`;
}

async function loadAdminStudents() {
  const filter = ($("#admin-student-filter")?.value) || "all";
  try {
    const students = await api(`/api/admin/students?status_filter=${filter}`);
    const list = $("#admin-students-list");
    if (!students.length) { list.innerHTML='<p class="text-sm text-slate-400 text-center py-4">No students.</p>'; return; }
    list.innerHTML = students.map(s => `
      <div class="flex items-center justify-between p-3 border border-slate-200 rounded-lg">
        <div>
          <div class="font-medium">${esc(s.name)} <span class="text-xs text-slate-500">(${esc(s.email)})</span></div>
          <div class="text-xs text-slate-500">Year ${s.year} ${esc(s.department)} · CGPA ${s.cgpa}</div>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs px-2 py-0.5 rounded-full ${s.placement_status==="placed"?"bg-emerald-100 text-emerald-700":"bg-amber-100 text-amber-700"}">${esc(s.placement_status)}</span>
          ${s.placement_status==="unplaced"
            ? `<button data-sid="${s.id}" class="mark-placed-btn text-xs px-2 py-1 bg-emerald-600 text-white rounded hover:bg-emerald-700">Mark Placed</button>`
            : `<button data-sid="${s.id}" class="mark-unplaced-btn text-xs px-2 py-1 bg-slate-200 text-slate-700 rounded hover:bg-slate-300">Mark Unplaced</button>`}
        </div>
      </div>`).join("");
    document.querySelectorAll(".mark-placed-btn").forEach(b   => { b.onclick = () => markPlacement(b.dataset.sid,"placed"); });
    document.querySelectorAll(".mark-unplaced-btn").forEach(b => { b.onclick = () => markPlacement(b.dataset.sid,"unplaced"); });
  } catch(e) { $("#admin-students-list").innerHTML=`<p class="text-sm text-rose-600">Failed: ${esc(e.message)}</p>`; }
}

async function markPlacement(studentId, status) {
  let companyId = null;
  if (status === "placed") {
    const opts = state.companies.map(c=>`${c.id}: ${c.name}`).join("\n");
    const choice = prompt(`Enter company ID:\n${opts}`);
    companyId = parseInt(choice, 10);
    if (!companyId) return;
  }
  try {
    await api(`/api/admin/students/${studentId}/placement`, {
      method:"PUT", body:JSON.stringify({ placement_status:status, placed_company_id:companyId }),
    });
    await loadAdminDashboard();
  } catch(e) { alert("Failed: "+e.message); }
}

async function loadAdminCompanies() {
  try {
    if (!state.companies.length) await loadCompanies();
    const list = $("#admin-companies-list");
    list.innerHTML = state.companies.map(c => `
      <div class="flex items-center justify-between p-3 border border-slate-200 rounded-lg">
        <div>
          <div class="font-medium">${esc(c.name)}</div>
          <div class="text-xs text-slate-500">${esc(c.sector||"")} · CGPA ≥ ${c.eligibility_cgpa??'—'} · ${esc(c.difficulty||"medium")}</div>
        </div>
        <button data-cid="${c.id}" class="del-company-btn text-xs px-2 py-1 bg-rose-600 text-white rounded hover:bg-rose-700">Delete</button>
      </div>`).join("");
    document.querySelectorAll(".del-company-btn").forEach(b => {
      b.onclick = async () => {
        if (!confirm("Delete this company?")) return;
        try { await api(`/api/admin/companies/${b.dataset.cid}`,{method:"DELETE"}); await loadCompanies(); await loadAdminCompanies(); }
        catch(e) { alert("Failed: "+e.message); }
      };
    });
  } catch(e) { console.error(e); }
}

async function submitNewCompany(ev) {
  ev.preventDefault();
  const payload = {
    name:             $("#ac-name").value.trim(),
    sector:           $("#ac-sector").value.trim(),
    ctc_min:          parseFloat($("#ac-ctc-min").value)||0,
    ctc_max:          parseFloat($("#ac-ctc-max").value)||0,
    eligibility_cgpa: parseFloat($("#ac-cgpa").value)||0,
    difficulty:       $("#ac-difficulty").value,
    rounds:           $("#ac-rounds").value.split(",").map(s=>s.trim()).filter(Boolean),
    topics:           $("#ac-topics").value.split(",").map(s=>s.trim()).filter(Boolean),
    description:      $("#ac-desc").value.trim(),
  };
  try {
    await api("/api/admin/companies",{method:"POST",body:JSON.stringify(payload)});
    $("#admin-company-modal").classList.add("hidden");
    ev.target.reset();
    await loadCompanies();
    await loadAdminCompanies();
  } catch(e) { alert("Failed: "+e.message); }
}

// ── Streak UI ─────────────────────────────────────────────────
function renderStreakDots(loginHistory) {
  const today = new Date();
  return Array.from({length:30}, (_,i) => {
    const d = new Date(today);
    d.setDate(today.getDate() - (29 - i));
    const iso = d.toISOString().slice(0,10);
    const active = loginHistory.includes(iso);
    return `<div title="${iso}" class="w-3 h-3 rounded-sm ${active?"bg-amber-400":"bg-slate-100"} border border-slate-200"></div>`;
  }).join("");
}

async function pingStreak() {
  const data = await api("/api/streak/ping",{method:"POST"});
  updateStreakUI(data);
  return data;
}

async function loadStreak() {
  const data = await api("/api/streak/me");
  updateStreakUI(data);
  return data;
}

function updateStreakUI(data) {
  if (!data || !isStudent()) return;
  const { current_streak, longest_streak, consistency_score, login_history } = data;
  const banner = $("#streak-banner");
  if (banner) {
    banner.classList.remove("hidden");
    const ec = $("#streak-current");     if(ec) ec.textContent = current_streak;
    const ecs = $("#streak-consistency");if(ecs) ecs.textContent = consistency_score;
    const el_ = $("#streak-longest");    if(el_) el_.textContent = longest_streak;
    const ed = $("#streak-dots");        if(ed) ed.innerHTML = renderStreakDots(login_history||[]);
  }
  const card = $("#profile-streak-card");
  if (card) {
    const psc = $("#ps-current");     if(psc) psc.textContent = current_streak;
    const psl = $("#ps-longest");     if(psl) psl.textContent = longest_streak;
    const psy = $("#ps-consistency"); if(psy) psy.textContent = consistency_score;
    const psh = $("#ps-heatmap");     if(psh) psh.innerHTML = renderStreakDots(login_history||[]);
    const psa = $("#ps-active-days"); if(psa) psa.textContent = `${(login_history||[]).length} days active`;
  }
  const sv = $("#chal-streak-val"); if(sv) sv.textContent = current_streak;
  // update in-memory user object too
  if (state.user) {
    state.user.current_streak = current_streak;
    state.user.longest_streak = longest_streak;
  }
}

// ── Wire events ───────────────────────────────────────────────
function wireEvents() {
  // Tab clicks
  $$(".tab-btn").forEach(btn => {
    btn.onclick = async () => {
      const tab = btn.dataset.tab;
      if (!isAuthed()) return showAuthView();
      showTab(tab);
      try {
        if (tab === "companies")   { await loadCompanies(); }
        if (tab === "experiences") { await loadExperiences($("#exp-filter").value); }
        if (tab === "challenge")   { await loadChallenge(); }
        if (tab === "ai")          { /* dropdowns already filled */ }
        if (tab === "profile")     { await loadProfile(); if(isStudent()) { try { await loadStreak(); } catch{} } }
        if (tab === "admin" && isOfficer()) await loadAdminDashboard();
      } catch(e) { console.error(e); }
    };
  });

  // Auth tabs
  $$(".auth-tab").forEach(b => {
    b.onclick = () => {
      const mode = b.dataset.auth;
      $$(".auth-tab").forEach(x => {
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

  $("#login-form").onsubmit = async ev => {
    ev.preventDefault();
    $("#auth-error").textContent = "";
    try { await doLogin($("#login-email").value.trim(), $("#login-password").value); await onAuthSuccess(); }
    catch(e) { $("#auth-error").textContent = e.message; }
  };

  $("#register-form").onsubmit = async ev => {
    ev.preventDefault();
    $("#auth-error").textContent = "";
    try {
      await doRegister({
        name:     $("#reg-name").value.trim(),
        email:    $("#reg-email").value.trim(),
        password: $("#reg-password").value,
        role:     $("#reg-role").value,
        cgpa:     parseFloat($("#reg-cgpa").value) || 0,
        year:     parseInt($("#reg-year").value, 10) || 3,
      });
      await onAuthSuccess();
    } catch(e) { $("#auth-error").textContent = e.message; }
  };

  const topLogin = $("#login-btn");
  if (topLogin) topLogin.onclick = showAuthView;

  // Modals
  $("#modal-close").onclick = () => $("#company-modal").classList.add("hidden");
  $("#company-modal").onclick = e => { if(e.target.id==="company-modal") $("#company-modal").classList.add("hidden"); };
  $("#share-close").onclick  = () => $("#share-modal").classList.add("hidden");
  $("#share-modal").onclick  = e => { if(e.target.id==="share-modal") $("#share-modal").classList.add("hidden"); };
  $("#share-exp-btn").onclick = () => { if(!isAuthed()) return showAuthView(); openShareModal(); };
  $("#share-form").onsubmit   = submitShare;
  $("#exp-filter").onchange   = e => loadExperiences(e.target.value);

  // Company filters
  const sectorF = $("#company-sector-filter");
  const diffF   = $("#company-diff-filter");
  if (sectorF) sectorF.onchange = renderCompanies;
  if (diffF)   diffF.onchange   = renderCompanies;

  // AI
  $("#btn-plan").onclick  = generatePlan;
  $("#btn-score").onclick = generateScore;
  $("#chat-form").onsubmit = sendChat;

  // Challenge: refresh / try another buttons
  const chalRefresh = $("#chal-refresh");
  if (chalRefresh) chalRefresh.onclick = loadNewChallenge;
  const tryAnother = $("#chal-try-another");
  if (tryAnother) tryAnother.onclick = loadNewChallenge;
  const practiceAnyway = $("#chal-practice-anyway");
  if (practiceAnyway) practiceAnyway.onclick = loadNewChallenge;

  // Profile
  $("#profile-form").onsubmit = saveProfile;
  const resumeForm = $("#resume-form");
  if (resumeForm) resumeForm.onsubmit = uploadResume;

  // Admin
  const adminFilter = $("#admin-student-filter");
  if (adminFilter) adminFilter.onchange = loadAdminStudents;
  const addBtn = $("#admin-add-company-btn");
  if (addBtn) addBtn.onclick = () => $("#admin-company-modal").classList.remove("hidden");
  const closeBtn = $("#admin-company-close");
  if (closeBtn) closeBtn.onclick = () => $("#admin-company-modal").classList.add("hidden");
  const newCompanyForm = $("#admin-company-form");
  if (newCompanyForm) newCompanyForm.onsubmit = submitNewCompany;
  const adminModal = $("#admin-company-modal");
  if (adminModal) adminModal.onclick = e => { if(e.target.id==="admin-company-modal") adminModal.classList.add("hidden"); };
}

// ── onAuthSuccess ─────────────────────────────────────────────
async function onAuthSuccess() {
  updateUserArea();
  setNavVisible(true);
  updateRoleVisibility();
  await loadCompanies();
  if (isStudent()) {
    try { await pingStreak(); } catch(e) { console.warn("streak ping failed", e); }
  }
  const tab = defaultTabForRole();
  showTab(tab);
  if (isOfficer()) await loadAdminDashboard();
}

// ── Init ──────────────────────────────────────────────────────
(async function init() {
  wireEvents();
  await checkHealth();
  const me = await fetchMe();
  updateUserArea();
  if (me) {
    setNavVisible(true);
    updateRoleVisibility();
    try { await loadCompanies(); } catch(e) { console.error(e); }
    if (isStudent()) { try { await pingStreak(); } catch(e) { console.warn(e); } }
    const tab = defaultTabForRole();
    showTab(tab);
    if (isOfficer()) { try { await loadAdminDashboard(); } catch(e) { console.error(e); } }
  } else {
    setNavVisible(false);
    showAuthView();
  }
})();
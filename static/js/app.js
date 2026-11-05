/**
 * app.js – Frontend logic for the AICTE Interview Trainer Agent
 * Communicates with the Flask REST API; renders results in-page.
 */

const API = "";   // same-origin; change to "http://localhost:5000" if running separately

// ── Simple markdown → HTML renderer ──────────────────────────────────────────
function renderMarkdown(text) {
  if (!text) return "";
  let html = text
    // headers
    .replace(/^### (.+)$/gm,   "<h3>$1</h3>")
    .replace(/^## (.+)$/gm,    "<h2>$1</h2>")
    .replace(/^# (.+)$/gm,     "<h1>$1</h1>")
    // bold
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    // italic
    .replace(/\*(.+?)\*/g,     "<em>$1</em>")
    // inline code
    .replace(/`(.+?)`/g,       "<code>$1</code>")
    // horizontal rule
    .replace(/^---$/gm,        "<hr>")
    // numbered list items
    .replace(/^\d+\.\s(.+)$/gm,"<li>$1</li>")
    // bullet list items
    .replace(/^[-•]\s(.+)$/gm, "<li>$1</li>")
    // line breaks
    .replace(/\n\n/g, "<br><br>")
    .replace(/\n/g,   "<br>");
  // wrap consecutive <li> in <ul>
  html = html.replace(/(<li>.*?<\/li>(<br>)?)+/gs, match =>
    "<ul>" + match.replace(/<br>/g, "") + "</ul>"
  );
  return html;
}

// ── DOM helpers ──────────────────────────────────────────────────────────────
const $  = id => document.getElementById(id);
const show  = el => el.classList.remove("hidden");
const hide  = el => el.classList.add("hidden");

function showToast(msg, type = "info") {
  const t = $("toast");
  t.textContent = msg;
  t.className = `toast ${type}`;
  setTimeout(() => t.classList.add("hidden"), 4000);
}

function showLoading(msg = "Generating with IBM Granite…") {
  $("loadingMsg").textContent = msg;
  show($("loadingOverlay"));
}
function hideLoading() { hide($("loadingOverlay")); }

// ── Tab navigation ────────────────────────────────────────────────────────────
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.add("hidden"));
    btn.classList.add("active");
    show($(`tab-${btn.dataset.tab}`));
  });
});

// ── Health check & populate dropdowns ─────────────────────────────────────────
async function initApp() {
  try {
    const [healthRes, rolesRes] = await Promise.all([
      fetch(`${API}/api/health`),
      fetch(`${API}/api/roles`),
    ]);
    if (healthRes.ok) {
      const h = await healthRes.json();
      const badge = $("statusBadge");
      badge.textContent = `✓ ${h.model.split("/").pop()}`;
      badge.className = "status-badge healthy";
    }
    if (rolesRes.ok) {
      const r = await rolesRes.json();
      const roleSelects = ["jobRole","resumeRole","evalRole","stratRole","searchRole"];
      roleSelects.forEach(id => {
        const sel = $(id);
        if (!sel) return;
        r.roles.forEach(role => {
          const opt = document.createElement("option");
          opt.value = role;
          opt.textContent = role;
          sel.appendChild(opt);
        });
      });
    }
  } catch {
    const badge = $("statusBadge");
    badge.textContent = "⚠ Offline";
    badge.className = "status-badge error";
  }
}

// ── Build profile result panel ────────────────────────────────────────────────
function buildPlanResult(data, containerId) {
  const panel = $(containerId);
  show(panel);

  const p = data.profile || {};
  const skills = (p.skills || []).slice(0, 8).join(", ");

  panel.innerHTML = `
    <div class="result-header">
      <span>🎯</span>
      <h3>Interview Preparation Plan — ${p.name || "Candidate"}</h3>
    </div>
    <div class="result-body">
      <div class="profile-badge">
        <span class="badge badge-name">👤 ${p.name || "—"}</span>
        <span class="badge badge-role">💼 ${p.job_role || "—"}</span>
        <span class="badge badge-level">📊 ${(p.experience_level || "—").toUpperCase()}</span>
        ${skills ? `<span class="badge badge-role">🛠 ${skills}</span>` : ""}
      </div>

      <div class="result-tabs">
        <button class="res-tab-btn active" data-res-tab="qa">📝 Questions &amp; Answers</button>
        <button class="res-tab-btn" data-res-tab="strategy">🗓️ Study Roadmap</button>
      </div>

      <div id="res-qa" class="res-tab-content active">
        <div class="rendered-content">${renderMarkdown(data.questions_and_answers || "No questions generated.")}</div>
      </div>
      <div id="res-strategy" class="res-tab-content">
        <div class="rendered-content">${renderMarkdown(data.preparation_strategy || "No strategy generated.")}</div>
      </div>
    </div>
  `;

  // inner result tab switching
  panel.querySelectorAll(".res-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      panel.querySelectorAll(".res-tab-btn").forEach(b => b.classList.remove("active"));
      panel.querySelectorAll(".res-tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const tabId = `res-${btn.dataset.resTab}`;
      panel.querySelector(`#${tabId}`).classList.add("active");
    });
  });

  panel.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ── 1. Generate plan from profile ────────────────────────────────────────────
$("btnGeneratePlan").addEventListener("click", async () => {
  const name  = $("name").value.trim();
  const role  = $("jobRole").value;
  const level = $("expLevel").value;
  const skills = $("skills").value.split(",").map(s => s.trim()).filter(Boolean);
  const timeline = parseInt($("timeline").value) || 30;

  if (!name)  { showToast("Please enter your name.", "error"); return; }
  if (!role)  { showToast("Please select a job role.", "error"); return; }
  if (!level) { showToast("Please select an experience level.", "error"); return; }

  showLoading("Generating tailored interview questions with IBM Granite…");
  $("btnGeneratePlan").disabled = true;

  try {
    const res = await fetch(`${API}/api/prepare/profile`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ name, job_role: role, experience_level: level, skills, timeline_days: timeline }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Server error");
    buildPlanResult(data, "profileResult");
    showToast("Plan generated successfully! 🎉", "success");
  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
    $("profileResult").innerHTML = `<div class="result-body" style="color:var(--danger);padding:24px">⚠ ${err.message}</div>`;
    show($("profileResult"));
  } finally {
    hideLoading();
    $("btnGeneratePlan").disabled = false;
  }
});

// ── 2. Upload Resume ──────────────────────────────────────────────────────────
const uploadZone = $("uploadZone");
const resumeFile = $("resumeFile");

uploadZone.addEventListener("click", () => resumeFile.click());
uploadZone.addEventListener("dragover", e => { e.preventDefault(); uploadZone.classList.add("dragover"); });
uploadZone.addEventListener("dragleave", () => uploadZone.classList.remove("dragover"));
uploadZone.addEventListener("drop", e => {
  e.preventDefault();
  uploadZone.classList.remove("dragover");
  if (e.dataTransfer.files[0]) {
    resumeFile.files = e.dataTransfer.files;
    showFileInfo(e.dataTransfer.files[0]);
  }
});
resumeFile.addEventListener("change", () => {
  if (resumeFile.files[0]) showFileInfo(resumeFile.files[0]);
});

function showFileInfo(file) {
  const fi = $("fileInfo");
  fi.innerHTML = `📎 <strong>${file.name}</strong> &nbsp;·&nbsp; ${(file.size / 1024).toFixed(1)} KB`;
  show(fi);
}

$("btnUploadResume").addEventListener("click", async () => {
  if (!resumeFile.files[0]) { showToast("Please select a resume file.", "error"); return; }

  const fd = new FormData();
  fd.append("file", resumeFile.files[0]);
  const role  = $("resumeRole").value;
  const level = $("resumeLevel").value;
  const timeline = parseInt($("resumeTimeline").value) || 30;
  if (role)    fd.append("job_role", role);
  if (level)   fd.append("experience_level", level);
  fd.append("timeline_days", timeline);

  showLoading("Parsing resume and generating plan with IBM Granite…");
  $("btnUploadResume").disabled = true;

  try {
    const res  = await fetch(`${API}/api/prepare/resume`, { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Server error");
    buildPlanResult(data, "resumeResult");
    showToast("Resume analysed successfully! 🎉", "success");
  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
    $("resumeResult").innerHTML = `<div class="result-body" style="color:var(--danger);padding:24px">⚠ ${err.message}</div>`;
    show($("resumeResult"));
  } finally {
    hideLoading();
    $("btnUploadResume").disabled = false;
  }
});

// ── 3. Evaluate Answer ────────────────────────────────────────────────────────
$("btnEvaluate").addEventListener("click", async () => {
  const role     = $("evalRole").value;
  const question = $("evalQuestion").value.trim();
  const answer   = $("evalAnswer").value.trim();

  if (!role)     { showToast("Please select a role.", "error"); return; }
  if (!question) { showToast("Please enter a question.", "error"); return; }
  if (!answer)   { showToast("Please enter your answer.", "error"); return; }

  showLoading("Evaluating your answer with IBM Granite…");
  $("btnEvaluate").disabled = true;

  try {
    const res  = await fetch(`${API}/api/evaluate`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ role, question, candidate_answer: answer }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Server error");

    const panel = $("evaluateResult");
    show(panel);
    panel.innerHTML = `
      <div class="result-header"><span>📊</span><h3>Answer Evaluation</h3></div>
      <div class="result-body">
        <div class="profile-badge">
          <span class="badge badge-role">💼 ${role}</span>
        </div>
        <div class="rendered-content">${renderMarkdown(data.feedback || "No feedback.")}</div>
      </div>
    `;
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
    showToast("Evaluation complete!", "success");
  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
  } finally {
    hideLoading();
    $("btnEvaluate").disabled = false;
  }
});

// ── 4. Strategy / Roadmap ─────────────────────────────────────────────────────
$("btnStrategy").addEventListener("click", async () => {
  const role     = $("stratRole").value;
  const level    = $("stratLevel").value;
  const skills   = $("stratSkills").value.split(",").map(s => s.trim()).filter(Boolean);
  const timeline = parseInt($("stratTimeline").value) || 30;

  if (!role)  { showToast("Please select a role.", "error"); return; }
  if (!level) { showToast("Please select an experience level.", "error"); return; }

  showLoading("Building your study roadmap with IBM Granite…");
  $("btnStrategy").disabled = true;

  try {
    const res  = await fetch(`${API}/api/strategy`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ job_role: role, experience_level: level, skills, timeline_days: timeline }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Server error");

    const panel = $("strategyResult");
    show(panel);
    panel.innerHTML = `
      <div class="result-header"><span>🗓️</span><h3>${timeline}-Day Study Roadmap — ${role}</h3></div>
      <div class="result-body">
        <div class="profile-badge">
          <span class="badge badge-role">💼 ${role}</span>
          <span class="badge badge-level">📊 ${level.toUpperCase()}</span>
          <span class="badge badge-name">📅 ${timeline} days</span>
        </div>
        <div class="rendered-content">${renderMarkdown(data.strategy || "No strategy generated.")}</div>
      </div>
    `;
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
    showToast("Roadmap generated! 🗓️", "success");
  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
  } finally {
    hideLoading();
    $("btnStrategy").disabled = false;
  }
});

// ── 5. Search Knowledge Base ──────────────────────────────────────────────────
async function doSearch() {
  const q    = $("searchQuery").value.trim();
  const role = $("searchRole").value || "";

  if (!q) { showToast("Please enter a search query.", "error"); return; }

  showLoading("Searching knowledge base…");
  $("btnSearch").disabled = true;

  try {
    const url = `${API}/api/questions/search?q=${encodeURIComponent(q)}${role ? `&role=${encodeURIComponent(role)}` : ""}`;
    const res  = await fetch(url);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Server error");

    const panel = $("searchResult");
    show(panel);

    if (!data.results || data.results.length === 0) {
      panel.innerHTML = `<div class="result-body" style="padding:24px;color:var(--muted)">No results found for "<strong>${q}</strong>".</div>`;
    } else {
      const items = data.results.map((doc, i) =>
        `<div class="search-item"><div class="search-meta">Result ${i + 1}</div>${doc}</div>`
      ).join("");
      panel.innerHTML = `
        <div class="result-header"><span>🔎</span><h3>${data.count} result(s) for "${q}"</h3></div>
        <div class="result-body">${items}</div>
      `;
    }
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
  } finally {
    hideLoading();
    $("btnSearch").disabled = false;
  }
}

$("btnSearch").addEventListener("click", doSearch);
$("searchQuery").addEventListener("keydown", e => { if (e.key === "Enter") doSearch(); });

// ── Boot ──────────────────────────────────────────────────────────────────────
initApp();

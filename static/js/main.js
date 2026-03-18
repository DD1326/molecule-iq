/* ============================================================
   MoleculeIQ — main.js
   AI Avengers · SVCE Blueprints 2026
   ============================================================ */

"use strict";

// ── Claude API Key (entered by user at first run) ──────────
let ANTHROPIC_KEY = localStorage.getItem("moleculeiq_api_key") || "";

// ── DOM references ──────────────────────────────────────────
const searchInput   = document.getElementById("search-input");
const analyzeBtn    = document.getElementById("analyze-btn");
const loadingSection = document.getElementById("loading-section");
const statsSection  = document.getElementById("stats-section");
const dataSection   = document.getElementById("data-section");
const reportSection = document.getElementById("report-section");
const errorBanner   = document.getElementById("error-banner");
const errorMsg      = document.getElementById("error-msg");

// Stat elements
const statPapers    = document.getElementById("stat-papers");
const statTrials    = document.getElementById("stat-trials");
const statFDA       = document.getElementById("stat-fda");
const statClasses   = document.getElementById("stat-classes");

// Card bodies
const papersBody    = document.getElementById("papers-body");
const trialsBody    = document.getElementById("trials-body");
const fdaBody       = document.getElementById("fda-body");
const rxnormBody    = document.getElementById("rxnorm-body");

// Counts
const papersCount   = document.getElementById("papers-count");
const trialsCount   = document.getElementById("trials-count");
const fdaCount      = document.getElementById("fda-count");
const rxnormCount   = document.getElementById("rxnorm-count");

// Report
const reportMolName  = document.getElementById("report-mol-name");
const reportBody     = document.getElementById("report-body");

// Loading steps
const loadingStepEls = document.querySelectorAll(".loading-step");

// ── Helpers ─────────────────────────────────────────────────

function showError(msg) {
  errorBanner.classList.add("visible");
  errorMsg.textContent = msg;
}
function hideError() {
  errorBanner.classList.remove("visible");
}

function hide(el) { el.style.display = "none"; }
function show(el, display = "block") { el.style.display = display; }

/** Animate a counter from 0 to target. */
function animateCounter(el, target, duration = 800) {
  const start = performance.now();
  const update = (now) => {
    const pct = Math.min((now - start) / duration, 1);
    el.textContent = Math.round(pct * target);
    if (pct < 1) requestAnimationFrame(update);
    else el.textContent = target;
  };
  requestAnimationFrame(update);
}

// ── Loading step animation ──────────────────────────────────

function resetLoadingSteps() {
  loadingStepEls.forEach(el => {
    el.classList.remove("active", "done");
    el.querySelector(".step-icon").textContent = el.dataset.icon || "○";
  });
}

function activateStep(index) {
  // Mark previous as done
  if (index > 0) {
    loadingStepEls[index - 1].classList.remove("active");
    loadingStepEls[index - 1].classList.add("done");
    loadingStepEls[index - 1].querySelector(".step-icon").textContent = "✓";
  }
  if (index < loadingStepEls.length) {
    loadingStepEls[index].classList.add("active");
    loadingStepEls[index].querySelector(".step-icon").textContent =
      loadingStepEls[index].dataset.active || "⟳";
  }
}

function markAllStepsDone() {
  loadingStepEls.forEach(el => {
    el.classList.remove("active");
    el.classList.add("done");
    el.querySelector(".step-icon").textContent = "✓";
  });
}

// ── Quick search / pills ────────────────────────────────────

function quickSearch(molecule) {
  searchInput.value = molecule;
  startAnalysis();
}

// ── Main analysis flow ──────────────────────────────────────

async function startAnalysis() {
  const molecule = searchInput.value.trim();
  if (!molecule) {
    searchInput.focus();
    return;
  }

  // Ensure we have an API key
  if (!ANTHROPIC_KEY) {
    const key = prompt(
      "Enter your Anthropic API key to enable AI report generation:\n(Leave blank to view raw data only)"
    );
    if (key && key.trim()) {
      ANTHROPIC_KEY = key.trim();
      localStorage.setItem("moleculeiq_api_key", ANTHROPIC_KEY);
    }
  }

  // ── UI reset ──
  hideError();
  hide(statsSection);
  hide(dataSection);
  hide(reportSection);
  show(loadingSection);
  analyzeBtn.disabled = true;
  resetLoadingSteps();

  // Step 0 – PubMed
  activateStep(0);
  await sleep(400);

  let data;
  try {
    // Steps run in parallel on the backend — we stagger the UI
    const fetchPromise = fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ molecule }),
      signal: AbortSignal.timeout(20000),
    });

    // Stagger loading messages while waiting
    await sleep(800);  activateStep(1);
    await sleep(800);  activateStep(2);
    await sleep(800);  activateStep(3);

    const res = await fetchPromise;
    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    data = await res.json();

    activateStep(4);   // AI synthesizing
    await sleep(600);
  } catch (err) {
    console.error("[analyze]", err);
    hide(loadingSection);
    show(errorBanner);
    showError(
      err.name === "TimeoutError"
        ? "Request timed out (>20 s). Check your network and try again."
        : `Data retrieval failed: ${err.message}`
    );
    analyzeBtn.disabled = false;
    return;
  }

  // ── Render raw data ──
  updateStats(data.papers, data.trials, data.fda, data.rxnorm);
  renderPapers(data.papers);
  renderTrials(data.trials);
  renderFDA(data.fda);
  renderRxNorm(data.rxnorm);

  show(statsSection);
  show(dataSection);

  // ── AI report ──
  if (ANTHROPIC_KEY) {
    show(reportSection);
    reportMolName.textContent = data.molecule;
    reportBody.innerHTML = `
      <div class="report-loading">
        <div class="spinner"></div>
        <p>Claude is generating your Innovation Report…</p>
      </div>`;
    reportSection.scrollIntoView({ behavior: "smooth", block: "start" });
    await buildAndRunAIReport(data.molecule, data);
  } else {
    // Show data without AI report
    dataSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  markAllStepsDone();
  hide(loadingSection);
  analyzeBtn.disabled = false;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── Stat counters ────────────────────────────────────────────

function updateStats(papers, trials, fda, rxnorm) {
  animateCounter(statPapers,  papers.length);
  animateCounter(statTrials,  trials.length);
  animateCounter(statFDA,     fda.length);
  animateCounter(statClasses, (rxnorm.drug_classes || []).length);
}

// ── Render: PubMed Papers ────────────────────────────────────

function renderPapers(papers) {
  papersCount.textContent = papers.length;
  if (!papers.length) {
    papersBody.innerHTML = emptyState("🔬", "No papers found for this molecule");
    return;
  }
  papersBody.innerHTML = papers.map(p => `
    <div class="paper-item">
      <a href="${escHtml(p.url)}" target="_blank" rel="noopener" class="paper-title">
        ${escHtml(p.title)}
      </a>
      <div class="paper-meta">
        ${escHtml(p.journal)} · ${escHtml(p.year)} · ${escHtml(p.authors)}
        <br>PMID: ${escHtml(p.pmid)}
      </div>
    </div>`).join("");
}

// ── Render: Clinical Trials ──────────────────────────────────

function renderTrials(trials) {
  trialsCount.textContent = trials.length;
  if (!trials.length) {
    trialsBody.innerHTML = emptyState("🧪", "No active clinical trials found");
    return;
  }
  trialsBody.innerHTML = trials.map(t => `
    <div class="trial-item">
      <a href="${escHtml(t.url)}" target="_blank" rel="noopener" class="trial-title">
        ${escHtml(t.title)}
      </a>
      <div class="trial-badges">
        <span class="${phaseCss(t.phase)}">${escHtml(t.phase)}</span>
        <span class="${statusCss(t.status)}">${escHtml(t.status)}</span>
        ${t.conditions.map(c => `<span class="tag tag-related" style="font-size:0.68rem">${escHtml(c)}</span>`).join("")}
      </div>
    </div>`).join("");
}

function phaseCss(phase) {
  const p = (phase || "").toLowerCase();
  if (p.includes("1")) return "phase-badge phase-1";
  if (p.includes("2")) return "phase-badge phase-2";
  if (p.includes("3")) return "phase-badge phase-3";
  if (p.includes("4")) return "phase-badge phase-4";
  return "phase-badge phase-n";
}
function statusCss(status) {
  const s = (status || "").toUpperCase();
  if (s.includes("RECRUIT")) return "status-badge status-recruiting";
  if (s.includes("COMPLET")) return "status-badge status-completed";
  if (s.includes("ACTIVE"))  return "status-badge status-active";
  if (s.includes("TERM"))    return "status-badge status-terminated";
  return "status-badge status-other";
}

// ── Render: FDA Labels ───────────────────────────────────────

function renderFDA(labels) {
  fdaCount.textContent = labels.length;
  if (!labels.length) {
    fdaBody.innerHTML = emptyState("💊", "No FDA label records found");
    return;
  }
  fdaBody.innerHTML = labels.map(f => `
    <div class="fda-item">
      <div class="fda-brand">${escHtml(f.brand_name)}</div>
      <div class="fda-meta">
        Generic: ${escHtml(f.generic_name)} · Route: ${escHtml(f.route)} · ${escHtml(f.manufacturer)}
      </div>
      <div class="fda-indications">${escHtml(f.indications)}</div>
    </div>`).join("");
}

// ── Render: RxNorm ───────────────────────────────────────────

function renderRxNorm(rxnorm) {
  const classes  = rxnorm.drug_classes  || [];
  const related  = rxnorm.related_drugs || [];
  rxnormCount.textContent = classes.length;

  if (!rxnorm.rxcui && !classes.length && !related.length) {
    rxnormBody.innerHTML = emptyState("🔗", "Drug not found in RxNorm database");
    return;
  }

  let html = "";
  if (classes.length) {
    html += `<div class="rxnorm-section">
      <div class="rxnorm-heading">Drug Classes</div>
      <div class="tag-wrap">${classes.map(c => `<span class="tag tag-class">${escHtml(c)}</span>`).join("")}</div>
    </div>`;
  }
  if (related.length) {
    html += `<div class="rxnorm-section">
      <div class="rxnorm-heading">Related Drugs</div>
      <div class="tag-wrap">${related.map(r => `<span class="tag tag-related">${escHtml(r)}</span>`).join("")}</div>
    </div>`;
  }
  if (rxnorm.rxcui) {
    html += `<div class="rxcui-display">RxCUI: <span style="color:var(--accent2)">${escHtml(String(rxnorm.rxcui))}</span></div>`;
  }
  rxnormBody.innerHTML = html;
}

// ── AI Report ────────────────────────────────────────────────

async function buildAndRunAIReport(molecule, context) {
  // Fetch structured prompt from backend
  let prompt;
  try {
    const res = await fetch("/stream_analysis", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(context),
    });
    const data = await res.json();
    prompt = data.prompt;
  } catch (err) {
    reportBody.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div>
      Failed to build AI prompt: ${escHtml(err.message)}</div>`;
    return;
  }

  // Call Anthropic API from browser
  try {
    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "anthropic-dangerous-direct-browser-access": "true",
      },
      body: JSON.stringify({
        model: "claude-opus-4-5",
        max_tokens: 2000,
        messages: [{ role: "user", content: prompt }],
      }),
      signal: AbortSignal.timeout(60000),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error?.message || `HTTP ${res.status}`);
    }

    const data = await res.json();
    const text = data.content?.[0]?.text || "No response received.";
    renderReport(text);
  } catch (err) {
    reportBody.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🤖</div>
        <p>AI analysis unavailable — displaying raw data only.</p>
        <p style="font-size:0.78rem;margin-top:8px;color:var(--accent3)">${escHtml(err.message)}</p>
      </div>`;
  }
}

// ── Markdown → HTML renderer ─────────────────────────────────

function renderReport(markdown) {
  // Use marked.js if loaded, otherwise simple regex fallback
  if (typeof marked !== "undefined") {
    reportBody.innerHTML = marked.parse(markdown);
  } else {
    reportBody.innerHTML = simpleMarkdown(markdown);
  }
}

/** Lightweight markdown → HTML (covers headings, bold, italic, lists, inline code) */
function simpleMarkdown(md) {
  return md
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;") // sanitise first
    .replace(/^#{2} (.+)$/gm, "<h2>$1</h2>")
    .replace(/^#{3} (.+)$/gm, "<h3>$1</h3>")
    .replace(/^#{1} (.+)$/gm, "<h2>$1</h2>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>")
    .replace(/^\s*[-*] (.+)$/gm, "<li>$1</li>")
    .replace(/^\d+\. (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>[\s\S]+?<\/li>)+/g, "<ul>$&</ul>")
    .replace(/\n{2,}/g, "</p><p>")
    .replace(/^(?!<[huli])(.+)$/gm, "<p>$1</p>")
    .replace(/<p><\/p>/g, "");
}

// ── PDF Export ───────────────────────────────────────────────

function exportReport() {
  window.print();
}

// ── Utilities ────────────────────────────────────────────────

function escHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function emptyState(icon, msg) {
  return `<div class="empty-state"><div class="empty-icon">${icon}</div>${escHtml(msg)}</div>`;
}

// ── Event Listeners ──────────────────────────────────────────

analyzeBtn.addEventListener("click", startAnalysis);
searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") startAnalysis();
});

// Expose globally for inline onclick handlers
window.quickSearch = quickSearch;
window.startAnalysis = startAnalysis;
window.exportReport = exportReport;

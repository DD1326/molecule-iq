/* ============================================================
   MoleculeIQ v2 — main.js
   AI Avengers · SVCE Blueprints 2026
   10 real-time APIs · Smart Report Generator
   ============================================================ */

"use strict";

// ── DOM references ──────────────────────────────────────────
const searchInput = document.getElementById("search-input");
const analyzeBtn = document.getElementById("analyze-btn");
const loadingSection = document.getElementById("loading-section");
const statsSection = document.getElementById("stats-section");
const dataSection = document.getElementById("data-section");
const reportSection = document.getElementById("report-section");
const errorBanner = document.getElementById("error-banner");
const errorMsg = document.getElementById("error-msg");
const voiceBtn = document.getElementById("voice-btn");
const autocompleteDropdown = document.getElementById("autocomplete-results");
let latestAnalysisResults = null; // SCAN: Captures current page data for Chatbot

const statPapers = document.getElementById("stat-papers");
const statPreprints = document.getElementById("stat-preprints");
const statTrials = document.getElementById("stat-trials");
const statGlobalTrials = document.getElementById("stat-global-trials");
const statFDA = document.getElementById("stat-fda");
const statClasses = document.getElementById("stat-classes");

const papersBody = document.getElementById("papers-body");
const trialsBody = document.getElementById("trials-body");
const fdaBody = document.getElementById("fda-body");
const rxnormBody = document.getElementById("rxnorm-body");
const preprintsBody = document.getElementById("preprints-body");
const chemblBody = document.getElementById("chembl-body");

const papersCount = document.getElementById("papers-count");
const trialsCount = document.getElementById("trials-count");
const fdaCount = document.getElementById("fda-count");
const rxnormCount = document.getElementById("rxnorm-count");
const preprintsCount = document.getElementById("preprints-count");
const chemblCount = document.getElementById("chembl-count");

const reportMolName = document.getElementById("report-mol-name");
const reportBody = document.getElementById("report-body");

const loadingStepEls = document.querySelectorAll(".loading-step");
const chatbotStatus = document.getElementById("chatbot-status");
const statusText = document.getElementById("status-text");

const bannedModal = document.getElementById("banned-modal");
const bannedMolName = document.getElementById("banned-mol-name");
const bannedCat = document.getElementById("banned-cat");
const bannedReason = document.getElementById("banned-reason");

function showBannedModal(data) {
  bannedMolName.textContent = data.molecule || data.name;
  bannedCat.textContent = data.category;
  bannedReason.textContent = data.reason;
  bannedModal.classList.remove("hidden");
}

function closeBannedModal() {
  bannedModal.classList.add("hidden");
}

window.closeBannedModal = closeBannedModal;

// ── Helpers ─────────────────────────────────────────────────

function showError(msg) {
  errorBanner.classList.add("visible");
  errorMsg.textContent = msg;
}
function hideError() { errorBanner.classList.remove("visible"); }
function hide(el) { if (el) el.style.display = "none"; }
function show(el, display = "block") { if (el) el.style.display = display; }
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function animateCounter(el, target, duration = 800) {
  if (!el) return;
  const start = performance.now();
  const update = (now) => {
    const pct = Math.min((now - start) / duration, 1);
    el.textContent = Math.round(pct * target);
    if (pct < 1) requestAnimationFrame(update);
    else el.textContent = target;
  };
  requestAnimationFrame(update);
}

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

function daysAgo(dateStr) {
  if (!dateStr) return null;
  const d = new Date(dateStr);
  if (isNaN(d)) return null;
  const diff = Math.floor((Date.now() - d.getTime()) / 86400000);
  return diff;
}

function recencyBadge(dateStr) {
  const days = daysAgo(dateStr);
  if (days === null) return "";
  if (days <= 0) return `<span class="recency-badge recency-today">Today</span>`;
  if (days <= 7) return `<span class="recency-badge recency-week">${days}d ago</span>`;
  if (days <= 30) return `<span class="recency-badge recency-month">${days}d ago</span>`;
  return `<span class="recency-badge recency-old">${days}d ago</span>`;
}

function sourceBadge(source) {
  if (!source) return "";
  const cls = {
    "PubMed": "src-pubmed",
    "Europe PMC": "src-europepmc",
    "Semantic Scholar": "src-semantic",
    "CrossRef": "src-crossref",
    "medRxiv preprint": "src-medrxiv",
    "ClinicalTrials.gov": "src-ctgov",
    "WHO ICTRP": "src-who",
  }[source] || "src-other";
  return `<span class="source-badge ${cls}">${escHtml(source)}</span>`;
}

// ── Loading steps ────────────────────────────────────────────

function resetLoadingSteps() {
  loadingStepEls.forEach(el => {
    el.classList.remove("active", "done");
    el.querySelector(".step-icon").textContent = el.dataset.icon || "○";
  });
}

function activateStep(index) {
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

// ── Quick search pills ───────────────────────────────────────

function quickSearch(molecule) {
  searchInput.value = molecule;
  startAnalysis();
}

// ── Main analysis flow ───────────────────────────────────────

async function startAnalysis() {
  if (analyzeBtn.disabled) return; // v2.3.4 Execution Guard

  const molecule = searchInput.value.trim();
  if (!molecule) { searchInput.focus(); return; }

  // ── Proactive Banned Check ──
  try {
    const checkRes = await fetch("/api/check-banned", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ molecule })
    });
    const checkData = await checkRes.json();
    if (checkData.is_banned) {
      showBannedModal({ ...checkData, molecule });
      return; // Stop execution
    }
  } catch (err) {
    console.warn("[SafeCheck Error]", err);
  }

  // ── UI reset ──
  hideError();
  hide(statsSection);
  hide(dataSection);
  hide(reportSection);
  show(loadingSection);
  analyzeBtn.disabled = true;
  hideAutocomplete(); // Ensure cleanup
  resetLoadingSteps();

  activateStep(0);
  await sleep(400);

  let data;
  try {
    const fetchPromise = fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ molecule }),
      signal: AbortSignal.timeout(60000), // v2.1: extended to 60s for parallel APIs
    });

    // 7 loading steps
    await sleep(600); activateStep(1);
    await sleep(600); activateStep(2);
    await sleep(600); activateStep(3);
    await sleep(600); activateStep(4);
    await sleep(600); activateStep(5);

    const res = await fetchPromise;
    if (!res.ok) {
      let errMsg = `Server error: ${res.status}`;
      try {
        const errJson = await res.json();
        if (errJson.error) errMsg = errJson.error;
      } catch (e) { }
      throw new Error(errMsg);
    }
    data = await res.json();
    latestAnalysisResults = data; // Save for Chatbot scan

    activateStep(6);
    await sleep(600);

  } catch (err) {
    console.error("[analyze]", err);
    hide(loadingSection);
    showError(
      err.name === "TimeoutError"
        ? "Request timed out. Check your network and try again."
        : `Data retrieval failed: ${err.message}`
    );
    analyzeBtn.disabled = false;
    return;
  }

  // ── Render data cards ──
  renderExperimentalBanner(data.experimental_banner);
  updateStats(data);
  renderPapers(data.papers || []);
  renderTrials(data.clinical_trials || []);
  renderFDA(data.fda_labels || []);
  renderRxNorm(data.rxnorm || {}, data.chembl || {});
  renderPreprints(data.preprints || []);
  renderChEMBL(data.chembl || {}, data.rxnorm || {});

  show(statsSection);
  show(dataSection);

  // ── Generate report from real data ──
  show(reportSection);
  reportMolName.textContent = data.molecule || molecule;
  reportBody.innerHTML = `
    <div class="report-loading">
      <div class="spinner"></div>
      <p>Synthesising Innovation Report from real data…</p>
    </div>`;
  reportSection.scrollIntoView({ behavior: "smooth", block: "start" });

  await sleep(1400);
  generateSmartReport(molecule, data);

  markAllStepsDone();
  hide(loadingSection);
  analyzeBtn.disabled = false;
}

// ── UX Polish: Autocomplete & Voice v2.3 (Google Standard) ──

let debounceTimer;
let activeIndex = -1;
let suggestionsList = [];

searchInput.addEventListener("input", () => {
  clearTimeout(debounceTimer);
  const q = searchInput.value.trim();
  if (q.length === 0) {
    hideAutocomplete();
    return;
  }
  if (q.length < 2) return;
  debounceTimer = setTimeout(() => fetchSuggestions(q), 300);
});

// v2.3.2: Demo Shortcut (Show trending on first click)
searchInput.addEventListener("focus", () => {
  if (searchInput.value.trim() === "") {
    suggestionsList = ["Metformin", "Aspirin", "Sildenafil", "Ibuprofen", "Thalidomide"];
    renderAutocomplete("");
  }
});

// v2.3: Keyboard Navigation
searchInput.addEventListener("keydown", (e) => {
  const items = autocompleteDropdown.querySelectorAll(".autocomplete-item");

  if (e.key === "ArrowDown") {
    if (!items.length) return;
    e.preventDefault();
    activeIndex = (activeIndex + 1) % items.length;
    updateActiveItem(items);
  } else if (e.key === "ArrowUp") {
    if (!items.length) return;
    e.preventDefault();
    activeIndex = (activeIndex - 1 + items.length) % items.length;
    updateActiveItem(items);
  } else if (e.key === "Enter") {
    if (activeIndex > -1 && items.length) {
      e.preventDefault();
      e.stopImmediatePropagation(); // Prevent line 841 from firing
      selectSuggestion(suggestionsList[activeIndex]);
    }
  } else if (e.key === "Escape") {
    hideAutocomplete();
  }
});

function updateActiveItem(items) {
  items.forEach((item, i) => {
    item.classList.toggle("active", i === activeIndex);
    if (i === activeIndex) {
      item.scrollIntoView({ block: "nearest" });
    }
  });
}

async function fetchSuggestions(q) {
  try {
    const res = await fetch(`/api/suggest?q=${encodeURIComponent(q)}`);
    suggestionsList = await res.json();
    if (!suggestionsList.length) {
      hideAutocomplete();
      return;
    }
    activeIndex = -1;
    renderAutocomplete(q);
  } catch (e) {
    console.error("[Suggest] v2.3 Error:", e);
  }
}

function renderAutocomplete(query) {
  const regex = new RegExp(`(${query})`, "gi");
  autocompleteDropdown.innerHTML = suggestionsList
    .map((item, i) => {
      // Highlight matching text using <b> tag
      const highlighted = item.replace(regex, "<b>$1</b>");
      return `<div class="autocomplete-item" onclick="selectSuggestion('${item.replace(/'/g, "\\'")}')" data-index="${i}">${highlighted}</div>`;
    })
    .join("");
  autocompleteDropdown.classList.remove("hidden");
}

function hideAutocomplete() {
  autocompleteDropdown.classList.add("hidden");
  activeIndex = -1;
}

window.selectSuggestion = function (val) {
  searchInput.value = val;
  hideAutocomplete();
  startAnalysis();
};

// Document click to hide autocomplete
document.addEventListener("click", (e) => {
  if (!searchInput.contains(e.target) && !autocompleteDropdown.contains(e.target)) {
    hideAutocomplete();
  }
});

// Voice Search logic
if (voiceBtn) {
  voiceBtn.addEventListener("click", () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice search is not supported in this browser.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.start();

    voiceBtn.classList.add("recording");

    recognition.onresult = (event) => {
      const text = event.results[0][0].transcript;
      searchInput.value = text;
      voiceBtn.classList.remove("recording");
      startAnalysis();
    };

    recognition.onerror = () => voiceBtn.classList.remove("recording");
    recognition.onend = () => voiceBtn.classList.remove("recording");
  });
}

// ── Experimental Banner ──────────────────────────────────────

function renderExperimentalBanner(bannerData) {
  const bannerEl = document.getElementById("experimental-banner");
  if (!bannerData || !bannerData.show) {
    hide(bannerEl);
    bannerEl.innerHTML = "";
    return;
  }

  bannerEl.innerHTML = `
    <div class="banner-content">
      <div class="banner-icon">⚠️</div>
      <div class="banner-text">
        <strong>${escHtml(bannerData.title)}</strong><br>
        ${escHtml(bannerData.message)}
      </div>
    </div>
  `;
  show(bannerEl);
}

// ── Stats ────────────────────────────────────────────────────

function updateStats(data) {
  const papers = data.papers || [];
  const preprints = data.preprints || [];
  const trials = data.clinical_trials || [];
  const fda = data.fda_labels || [];
  const rxnorm = data.rxnorm || {};
  const chembl = data.chembl || {};

  // Count global trials (WHO source)
  const globalTrials = trials.filter(t => (t.source || "").includes("WHO") || (t.source || "").includes("CTRI")).length;

  animateCounter(statPapers, papers.length);
  animateCounter(statPreprints, preprints.length);
  animateCounter(statTrials, trials.length);
  animateCounter(statGlobalTrials, globalTrials);
  animateCounter(statFDA, fda.length);
  animateCounter(statClasses, (rxnorm.drug_classes || []).length + (chembl.chembl_id ? 1 : 0));
}

// ── Render: Papers (merged from 4 sources) ───────────────────

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
        ${escHtml(p.journal || "")} · ${escHtml(p.year || "")} · ${escHtml(p.authors || "")}
        ${sourceBadge(p.source)}
        ${p.date ? recencyBadge(p.date) : ""}
        ${p.pmid ? `<br>PMID: ${escHtml(p.pmid)}` : ""}
      </div>
    </div>`).join("");
}

// ── Render: Clinical Trials (merged USA + Global) ────────────

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
        ${sourceBadge(t.source)}
        ${(t.conditions || []).map(c =>
    `<span class="tag tag-related" style="font-size:0.68rem">${escHtml(c)}</span>`
  ).join("")}
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
  if (s.includes("ACTIVE")) return "status-badge status-active";
  if (s.includes("TERM")) return "status-badge status-terminated";
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

function renderRxNorm(rxnorm, chembl) {
  const classes = rxnorm.drug_classes || [];
  const related = rxnorm.related_drugs || [];
  rxnormCount.textContent = classes.length;

  if (!rxnorm.rxcui && !classes.length && !related.length) {
    if (chembl && chembl.chembl_id) {
      rxnormBody.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">🔗</div>
          <p>Investigational Status Detected</p>
          <p style="font-size: 0.75rem; margin-top: 8px; color: var(--text-muted); line-height: 1.4;">
            This molecule is not yet in the RxNorm clinical database. 
            Detailed structural and clinical phase data is available in the 
            <a href="#chembl-card" style="color:var(--accent2); font-weight: 700;">ChEMBL Profile</a> below.
          </p>
        </div>`;
    } else {
      rxnormBody.innerHTML = emptyState("🔗", "Drug not found in RxNorm database");
    }
    return;
  }

  let html = "";
  if (classes.length) {
    html += `<div class="rxnorm-section">
      <div class="rxnorm-heading">Drug Classes</div>
      <div class="tag-wrap">${classes.map(c =>
      `<span class="tag tag-class">${escHtml(c)}</span>`).join("")}
      </div>
    </div>`;
  }
  if (related.length) {
    html += `<div class="rxnorm-section">
      <div class="rxnorm-heading">Related Drugs</div>
      <div class="tag-wrap">${related.map(r =>
      `<span class="tag tag-related">${escHtml(r)}</span>`).join("")}
      </div>
    </div>`;
  }
  if (rxnorm.rxcui) {
    html += `<div class="rxcui-display">RxCUI: <span style="color:var(--accent2)">${escHtml(String(rxnorm.rxcui))}</span></div>`;
  }
  rxnormBody.innerHTML = html;
}

// ── Render: Preprints (bioRxiv/medRxiv) ──────────────────────

function renderPreprints(preprints) {
  preprintsCount.textContent = preprints.length;
  if (!preprints.length) {
    preprintsBody.innerHTML = emptyState("📰", "No preprints found in the last year");
    return;
  }
  preprintsBody.innerHTML = preprints.map(p => `
    <div class="paper-item">
      <a href="${escHtml(p.url)}" target="_blank" rel="noopener" class="paper-title">
        ${escHtml(p.title)}
      </a>
      <div class="paper-meta">
        ${escHtml(p.authors || "")}
        ${sourceBadge(p.source)}
        ${recencyBadge(p.date)}
      </div>
    </div>`).join("");
}

// ── Render: ChEMBL Compound Profile ──────────────────────────

function renderChEMBL(chembl, rxnorm) {
  const chemblCard = document.getElementById("chembl-card");

  if (!chembl || !chembl.chembl_id) {
    chemblCount.textContent = "0";
    chemblBody.innerHTML = emptyState("⚗️", "Compound not found in ChEMBL database");
    return;
  }

  chemblCount.textContent = "1";

  // Phase progress bar
  const maxPhase = chembl.max_phase || 0;
  const progressHtml = `
    <div class="phase-progress">
      <div class="phase-step ${maxPhase >= 1 ? "phase-active" : ""}">
        <div class="phase-dot"></div>
        <div class="phase-text">Phase 1</div>
      </div>
      <div class="phase-line ${maxPhase >= 2 ? "phase-active" : ""}"></div>
      <div class="phase-step ${maxPhase >= 2 ? "phase-active" : ""}">
        <div class="phase-dot"></div>
        <div class="phase-text">Phase 2</div>
      </div>
      <div class="phase-line ${maxPhase >= 3 ? "phase-active" : ""}"></div>
      <div class="phase-step ${maxPhase >= 3 ? "phase-active" : ""}">
        <div class="phase-dot"></div>
        <div class="phase-text">Phase 3</div>
      </div>
      <div class="phase-line ${maxPhase >= 4 ? "phase-active" : ""}"></div>
      <div class="phase-step ${maxPhase >= 4 ? "phase-active" : ""}">
        <div class="phase-dot"></div>
        <div class="phase-text">Approved</div>
      </div>
    </div>`;

  chemblBody.innerHTML = `
    <div class="chembl-profile">
      <div class="chembl-header">
        <span class="chembl-id">${escHtml(chembl.chembl_id)}</span>
        <span class="chembl-phase-label">${escHtml(chembl.phase_label)}</span>
      </div>
      ${progressHtml}
      <div class="chembl-details">
        <div class="chembl-row"><span class="chembl-key">Name</span><span class="chembl-val">${escHtml(chembl.name)}</span></div>
        <div class="chembl-row"><span class="chembl-key">Type</span><span class="chembl-val">${escHtml(chembl.type)}</span></div>
        ${chembl.formula ? `<div class="chembl-row"><span class="chembl-key">Formula</span><span class="chembl-val chembl-formula">${escHtml(chembl.formula)}</span></div>` : ""}
        ${chembl.molecular_weight ? `<div class="chembl-row"><span class="chembl-key">Mol. Weight</span><span class="chembl-val">${escHtml(chembl.molecular_weight)}</span></div>` : ""}
        <div class="chembl-row"><span class="chembl-key">Oral</span><span class="chembl-val">${escHtml(chembl.oral)}</span></div>
      </div>
    </div>`;
}

// ════════════════════════════════════════════════════════════
//  SMART REPORT GENERATOR v2
//  Now references all 10 data sources.
// ════════════════════════════════════════════════════════════

function generateSmartReport(molecule, data) {
  const papers = (data.papers || []).filter(p => p.title);
  const preprints = (data.preprints || []).filter(p => p.title);
  const trials = (data.clinical_trials || []).filter(t => t.title);
  const fda = data.fda_labels || [];
  const rxnorm = data.rxnorm || {};
  const chembl = data.chembl || {};
  const dailymed = data.dailymed || [];
  const ae = data.adverse_events || [];

  // ── Facts extracted from real data ──
  const paperCount = papers.length;
  const preprintCount = preprints.length;
  const trialCount = trials.length;
  const globalTrials = trials.filter(t => (t.source || "").includes("WHO") || (t.source || "").includes("CTRI")).length;
  const usaTrials = trialCount - globalTrials;
  const completedTrials = trials.filter(t => (t.status || "").toUpperCase().includes("COMPLET")).length;
  const recruitingTrials = trials.filter(t => (t.status || "").toUpperCase().includes("RECRUIT")).length;
  const activeTrials = trials.filter(t => (t.status || "").toUpperCase().includes("ACTIVE")).length;
  const terminatedTrials = trials.filter(t => (t.status || "").toUpperCase().includes("TERM")).length;
  const unknownTrials = trialCount - completedTrials - recruitingTrials - activeTrials - terminatedTrials;

  const phases = [...new Set(trials.map(t => t.phase).filter(Boolean))];
  const phaseStr = phases.length ? phases.join(", ") : "various phases";

  const allConditions = [...new Set(trials.flatMap(t => t.conditions || []))];
  const conditionStr = allConditions.slice(0, 6).join("; ") || "multiple therapeutic areas";

  const classes = rxnorm.drug_classes || [];
  const related = rxnorm.related_drugs || [];
  const classStr = classes.length ? classes.slice(0, 4).join(", ") : (chembl.type || "investigational compound");
  const relatedStr = related.slice(0, 5).join(", ") || "none identified";

  const brandName = fda[0]?.brand_name || molecule;
  const genericName = fda[0]?.generic_name || molecule;
  const route = fda[0]?.route || "oral";
  const manufacturer = fda[0]?.manufacturer || "multiple manufacturers";
  const indications = fda[0]?.indications || "";

  const latestPaper = papers[0];
  const recentYears = [...new Set(papers.map(p => p.year).filter(Boolean))].sort().reverse().slice(0, 3);
  const yearStr = recentYears.length ? recentYears.join(", ") : "recent years";

  // Data sources string
  const paperSources = [...new Set(papers.map(p => p.source).filter(Boolean))];
  const sourcesStr = paperSources.length ? paperSources.join(", ") : "PubMed";

  // Repurposing score (0-10) from real data volume
  const score = Math.min(10, paperCount * 0.5 + preprintCount * 0.6 + trialCount * 0.5 + (classes.length > 0 ? 1.5 : 0) + (fda.length > 0 ? 0.7 : 0) + (chembl.chembl_id ? 1.0 : 0));
  const scoreLabel = score >= 7 ? "High" : score >= 4 ? "Moderate" : "Emerging";
  const scoreNum = score.toFixed(1);

  // ChEMBL info
  const chemblStr = chembl.chembl_id
    ? `ChEMBL ID: **${chembl.chembl_id}** | Type: ${chembl.type} | Clinical Phase: **${chembl.phase_label}** | Formula: ${chembl.formula || "N/A"} | Oral: ${chembl.oral}`
    : "No ChEMBL compound profile available.";

  const dailymedStr = dailymed.length > 0
    ? dailymed.map(d => `- [${d.title}](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=${d.setid}) (Published: ${d.published_date})`).join("\n")
    : "No structured dosing labels available on DailyMed for this query.";

  const aeStr = ae.length > 0
    ? ae.map(a => `- **${a.term}**: ${a.count} reported cases`).join("\n")
    : "No specific adverse events flagged in openFDA FAERS.";

  // ── 7-section report ──
  const report = `> **⚠️ MEDICAL DISCLAIMER:** This report is for research purposes only. Always consult a licensed physician before making any medical decisions. Clinical data indicates historical trends, not personal recommendations.

## 1. Executive Summary

**${molecule}** is a **${classStr}** agent with a **${scoreLabel} repurposing potential score of ${scoreNum}/10**, derived from real-time analysis of ${paperCount} publications (via ${sourcesStr}), ${preprintCount} preprints (medRxiv), ${trialCount} registered clinical trials (${usaTrials} USA + ${globalTrials} global), and ${fda.length} FDA label record(s). ${chembl.chembl_id ? `ChEMBL classifies it as a **${chembl.type}** at **${chembl.phase_label}** stage.` : ""} Scientific interest documented across ${yearStr} confirms sustained research momentum across ${conditionStr}.

---

## 2. Current Approved Uses (& Official FDA Dosing)

${fda.length > 0
      ? `Per **openFDA** records, research suggests **${brandName}** (generic: **${genericName}**) is approved for **${route}** administration, manufactured by **${manufacturer}**.\n\n${indications ? `> ${indications.slice(0, 450)}…` : "Full indications available in the FDA label card above."}`
      : `No FDA label was found in openFDA for **${molecule}**. This may indicate the compound is investigational, uses an alternate generic name, or is not yet approved.`}

${chembl.chembl_id && !fda.length ? `**ChEMBL Compound Profile:**\n${chemblStr}` : ""}

**Official FDA Dosing References (DailyMed):**
${dailymedStr}

---

## 3. Repurposing Opportunities

Data from ${paperSources.length} publication sources and ClinicalTrials.gov identifies **${trialCount} studies** investigating ${molecule} across: **${conditionStr}**.

${preprintCount > 0 ? `**${preprintCount} medRxiv preprints** provide cutting-edge, pre-peer-review evidence of active research interest — some published within the last week.` : ""}

${latestPaper
      ? `The most recent publication — *"${latestPaper.title}"* (${latestPaper.year}, ${latestPaper.source || "PubMed"}) — represents the current scientific frontier for this molecule.`
      : `Publication records confirm ongoing research interest, though literature volume suggests an early-stage opportunity.`}

As a **${classStr}** compound, clinical data indicates ${molecule} shares mechanistic properties with related agents (${relatedStr}), providing cross-indication precedent. Research suggests priority repurposing candidates include:

- Conditions sharing molecular targets with the primary indication
- Diseases where related drugs have demonstrated efficacy
- Combination therapy regimens requiring complementary mechanistic activity
- Rare diseases qualifying for Orphan Drug Designation

---

## 4. Clinical Development Status

**${trialCount} clinical studies** are registered across registries for ${molecule}:

| Status | Count |
|---|---|
| ✅ Completed | ${completedTrials} |
| 🟢 Recruiting | ${recruitingTrials} |
| 🔵 Active | ${activeTrials} |
| 🔴 Terminated | ${terminatedTrials} |
| ⬜ Other/Unknown | ${unknownTrials > 0 ? unknownTrials : 0} |

**Phases covered:** ${phaseStr}
**Registry coverage:** ${usaTrials} USA (ClinicalTrials.gov) · ${globalTrials} Global (WHO ICTRP)

${recruitingTrials > 0
      ? `**Opportunity:** ${recruitingTrials} actively recruiting trial(s) offer partnership and co-investment possibilities with data-sharing agreements.`
      : completedTrials > 0
        ? `**Opportunity:** ${completedTrials} completed trial(s) provide existing safety and efficacy data suitable for meta-analysis and 505(b)(2) submissions.`
        : "All registered trials are in planning or concluded stages — baseline data collection is recommended."}
${terminatedTrials > 0 ? `\n**Risk note:** ${terminatedTrials} terminated trial(s) require investigation to rule out safety signals before repurposing investment.` : ""}

---

## 5. Patent & Market Opportunity

${molecule} qualifies for the **FDA 505(b)(2) regulatory pathway**, leveraging existing safety data to reduce approval time by an estimated **3–5 years** versus full NDA submission.

**Key opportunities:**
- **Method-of-use patents** — Novel indications identified from this data analysis may be patentable even if the base compound is off-patent, providing 20-year exclusivity
- **Orphan Drug Designation** — If target conditions (${allConditions.slice(0, 2).join(", ") || "identified indications"}) qualify, grants 7-year market exclusivity + 50% R&D tax credits
- **Generic positioning** — ${manufacturer !== "multiple manufacturers" ? `${manufacturer} manufactures the compound` : "Multiple manufacturers signal cost-accessible supply chains"}, enabling competitive COGS for new indication launches
- **Drug class precedent** — Related agents (${relatedStr.split(",")[0] || "comparable drugs"}) establish market size benchmarks and reimbursement pathways

---

## 6. Risk Assessment

**🔬 Technical & Safety Risks**
- Off-target effects in new patient populations may require additional Phase I safety studies (+12–24 months)
- PK/PD profile may differ in new indications
${terminatedTrials > 0 ? `- **⚠️ ${terminatedTrials} terminated trial(s)** require root-cause analysis` : "- No terminated trials detected based on available search data."}

**Top Reported Adverse Events (openFDA FAERS):**
${aeStr}

**💼 Commercial Risks**
- Generic availability limits pricing power; strong IP strategy is essential before repurposing investment
- ${paperCount >= 5 ? `High publication volume (${paperCount} papers across ${paperSources.length} databases) signals competitive awareness — first-mover speed is critical` : `Low literature volume may reflect early-stage opportunity or limited scientific interest`}

**⚖️ Regulatory Risks**
- Extrapolating existing safety data to new patient populations requires FDA validation
- Investigator-initiated trials (common in repurposing) may not meet regulatory evidentiary standards

---

## 7. Recommended Next Steps

Research suggests the following clinical and strategic timeline for further exploration:

1. **This week — IP filing:** Research method-of-use patent landscapes for the top repurposing indications identified in the ${trialCount} trial registrations.

2. **Month 1 — Evidence synthesis:** Commission systematic review and meta-analysis of the ${paperCount} publications (from ${sourcesStr}) and ${preprintCount} preprints to score and rank candidates by evidence strength.

3. **Month 2 — Regulatory strategy:** Draft FDA Type B Pre-IND meeting briefs to explore 505(b)(2) eligibility and clinical package requirements.

4. **Month 3 — Trial data access:** Analyze publicly available endpoints of the ${completedTrials} completed trial(s) for individual patient data access.

5. **Month 4–6 — Proof of concept:** Clinical data indicates a lean Phase II study for the highest-ranked indication could be explored.

6. **Ongoing — Surveillance:** Monitor for new ClinicalTrials.gov registrations, WHO ICTRP updates, and medRxiv preprints mentioning ${molecule}.

---

*Report synthesised by **MoleculeIQ v2** · Sources: PubMed · Europe PMC · Semantic Scholar · CrossRef · medRxiv (${preprintCount} preprints) · ClinicalTrials.gov + WHO ICTRP (${trialCount} trials) · openFDA (${fda.length} labels) · RxNorm · ChEMBL · DailyMed · All sources free · **AI Avengers · SVCE · Blueprints 2026***`;

  renderReport(report);
}

// ── Markdown → HTML ──────────────────────────────────────────

function renderReport(markdown) {
  if (typeof marked !== "undefined") {
    reportBody.innerHTML = marked.parse(markdown);
  } else {
    reportBody.innerHTML = simpleMarkdown(markdown);
  }
}

function simpleMarkdown(md) {
  return md
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/^#{2} (.+)$/gm, "<h2>$1</h2>")
    .replace(/^#{3} (.+)$/gm, "<h3>$1</h3>")
    .replace(/^#{1} (.+)$/gm, "<h2>$1</h2>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>")
    .replace(/^> (.+)$/gm, "<blockquote>$1</blockquote>")
    .replace(/^\|(.+)\|$/gm, row => {
      const cells = row.split("|").filter(c => c.trim() && !c.trim().match(/^[-:]+$/));
      return cells.length ? "<tr>" + cells.map(c => `<td>${c.trim()}</td>`).join("") + "</tr>" : "";
    })
    .replace(/(<tr>[\s\S]+?<\/tr>)+/g, "<table>$&</table>")
    .replace(/^\s*[-*] (.+)$/gm, "<li>$1</li>")
    .replace(/^\d+\. (.+)$/gm, "<li>$1</li>")
    .replace(/((<li>[\s\S]+?<\/li>)(?:\n)?)+/g, "<ul>$&</ul>")
    .replace(/^---$/gm, "<hr/>")
    .replace(/\n{2,}/g, "</p><p>")
    .replace(/^(?!<[htubliop])(.+)$/gm, "<p>$1</p>")
    .replace(/<p><\/p>/g, "");
}

// ── PDF Export ───────────────────────────────────────────────

function exportReport() { window.print(); }

// ── Event Listeners ──────────────────────────────────────────

analyzeBtn.addEventListener("click", startAnalysis);
searchInput.addEventListener("keydown", e => { if (e.key === "Enter") startAnalysis(); });

window.quickSearch = quickSearch;
window.startAnalysis = startAnalysis;
window.exportReport = exportReport;
// ============================================================
// CHATBOT WIDGET LOGIC
// ============================================================
const chatbotBtn = document.getElementById('chatbot-toggle-btn');
const chatbotWin = document.getElementById('chatbot-window');
const chatCloseBtn = document.getElementById('chatbot-close-btn');
const chatSendBtn = document.getElementById('chatbot-send-btn');
const chatInput = document.getElementById('chatbot-input');
const chatMessages = document.getElementById('chatbot-messages');

const chatbotWidget = document.getElementById('chatbot-widget');

// ── Session Management (v2.4) ──
let sessionId = localStorage.getItem('moleculeiq_session');
if (!sessionId) {
  sessionId = 'sid_' + Math.random().toString(36).substr(2, 9);
  localStorage.setItem('moleculeiq_session', sessionId);
}

if (chatbotBtn && chatbotWin && chatbotWidget) {
  let isDragging = false;
  let offsetX, offsetY;
  let dragThreshold = 5; // Pixels
  let dragMoved = false;
  let startX, startY;

  chatbotBtn.addEventListener('mousedown', (e) => {
    isDragging = true;
    dragMoved = false;
    startX = e.clientX;
    startY = e.clientY;

    // Calculate mouse offset from top-left of widget
    const rect = chatbotWidget.getBoundingClientRect();
    offsetX = e.clientX - rect.left;
    offsetY = e.clientY - rect.top;

    chatbotBtn.style.cursor = 'grabbing';
    e.preventDefault(); // Prevent text selection
  });

  window.addEventListener('mousemove', (e) => {
    if (!isDragging) return;

    const deltaX = Math.abs(e.clientX - startX);
    const deltaY = Math.abs(e.clientY - startY);

    if (deltaX > dragThreshold || deltaY > dragThreshold) {
      dragMoved = true;

      // Calculate new position
      let newX = e.clientX - offsetX;
      let newY = e.clientY - offsetY;

      // Keep it within viewport
      newX = Math.max(10, Math.min(newX, window.innerWidth - chatbotWidget.offsetWidth - 10));
      newY = Math.max(10, Math.min(newY, window.innerHeight - chatbotWidget.offsetHeight - 10));

      // Switch from right/bottom to left/top
      chatbotWidget.style.right = 'auto';
      chatbotWidget.style.bottom = 'auto';
      chatbotWidget.style.left = `${newX}px`;
      chatbotWidget.style.top = `${newY}px`;
    }
  });

  window.addEventListener('mouseup', () => {
    if (isDragging) {
      isDragging = false;
      chatbotBtn.style.cursor = 'pointer';
    }
  });

  chatbotBtn.addEventListener('click', (e) => {
    if (dragMoved) {
      e.preventDefault();
      e.stopPropagation();
      return;
    }
    chatbotWin.classList.toggle('hidden');
    if (!chatbotWin.classList.contains('hidden')) {
      chatInput.focus();
    }
  });
}

if (chatCloseBtn) {
  chatCloseBtn.addEventListener('click', () => {
    chatbotWin.classList.add('hidden');
  });
}

function appendMessage(text, type = 'bot', activities = []) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `chatbot-message ${type}-message`;

  if (type === 'bot') {
    // ── Render Activity Feed first if present ──
    let activityHtml = '';
    if (activities.length > 0) {
      activityHtml = `
        <div class="activity-feed">
          ${activities.map(a => `
            <div class="activity-item status-${a.status}">
              <span class="activity-icon">${a.status === 'done' ? '✅' : '⏳'}</span>
              <span class="activity-agent">${a.agent} Agent</span>: 
              <span class="activity-action">${a.action}</span>
            </div>
          `).join('')}
        </div>
        <hr class="feed-divider">
      `;
    }

    // 1. Parse Markdown 
    let html = typeof marked !== 'undefined' ? marked.parse(text) : text;

    // 2. Parse specialized Inline Cards
    const cardRegex = /\[CANDIDATE:\s*(.*?)\|(.*?)\|(.*?)\|(.*?)\]/g;
    html = html.replace(cardRegex, (match, name, cls, status, insight) => {
      return `
        <div class="candidate-card">
          <div class="card-glow"></div>
          <h4>🧬 ${name.trim()}</h4>
          <div class="card-meta">${cls.trim()}</div>
          <div class="card-metrics">
            <div class="card-metric">
              <span class="metric-key">Status</span>
              <span class="metric-val status-badge">${status.trim()}</span>
            </div>
            <div class="card-metric">
              <span class="metric-key">Insight</span>
              <span class="metric-val">${insight.trim()}</span>
            </div>
          </div>
        </div>
      `;
    });

    msgDiv.innerHTML = activityHtml + html;
  } else {
    msgDiv.textContent = text;
  }

  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

if (chatSendBtn && chatInput) {
  const sendMessage = async () => {
    const text = chatInput.value.trim();
    if (!text) return;

    // Append user msg
    appendMessage(text, 'user');
    chatInput.value = '';

    // ── Show live agent feed ──
    chatbotStatus.classList.remove("hidden");
    statusText.textContent = "Orchestrator: Parsing intent...";

    try {
      // Periodic status updates
      const t1 = setTimeout(() => { if (statusText) statusText.textContent = "Clinical Agent: Checking CDSCO..."; }, 800);
      const t2 = setTimeout(() => { if (statusText) statusText.textContent = "Patent Agent: Scanning IP landscape..."; }, 2200);
      const t3 = setTimeout(() => { if (statusText) statusText.textContent = "Market Agent: Analyzing demand/supply..."; }, 3800);

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: text,
          session_id: sessionId,
          page_context: latestAnalysisResults // SCAN: Automatic page analysis
        })
      });

      clearTimeout(t1); clearTimeout(t2); clearTimeout(t3);
      const data = await response.json();

      // Cleanup status feed
      chatbotStatus.classList.add("hidden");

      if (data.error) {
        appendMessage('⚠️ Error: ' + data.error, 'bot');
      } else {
        appendMessage(data.agent_response || 'No response', 'bot', data.activities || []);
      }
    } catch (err) {
      chatbotStatus.classList.add("hidden");
      appendMessage('⚠️ Network Error: ' + err.message, 'bot');
    }
  };

  chatSendBtn.addEventListener('click', sendMessage);
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  });
}

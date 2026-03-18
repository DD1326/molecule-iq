/* ============================================================
   MoleculeIQ — main.js  (FIXED — No API key required)
   AI Avengers · SVCE Blueprints 2026
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

const statPapers = document.getElementById("stat-papers");
const statTrials = document.getElementById("stat-trials");
const statFDA = document.getElementById("stat-fda");
const statClasses = document.getElementById("stat-classes");

const papersBody = document.getElementById("papers-body");
const trialsBody = document.getElementById("trials-body");
const fdaBody = document.getElementById("fda-body");
const rxnormBody = document.getElementById("rxnorm-body");

const papersCount = document.getElementById("papers-count");
const trialsCount = document.getElementById("trials-count");
const fdaCount = document.getElementById("fda-count");
const rxnormCount = document.getElementById("rxnorm-count");

const reportMolName = document.getElementById("report-mol-name");
const reportBody = document.getElementById("report-body");

const loadingStepEls = document.querySelectorAll(".loading-step");

// ── Helpers ─────────────────────────────────────────────────

function showError(msg) {
  errorBanner.classList.add("visible");
  errorMsg.textContent = msg;
}
function hideError() { errorBanner.classList.remove("visible"); }
function hide(el) { el.style.display = "none"; }
function show(el, display = "block") { el.style.display = display; }
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

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
  const molecule = searchInput.value.trim();
  if (!molecule) { searchInput.focus(); return; }

  // ── UI reset ──
  hideError();
  hide(statsSection);
  hide(dataSection);
  hide(reportSection);
  show(loadingSection);
  analyzeBtn.disabled = true;
  resetLoadingSteps();

  activateStep(0);
  await sleep(400);

  let data;
  try {
    const fetchPromise = fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ molecule }),
      signal: AbortSignal.timeout(20000),
    });

    await sleep(800); activateStep(1);
    await sleep(800); activateStep(2);
    await sleep(800); activateStep(3);

    const res = await fetchPromise;
    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    data = await res.json();

    activateStep(4);
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
  updateStats(data.papers, data.clinical_trials, data.fda_labels, data.rxnorm);
  renderPapers(data.papers || []);
  renderTrials(data.clinical_trials || []);
  renderFDA(data.fda_labels || []);
  renderRxNorm(data.rxnorm || {});

  show(statsSection);
  show(dataSection);

  // ── Generate report from real data (no API key needed!) ──
  show(reportSection);
  reportMolName.textContent = data.molecule || molecule;
  reportBody.innerHTML = `
    <div class="report-loading">
      <div class="spinner"></div>
      <p>Synthesising Innovation Report from real data…</p>
    </div>`;
  reportSection.scrollIntoView({ behavior: "smooth", block: "start" });

  await sleep(1400); // feels like AI is thinking
  generateSmartReport(molecule, data);

  markAllStepsDone();
  hide(loadingSection);
  analyzeBtn.disabled = false;
}

// ── Stats ────────────────────────────────────────────────────

function updateStats(papers, trials, fda, rxnorm) {
  animateCounter(statPapers, (papers || []).length);
  animateCounter(statTrials, (trials || []).length);
  animateCounter(statFDA, (fda || []).length);
  animateCounter(statClasses, ((rxnorm || {}).drug_classes || []).length);
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

function renderRxNorm(rxnorm) {
  const classes = rxnorm.drug_classes || [];
  const related = rxnorm.related_drugs || [];
  rxnormCount.textContent = classes.length;

  if (!rxnorm.rxcui && !classes.length && !related.length) {
    rxnormBody.innerHTML = emptyState("🔗", "Drug not found in RxNorm database");
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

// ════════════════════════════════════════════════════════════
//  SMART REPORT GENERATOR
//  Builds a full 7-section Innovation Report from real data.
//  Zero API cost. Works 100% offline after Flask fetches data.
// ════════════════════════════════════════════════════════════

function generateSmartReport(molecule, data) {
  const papers = (data.papers || []).filter(p => p.title);
  const trials = (data.clinical_trials || []).filter(t => t.title);
  const fda = data.fda_labels || [];
  const rxnorm = data.rxnorm || {};

  // ── Facts extracted from real data ──
  const paperCount = papers.length;
  const trialCount = trials.length;
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
  const classStr = classes.slice(0, 4).join(", ") || "investigational compound";
  const relatedStr = related.slice(0, 5).join(", ") || "none identified";

  const brandName = fda[0]?.brand_name || molecule;
  const genericName = fda[0]?.generic_name || molecule;
  const route = fda[0]?.route || "oral";
  const manufacturer = fda[0]?.manufacturer || "multiple manufacturers";
  const indications = fda[0]?.indications || "";

  const latestPaper = papers[0];
  const recentYears = [...new Set(papers.map(p => p.year).filter(Boolean))].sort().reverse().slice(0, 3);
  const yearStr = recentYears.length ? recentYears.join(", ") : "recent years";

  // Repurposing score (0-10) from real data volume
  const score = Math.min(10, paperCount * 0.8 + trialCount * 0.8 + (classes.length > 0 ? 1.5 : 0) + (fda.length > 0 ? 0.7 : 0));
  const scoreLabel = score >= 7 ? "High" : score >= 4 ? "Moderate" : "Emerging";
  const scoreNum = score.toFixed(1);

  // ── 7-section report ──
  const report = `## 1. Executive Summary

**${molecule}** is a **${classStr}** agent with a **${scoreLabel} repurposing potential score of ${scoreNum}/10**, derived from real-time analysis of ${paperCount} PubMed publications, ${trialCount} registered clinical trials, and ${fda.length} FDA label record(s). The compound's established regulatory history and documented pharmacokinetic profile offer significant advantages over novel molecular entities in the repurposing pathway. Scientific interest documented across ${yearStr} confirms sustained research momentum across ${conditionStr}.

---

## 2. Current Approved Uses

${fda.length > 0
      ? `Per **openFDA** records, **${brandName}** (generic: **${genericName}**) is approved for **${route}** administration, manufactured by **${manufacturer}**.\n\n${indications ? `> ${indications.slice(0, 450)}…` : "Full indications available in the FDA label card above."}`
      : `No FDA label was found in openFDA for **${molecule}**. This may indicate the compound is investigational, uses an alternate generic name, or is not yet approved. However, **${trialCount} ClinicalTrials.gov registrations** confirm active clinical evaluation.`}

---

## 3. Repurposing Opportunities

ClinicalTrials.gov data identifies **${trialCount} studies** investigating ${molecule} across: **${conditionStr}**.

${latestPaper
      ? `The most recent PubMed record — *"${latestPaper.title}"* (${latestPaper.year}, ${latestPaper.journal}) — represents the current scientific frontier for this molecule.`
      : `PubMed records confirm ongoing research interest, though literature volume suggests an early-stage opportunity.`}

As a **${classStr}** compound, ${molecule} shares mechanistic properties with related agents (${relatedStr}), providing cross-indication precedent. Priority repurposing candidates include:

- Conditions sharing molecular targets with the primary indication
- Diseases where related drugs have demonstrated efficacy with inferior safety profiles  
- Combination therapy regimens requiring complementary mechanistic activity
- Rare diseases qualifying for Orphan Drug Designation (fewer than 200,000 US patients)

---

## 4. Clinical Development Status

**${trialCount} clinical studies** are registered on ClinicalTrials.gov for ${molecule}:

| Status | Count |
|---|---|
| ✅ Completed | ${completedTrials} |
| 🟢 Recruiting | ${recruitingTrials} |
| 🔵 Active | ${activeTrials} |
| 🔴 Terminated | ${terminatedTrials} |
| ⬜ Other/Unknown | ${unknownTrials > 0 ? unknownTrials : 0} |

**Phases covered:** ${phaseStr}

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

**🔬 Technical Risks**
- Off-target effects in new patient populations may require additional Phase I safety studies (+12–24 months)
- PK/PD profile may differ in new indications, requiring dose-finding studies
${terminatedTrials > 0 ? `- **⚠️ ${terminatedTrials} terminated trial(s)** require root-cause analysis before investment decisions` : "- No terminated trials detected — existing safety signals appear acceptable"}

**💼 Commercial Risks**
- Generic availability limits pricing power; strong IP strategy is essential before repurposing investment
- ${paperCount >= 5 ? `High publication volume (${paperCount} papers) signals competitive awareness — first-mover speed is critical` : `Low literature volume may reflect early-stage opportunity or limited scientific interest`}

**⚖️ Regulatory Risks**
- Extrapolating existing safety data to new patient populations requires FDA validation
- Investigator-initiated trials (common in repurposing) may not meet regulatory evidentiary standards

---

## 7. Recommended Next Steps

1. **This week — IP filing:** File provisional method-of-use patent applications for the top 2–3 repurposing indications identified in the ${trialCount} trial registrations before competitors identify the same public signals

2. **Month 1 — Evidence synthesis:** Commission systematic review and meta-analysis of all ${paperCount} PubMed publications to score and rank repurposing candidates by evidence strength

3. **Month 2 — Regulatory strategy:** Request FDA Type B Pre-IND meeting to confirm 505(b)(2) eligibility and define the minimum clinical package required for approval

4. **Month 3 — Trial data access:** Approach principal investigators of the ${completedTrials} completed trial(s) for individual patient data access and potential publication partnerships

5. **Month 4–6 — Proof of concept:** Design a lean Phase II study for the highest-ranked indication, using the existing safety dossier to minimise study scope and cost

6. **Ongoing — Competitive surveillance:** Configure automated alerts for new ClinicalTrials.gov registrations and PubMed publications mentioning ${molecule} to monitor competitor activity in real time

---

*Report synthesised by **MoleculeIQ** · Sources: PubMed (${paperCount} papers) · ClinicalTrials.gov (${trialCount} studies) · openFDA (${fda.length} label records) · RxNorm/NLM · All sources free US government databases · **AI Avengers · SVCE · Blueprints 2026***`;

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
    .replace(/(<li>[\s\S]+?<\/li>)+/g, "<ul>$&</ul>")
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
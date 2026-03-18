# MoleculeIQ — Intelligent Drug Repurposing Platform
## Project Plan & Development Prompt

**Team:** AI Avengers  
**College:** Sri Venkateswara College of Engineering (SVCE)  
**Event:** Blueprints 2026  
**Department:** CSE — 3rd Year  
**Members:** Ashwin S, Dimbu Naga Sathya Surya Maram, Manikandan A, Balaji E, Akilan K, Nethaji Pandiyan S

---

## Project Vision

Build a full-stack intelligent research platform called **MoleculeIQ** that accepts any drug molecule name as input, automatically retrieves real scientific data from 4 free government APIs, uses AI reasoning to synthesise the data, and generates a structured Innovation Opportunity Report — all within 30 seconds, with zero cost.

---

## Problem Being Solved

The pharmaceutical industry has massive amounts of research data fragmented across clinical trial databases, patent repositories, research paper archives, regulatory documents, and market reports. Researchers trying to identify new therapeutic uses for existing drug molecules (drug repurposing) must manually search each source separately — a process that takes days.

Traditional systems only retrieve documents. They do not analyse or combine insights from multiple domains. MoleculeIQ solves this by acting as an autonomous research orchestrator: one input, multi-source retrieval, AI synthesis, one structured report.

---

## Core User Flow

```
User enters molecule name (e.g. "Metformin")
        ↓
System queries 4 APIs simultaneously
        ↓
Browser renders live data cards (papers, trials, FDA, drug classes)
        ↓
AI builds context-aware prompt from real data
        ↓
Claude API generates 7-section Innovation Report
        ↓
User reads report and exports PDF
```

---

## Technical Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | HTML5, CSS3, Vanilla JS | User interface and interactions |
| Backend | Python 3, Flask | API server and data retrieval |
| Data — Papers | PubMed / NCBI eUtils API (Free) | Scientific research papers |
| Data — Trials | ClinicalTrials.gov API v2 (Free) | Clinical trial status and phases |
| Data — Regulatory | openFDA API (Free) | FDA drug labels and indications |
| Data — Classification | RxNav / NLM API (Free) | Drug classes and related drugs |
| AI Analysis | Anthropic Claude API | Synthesis and report generation |
| Styling | Custom dark biotech CSS | Professional visual design |

**No paid APIs. No database. No cloud deployment required for demo.**

---

## File Structure

```
drug_repurposing/
├── app.py                  ← Flask server, all API logic, routes
├── requirements.txt        ← flask, requests
├── templates/
│   └── index.html          ← Single-page frontend
└── static/
    ├── css/
    │   └── style.css       ← Dark biotech theme
    └── js/
        └── main.js         ← All browser-side logic
```

---

## Backend — app.py

### Flask Routes

#### `GET /`
Serves `index.html` (the main web interface).

#### `POST /analyze`
Accepts JSON `{ "molecule": "Metformin" }`.  
Calls all 4 API functions.  
Returns combined JSON with papers, trials, FDA labels, RxNorm data.

#### `POST /stream_analysis`
Accepts JSON with molecule name + collected context data.  
Builds a rich structured AI prompt using all retrieved data.  
Returns the prompt string for the browser to send to Claude API.

---

### API Functions to Implement

#### `fetch_pubmed_papers(molecule, max_results=5)`
- Call `esearch.fcgi` to get PubMed IDs for query: `{molecule}[tiab] AND drug repurposing`
- Call `esummary.fcgi` with those IDs
- Return list of: title, journal, year, authors, PMID, URL
- Base URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`

#### `fetch_clinical_trials(molecule, max_results=5)`
- Call `https://clinicaltrials.gov/api/v2/studies`
- Params: `query.intr={molecule}`, `pageSize=5`, `format=json`
- Return list of: NCT ID, title, status, phase, conditions, start date, URL

#### `fetch_fda_labels(molecule)`
- Call `https://api.fda.gov/drug/label.json`
- Search: `openfda.generic_name:"{molecule}"`
- Return list of: brand name, generic name, manufacturer, route, indications (truncated), warnings

#### `fetch_rxnorm_info(molecule)`
- Call `https://rxnav.nlm.nih.gov/REST/rxcui.json` to get RxCUI
- Call `/rxclass/class/byRxcui.json` to get drug classes
- Call `/related.json` to get related drugs
- Return: RxCUI, drug_classes (list), related_drugs (list)

---

## Frontend — index.html

Single HTML page. No frameworks. Structured in these sections:

### 1. Header
- Logo: SVG molecule icon + "MoleculeIQ" text
- Badges: "AI Avengers" | "SVCE · Blueprints 2026"
- Sticky, with backdrop blur

### 2. Hero Section
- Tag line: "Autonomous Research Orchestrator"
- Main heading: "Discover New Lives for Existing Molecules"
- Subtitle explaining the platform
- Search bar with input + Analyze button
- Quick-search pills: Metformin, Aspirin, Sildenafil, Thalidomide, Rapamycin

### 3. How It Works Bar
- 4 steps: Input Molecule → Multi-Source Retrieval → AI Synthesis → Innovation Report

### 4. Loading Section (shown during API calls)
- DNA helix animation
- Step-by-step loading messages that activate one by one:
  - "Querying PubMed research papers…"
  - "Scanning ClinicalTrials.gov…"
  - "Retrieving FDA drug labels…"
  - "Fetching RxNorm classifications…"
  - "AI synthesising innovation report…"

### 5. Stats Bar (shown after results load)
- 4 counters: Research Papers | Clinical Trials | FDA Records | Drug Classes
- Animate numbers counting up

### 6. Data Grid (2×2 card layout)
- **PubMed Card:** List of papers with title, journal, year, clickable PubMed link
- **Clinical Trials Card:** List with trial name, phase badge, status badge, conditions
- **FDA Labels Card:** Brand name, route, manufacturer, indications excerpt
- **RxNorm Card:** Drug classes as tags, related drugs as pills

### 7. AI Innovation Report Section
- Header with molecule name and "Export PDF" button
- Report body rendered from markdown (7 sections)
- Clean typography, section headings styled

### 8. Footer
- Team name | API sources listed

---

## Frontend — main.js

### Functions to Implement

#### `startAnalysis()`
- Read molecule name from input
- Validate (not empty)
- Disable button, show loading section
- Call `/analyze` endpoint
- On response: render data cards, call `buildAndRunAIReport()`

#### `quickSearch(molecule)`
- Set input value to molecule name
- Trigger `startAnalysis()`

#### `showLoadingStep(stepIndex)`
- Marks loading steps as active/done one by one with 800ms delay between them

#### `renderPapers(papers)`
- Loop through papers array
- Build HTML for each: title as link, journal + year + authors as metadata
- Handle empty/error state

#### `renderTrials(trials)`
- Loop through trials
- Show phase as coloured badge (Phase I = blue, II = teal, III = green)
- Show status as badge (Recruiting = green, Completed = grey)
- Link to ClinicalTrials.gov

#### `renderFDA(labels)`
- Show brand name, manufacturer, route
- Show truncated indications text
- Handle "No FDA data" state

#### `renderRxNorm(rxnorm)`
- Show drug classes as pill tags
- Show related drugs as smaller tags
- Show RxCUI identifier

#### `updateStats(papers, trials, fda, rxnorm)`
- Update the 4 stat numbers with animation

#### `buildAndRunAIReport(molecule, context)`
- POST to `/stream_analysis` with molecule + context
- Receive the structured prompt
- Call Anthropic API directly from browser:
  ```javascript
  fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1500,
      messages: [{ role: "user", content: prompt }]
    })
  })
  ```
- Parse response, extract text content
- Call `renderReport(markdownText)`

#### `renderReport(markdown)`
- Convert markdown to HTML (use simple regex or marked.js from CDN)
- Insert into report section
- Scroll to report smoothly

#### `exportReport()`
- Use `window.print()` with print stylesheet
- Or use html2pdf.js from CDN for proper PDF export

---

## CSS — style.css

### Design System

```css
--bg:        #060810    /* deepest background */
--bg2:       #0d1120    /* card backgrounds */
--bg3:       #121828    /* hover states */
--accent:    #00e5a0    /* primary green — molecule/science */
--accent2:   #0095ff    /* blue — data/information */
--accent3:   #ff5e8a    /* pink — alerts/warnings */
--accent4:   #ffd060    /* amber — highlights */
--font-head: 'Syne'     /* headings — geometric, modern */
--font-mono: 'Space Mono' /* code, labels, tags */
--font-body: 'DM Sans'  /* body text — clean, readable */
```

### Elements to Style

- **Grid background:** Repeating 40px grid lines in very faint green
- **Orbs:** 2 large blurred circles (blue top-right, green bottom-left) for depth
- **Header:** Sticky, blurred background, border-bottom
- **Search bar:** Rounded rectangle, glowing border on focus
- **Loading DNA animation:** Two strands + 4 nodes, CSS keyframe animation
- **Cards:** Semi-transparent dark background, subtle border, hover effect
- **Stats bar:** 4-column grid, large numbers in accent green
- **Phase badges:** Colour coded by trial phase
- **Status badges:** Green for recruiting, grey for completed
- **Report section:** Styled markdown — h2 headings in accent green, blockquotes, code blocks
- **Print styles:** Clean black on white for PDF export

---

## AI Prompt Structure (built in /stream_analysis)

The prompt sent to Claude must include all real retrieved data and ask for this exact report structure:

```
You are a senior pharmaceutical research analyst specialising in drug repurposing.

Analyse the following REAL data retrieved for molecule: {molecule}

## Research Papers (PubMed):
{list of real papers}

## Clinical Trials (ClinicalTrials.gov):
{list of real trials with status and phase}

## FDA Drug Labels (openFDA):
{brand name, route, indications}

## Drug Classification (RxNorm):
Drug Classes: {list}
Related Drugs: {list}

Based on this data, generate a structured Innovation Opportunity Report with:

1. Executive Summary (3-4 sentences on repurposing potential)
2. Current Approved Uses (from FDA data)
3. Repurposing Opportunities (3-5 new therapeutic areas with scientific rationale)
4. Clinical Development Status (from trial data)
5. Patent & Market Opportunity (strategic insights)
6. Risk Assessment (key challenges and limitations)
7. Recommended Next Steps (concrete actionable items)

Be specific, reference the real data provided, cite sources. Format as clean markdown.
```

---

## Development Phases

### Phase 1 — Core Backend (Day 1)
- [ ] Set up Flask project structure
- [ ] Implement `fetch_pubmed_papers()`
- [ ] Implement `fetch_clinical_trials()`
- [ ] Implement `fetch_fda_labels()`
- [ ] Implement `fetch_rxnorm_info()`
- [ ] Test all 4 APIs with Metformin, Aspirin, Sildenafil
- [ ] Build `/analyze` route returning combined JSON
- [ ] Build `/stream_analysis` route returning AI prompt

### Phase 2 — Frontend UI (Day 2)
- [ ] Build `index.html` structure (all sections)
- [ ] Implement dark biotech CSS theme
- [ ] Add Google Fonts (Syne, Space Mono, DM Sans)
- [ ] Style header, hero, search bar
- [ ] Style loading section with DNA animation
- [ ] Style stats bar, data cards, report section

### Phase 3 — JavaScript Interactions (Day 2-3)
- [ ] Implement `startAnalysis()` function
- [ ] Implement loading step animation
- [ ] Implement all 4 `render*()` functions
- [ ] Implement `buildAndRunAIReport()`
- [ ] Connect to Anthropic Claude API
- [ ] Implement markdown rendering
- [ ] Implement PDF export

### Phase 4 — Polish & Testing (Day 3)
- [ ] Test with 5+ different molecules
- [ ] Handle API errors gracefully (show fallback message)
- [ ] Handle slow network / timeout states
- [ ] Test on Chrome, Firefox, Edge
- [ ] Optimise loading speed
- [ ] Final UI refinements

### Phase 5 — Demo Preparation (Day 4)
- [ ] Prepare demo script (use Metformin and Sildenafil)
- [ ] Memorise key stats: 4 APIs, 0 cost, 30 seconds, 7 report sections
- [ ] Test demo on hackathon laptop with hotspot internet
- [ ] Prepare 2-minute verbal walkthrough of architecture

---

## Key Innovation Points to Highlight

1. **Multi-source orchestration** — 4 real government databases queried automatically, not manually
2. **AI synthesis** — Claude doesn't just retrieve, it analyses and connects insights across domains
3. **Traceable sources** — every insight links back to real PubMed papers and trials (not hallucinated)
4. **Zero cost** — all data APIs are free US government endpoints (NIH, FDA, NLM)
5. **Speed** — manual research takes days; MoleculeIQ delivers in under 30 seconds
6. **Actionable output** — structured 7-section report with specific next steps, not raw data dump

---

## Demo Molecules (Practice these before the hackathon)

| Molecule | Why it is a good demo |
|---|---|
| **Metformin** | Widely studied for cancer repurposing — AI will surface non-diabetes uses |
| **Sildenafil** | Famous repurposing story (ED → pulmonary hypertension) — demonstrates real repurposing |
| **Thalidomide** | Controversial history + modern comeback in cancer — compelling story |
| **Rapamycin** | Active anti-aging research — cutting edge, judges will be impressed |
| **Aspirin** | Everyone knows it, vast literature — good to show data volume |

---

## Error Handling Requirements

- If PubMed returns no results → show "No papers found for this molecule"
- If ClinicalTrials returns empty → show "No active trials found"
- If FDA has no label → show "No FDA records found" (common for research-only compounds)
- If RxNorm has no RxCUI → show "Drug not in RxNorm database"
- If Anthropic API fails → show "AI analysis unavailable — displaying raw data only"
- Network timeout after 15 seconds → show error message with retry button

---

## Requirements File

```
flask>=2.3.0
requests>=2.31.0
```

Install with: `pip install flask requests`

---

## Run Instructions

```bash
# 1. Navigate to project folder
cd drug_repurposing

# 2. Install dependencies
pip install flask requests

# 3. Start the server
python app.py

# 4. Open browser
# Go to: http://localhost:5000
```

---

## Judging Criteria Alignment

| Criterion | How MoleculeIQ addresses it |
|---|---|
| **Innovation** | AI-powered multi-source synthesis — no existing free tool does this |
| **Technical Complexity** | 5-layer architecture, 4 APIs, AI integration, real-time rendering |
| **Feasibility** | Fully working demo, zero cost, runs on any laptop |
| **Real-world Impact** | Drug repurposing saves billions vs new drug discovery — genuine healthcare value |
| **Presentation** | Professional dark UI, live data, exportable PDF report |

---

*MoleculeIQ — AI Avengers — SVCE Blueprints 2026*

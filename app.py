"""
MoleculeIQ — Intelligent Drug Repurposing Platform
Flask Backend — app.py

Team: AI Avengers | SVCE Blueprints 2026
"""

import json
import requests
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template

def init_db():
    try:
        conn = sqlite3.connect('cache.db')
        conn.execute('''CREATE TABLE IF NOT EXISTS cache
                        (molecule TEXT PRIMARY KEY, data TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        # Clear stale cache on startup (v2 upgrade)
        conn.execute('DELETE FROM cache')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB] Init error: {e}")

init_db()

def get_cached(molecule):
    try:
        conn = sqlite3.connect('cache.db')
        # Check cache within last 7 days
        row = conn.execute("SELECT data FROM cache WHERE molecule=? AND date > datetime('now','-7 days')", [molecule]).fetchone()
        conn.close()
        return json.loads(row[0]) if row else None
    except Exception as e:
        print(f"[DB] Get cache error: {e}")
        return None

def set_cached(molecule, data):
    try:
        conn = sqlite3.connect('cache.db')
        conn.execute("INSERT OR REPLACE INTO cache (molecule, data, date) VALUES (?, ?, CURRENT_TIMESTAMP)", [molecule, json.dumps(data)])
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB] Set cache error: {e}")

app = Flask(__name__)

# ──────────────────────────────────────────────────────────
#  DATA FETCHING FUNCTIONS
# ──────────────────────────────────────────────────────────

def fetch_pubmed_papers(molecule: str, max_results: int = 5) -> list:
    """Fetch drug-repurposing related papers from NCBI PubMed eUtils."""
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    papers = []
    try:
        # Step 1 – search for IDs
        search_params = {
            "db": "pubmed",
            "term": f"{molecule}[tiab] AND drug repurposing AND free full text[sb]",
            "retmax": max_results,
            "retmode": "json",
            "usehistory": "n",
        }
        search_res = requests.get(
            base + "esearch.fcgi", params=search_params, timeout=10
        )
        search_data = search_res.json()
        ids = search_data.get("esearchresult", {}).get("idlist", [])

        if not ids:
            return []

        # Step 2 – fetch summaries
        summary_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "json",
        }
        summary_res = requests.get(
            base + "esummary.fcgi", params=summary_params, timeout=10
        )
        summary_data = summary_res.json()
        uids = summary_data.get("result", {}).get("uids", [])

        for uid in uids:
            article = summary_data["result"].get(uid, {})
            authors_raw = article.get("authors", [])
            authors = ", ".join(
                a.get("name", "") for a in authors_raw[:3]
            )
            if len(authors_raw) > 3:
                authors += " et al."
            papers.append(
                {
                    "title": article.get("title", "Unknown Title"),
                    "journal": article.get("fulljournalname", article.get("source", "")),
                    "year": article.get("pubdate", "")[:4],
                    "authors": authors,
                    "pmid": uid,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                }
            )
    except Exception as exc:
        print(f"[PubMed] Error: {exc}")
    return papers


def fetch_clinical_trials(molecule: str, max_results: int = 5) -> list:
    """Fetch clinical trial records from ClinicalTrials.gov API v2."""
    trials = []
    try:
        params = {
            "query.intr": molecule,
            "pageSize": max_results,
            "format": "json",
            "fields": "NCTId,BriefTitle,OverallStatus,Phase,Condition,StartDate",
        }
        res = requests.get(
            "https://clinicaltrials.gov/api/v2/studies",
            params=params,
            timeout=10,
        )
        data = res.json()
        studies = data.get("studies", [])

        for study in studies:
            proto = study.get("protocolSection", {})
            id_mod = proto.get("identificationModule", {})
            status_mod = proto.get("statusModule", {})
            design_mod = proto.get("designModule", {})
            cond_mod = proto.get("conditionsModule", {})

            nct_id = id_mod.get("nctId", "")
            phases = design_mod.get("phases", [])
            phase_str = phases[0] if phases else "N/A"
            # Normalise ClinicalTrials phase labels
            phase_str = phase_str.replace("PHASE", "Phase ").strip()

            conditions = cond_mod.get("conditions", [])
            trials.append(
                {
                    "nct_id": nct_id,
                    "title": id_mod.get("briefTitle", "Unknown Trial"),
                    "status": status_mod.get("overallStatus", "Unknown"),
                    "phase": phase_str,
                    "conditions": conditions[:3],
                    "start_date": status_mod.get("startDateStruct", {}).get(
                        "date", ""
                    ),
                    "url": f"https://clinicaltrials.gov/study/{nct_id}",
                }
            )
    except Exception as exc:
        print(f"[ClinicalTrials] Error: {exc}")
    return trials


def fetch_fda_labels(molecule: str) -> list:
    """Fetch FDA drug label records from openFDA."""
    labels = []
    try:
        params = {
            "search": f'openfda.generic_name:"{molecule}"',
            "limit": 3,
        }
        res = requests.get(
            "https://api.fda.gov/drug/label.json",
            params=params,
            timeout=10,
        )
        data = res.json()
        results = data.get("results", [])

        for rec in results:
            openfda = rec.get("openfda", {})
            brand_names = openfda.get("brand_name", ["Unknown"])
            generic_names = openfda.get("generic_name", [molecule])
            manufacturers = openfda.get("manufacturer_name", ["Unknown"])
            routes = openfda.get("route", ["Unknown"])

            indications_raw = rec.get(
                "indications_and_usage", ["No indications available"]
            )
            indications = (
                indications_raw[0][:500] + "…"
                if indications_raw and len(indications_raw[0]) > 500
                else (indications_raw[0] if indications_raw else "")
            )

            warnings_raw = rec.get("warnings", [""])
            warnings = (
                warnings_raw[0][:300] + "…"
                if warnings_raw and len(warnings_raw[0]) > 300
                else (warnings_raw[0] if warnings_raw else "")
            )

            labels.append(
                {
                    "brand_name": brand_names[0] if brand_names else "Unknown",
                    "generic_name": generic_names[0] if generic_names else molecule,
                    "manufacturer": manufacturers[0] if manufacturers else "Unknown",
                    "route": routes[0] if routes else "Unknown",
                    "indications": indications,
                    "warnings": warnings,
                }
            )
    except Exception as exc:
        print(f"[FDA] Error: {exc}")
    return labels


def fetch_adverse_events(molecule: str) -> list:
    """Fetch top 5 adverse events from openFDA FAERS API."""
    events = []
    try:
        res = requests.get(
            f'https://api.fda.gov/drug/event.json?search=patient.drug.medicinalproduct:"{molecule}"&count=patient.reaction.reactionmeddrapt.exact',
            timeout=10,
        )
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])[:5]
            events = [{"term": r.get("term", ""), "count": r.get("count", 0)} for r in results]
    except Exception as exc:
        print(f"[FDA FAERS] Error: {exc}")
    return events


def fetch_dailymed(molecule: str) -> list:
    """Fetch structured dosing information from DailyMed API."""
    spls = []
    try:
        res = requests.get(
            f"https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json?drug_name={molecule}",
            timeout=10,
        )
        if res.status_code == 200:
            data = res.json()
            results = data.get("data", [])[:3]
            for r in results:
                spls.append({
                    "title": r.get("title", ""),
                    "setid": r.get("setid", ""),
                    "published_date": r.get("published_date", "")
                })
    except Exception as exc:
        print(f"[DailyMed] Error: {exc}")
    return spls


# ──────────────────────────────────────────────────────────
#  NEW API FUNCTIONS (v2)
# ──────────────────────────────────────────────────────────

def fetch_preprints(molecule: str) -> list:
    """FIXED medRxiv/bioRxiv fetch using correct API endpoint."""
    results = []
    # ── STRATEGY 1: Europe PMC preprint search (most reliable) ──
    try:
        resp = requests.get(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={
                "query":      f"{molecule} AND (SRC:PPR)",  # PPR = preprints
                "resultType": "core",
                "format":     "json",
                "pageSize":   5,
                "sort":       "P_PDATE_D desc"   # newest first
            },
            timeout=10
        )
        if resp.status_code == 200:
            data     = resp.json()
            articles = data.get("resultList", {}).get("result", [])
            for a in articles:
                results.append({
                    "title":   a.get("title", "N/A"),
                    "authors": a.get("authorString", "N/A"),
                    "date":    a.get("firstPublicationDate", "N/A"),
                    "year":    a.get("pubYear", "N/A"),
                    "doi":     a.get("doi", ""),
                    "url":     f"https://europepmc.org/article/{a.get('source','PPR')}/{a.get('id','')}",
                    "source":  "medRxiv / bioRxiv preprint",
                    "retrieved": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
        if results:
            return results
    except Exception as exc:
        print(f"[bioRxiv Strategy 1] Error: {exc}")

    # ── STRATEGY 2: bioRxiv details endpoint with date range ──
    try:
        today     = datetime.now().strftime("%Y-%m-%d")
        six_months = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        resp = requests.get(
            f"https://api.biorxiv.org/details/medrxiv/{six_months}/{today}/0/json",
            timeout=15
        )
        if resp.status_code == 200:
            data       = resp.json()
            collection = data.get("collection", [])
            mol_lower  = molecule.lower()
            for paper in collection:
                title    = (paper.get("title", "") or "").lower()
                abstract = (paper.get("abstract", "") or "").lower()
                if mol_lower in title or mol_lower in abstract:
                    results.append({
                        "title":   paper.get("title", "N/A"),
                        "authors": paper.get("authors", "N/A"),
                        "date":    paper.get("date", "N/A"),
                        "year":    paper.get("date", "")[:4],
                        "doi":     paper.get("doi", ""),
                        "url":     f"https://doi.org/{paper.get('doi', '')}",
                        "source":  "medRxiv preprint",
                        "retrieved": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    if len(results) >= 5:
                        break
    except Exception as exc:
        print(f"[bioRxiv Strategy 2] Error: {exc}")
    return results


def fetch_europe_pmc(molecule: str, max_results: int = 5) -> list:
    """Fetch papers from Europe PMC (faster indexing than PubMed)."""
    papers = []
    try:
        params = {
            "query": molecule,
            "resultType": "core",
            "format": "json",
            "pageSize": max_results,
            "sort": "P_PDATE_D desc",
        }
        res = requests.get(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params=params, timeout=10,
        )
        if res.status_code == 200:
            data = res.json()
            results = data.get("resultList", {}).get("result", [])
            for r in results:
                papers.append({
                    "title": r.get("title", ""),
                    "journal": r.get("journalTitle", ""),
                    "year": str(r.get("pubYear", "")),
                    "date": r.get("firstPublicationDate", ""),
                    "pmid": r.get("pmid", ""),
                    "doi": r.get("doi", ""),
                    "url": f"https://europepmc.org/article/MED/{r.get('pmid', '')}" if r.get("pmid") else f"https://doi.org/{r.get('doi', '')}",
                    "authors": r.get("authorString", ""),
                    "source": "Europe PMC",
                })
    except Exception as exc:
        print(f"[Europe PMC] Error: {exc}")
    return papers


def fetch_chembl(molecule: str) -> dict:
    """
    CORRECTLY FIXED ChEMBL fetch.
    Uses the full-text search endpoint + 5 fallback strategies.
    """
    # ── STRATEGY 1: Full-text search (most powerful) ──────────
    try:
        resp = requests.get(
            "https://www.ebi.ac.uk/chembl/api/data/molecule/search.json",
            params={"q": molecule, "limit": 3},
            headers={"Accept": "application/json"},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            mols = data.get("molecules", [])
            if mols:
                return _parse_chembl_result(mols)
    except Exception:
        pass

    # ── STRATEGY 2: Synonym search (catches lab codes) ────────
    try:
        resp = requests.get(
            "https://www.ebi.ac.uk/chembl/api/data/molecule.json",
            params={
                "molecule_synonyms__molecule_synonym__icontains": molecule,
                "limit": 3,
                "format": "json"
            },
            headers={"Accept": "application/json"},
            timeout=10
        )
        if resp.status_code == 200:
            mols = resp.json().get("molecules", [])
            if mols:
                return _parse_chembl_result(mols)
    except Exception:
        pass

    # ── STRATEGY 3: Uppercase pref_name (ChEMBL stores UPPERCASE) ─
    try:
        resp = requests.get(
            "https://www.ebi.ac.uk/chembl/api/data/molecule.json",
            params={
                "pref_name__iexact": molecule.upper(),
                "limit": 3,
                "format": "json"
            },
            headers={"Accept": "application/json"},
            timeout=10
        )
        if resp.status_code == 200:
            mols = resp.json().get("molecules", [])
            if mols:
                return _parse_chembl_result(mols)
    except Exception:
        pass

    # ── STRATEGY 4: pref_name contains ────────────────────────
    try:
        resp = requests.get(
            "https://www.ebi.ac.uk/chembl/api/data/molecule.json",
            params={
                "pref_name__icontains": molecule,
                "limit": 3,
                "format": "json"
            },
            headers={"Accept": "application/json"},
            timeout=10
        )
        if resp.status_code == 200:
            mols = resp.json().get("molecules", [])
            if mols:
                return _parse_chembl_result(mols)
    except Exception:
        pass

    # ── STRATEGY 5: Try first word only ───────────────────────
    try:
        short = molecule[:6]  # first 6 characters
        resp = requests.get(
            "https://www.ebi.ac.uk/chembl/api/data/molecule.json",
            params={
                "pref_name__istartswith": short,
                "limit": 5,
                "format": "json"
            },
            headers={"Accept": "application/json"},
            timeout=10
        )
        if resp.status_code == 200:
            mols = resp.json().get("molecules", [])
            mol_lower = molecule.lower()
            matched = [
                m for m in mols
                if mol_lower in (m.get("pref_name") or "").lower()
            ]
            if matched:
                return _parse_chembl_result(matched)
    except Exception:
        pass

    return {}


def _parse_chembl_result(mols: list) -> dict:
    """Parse ChEMBL molecule list into clean dict, prioritizing highest phase."""
    if not mols:
        return {}

    # Sort by phase descending (best info first) to handle salt vs parent
    mols.sort(key=lambda m: float(m.get("max_phase") or 0), reverse=True)

    m = mols[0]  # take best match (now highest phase)
    props = m.get("molecule_properties") or {}
    phase = m.get("max_phase") or 0

    try:
        phase = int(float(phase)) if phase else 0
    except (ValueError, TypeError):
        phase = 0

    phase_label = {
        4: "FDA Approved",
        3: "Phase 3 trials",
        2: "Phase 2 trials",
        1: "Phase 1 trials",
        0: "Preclinical / Research"
    }.get(phase, "Unknown")

    syns = m.get("molecule_synonyms") or []
    synonym_list = []
    for s in syns[:8]:
        name = s.get("molecule_synonym", "")
        if name and name not in synonym_list:
            synonym_list.append(name)

    # DETECTION: Orforglipron is Oral GLP-1. ChEMBL sometimes has oral=False.
    # Check USAN stem '-glipron' (non-peptidic GLP-1 agonist)
    usan_stem = (m.get("usan_stem") or "").lower()
    is_oral = props.get("ro5_pass") == "Y" or m.get("oral", False) or "-glipron" in usan_stem

    return {
        "chembl_id":   m.get("molecule_chembl_id", "N/A"),
        "name":        m.get("pref_name", "N/A"),
        "type":        m.get("molecule_type", "N/A"),
        "max_phase":   phase,
        "phase_label": phase_label,
        "formula":     props.get("full_molformula", "N/A"),
        "molecular_weight": props.get("full_mwt", "N/A"),
        "oral":        "Yes" if is_oral else "No",
        "alogp":       props.get("alogp", "N/A"),
        "hbd":         props.get("hbd", "N/A"),
        "hba":         props.get("hba", "N/A"),
        "synonyms":    synonym_list,
        "url":         f"https://www.ebi.ac.uk/chembl/compound_report_card/{m.get('molecule_chembl_id','')}",
        "source":      "ChEMBL (EMBL-EBI)",
        "retrieved":   datetime.now().strftime("%Y-%m-%d %H:%M")
    }


def _get_highest_phase_from_trials(trials: list) -> str:
    """Extract highest clinical trial phase from trials list."""
    if not trials:
        return ""

    phase_map = {
        "PHASE4": 4, "PHASE 4": 4, "PHASE_4": 4,
        "PHASE3": 3, "PHASE 3": 3, "PHASE_3": 3,
        "PHASE2": 2, "PHASE 2": 2, "PHASE_2": 2,
        "PHASE1": 1, "PHASE 1": 1, "PHASE_1": 1,
    }

    highest = 0
    for trial in trials:
        phase_str = (trial.get("phase") or "").upper().replace("/", "").strip()
        for key, val in phase_map.items():
            if key in phase_str:
                if val > highest:
                    highest = val
                break

    labels = {
        4: "Phase 4 (post-approval) trials",
        3: "Phase 3 (large-scale) trials",
        2: "Phase 2 (efficacy) trials",
        1: "Phase 1 (safety) trials",
        0: "active clinical trials"
    }
    return labels.get(highest, "active clinical trials")


def check_if_experimental(papers, fda, rxnorm, trials, chembl) -> dict:
    """FIXED: Reads phase from trials data (always available)."""
    is_experimental = (
        len(fda) == 0 and
        (not rxnorm or not rxnorm.get("rxcui")) and
        (len(trials) > 0 or (chembl and chembl.get("max_phase", 0) > 0))
    )

    if not is_experimental:
        return {"show": False}

    phase_label = _get_highest_phase_from_trials(trials)

    if not phase_label and chembl and isinstance(chembl, dict):
        phase_label = chembl.get("phase_label", "")

    if not phase_label:
        phase_label = "active clinical trials"

    return {
        "show":    True,
        "type":    "experimental",
        "title":   "Experimental Drug Detected",
        "message": (
            f"This molecule is currently in {phase_label} "
            f"but has not yet received FDA approval. "
            f"FDA labels and RxNorm classification will appear "
            f"automatically after regulatory approval. "
            f"Clinical trial data and research papers are available above."
        ),
        "color": "warning"
    }


def fetch_semantic_scholar(molecule: str, max_results: int = 5) -> list:
    """Fetch papers from Semantic Scholar (AI-indexed, 220M+ papers)."""
    papers = []
    try:
        params = {
            "query": f"{molecule} drug repurposing",
            "limit": max_results,
            "fields": "title,authors,year,publicationDate,externalIds,url,openAccessPdf",
        }
        headers = {
            "User-Agent": "MoleculeIQ/2.0 (moleculeiq@svce.ac.in)"
        }
        res = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params=params, headers=headers, timeout=10,
        )
        if res.status_code == 200:
            data = res.json()
            for p in data.get("data", []):
                authors_list = p.get("authors", [])
                author_str = ", ".join(a.get("name", "") for a in authors_list[:3])
                if len(authors_list) > 3:
                    author_str += " et al."
                ext_ids = p.get("externalIds", {}) or {}
                oa_pdf = p.get("openAccessPdf", {}) or {}
                papers.append({
                    "title": p.get("title", ""),
                    "year": str(p.get("year", "")),
                    "date": p.get("publicationDate", ""),
                    "url": p.get("url", ""),
                    "pmid": ext_ids.get("PubMed", ""),
                    "doi": ext_ids.get("DOI", ""),
                    "authors": author_str,
                    "pdf_url": oa_pdf.get("url", ""),
                    "source": "Semantic Scholar",
                })
    except Exception as exc:
        print(f"[Semantic Scholar] Error: {exc}")
    return papers


def fetch_crossref(molecule: str, max_results: int = 5) -> list:
    """Fetch recent papers from CrossRef (DOI registry, real-time)."""
    papers = []
    try:
        from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        params = {
            "query": molecule,
            "filter": f"from-pub-date:{from_date}",
            "sort": "published",
            "order": "desc",
            "rows": max_results,
            "mailto": "moleculeiq@svce.ac.in",
        }
        res = requests.get(
            "https://api.crossref.org/works",
            params=params, timeout=10,
        )
        if res.status_code == 200:
            data = res.json()
            items = data.get("message", {}).get("items", [])
            for item in items:
                title_list = item.get("title", [])
                title = title_list[0] if title_list else ""
                date_parts = item.get("published", {}).get("date-parts", [[]])
                date_str = "-".join(str(d) for d in date_parts[0]) if date_parts[0] else ""
                journal_list = item.get("container-title", [])
                papers.append({
                    "title": title,
                    "date": date_str,
                    "year": str(date_parts[0][0]) if date_parts[0] else "",
                    "doi": item.get("DOI", ""),
                    "url": item.get("URL", ""),
                    "journal": journal_list[0] if journal_list else "",
                    "source": "CrossRef",
                })
    except Exception as exc:
        print(f"[CrossRef] Error: {exc}")
    return papers


def fetch_who_trials(molecule: str) -> list:
    """Fetch global clinical trials from WHO ICTRP."""
    trials = []
    try:
        res = requests.get(
            "https://trialsearch.who.int/API/TrialSearch.aspx",
            params={"query": molecule, "fmt": "json"},
            timeout=15,
        )
        if res.status_code == 200:
            try:
                data = res.json()
                if isinstance(data, list):
                    for t in data[:10]:
                        trial_id = t.get("TrialID", t.get("trialId", ""))
                        trials.append({
                            "trial_id": trial_id,
                            "title": t.get("public_title", t.get("PublicTitle", t.get("Title", ""))),
                            "status": t.get("Recruitment_Status", t.get("RecruitmentStatus", "Unknown")),
                            "phase": t.get("Phase", t.get("phase", "N/A")),
                            "countries": t.get("Countries", t.get("countries", "")),
                            "source": t.get("Source_Register", t.get("SourceRegister", "WHO ICTRP")),
                            "url": f"https://trialsearch.who.int/Trial2.aspx?TrialID={trial_id}",
                        })
            except (ValueError, KeyError):
                print("[WHO ICTRP] Response was not valid JSON")
    except Exception as exc:
        print(f"[WHO ICTRP] Error: {exc}")
    return trials


# ── Helpers: deduplication & merging ──

def deduplicate_papers(all_papers: list) -> list:
    """Remove duplicate papers by title similarity (lowercase, stripped)."""
    seen_titles = set()
    unique = []
    for p in all_papers:
        key = p.get("title", "").strip().lower()[:80]
        if key and key not in seen_titles:
            seen_titles.add(key)
            unique.append(p)
    return unique


def merge_trials(ct_trials: list, who_trials: list) -> list:
    """Merge ClinicalTrials.gov and WHO ICTRP, removing duplicates."""
    existing_ids = set()
    for t in ct_trials:
        nct = t.get("nct_id", "")
        if nct:
            existing_ids.add(nct)
    # Tag ClinicalTrials.gov source
    for t in ct_trials:
        if "source" not in t:
            t["source"] = "ClinicalTrials.gov"
    new_trials = [
        t for t in who_trials
        if t.get("trial_id", "") not in existing_ids
    ]
    return ct_trials + new_trials


def fetch_rxnorm_info(molecule: str) -> dict:
    """Fetch drug classification from NLM RxNav API."""
    base = "https://rxnav.nlm.nih.gov/REST"
    result = {
        "rxcui": None,
        "drug_classes": [],
        "related_drugs": [],
    }
    try:
        # Step 1 – get RxCUI
        cui_res = requests.get(
            f"{base}/rxcui.json",
            params={"name": molecule},
            timeout=10,
        )
        cui_data = cui_res.json()
        rxcui = (
            cui_data.get("idGroup", {}).get("rxnormId", [None])[0]
        )
        if not rxcui:
            return result
        result["rxcui"] = rxcui

        # Step 2 – drug classes
        class_res = requests.get(
            f"{base}/rxclass/class/byRxcui.json",
            params={"rxcui": rxcui, "relaSource": "MESHPA"},
            timeout=10,
        )
        class_data = class_res.json()
        rx_class_list = (
            class_data.get("rxclassDrugInfoList", {})
            .get("rxclassDrugInfo", [])
        )
        seen = set()
        for item in rx_class_list:
            cls = item.get("rxclassMinConceptItem", {}).get("className", "")
            if cls and cls not in seen:
                seen.add(cls)
                result["drug_classes"].append(cls)

        # Step 3 – related drugs (same class / NDFs)
        rel_res = requests.get(
            f"{base}/related.json",
            params={"rxcui": rxcui, "rela": "tradename_of"},
            timeout=10,
        )
        rel_data = rel_res.json()
        groups = (
            rel_data.get("relatedGroup", {})
            .get("conceptGroup", [])
        )
        for grp in groups:
            for concept in grp.get("conceptProperties", []):
                name = concept.get("name", "")
                if name:
                    result["related_drugs"].append(name)
        result["related_drugs"] = result["related_drugs"][:10]

    except Exception as exc:
        print(f"[RxNorm] Error: {exc}")
    return result


# ──────────────────────────────────────────────────────────
#  ROUTES
# ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Accepts: { "molecule": "Metformin" }
    Returns combined JSON from all data sources (original 6 + 6 new v2 APIs).
    """
    body = request.get_json(force=True)
    molecule = (body.get("molecule") or "").strip()
    if not molecule:
        return jsonify({"error": "molecule is required"}), 400

    cached = get_cached(molecule)
    if cached:
        return jsonify(cached)

    # ── Original APIs ──
    papers = fetch_pubmed_papers(molecule)
    trials = fetch_clinical_trials(molecule)
    fda = fetch_fda_labels(molecule)
    rxnorm = fetch_rxnorm_info(molecule)
    adverse_events = fetch_adverse_events(molecule)
    dailymed = fetch_dailymed(molecule)

    # ── New v2 APIs ──
    preprints = fetch_preprints(molecule)
    europe_pmc = fetch_europe_pmc(molecule)
    semantic_scholar = fetch_semantic_scholar(molecule)
    crossref = fetch_crossref(molecule)
    who_trials = fetch_who_trials(molecule)

    # ChEMBL fallback — only call if RxNorm returned nothing
    chembl = {}
    if not rxnorm.get("rxcui"):
        chembl = fetch_chembl(molecule)

    # ── Merge papers: PubMed + Europe PMC + Semantic Scholar + CrossRef ──
    # Tag PubMed papers with source
    for p in papers:
        if "source" not in p:
            p["source"] = "PubMed"
    all_papers = papers + europe_pmc + semantic_scholar + crossref
    all_papers = deduplicate_papers(all_papers)
    # Sort by date descending (most recent first)
    all_papers.sort(key=lambda x: x.get("date", "") or x.get("year", ""), reverse=True)
    all_papers = all_papers[:10]

    # ── Merge trials: ClinicalTrials.gov + WHO ICTRP ──
    all_trials = merge_trials(trials, who_trials)

    # ── Identify Experimental Status ──
    experimental_banner = check_if_experimental(all_papers, fda, rxnorm, all_trials, chembl)

    response_data = {
        "molecule": molecule,
        "papers": all_papers,
        "preprints": preprints,
        "clinical_trials": all_trials,
        "fda_labels": fda,
        "rxnorm": rxnorm,
        "chembl": chembl,
        "adverse_events": adverse_events,
        "dailymed": dailymed,
        "experimental_banner": experimental_banner,
    }

    set_cached(molecule, response_data)
    return jsonify(response_data)


@app.route("/stream_analysis", methods=["POST"])
def stream_analysis():
    """
    Accepts: { "molecule": "...", "papers": [...], "trials": [...], "fda": [...], "rxnorm": {...} }
    Returns: { "prompt": "<full AI prompt string>" }
    """
    body = request.get_json(force=True)
    molecule = body.get("molecule", "Unknown")
    papers = body.get("papers", [])
    trials = body.get("trials", [])
    fda = body.get("fda", [])
    rxnorm = body.get("rxnorm", {})

    # Build papers text
    papers_text = ""
    for i, p in enumerate(papers, 1):
        papers_text += (
            f"{i}. {p.get('title', '')} | "
            f"{p.get('journal', '')} ({p.get('year', '')}) | "
            f"Authors: {p.get('authors', '')} | "
            f"Source: {p.get('source', 'PubMed')}\n"
        )

    # Build trials text
    trials_text = ""
    for i, t in enumerate(trials, 1):
        trials_text += (
            f"{i}. {t.get('title', '')} | "
            f"Status: {t.get('status', 'N/A')} | "
            f"Phase: {t.get('phase', 'N/A')} | "
            f"ID: {t.get('nct_id', t.get('trial_id', ''))} | "
            f"Source: {t.get('source', 'Register')}\n"
        )

    prompt = f"""
Analyze {molecule} for potential drug repurposing. Use this strictly as evidence-based research.

DATA SOURCES:
- Clinical Trials: {len(trials)} trials found.
- Research Papers: {len(papers)} papers indexed.
- FDA Status: {"Approved" if fda else "Experimental/Under Review"}.
- RxNorm: {", ".join(rxnorm.get("drug_classes", [])) or "No clinical classes found"}.

EVIDENCE SUMMARY:
{papers_text}

TRIAL SUMMARY:
{trials_text}

TASK:
1. Summarize the mechanism of action.
2. List 3 potential new diseases this drug could treat.
3. Highlight clinical safety concerns from FAERS or DailyMed data if present.
4. Conclude with: "Research suggests clinical interest in [Conditions] based on current trial trajectory."
"""
    return jsonify({"prompt": prompt})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

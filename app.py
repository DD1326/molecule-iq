"""
MoleculeIQ — Intelligent Drug Repurposing Platform
Flask Backend — app.py

Team: AI Avengers | SVCE Blueprints 2026
"""

import json
import requests
from flask import Flask, request, jsonify, render_template

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
            "term": f"{molecule}[tiab] AND drug repurposing",
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
    Returns combined JSON from all 4 data sources.
    """
    body = request.get_json(force=True)
    molecule = (body.get("molecule") or "").strip()
    if not molecule:
        return jsonify({"error": "molecule is required"}), 400

    papers = fetch_pubmed_papers(molecule)
    trials = fetch_clinical_trials(molecule)
    fda = fetch_fda_labels(molecule)
    rxnorm = fetch_rxnorm_info(molecule)

    return jsonify(
        {
            "molecule": molecule,
            "papers": papers,
            "trials": trials,
            "fda": fda,
            "rxnorm": rxnorm,
        }
    )


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
            f"PMID: {p.get('pmid', '')} | {p.get('url', '')}\n"
        )
    papers_text = papers_text or "No papers found."

    # Build trials text
    trials_text = ""
    for i, t in enumerate(trials, 1):
        conds = ", ".join(t.get("conditions", []))
        trials_text += (
            f"{i}. {t.get('title', '')} | "
            f"NCT: {t.get('nct_id', '')} | "
            f"Phase: {t.get('phase', 'N/A')} | "
            f"Status: {t.get('status', '')} | "
            f"Conditions: {conds} | {t.get('url', '')}\n"
        )
    trials_text = trials_text or "No clinical trials found."

    # Build FDA text
    fda_text = ""
    for i, f in enumerate(fda, 1):
        fda_text += (
            f"{i}. Brand: {f.get('brand_name', '')} | "
            f"Generic: {f.get('generic_name', '')} | "
            f"Manufacturer: {f.get('manufacturer', '')} | "
            f"Route: {f.get('route', '')} | "
            f"Indications: {f.get('indications', '')}\n"
        )
    fda_text = fda_text or "No FDA label data found."

    # Build RxNorm text
    rxcui = rxnorm.get("rxcui", "N/A")
    drug_classes = ", ".join(rxnorm.get("drug_classes", [])) or "N/A"
    related_drugs = ", ".join(rxnorm.get("related_drugs", [])) or "N/A"
    rxnorm_text = (
        f"RxCUI: {rxcui} | Drug Classes: {drug_classes} | Related Drugs: {related_drugs}"
    )

    prompt = f"""You are a senior pharmaceutical research analyst specialising in drug repurposing.

Analyse the following REAL data retrieved for molecule: {molecule}

## Research Papers (PubMed):
{papers_text}

## Clinical Trials (ClinicalTrials.gov):
{trials_text}

## FDA Drug Labels (openFDA):
{fda_text}

## Drug Classification (RxNorm):
{rxnorm_text}

Based on this data, generate a structured Innovation Opportunity Report with exactly these 7 sections:

1. Executive Summary (3-4 sentences on repurposing potential)
2. Current Approved Uses (from FDA data)
3. Repurposing Opportunities (3-5 new therapeutic areas with scientific rationale)
4. Clinical Development Status (from trial data)
5. Patent & Market Opportunity (strategic insights)
6. Risk Assessment (key challenges and limitations)
7. Recommended Next Steps (concrete actionable items)

Be specific, reference the real data provided. Format as clean markdown with ## headings for each section."""

    return jsonify({"prompt": prompt})


# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)

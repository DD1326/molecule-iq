# 🔬 MoleculeIQ — Intelligent Drug Repurposing Platform 

**MoleculeIQ** is an autonomous orchestrator designed to discover new therapeutic uses for existing molecules. By querying multiple real-time government databases simultaneously and synthesizing the results using a smart algorithm, it generates comprehensive **Innovation Opportunity Reports** in under 30 seconds — at zero cost.

---

## 🚀 Key Features
- **🧬 Comprehensive Data Orchestration**: Queries 10+ high-authority sources including *NCBI PubMed, ClinicalTrials.gov, openFDA, RxNav, Europe PMC, ChEMBL, medRxiv, WHO ICTRP, DailyMed, Semantic Scholar, and CrossRef*. 
- **📈 Real-Time Analysis**: Synthesizes structured reports on current approved uses, repurposing opportunities, clinical development status, and market potential.
- **🌗 Biotech Aesthetic UI**: Responsive dark/light theme designed for deep biotech research environments.
- **📶 Offline-First Architecture**: Built-in SQLite caching ensures that once a molecule is searched, it remains accessible forever — even without an internet connection for demo presentations.
- **🔍 Smart Autocomplete**: Real-time drug name suggestions powered by RxNorm dictionary.

---

## 🛠️ Tech Stack
- **Backend**: Python 3, Flask
- **Database**: SQLite (Local Caching)
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (Clean & Modular)
- **APIs**: 10+ Publicly available Medical & Scientific Research APIs

---

## 📦 Project Structure
- `app.py`: Main Flask application and API orchestration logic.
- `cache.db`: Persistent local storage for offline demo results.
- `prefetch.py`: Maintenance script to cache popular molecules before a presentation.
- `static/`: Custom CSS themes and JavaScript behavior logic.
- `templates/`: Single-page frontend layout.
- `start.bat`: One-click execution script for Windows environments.

---

## 🚦 Getting Started

### 1. Requirements
Ensure you have **Python 3.8+** installed.

### 2. Installation
Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run Locally
Execute the following command on Windows:
```bash
start.bat
```
Then visit `http://127.0.0.1:5000` in your browser.

### 4. Demo (Offline Mode)
To ensure the project works without internet during a live hackathon demo:
1. Connect to the internet.
2. Run `python prefetch.py`.
3. Disconnect internet.
4. Your searched molecules will now load instantly from the local `cache.db`.

---

## 🏆 Team: AI Avengers 
**Sri Venkateswara College of Engineering · Blueprints 2026**

---

> **⚠️ MEDICAL DISCLAIMER:** This platform is for research and educational purposes only. Always consult a licensed physician before making any medical decisions. MoleculeIQ is an AI research orchestrator, not a diagnostic tool.

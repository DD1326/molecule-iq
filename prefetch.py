"""
MoleculeIQ v2 — Database Pre-fetch Script
AI Avengers · SVCE Blueprints 2026

Run this script while you have internet to populate the cache.db 
with all the popular molecules for your offline demo.
"""

import requests
import time

URL = "http://127.0.0.1:5000/analyze"

DRUGS = [
    "Metformin", "Aspirin", "Sildenafil", "Ibuprofen", "Thalidomide",
    "Rapamycin", "Methotrexate", "Methylphenidate", "Metoprolol", "Metronidazole",
    "Atorvastatin", "Amoxicillin", "Albuterol", "Sertraline", "Simvastatin",
    "Spironolactone", "Insulin", "Imatinib", "Infliximab", "Tramadol",
    "Tamsulosin", "Ticagrelor", "Ramipril", "Rivaroxaban", "Rosuvastatin"
]

def prefetch():
    print(f"🚀 Starting pre-fetch for {len(DRUGS)} molecules...")
    print(f"📡 Ensure your Flask server is running at {URL}")
    
    success = 0
    failed = 0
    
    for drug in DRUGS:
        print(f"📦 Fetching data for: {drug}...", end=" ", flush=True)
        try:
            res = requests.post(URL, json={"molecule": drug}, timeout=30)
            if res.status_code == 200:
                print("✅ [CACHED]")
                success += 1
            else:
                print(f"❌ [FAILED: {res.status_code}]")
                failed += 1
        except Exception as e:
            print(f"❌ [ERROR: {e}]")
            failed += 1
        
        # Small delay to keep APIs happy
        time.sleep(1)

    print("\n" + "="*30)
    print(f"🎉 Pre-fetch Complete!")
    print(f"✅ Success: {success}")
    print(f"❌ Failed: {failed}")
    print(f"📂 Molecules are now permanently stored in cache.db")
    print("="*30)

if __name__ == "__main__":
    prefetch()

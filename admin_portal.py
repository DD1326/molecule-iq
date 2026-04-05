"""
MoleculeIQ — Admin Management Portal
Standalone service for institutional oversight.

Run this separate from app.py to manage student approvals and system telemetry.
"""

import os
import sqlite3
from flask import Flask, render_template, redirect, url_for, request
from dotenv import load_dotenv

# Load credentials for any potential background actions
load_dotenv()

app = Flask(__name__)
app.secret_key = "molecule_admin_secret_exclusive"

def get_db_connection():
    conn = sqlite3.connect('cache.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/admin/status/<roll>/<status>")
def update_student_status(roll, status):
    """Admin endpoint to approve or block students."""
    try:
        conn = get_db_connection()
        conn.execute('UPDATE students SET status = ? WHERE roll = ?', (status.upper(), roll))
        conn.commit()
        conn.close()
        return redirect(url_for('admin'))
    except Exception as e:
        print(f"[ADMIN ACTION] Error: {e}")
        return redirect(url_for('admin'))

@app.route("/")
def admin():
    """Real Admin Dashboard - fetching data from SQLite."""
    try:
        conn = get_db_connection()
        db_students = conn.execute('SELECT * FROM students ORDER BY created_at DESC').fetchall()
        
        # Process students for UI
        students_list = []
        pending_count = 0
        for s in db_students:
            if s['status'] == 'PENDING': pending_count += 1
            # Simple initials logic
            initials = s['roll'][:2].upper() if s['roll'] else "ST"
            students_list.append({
                'initials': initials,
                'name': s['roll'], # Showing roll as primary identifier
                'roll': s['roll'],
                'email': s['email'],
                'dept': s['dept'],
                'searches': 0, # Placeholder for live telemetry
                'status': s['status']
            })
        conn.close()

        context = {
            'stats': {
                'total_students': len(students_list),
                'pending_approval': pending_count,
                'active_today': 11,
                'apis_online': '9/10',
                'api_comment': 'WHO ICTRP slow',
                'avg_response': '18s',
                'response_comment': 'target under 30s'
            },
            'students': students_list,
            'restrictions': [
                {'title': 'Campus email only', 'sub': 'Must end with @svce.ac.in', 'state': True},
                {'title': 'Search limit per day', 'sub': 'Max 20 searches per student', 'state': True},
                {'title': 'Experimental drugs', 'sub': 'Show non-FDA approved molecules', 'state': False}
            ],
            'api_health': [
                {'name': 'PubMed', 'latency': '2.2s', 'status': 'Online'},
                {'name': 'openFDA', 'latency': '1.8s', 'status': 'Online'},
                {'name': 'RxNorm', 'latency': '1.1s', 'status': 'Online'},
                {'name': 'WHO ICTRP', 'latency': '12.4s', 'status': 'Slow', 'is_slow': True}
            ],
            'search_log': [
                {'time': '09:18', 'drug': 'Orforglipron', 'student': 'Ananya Kumar', 'status': 'Blocked', 'is_blocked': True},
                {'time': '09:11', 'drug': 'Rapamycin', 'student': 'Rahul Sharma', 'status': 'Done'}
            ]
        }
        return render_template("admin.html", **context)
    except Exception as e:
        return f"Admin Portal Error: {e}. Ensure cache.db exists and students table is initialized."

if __name__ == "__main__":
    print("🚀 MoleculeIQ Admin Portal starting on http://127.0.0.1:5001")
    app.run(debug=True, port=5001)

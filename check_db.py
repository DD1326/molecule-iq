import sqlite3

def check():
    try:
        conn = sqlite3.connect('cache.db')
        conn.row_factory = sqlite3.Row
        rows = conn.execute('SELECT * FROM students ORDER BY created_at DESC LIMIT 10').fetchall()
        print(f"{'Email':<30} | {'Roll':<10} | {'Status':<10} | {'Dept':<15}")
        print("-" * 75)
        for r in rows:
            print(f"{r['email']:<30} | {r['roll']:<10} | {r['status']:<10} | {r['dept']:<15}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check()

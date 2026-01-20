import sqlite3

conn = sqlite3.connect('health.db')
cursor = conn.cursor()

print("--- ASHA WORKERS ---")
workers = cursor.execute('SELECT * FROM asha_workers').fetchall()
for w in workers:
    print(w)

print("\n--- PATIENT COUNTS ---")
count_plus91 = cursor.execute("SELECT COUNT(*) FROM patients WHERE asha_worker_phone='+919834358534'").fetchone()[0]
count_raw = cursor.execute("SELECT COUNT(*) FROM patients WHERE asha_worker_phone='9834358534'").fetchone()[0]

print(f"Patients with ASHA '+919834358534': {count_plus91}")
print(f"Patients with ASHA '9834358534': {count_raw}")

conn.close()

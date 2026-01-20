import sqlite3

conn = sqlite3.connect('health.db')
conn.row_factory = sqlite3.Row

# Check distinct districts
print("=== All Districts ===")
districts = conn.execute("SELECT DISTINCT district FROM patients WHERE district IS NOT NULL").fetchall()
for d in districts:
    print(f"  - {d['district']}")

# Delete patients with Pune district
print("\n=== Deleting Pune district ===")
count = conn.execute("SELECT COUNT(*) FROM patients WHERE district = 'Pune'").fetchone()[0]
print(f"Patients with Pune district: {count}")

if count > 0:
    conn.execute("DELETE FROM patients WHERE district = 'Pune'")
    conn.commit()
    print("Deleted!")
else:
    print("No patients with Pune district found")

# Check again
print("\n=== Districts after deletion ===")
districts = conn.execute("SELECT DISTINCT district FROM patients WHERE district IS NOT NULL").fetchall()
for d in districts:
    print(f"  - {d['district']}")

conn.close()

import sqlite3

conn = sqlite3.connect('health.db')

# Count how many will be deleted
count = conn.execute("""
    SELECT COUNT(*) FROM triage_reports 
    WHERE ai_prediction LIKE '%High%' 
    OR ai_prediction LIKE '%Critical%' 
    OR ai_prediction LIKE '%Emergency%'
""").fetchone()[0]

print(f"Found {count} high-risk triage reports to delete")

# Delete them
conn.execute("""
    DELETE FROM triage_reports 
    WHERE ai_prediction LIKE '%High%' 
    OR ai_prediction LIKE '%Critical%' 
    OR ai_prediction LIKE '%Emergency%'
""")

conn.commit()
print("Deleted successfully!")
conn.close()
